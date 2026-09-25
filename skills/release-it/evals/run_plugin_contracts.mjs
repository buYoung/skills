// Usage: node run_plugin_contracts.mjs /path/to/node_modules /tmp/new-output-directory
// Executes the documented plugin examples with the real API and stock prompt implementation.
// Prompt answers and notifications are local stubs; no registry or remote is contacted.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, symlinkSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

if (process.argv.length !== 4) {
  throw new Error('Usage: node run_plugin_contracts.mjs <node_modules> <new-output-directory>');
}
const dependencies = path.resolve(process.argv[2]);
const output = path.resolve(process.argv[3]);
if (existsSync(output)) throw new Error('Use a new disposable output directory.');
mkdirSync(output, { recursive: true });
const skill = fileURLToPath(new URL('../', import.meta.url));
const reference = readFileSync(path.join(skill, 'references/custom-plugin-development.md'), 'utf8');
const blocks = [...reference.matchAll(/```js\n([\s\S]*?)```/g)].map(match => match[1]);
function exampleContaining(marker) {
  const matches = blocks.filter(block => block.includes(marker));
  assert.equal(matches.length, 1, `Expected one executable example containing ${marker}`);
  return matches[0];
}
const minimal = exampleContaining('class MyVersionPlugin extends Plugin');
const webhook = exampleContaining('class WebhookPlugin extends Plugin');
const releaseRoot = path.join(dependencies, 'release-it');
const { default: release } = await import(pathToFileURL(path.join(releaseRoot, 'lib/index.js')));
const { default: Prompt } = await import(pathToFileURL(path.join(releaseRoot, 'lib/prompt.js')));
const version = JSON.parse(readFileSync(path.join(releaseRoot, 'package.json'), 'utf8')).version;
assert.equal(version, '21.0.1', 'These internal prompt/lifecycle checks target release-it 21.0.1');
const initialCwd = process.cwd();
const initialFetch = globalThis.fetch;
const results = [];

function fixture(name, source) {
  const directory = path.join(output, name);
  mkdirSync(directory);
  symlinkSync(dependencies, path.join(directory, 'node_modules'), 'dir');
  writeFileSync(path.join(directory, 'package.json'), JSON.stringify({
    name: 'tooling-fixture', private: true, type: 'module', version: '9.9.9'
  }));
  writeFileSync(path.join(directory, 'VERSION'), '1.2.3');
  const plugin = path.join(directory, 'plugin.mjs');
  writeFileSync(plugin, source);
  return { directory, plugin };
}

function logger(events) {
  return Object.fromEntries(['log', 'info', 'warn', 'error', 'verbose', 'obtrusive', 'preview', 'exec']
    .map(level => [level, (...args) => events.push({ level, args })]));
}

const baseOptions = {
  config: false, extends: false, ci: false, increment: '1.2.4',
  git: false, npm: { publish: false }, github: false, gitlab: false
};

async function checkExample(name, source, { isDryRun = false, hasQuestion = false, answer = true } = {}) {
  const { directory, plugin } = fixture(name, source);
  const events = [];
  const questions = [];
  const notifications = [];
  const prompt = new Prompt({ container: { createPrompt: async (type, options) => {
    assert.equal(type, 'confirm');
    assert.equal(options.message, 'Send release notification?');
    assert.equal(options.default, true);
    questions.push(options);
    return answer;
  } } });
  globalThis.fetch = async (url, options) => {
    assert.equal(url, 'https://example.invalid/notification-stub');
    notifications.push(JSON.parse(options.body));
    return { ok: true };
  };
  process.chdir(directory);
  const result = await release({
    ...baseOptions,
    'dry-run': isDryRun,
    plugins: { [plugin]: { name: 'product-fixture', webhookUrl: 'https://example.invalid/notification-stub' } }
  }, { prompt, log: logger(events) });
  assert.equal(result.latestVersion, '1.2.3');
  assert.equal(result.version, '1.2.4');
  assert.equal(readFileSync('VERSION', 'utf8'), isDryRun ? '1.2.3' : '1.2.4');
  assert.equal(JSON.parse(readFileSync('package.json', 'utf8')).version, '9.9.9');
  assert.equal(questions.length, hasQuestion && !isDryRun ? 1 : 0);
  assert.equal(notifications.length, hasQuestion && !isDryRun && answer ? 1 : 0);
  if (notifications.length) assert.equal(notifications[0].text, 'Released product-fixture v1.2.4');
  writeFileSync(path.join(directory, 'events.json'), JSON.stringify({ events, questions, notifications }, null, 2));
  return { version: result.version, questions: questions.length, notifications: notifications.length, isDryRun };
}

