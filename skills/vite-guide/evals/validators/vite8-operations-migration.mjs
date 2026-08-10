import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';

const root = process.argv[2];
const read = (file) => readFile(path.join(root, file), 'utf8');
const [pkgText, config, plugin, migrationLog, report] = await Promise.all([
  read('package.json'),
  read('vite.config.mjs'),
  read('build/auditPlugin.mjs'),
  read('MIGRATION_LOG.md'),
  read('REPORT.md').catch(() => '')
]);
const pkg = JSON.parse(pkgText);
const checks = [];
const check = (text, condition, evidence) => checks.push({ text, passed: Boolean(condition), evidence });
const reactGroup = config.indexOf("name: 'react-runtime'");
const vendorGroup = config.indexOf("name: 'vendor'");

check('Stable Vite 8 replaces the temporary override and Node floor is preserved', /^8\./.test(pkg.devDependencies?.vite ?? '') && !pkg.overrides?.vite && pkg.engines?.node === '>=22.12.0', 'package.json');
check('plugin-react remains on v5 during Vite core arrival', /^5\./.test(pkg.devDependencies?.['@vitejs/plugin-react'] ?? ''), 'package.json');
check('Deployment and diagnostics contracts are preserved', /base:\s*["']\/ops\/["']/.test(config) && /forwardConsole:\s*true/.test(config) && /sourcemap:\s*true/.test(config) && /target:\s*["']es2020["']/.test(config), 'vite.config.mjs');
check('Dependency optimization is expressed through the Vite 8 native bundler while keeping the exclusion', /optimizeDeps[\s\S]*rolldownOptions/.test(config) && !/esbuildOptions/.test(config) && /react-dom\/client/.test(config), 'vite.config.mjs optimizeDeps');
check('The legacy output split is represented through the Vite 8 native output model', /rolldownOptions/.test(config) && /codeSplitting/.test(config) && /groups\s*:/.test(config) && !/rollupOptions|manualChunks/.test(config), 'vite.config.mjs build output');
check('React runtime keeps precedence over the remaining cross-platform vendor group', reactGroup >= 0 && vendorGroup > reactGroup && /node_modules\[\\\\\/\]/.test(config) && /priority\s*:\s*20/.test(config) && /priority\s*:\s*10/.test(config), 'codeSplitting groups');
check('Esbuild-only minification and the temporary package alias are gone', !/minify:\s*["']esbuild["']|rolldown-vite/.test(config + pkgText), 'config and package.json');
check('Plugin implementation and ordering remain unchanged', /acme-audit-manifest/.test(plugin) && /plugins:\s*\[react\(\),\s*auditPlugin\(\)\]/.test(config) && /object-style chunk declaration/.test(migrationLog), 'audit plugin and supplied migration evidence');
check('The report derives a staged compatibility inventory without claiming unrun arrival checks', /rolldown-vite/i.test(report) && /manualChunks/i.test(report) && /plugin-react.*v?5/i.test(report) && /(rollback|restore)/i.test(report) && /(unverified|not run|runtime|build)/i.test(report), 'REPORT.md');

console.log(JSON.stringify({ checks }, null, 2));
assert.ok(checks.every((item) => item.passed), 'one or more checks failed');
