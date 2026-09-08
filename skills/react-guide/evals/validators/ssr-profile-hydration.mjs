import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

// Usage: node ssr-profile-hydration.mjs <repaired-fixture-root>
// Store execution and source checks only; JSX hydration and semantic review are separate.
const root = process.argv[2];
assert.ok(root, 'usage: node ssr-profile-hydration.mjs <repaired-fixture-root>');
const read = (file) => readFile(path.join(root, file), 'utf8');
const [packageText, server, client, component, report] = await Promise.all([
  read('package.json'), read('src/entry-server.jsx'),
  read('src/entry-client.jsx'), read('src/Profile.jsx'), read('REPORT.md').catch(() => '')
]);
const checks = [];
const check = (text, passed, evidence) => checks.push({ text, passed: Boolean(passed), evidence });
const pkg = JSON.parse(packageText);
check('React 18.3.1 and the existing renderer/host contract are preserved',
  pkg.dependencies.react === '18.3.1' && pkg.dependencies['react-dom'] === '18.3.1'
  && /renderPage/.test(server) && /renderToString/.test(server) && /\/assets\/client\.js/.test(server),
  'package versions, renderPage, renderToString, and fixed client asset in server source');

let stable = false;
let initialFixed = false;
let isolated = false;
let storeEvidence;
try {
  const { createProfileStore } = await import(pathToFileURL(path.join(root, 'src/profileStore.mjs')));
  const input = { name: 'Alice', visits: 2 };
  const alice = createProfileStore(input);
  const bob = createProfileStore({ name: 'Bob', visits: 9 });
  const first = alice.getSnapshot();
  const repeated = alice.getSnapshot();
  const serverFirst = alice.getServerSnapshot?.();
  let aliceCalls = 0;
  let bobCalls = 0;
  const unsubscribe = alice.subscribe(() => aliceCalls++);
  const unsubscribeBob = bob.subscribe(() => bobCalls++);
  alice.increment();
  const second = alice.getSnapshot();
  stable = first === repeated && second !== first && second === alice.getSnapshot()
    && first.visits === 2 && second.visits === 3 && input.visits === 2;
  initialFixed = serverFirst?.name === 'Alice' && serverFirst.visits === 2
    && alice.getServerSnapshot() === serverFirst;
  unsubscribe();
  alice.replace({ name: 'Alice updated', visits: 4 });
  initialFixed = initialFixed && alice.getServerSnapshot() === serverFirst && serverFirst.visits === 2;
  isolated = bob.getSnapshot().name === 'Bob' && bob.getSnapshot().visits === 9
    && aliceCalls === 1 && bobCalls === 0;
  unsubscribeBob();
  storeEvidence = `stable=${stable}, initialFixed=${initialFixed}, isolated=${isolated}, notifications=${aliceCalls}/${bobCalls}`;
} catch (error) {
  storeEvidence = `${error.name}: ${error.message}`;
}
check('External-store snapshots are stable and immutable across updates', stable, storeEvidence);
check('Initial server snapshots remain fixed while live snapshots advance', initialFixed, storeEvidence);
check('Separate store instances do not share request data or notifications', isolated, storeEvidence);
check('The client hydrates transferred request data with matching IDs and timestamp',
  /hydrateRoot/.test(client) && !/createRoot/.test(client)
  && /identifierPrefix/.test(server) && /identifierPrefix/.test(client)
  && /renderedAt/.test(client) && /renderedAt/.test(component)
  && !/new Date/.test(component) && /getServerSnapshot/.test(component)
  && /createProfileStore/.test(server),
  'Source wiring only: semantic review must trace the same payload and prefix into both renders');
check('Server payload transfer is safe and browser cache does not override hydration',
  /script/i.test(server) && /JSON\.stringify|serialize/.test(server)
  && /\\u003[cC]|serialize|escape/i.test(server) && !/localStorage/.test(client),
  'Source indicators only: semantic review must inspect serializer and per-request store placement');
check('Profile interactions and note identity are preserved without warning suppression',
  /store\.increment/.test(component) && /useState/.test(component) && /onChange/.test(component)
  && !/key=\{profile\.visits\}/.test(component)
  && !/suppressHydrationWarning/.test(server + client + component),
  'Component source retains store updates and note state without visit-dependent remount');
check('The report explains hydration causes, request isolation, and unrun runtime checks',
  /hydrat/i.test(report) && /request/i.test(report) && /snapshot/i.test(report)
  && /not run|unverified|not executed|not performed/i.test(report),
  'REPORT.md topic presence only; explanation validity is reviewed separately');
console.log(JSON.stringify({ checks, limitations: ['No React renderer or browser execution', 'Source indicators need semantic review'] }, null, 2));
assert.ok(checks.every((item) => item.passed), 'one or more checks failed');