async function checkOrder() {
  const source = `import { Plugin } from 'release-it';
export default class Marker extends Plugin {
  static disablePlugin() { return 'npm'; }
  getLatestVersion() { return '1.2.3'; }
  beforeBump() { this.log.info('beforeBump:' + this.options.id); }
  bump() { this.log.info('bump:' + this.options.id); }
  beforeRelease() { this.log.info('beforeRelease:' + this.options.id); }
  release() { this.log.info('release:' + this.options.id); }
  afterRelease() { this.log.info('afterRelease:' + this.options.id); }
}`;
  const { directory, plugin } = fixture('plugin-group-order', source);
  const second = path.join(directory, 'second.mjs');
  writeFileSync(second, source);
  const events = [];
  const phases = ['beforeBump', 'bump', 'beforeRelease', 'release', 'afterRelease'];
  process.chdir(directory);
  await release({
    ...baseOptions,
    plugins: { [plugin]: { id: 'A' }, [second]: { id: 'B' } },
    hooks: Object.fromEntries(phases.map(phase => [`before:version:${phase}`, `${phase}:core`]))
  }, {
    log: logger(events),
    shell: { exec: async command => { events.push({ level: 'info', args: [command] }); return ''; } }
  });
  const order = events.filter(event => event.level === 'info' && /^(beforeBump|bump|beforeRelease|release|afterRelease):/.test(event.args[0]))
    .map(event => event.args[0]);
  const expected = phases.flatMap(phase => (['release', 'afterRelease'].includes(phase)
    ? ['core', 'A', 'B'] : ['A', 'B', 'core']).map(id => `${phase}:${id}`));
  assert.deepEqual(order, expected);
  return { order };
}

async function checkApiError() {
  const { directory, plugin } = fixture('api-error-ownership', `import { Plugin } from 'release-it';
export default class Failure extends Plugin {
  static disablePlugin() { return 'npm'; }
  getLatestVersion() { return '1.2.3'; }
  beforeBump() { throw new Error('Plugin fixture failed'); }
}`);
  const events = [];
  process.chdir(directory);
  await assert.rejects(release({ ...baseOptions, plugins: { [plugin]: {} } }, { log: logger(events) }),
    { message: 'Plugin fixture failed' });
  assert.deepEqual(events.filter(event => event.level === 'error').map(event => event.args), [['Plugin fixture failed']]);
  assert.equal(readFileSync('VERSION', 'utf8'), '1.2.3');
  return { errorMessages: 1 };
}

const cases = [
  ['version-provider', () => checkExample('version-provider', minimal)],
  ['version-provider-dry-run', () => checkExample('version-provider-dry-run', minimal, { isDryRun: true })],
  ['webhook-approve', () => checkExample('webhook-approve', webhook, { hasQuestion: true })],
  ['webhook-decline', () => checkExample('webhook-decline', webhook, { hasQuestion: true, answer: false })],
  ['webhook-dry-run', () => checkExample('webhook-dry-run', webhook, { hasQuestion: true, isDryRun: true })],
  ['plugin-group-order', checkOrder],
  ['api-error-ownership', checkApiError]
];
for (const [name, run] of cases) {
  try { results.push({ name, passed: true, ...await run() }); }
  catch (error) { results.push({ name, passed: false, error: error.stack }); }
  finally { process.chdir(initialCwd); globalThis.fetch = initialFetch; }
  console.log(JSON.stringify(results.at(-1)));
}
writeFileSync(path.join(output, 'results.json'), JSON.stringify({
  releaseItVersion: version,
  referenceSha256: createHash('sha256').update(reference).digest('hex'),
  results
}, null, 2) + '\n');
if (results.some(result => !result.passed)) process.exitCode = 1;
