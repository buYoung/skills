import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';

const root = process.argv[2];
const read = (file) => readFile(path.join(root, file), 'utf8');
const [pkgText, config, contract, dashboard, report] = await Promise.all([
  read('package.json'),
  read('vite.config.mjs'),
  read('COMPILER_CONTRACT.md'),
  read('src/Dashboard.jsx'),
  read('REPORT.md').catch(() => '')
]);
const pkg = JSON.parse(pkgText);
const checks = [];
const check = (text, condition, evidence) => checks.push({ text, passed: Boolean(condition), evidence });
const virtualAt = config.indexOf('virtualFlagsPlugin()');
const reactAt = config.indexOf('react()', virtualAt);
const babelAt = config.indexOf('babel(', reactAt);

check('Vite 8 and Node 22.12 remain fixed while plugin-react reaches v6', /^8\./.test(pkg.devDependencies?.vite ?? '') && /^6\./.test(pkg.devDependencies?.['@vitejs/plugin-react'] ?? '') && pkg.engines?.node === '>=22.12.0', 'package.json');
check('The supported external Babel adapter is declared', Boolean(pkg.devDependencies?.['@rolldown/plugin-babel']), 'package.json');
check('The plugin package\'s Compiler bridge and the external transformer are used', /reactCompilerPreset/.test(config) && /from\s+["']@vitejs\/plugin-react["']/.test(config) && /from\s+["']@rolldown\/plugin-babel["']/.test(config), 'vite.config.mjs imports');
check('React Refresh no longer owns the removed inline transformation option', /react\(\s*\)/.test(config) && !/react\(\s*\{[\s\S]*?babel\s*:/.test(config), 'vite.config.mjs React plugin');
check('The external adapter preserves the caller-owned Compiler target and mode', /presets\s*:\s*\[\s*reactCompilerPreset\(\s*\{[\s\S]*target\s*:\s*["']19["'][\s\S]*compilationMode\s*:\s*["']annotation["']/.test(config) && /Compiler target: React 19/.test(contract) && /Compilation mode: annotation/.test(contract), 'vite.config.mjs and COMPILER_CONTRACT.md');
check('Virtual flags, React Refresh, and Compiler transformation retain semantic order', virtualAt >= 0 && reactAt > virtualAt && babelAt > reactAt, `indices ${virtualAt}, ${reactAt}, ${babelAt}`);
check('Existing Vite diagnostics/build and virtual plugin contracts are preserved', /forwardConsole:\s*true/.test(config) && /sourcemap:\s*true/.test(config) && /release-flags/.test(config), 'vite.config.mjs preserved contracts');
check('React-owned source and memoization remain untouched', dashboard.trim() === "// SENTINEL: react-owner-controlled-do-not-edit\nimport { memo } from 'react';\n\nexport const Dashboard = memo(function Dashboard({ metrics }) {\n  'use memo';\n  return <output>{metrics.join(', ')}</output>;\n});", 'src/Dashboard.jsx');
check('The report derives version gates, separate stages, verification, and rollback without performance claims', /Vite[^\n]*8\.0/i.test(report) && /plugin-react[^\n]*6/i.test(report) && /(@rolldown\/plugin-babel|external Babel)/i.test(report) && /(stage|separate)/i.test(report) && /rollback/i.test(report) && /(dev|refresh)/i.test(report) && /(production|build)/i.test(report) && /(no performance improvement|does not claim|same-condition baseline)/i.test(report), 'REPORT.md');

console.log(JSON.stringify({ checks }, null, 2));
assert.ok(checks.every((item) => item.passed), 'one or more checks failed');
