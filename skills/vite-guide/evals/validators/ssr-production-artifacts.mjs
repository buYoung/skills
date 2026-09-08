import assert from 'node:assert/strict';
import { cp, mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { pathToFileURL } from 'node:url';

// Usage: node ssr-production-artifacts.mjs <repaired-fixture-root>
// The import smoke uses synthetic build artifacts; it is not a Vite build or deployment test.
const root = process.argv[2];
assert.ok(root, 'usage: node ssr-production-artifacts.mjs <repaired-fixture-root>');
const read = (file) => readFile(path.join(root, file), 'utf8');
const [packageText, config, server, client, renderer, report] = await Promise.all([
  read('package.json'), read('vite.config.mjs'), read('server.mjs'),
  read('src/entry-client.js'), read('src/entry-server.js'), read('REPORT.md').catch(() => '')
]);
const pkg = JSON.parse(packageText);
const scripts = Object.values(pkg.scripts ?? {}).join('\n');
const checks = [];
const check = (text, passed, evidence) => checks.push({ text, passed: Boolean(passed), evidence });
const clientBuild = Object.values(pkg.scripts ?? {}).find((script) => /vite build/.test(script) && /dist\/client/.test(script));
check('Client and server builds are separate and the client emits the SSR manifest',
  clientBuild && /dist\/server/.test(scripts) && /--ssr\s+src\/entry-server\.js/.test(scripts)
  && (/--ssrManifest/.test(clientBuild) || /ssrManifest/.test(config)),
  'Build script/config presence; review actual flag placement and combined command order separately');

let smokePassed = false;
let smokeEvidence;
const temporaryRoot = await mkdtemp(path.join(os.tmpdir(), 'vite-ssr-validator-'));
try {
  await cp(root, temporaryRoot, { recursive: true, filter: (source) => !source.split(path.sep).includes('node_modules') });
  await mkdir(path.join(temporaryRoot, 'dist/client/.vite'), { recursive: true });
  await mkdir(path.join(temporaryRoot, 'dist/server'), { recursive: true });
  await writeFile(path.join(temporaryRoot, 'dist/client/index.html'), '<!doctype html><html><head><!--preload-links--></head><body><!--app-html--><script src="/console/assets/client-smoke.js"></script></body></html>');
  await writeFile(path.join(temporaryRoot, 'dist/client/.vite/ssr-manifest.json'), JSON.stringify({ 'src/entry-client.js': ['/console/assets/client-smoke.js', '/console/assets/client-smoke.css'] }));
  await writeFile(path.join(temporaryRoot, 'dist/server/entry-server.js'), `export async function render(url, manifest) {
    if (url !== '/console/profile') throw new Error('Request URL was not preserved');
    const files = manifest['src/entry-client.js'];
    if (!files?.includes('/console/assets/client-smoke.css')) throw new Error('Client SSR manifest was not passed');
    return { html: '<h1>built-server-smoke</h1>', preloadLinks: '<link rel="stylesheet" href="/console/assets/client-smoke.css">' };
  }`);
  const { createPageHandler } = await import(pathToFileURL(path.join(temporaryRoot, 'server.mjs')));
  const renderPage = await createPageHandler({ isProduction: true, root: temporaryRoot });
  const html = await renderPage('/console/profile');
  smokePassed = html.includes('built-server-smoke') && html.includes('/console/assets/client-smoke.js')
    && html.includes('/console/assets/client-smoke.css') && !/\/src\/|@vite\/client|<!--app-html-->|<!--preload-links-->|\/console\/console\//.test(html);
  smokeEvidence = `Synthetic built HTML + built renderer + client SSR manifest, no installed Vite: ${smokePassed}`;
} catch (error) {
  smokeEvidence = `${error.name}: ${error.message}`;
} finally {
  await rm(temporaryRoot, { recursive: true, force: true });
}
check('Production imports built server output and consumes built client HTML and manifest without Vite', smokePassed, smokeEvidence);
check('Development retains middleware mode, HTML transforms, and ssrLoadModule',
  /middlewareMode:\s*true/.test(server) && /appType:\s*['"]custom['"]/.test(server)
  && /transformIndexHtml/.test(server) && /ssrLoadModule/.test(server),
  'Development source indicators; semantic review checks branching and lifecycle');
let configurationPassed = false;
let configurationEvidence;
try {
  const { default: configExport } = await import(pathToFileURL(path.join(root, 'vite.config.mjs')));
  const resolved = typeof configExport === 'function' ? await configExport({ command: 'build', mode: 'production', isSsrBuild: true }) : configExport;
  const ssr = resolved.ssr;
  const noExternalRules = Array.isArray(ssr?.noExternal) ? ssr.noExternal : [ssr?.noExternal];
  const matchesNoExternal = (name) => noExternalRules.some((rule) =>
    typeof rule === 'string' ? rule === name : rule instanceof RegExp && rule.test(name));
  configurationPassed = Array.isArray(ssr?.external) && ssr.external.includes('@fixture/banner')
    && !ssr.external.includes('@fixture/theme') && ssr.noExternal !== true
    && matchesNoExternal('@fixture/theme') && !matchesNoExternal('@fixture/banner')
    && ssr.resolve?.externalConditions?.includes('custom');
  configurationEvidence = JSON.stringify(ssr);
} catch (error) {
  configurationEvidence = `${error.name}: ${error.message}; inspect configuration manually if its imports need uninstalled dependencies`;
}
check('Runtime-external and transform-required packages have targeted resolution policies', configurationPassed, configurationEvidence);
check('Custom Node export conditions are aligned in dev and production launch commands',
  /--conditions(?:=|\s+)custom/.test(pkg.scripts?.dev ?? '')
  && /--conditions(?:=|\s+)custom/.test(pkg.scripts?.start ?? ''),
  'dev/start scripts explicitly carry the custom Node condition');
check('Base path, versions, client interaction, and server-secret boundaries are preserved',
  pkg.devDependencies.vite === '8.0.0' && pkg.engines.node === '>=22.12.0'
  && /base:\s*['"]\/console\/['"]/.test(config) && /addEventListener\(['"]click/.test(client)
  && /process\.env\.INTERNAL_API_TOKEN/.test(renderer) && !/INTERNAL_API_TOKEN/.test(client)
  && !/define:.*INTERNAL_API_TOKEN/.test(config),
  'Source/package checks; deployed dependency resolution and secret exposure need separate verification');
check('The report distinguishes manifest semantics and synthetic checks from real build/deployment validation',
  /manifest/i.test(report) && /client/i.test(report) && /production/i.test(report)
  && /not run|unverified|not executed|not performed/i.test(report),
  'REPORT.md topic presence only; explanation validity is reviewed separately');
console.log(JSON.stringify({ checks, limitations: ['Synthetic emitted artifacts only', 'No Vite build, external dependency installation, browser, or real deployment execution'] }, null, 2));
assert.ok(checks.every((item) => item.passed), 'one or more checks failed');
