import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';

const root = process.argv[2];
const read = (file) => readFile(path.join(root, file), 'utf8');
const [pkgText, config, nginx, bootstrap, app, ownership, report] = await Promise.all([
  read('package.json'),
  read('vite.config.mjs'),
  read('deploy/nginx.conf'),
  read('src/bootstrap.mjs'),
  read('src/App.jsx'),
  read('OWNERSHIP.md'),
  read('REPORT.md').catch(() => '')
]);
const pkg = JSON.parse(pkgText);
const checks = [];
const check = (text, condition, evidence) => checks.push({ text, passed: Boolean(condition), evidence });
const hasDirectDraftGate = /hasUnsavedDraft/.test(bootstrap);
const hasFrameworkMediatedGate = /CustomEvent/.test(bootstrap)
  && /(cancelable:\s*(?:true|canReload)|detail:[\s\S]*reload)/.test(bootstrap)
  && /dispatchEvent/.test(bootstrap);

check('Vite base matches the backend /console/ mount', /^8\./.test(pkg.devDependencies?.vite ?? '') && pkg.engines?.node === '>=22.12.0' && /base:\s*["']\/console\/["']/.test(config), 'package.json and vite.config.mjs');
check('Hashed assets remain under assets/', /assetsDir:\s*["']assets["']/.test(config) && /\[hash\]/.test(config), 'vite.config.mjs');
check('Current HTML is not stored while hashed assets remain immutable', /index\.html[\s\S]*(no-store|no-cache|max-age=0)/i.test(nginx) && /assets\/[\s\S]*max-age=31536000[\s\S]*immutable/i.test(nginx), 'deploy/nginx.conf');
check('Backend fallback still resolves to /console/index.html', /try_files[\s\S]*\/console\/index\.html/.test(nginx), 'deploy/nginx.conf');
check('A stale preload failure is intercepted and automatic recovery is bounded across reloads', /vite:preloadError/.test(bootstrap) && /preventDefault\(\)/.test(bootstrap) && /(sessionStorage|localStorage)/.test(bootstrap) && /reload\(\)/.test(bootstrap), 'src/bootstrap.mjs');
check('Unsaved work blocks automatic recovery and produces a framework-owner request', (hasDirectDraftGate || hasFrameworkMediatedGate) && /(dispatchEvent|CustomEvent)/.test(bootstrap), 'src/bootstrap.mjs');
check('The recovery guard is cleared or rotated after successful boot', /(removeItem|markSuccessfulPageLoad|rotateReloadGuardAfterSuccessfulLoad|pageshow|DOMContentLoaded|__CONSOLE_BUILD_ID__)/.test(bootstrap), 'src/bootstrap.mjs guard lifecycle');
check('Framework-owned React code remains untouched', app.trim() === "// SENTINEL: framework-owner-controlled-do-not-edit\nexport function App() {\n  return <main><h1>Incident console</h1></main>;\n}" && /React incident-console team; read-only/.test(ownership), 'src/App.jsx and OWNERSHIP.md');
check('The report records actual-topology verification, rollback, and framework-owner needs', /console/i.test(report) && /(old client|stale|404|preload)/i.test(report) && /rollback/i.test(report) && /(framework|React|UI owner)/i.test(report) && /(unverified|not run|runtime|browser)/i.test(report), 'REPORT.md');

console.log(JSON.stringify({ checks }, null, 2));
assert.ok(checks.every((item) => item.passed), 'one or more checks failed');
