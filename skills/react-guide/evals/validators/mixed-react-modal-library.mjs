import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';

const root = process.argv[2];
const read = (file) => readFile(path.join(root, file), 'utf8');
const [pkg, consumers, context, modal, exportsFile, types, report] = await Promise.all([
  read('package.json'),
  read('CONSUMERS.md'),
  read('src/ModalContext.jsx'),
  read('src/Modal.jsx'),
  read('src/index.js'),
  read('src/index.d.ts'),
  read('REPORT.md').catch(() => '')
]);
const checks = [];
const check = (text, condition, evidence) => checks.push({ text, passed: Boolean(condition), evidence });

check('The mixed React peer range remains >=18 <20', (pkg.match(/">=18 <20"/g) ?? []).length === 2, 'package.json peerDependencies');
check('Context provision executes under the oldest supported consumer', /<ModalContext\.Provider\s+value=/.test(context) && !/<ModalContext\s+value=/.test(context), 'ModalContext.jsx');
check('The public dialog ref attaches under the oldest supported consumer', /forwardRef/.test(modal) && /ref=\{(?:ref|forwardedRef|modalRef)\}/.test(modal) && !/function\s+Modal\s*\(\s*\{[^}]*\bref\b/.test(modal), 'Modal.jsx');
check('Escape lifecycle remains stable while observing current caller behavior', /useRef/.test(modal) && /keydown/.test(modal) && !/\[\s*open\s*,\s*onClose\s*\]/.test(modal), 'Modal.jsx Effect ownership');
check('Focus is captured and restored only to a connected element', /(activeElement|previouslyFocused|restoreFocus)/.test(modal) && /(isConnected|document\.contains)/.test(modal) && /\.focus\(\)/.test(modal), 'Modal.jsx focus lifecycle');
check('Dialog semantics and labelledBy are preserved', /role=["']dialog["']/.test(modal) && /aria-modal=["']true["']/.test(modal) && /aria-labelledby=\{labelledBy\}/.test(modal), 'Modal.jsx semantics');
check('Named and default public exports are preserved', /export\s+\{[^}]*\bModal\b[^}]*\}/.test(exportsFile) && /export\s+\{[^}]*\bdefault\b[^}]*\}/.test(exportsFile) && /ModalProvider/.test(exportsFile) && /useModalController/.test(exportsFile), 'src/index.js');
check('Runtime and declaration contracts agree on the dialog element ref', /HTMLDivElement/.test(types) && /(ForwardRefExoticComponent|RefAttributes)/.test(types) && /export\s+default\s+Modal/.test(types), 'src/index.d.ts');
check('The package and consumer evidence remain unchanged', (pkg.match(/">=18 <20"/g) ?? []).length === 2 && /18\.3\.1/.test(consumers) && /19\.2\.0/.test(consumers), 'package.json and CONSUMERS.md');
check('The report diagnoses compatibility and lifecycle causes without overstating verification', /React 18/i.test(report) && /(provider|context)/i.test(report) && /(listener|callback|effect)/i.test(report) && /(focus|active element)/i.test(report) && /(runtime|browser|unverified|not run)/i.test(report), 'REPORT.md');

console.log(JSON.stringify({ checks }, null, 2));
assert.ok(checks.every((item) => item.passed), 'one or more checks failed');
