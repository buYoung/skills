import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';

const root = process.argv[2];
const read = (file) => readFile(path.join(root, file), 'utf8');
const [source, pkg, vite, api, audit, report] = await Promise.all([
  read('src/orders/OrderWorkspace.jsx'),
  read('package.json'),
  read('vite.config.mjs'),
  read('src/orders/orderApi.mjs'),
  read('src/orders/OrderAuditPanel.jsx'),
  read('REPORT.md').catch(() => '')
]);

const checks = [];
const check = (text, condition, evidence) => checks.push({ text, passed: Boolean(condition), evidence });
const componentAt = source.indexOf('export function OrderWorkspace');
const lazyAt = source.indexOf('lazy(');
const effectDeps = source.match(/useEffect\([\s\S]*?\},\s*\[([^\]]*)\]\s*\)/)?.[1] ?? '';
const hasFreshCallbackChannel = /useEffectEvent/.test(source)
  || (/useRef/.test(source) && /\.current\s*=\s*onResolved/.test(source));

check('React 19.2 dependency contract is preserved', pkg.includes('"react": "19.2.0"') && pkg.includes('"react-dom": "19.2.0"'), 'package.json');
check('Audit-panel identity remains stable across workspace renders', lazyAt >= 0 && lazyAt < componentAt && source.indexOf('lazy(', componentAt) === -1, `lazy index ${lazyAt}, component index ${componentAt}`);
check('Superseded requests cannot commit and cancellation is not shown as failure', /AbortController/.test(source) && /signal\s*:\s*\w+\.signal/.test(source) && /\.abort\(\)/.test(source) && /(AbortError|signal\.aborted|isObsolete|isCurrentRequest)/.test(source), 'OrderWorkspace.jsx cancellation path');
check('Callback freshness does not control request synchronization lifetime', hasFreshCallbackChannel && !/onResolved/.test(effectDeps), `effect dependencies: [${effectDeps}]`);
check('Initial load and refresh preserve distinct user-visible behavior and editable state', /(!order|hasCurrentOrder)/.test(source) && /isLoading/.test(source) && /refresh/i.test(source) && !/setOrder\(null\)/.test(source), 'OrderWorkspace.jsx state model');
check('Error recovery is announced and exposes retry', /(role=["']alert["']|aria-live=["']assertive["'])/.test(source) && /retry/i.test(source), 'OrderWorkspace.jsx error UI');
check('Only React-owned incident files change', vite.trim() === "// SENTINEL: build-owner-controlled-do-not-edit\nexport default { base: '/operations/' };" && /fetch\(`\/api\/orders\/\$\{orderId\}`/.test(api) && /Audit for \{orderId\}/.test(audit), 'Vite, request API, and audit panel evidence');
check('The report explains root causes and separates performed verification from runtime checks', /(race|stale|supersed|abort)/i.test(report) && /(callback|onResolved|identity|non-reactive)/i.test(report) && /(lazy|component identity|module scope)/i.test(report) && /verification/i.test(report) && /(runtime|browser|unverified|remaining|not run)/i.test(report), 'REPORT.md');

console.log(JSON.stringify({ checks }, null, 2));
assert.ok(checks.every((item) => item.passed), 'one or more checks failed');
