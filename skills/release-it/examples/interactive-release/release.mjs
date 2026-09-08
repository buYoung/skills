import { existsSync, readFileSync, realpathSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { select, input } from '@inquirer/prompts';
import semver from 'semver';
import release, { Config } from 'release-it';
import { InquirerPrompt, ReleaseStopped, requireAnswer } from './release-prompts.mjs';

// Copy both example modules into the project's scripts/ directory.
const root = realpathSync(fileURLToPath(new URL('../', import.meta.url)));
const guardPath = fileURLToPath(new URL('./release-prompts.mjs', import.meta.url));
const prompt = new InquirerPrompt();
// Apply before Config.init(): snapshot expansion also rewrites Git/npm options.
const interactiveOptions = {
  ci: false,
  'only-version': false,
  'release-version': false,
  changelog: false,
  'dry-run': false,
  snapshot: false,
  preRelease: false
};
const readJSON = file => JSON.parse(readFileSync(file, 'utf8'));
const git = (...args) => execFileSync('git', args, { cwd: root, encoding: 'utf8' }).trim();
let headBefore;
let targetDirectory;

async function chooseTarget() {
  const rootPackage = readJSON(path.join(root, 'package.json'));
  const manifestPath = path.join(root, '.release-targets.json');
  const declarations = Array.isArray(rootPackage.workspaces)
    ? rootPackage.workspaces : rootPackage.workspaces?.packages;
  const projects = JSON.parse(execFileSync('pnpm', ['list', '--recursive', '--depth', '-1', '--json'], {
    cwd: root, encoding: 'utf8'
  }));
  // pnpm-workspace.yaml can contain only build settings in a single project.
  // Use actual workspace projects, declarations, or the setup-verified manifest.
  const isMonorepo = projects.some(project => realpathSync(project.path) !== root) ||
    Boolean(declarations?.length) || existsSync(manifestPath);
  if (!isMonorepo) return { name: rootPackage.name || 'project', path: '.', config: true };

  if (!existsSync(manifestPath)) {
    throw new Error('Define verified service apps in .release-targets.json during setup.');
  }
  const { serviceApps } = readJSON(manifestPath);
  if (!Array.isArray(serviceApps) || !serviceApps.length || serviceApps.some(app =>
    typeof app.name !== 'string' || typeof app.path !== 'string' || !app.name || !app.path
  ) || new Set(serviceApps.map(app => app.path)).size !== serviceApps.length) {
    throw new Error('Expected a nonempty list of distinct service-app paths.');
  }
  return requireAnswer(select({
    message: 'Select one service app:',
    choices: serviceApps.map(app => ({ value: app, name: app.name, description: app.path }))
  }), 'service app');
}

async function chooseVersion(currentVersion) {
  const increments = [
    ['patch'], ['minor'], ['prepatch', 'alpha'], ['preminor', 'beta'],
    ['prerelease', semver.prerelease(currentVersion)?.[0] || 'rc'],
    ['major'], ['premajor', 'alpha']
  ];
  const choices = increments.map(([increment, identifier]) => {
    const version = semver.inc(currentVersion, increment, String(identifier || ''));
    return { value: version, name: `${increment}: ${currentVersion} → ${version}` };
  }).filter(option => option.value && semver.gt(option.value, currentVersion));
  const selected = await requireAnswer(select({
    message: `Select version (current: ${currentVersion}):`,
    choices: [...choices, { value: 'custom', name: 'Enter an exact version' }]
  }), 'version');
  if (selected !== 'custom') return selected;
  const entered = await requireAnswer(input({
    message: `Next version (current: ${currentVersion}):`,
    validate: value => !semver.valid(value) || !semver.gt(value, currentVersion)
      ? `Enter a valid semver greater than ${currentVersion}.` : true
  }), 'version');
  return semver.valid(entered);
}

function reportState() {
  if (!headBefore) return;
  try {
    console.info(`HEAD before: ${headBefore}\nHEAD now: ${git('rev-parse', 'HEAD')}`);
    console.info(`Remaining index/worktree changes:\n${git('status', '--short') || '(clean)'}`);
    if (targetDirectory) {
      console.info(`Version on disk: ${readJSON(path.join(targetDirectory, 'package.json')).version}`);
    }
    if (prompt.tagName) {
      let tagRef;
      try { tagRef = git('show-ref', '--verify', `refs/tags/${prompt.tagName}`); }
      catch { tagRef = '(not present locally)'; }
      console.info(`Local tag ${prompt.tagName}: ${tagRef}`);
    }
    const pushState = prompt.completed.includes('push') ? 'push command completed' :
      prompt.attempted.includes('push') ? 'push attempted; remote state requires inspection' : 'push not attempted';
    console.info(pushState);
  } catch (error) {
    console.warn(`Could not fully inspect remaining state: ${error.message}`);
  }
}

try {
  if (!process.stdin.isTTY || !process.stdout.isTTY) {
    throw new Error('An interactive terminal is required; no release work was started.');
  }
  if (process.argv.length > 2) {
    throw new Error('Run pnpm release without arguments; choose the version in the prompt.');
  }
  process.chdir(root);
  // This check also catches untracked files, unlike release-it's git diff check.
  if (git('status', '--porcelain', '--untracked-files=all')) {
    throw new Error('The entire repository must be clean before starting a release.');
  }
  headBefore = git('rev-parse', 'HEAD');
  const target = await chooseTarget();
  targetDirectory = realpathSync(path.resolve(root, target.path));
  const relativeTarget = path.relative(root, targetDirectory);
  if (relativeTarget === '..' || relativeTarget.startsWith(`..${path.sep}`) || path.isAbsolute(relativeTarget)) {
    throw new Error('The selected service app must be inside this project.');
  }
  process.chdir(targetDirectory);
  const config = new Config({ config: target.config ?? true, ...interactiveOptions });
  await config.init();
  const options = config.getContext();
  if (!options.git || !options.git.commit || !options.git.tag || !options.git.push) {
    throw new Error('The interactive flow requires git commit, tag, and push to be enabled.');
  }
  if (!options.npm || options.npm.ignoreVersion || options.npm.publish !== false ||
      options.github?.release || options.gitlab?.release) {
    throw new Error('This example requires package.json versioning and no publishing or hosted release.');
  }
  const currentVersion = readJSON(path.join(targetDirectory, 'package.json')).version;
  if (!semver.valid(currentVersion)) throw new Error('The selected app needs a valid package.json version.');
  const selectedVersion = await chooseVersion(currentVersion);
  await release({
    ...options,
    config: false,
    extends: false,
    ...interactiveOptions,
    increment: selectedVersion,
    // Keep all other target options. The clean check above replaces the built-in
    // check so release-it does not attach destructive exit/SIGINT rollback handlers.
    git: { ...options.git, requireCleanWorkingDir: false },
    plugins: {
      [guardPath]: { currentVersion, selectedVersion },
      ...options.plugins
    }
  }, { prompt });
  console.info(`Released ${target.name} ${selectedVersion}.`);
} catch (error) {
  if (error instanceof ReleaseStopped) console.warn(error.message);
  else console.error(error.message);
  process.exitCode = 1;
} finally {
  process.chdir(root);
  reportState();
}
