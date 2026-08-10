import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import { readFile } from 'node:fs/promises';
import path from 'node:path';

const root = process.argv[2];
const read = (file) => readFile(path.join(root, file), 'utf8');
const fixtureStoreUrl = new URL('../fixtures/external-store-grid-performance/src/gridStore.mjs', import.meta.url);
const [grid, storeSource, fixtureStoreSource, pkg, vite, report] = await Promise.all([
  read('src/Grid.jsx'),
  read('src/gridStore.mjs'),
  readFile(fixtureStoreUrl, 'utf8'),
  read('package.json'),
  read('vite.config.mjs'),
  read('REPORT.md').catch(() => '')
]);
const { createGridStore } = await import(pathToFileURL(path.join(root, 'src/gridStore.mjs')));
const store = createGridStore([{ id: 'a', name: 'A', price: 1 }, { id: 'b', name: 'B', price: 2 }]);
let rowA = 0;
let rowB = 0;
store.subscribeRow('a', () => rowA++);
store.subscribeRow('b', () => rowB++);
store.updatePrice('a', 3);

const checks = [];
const check = (text, condition, evidence) => checks.push({ text, passed: Boolean(condition), evidence });
check('The store still notifies only the changed row subscriber', rowA === 1 && rowB === 0 && store.getRow('a').price === 3, `rowA=${rowA}, rowB=${rowB}`);
check('The grid shell observes only structural collection changes', /subscribeIds/.test(grid) && /getIds/.test(grid) && !/store\.subscribe\b/.test(grid) && !/store\.getSnapshot\b/.test(grid), 'Grid.jsx shell subscription');
check('Each rendered row observes only its own external snapshot', /subscribeRow/.test(grid) && /getRow/.test(grid) && /useSyncExternalStore/.test(grid), 'Grid.jsx row subscription');
check('Per-row subscription identity is stable across renders', /useCallback/.test(grid) || /function\s+createRowSubscription/.test(grid) || /const\s+subscribe\w*\s*=\s*\([^)]*\)\s*=>\s*store\.subscribeRow/.test(grid), 'Grid.jsx subscription identity');
check('Row-local draft state is preserved', /useState\(/.test(grid) && /draft/.test(grid) && /setDraft/.test(grid), 'GridRow local state');
check('No deep-stringify workaround is introduced', !/JSON\.stringify|deepEqual|lodash\.isEqual/.test(grid), 'Grid.jsx comparison strategy');
check('Store and build ownership remain unchanged', storeSource === fixtureStoreSource && /"react": "19\.2\.0"/.test(pkg) && vite.trim() === "// SENTINEL: performance-build-owner-do-not-edit\nexport default { build: { sourcemap: true } };", 'gridStore.mjs, package.json, and vite.config.mjs');
check('The report identifies invalidation ownership and does not claim an unmeasured duration', /10,?000/.test(report) && /184\s*ms/i.test(report) && /(subscription|snapshot|invalidation|owner)/i.test(report) && /(expected|unverified|measure|profil|not run)/i.test(report), 'REPORT.md');

console.log(JSON.stringify({ checks }, null, 2));
assert.ok(checks.every((item) => item.passed), 'one or more checks failed');
