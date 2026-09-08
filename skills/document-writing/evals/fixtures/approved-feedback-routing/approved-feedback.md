# Approved feedback record F12
The product council approved a focused correction to the comparison pattern, preserving the current direction. In three procurement sessions users mistook the headline quote as unconditional because eligibility was visible only in the details panel. For quotes with eligibility conditions, keep the condition next to the headline cost and retain its currency; link the full rationale. Unconditional quotes do not need an invented condition. Alternative: concise cost and eligibility summary linked to full evidence, not hiding the condition or adding every detail to the summary.

Validation record F12-V: reviewers checked conditional and unconditional quotes against the correction. Both passed document-to-example verification; no live application test was performed.

Comparable follow-up ledger (evaluation data): F12-B checked the same 10 conditional quote examples at the same desktop viewport before the document correction and found 4 hidden-eligibility failures. F12-A checked those same examples, inputs, and viewport with document revision F12 and found 1 remaining failure. These are document-to-example observations, not live usage metrics. The remaining failure occurred in Q7, whose condensed-summary example still pointed to the retired pattern. The source of that missed reference is not yet confirmed. The approved next check is to inspect that reference and repeat Q7 plus an unaffected unconditional example under the same conditions. Do not claim the failure is eliminated or generalize the 4-to-1 result to all customers.

One stakeholder separately preferred all headings to be violet once. That preference was not approved.

Implementation defect I9: the existing renderer drops the currency even though the current document rule already requires it. This is a consumer defect, not approval to weaken the rule. A future deterministic renderer check may catch missing currency, but no new automation is authorized. A stale preview cache in the execution tool caused an outdated screenshot to reappear; do not infer a design rule from it.

Update only patterns.md and governance.md. Keep this record, foundations, index, and renderer.ts unchanged.
