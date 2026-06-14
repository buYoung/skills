# Tiering: capability x deliberation

Phases are not all equally hard. Some need the strongest judgment available; some are mechanical and should run on the cheaper setting. Tiering is how the orchestrator spends capability where it matters and saves it where it does not. This file defines the two axes, the assignment rules that map a phase to a tier, and how to bind abstract tiers to a concrete runtime without locking the skill to one platform.

## Two axes, not one ordinal

A tier is a point on two independent axes:

- **capability** — the model's reasoning ceiling. Bound to *model choice*.
- **deliberation** — how much thinking budget the model spends per call. Bound to a *thinking/effort/reasoning setting*, where the runtime exposes one per agent.

These are orthogonal. "Same model, more deliberation" raises quality at the same capability ceiling and is cheap to dial. "Stronger model" raises the ceiling and changes failure modes. Collapsing both into a single 1-D "tier 1 / tier 2" hides which lever you are actually pulling, and the two levers do not substitute cleanly.

> Origin note: the run this skill generalizes used **one model at two deliberation levels** (a single capable model, switched between a high and a standard reasoning setting per phase). It did *not* use two different models. Keep that distinction in mind when binding — see "When the runtime has no per-agent deliberation" below.

## Two tiers

Keep it to two. A third tier is almost always scope creep — the proven shape is binary.

- **JUDGE tier** — high capability, high deliberation.
- **WORKER tier** — standard capability, standard deliberation.

## Assignment rules (the part that matters)

A tier *label* with no assignment rule is decoration. Assign by the nature of the phase:

**JUDGE tier** — work where a wrong answer is expensive and judgment is the product:

- design and decomposition decisions
- evaluation, scoring, or grading of outputs
- adversarial review and red-teaming
- synthesis across many inputs into a single conclusion
- anything whose output other phases will trust without re-checking

**WORKER tier** — work that is mechanical, verifiable, or bounded:

- investigation and surveying ("what is here, how many, how big")
- running commands, tools, or external CLIs
- transforming or reformatting data
- aggregating metrics and collating outputs
- producing a first draft that a later JUDGE phase will scrutinize

Tie-breaker: if a phase's output feeds a user-facing judgment or another phase's correctness, lift it to JUDGE. If it is re-checked downstream anyway, keep it WORKER.

## Binding abstract tiers to a runtime

The skill core stays abstract. Bind tiers to concrete settings at the edge, as *examples* — never hardcode a model name into the workflow logic.

| Tier | Runtime with per-agent deliberation (example) | Runtime with model choice only (example) |
|------|----------------------------------------------|------------------------------------------|
| JUDGE | strongest model + highest deliberation setting | strongest available model |
| WORKER | same model + standard deliberation setting | standard / mid model |

Read the columns as *patterns*, not a fixed mapping. On a runtime that exposes a per-agent reasoning/effort control, JUDGE and WORKER can be **the same model at two deliberation settings** — the faithful, cheap form. On a runtime that exposes only model choice per sub-agent, you cannot reproduce that; the tiering **collapses onto capability** — JUDGE becomes a stronger model, WORKER a standard one.

## When the runtime has no per-agent deliberation

This is the common case and it needs an honest caveat in the run plan, not a silent substitution:

- The deliberation axis disappears. You are left with capability (model choice) only.
- Substituting "stronger model" for "more deliberation" is an **approximation**, not an equivalence: it changes the capability ceiling and the failure modes, not just the thinking budget.
- **Do not assume the approximation holds — validate it.** The cheap-proof gate (SKILL Step 4) is exactly the validator: a mis-bound tier shows up as a quality cliff on the cheap representative slice, before the expensive step. State in the run plan that the binding is approximate and that the cheap slice is what confirms it.

## Cost note

On a runtime where the cheap lever was per-agent deliberation, dropping a phase from high to standard deliberation saved cost at the same model. Where that lever is absent, the only lever is model choice — and a high-capability model assigned to every JUDGE phase across a wide fan-out is a real cost, multiplied by every item and every round. Surface the expected JUDGE-phase count when you present the run plan, so the cost is visible before the fan-out, not after.
