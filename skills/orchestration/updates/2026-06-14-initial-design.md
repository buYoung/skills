# 2026-06-14 — Initial design and adversarial trail

## Provenance

This skill generalizes an observed orchestration run in which a main agent managed a
sequence of ~56 isolated sub-agents through heterogeneous phases (investigate, produce,
run, evaluate, analyze, report) for a measurement task. The goal here was to extract the
**reusable orchestration pattern** — not the measurement methodology that ran on top of it.

## What was deliberately kept out (leak check)

The source run was a benchmark. Benchmark-specific machinery was **excluded** so the skill
reads as general orchestration, not as a benchmark harness:

- public/private answer split, anti-cheat forbidden-file lists, scoring rubrics, and
  within-model improvement targets — all benchmark-domain, not orchestration.

What was kept is domain-general: manager-only orchestration, per-phase isolation and
path-passing, capability-by-deliberation tiering, the cheap sanity slice before fan-out,
user-judged review, run-id/superseded re-versioning, and lifecycle/orphan accounting.

## Adversarial review trail (what changed because of it)

1. **Tier axis was mischaracterized.** An early draft bound the two tiers to two *models*
   (strong vs standard). The source run actually used **one model at two deliberation
   levels**. Fix: model the tier as two orthogonal axes — capability (model) and
   deliberation (effort/thinking budget) — and state honestly that runtimes without a
   per-agent deliberation control collapse onto capability-only, re-validated by the
   sanity gate. See `references/tiering.md`.

2. **A fabricated third tier.** An early draft added a SCOUT tier bound to a small model.
   In the source run, that small model was a *subject under test*, never an orchestration
   worker; all orchestration agents were the same model. Fix: two tiers only.

3. **Review autonomy vs user judgment.** The source run's reviewers were sub-agents, but
   the *judgment* was always the user's, and the one attempt at external verification was
   policy-blocked. Constraint set by the user: orchestration may **generate** constructive
   and adversarial critique but must **halt** and let the user judge accept/reject. Fix:
   `references/review_gate.md` splits generate (agent) from judge (user).

4. **Halt scoping.** Halting at every phase would destroy the long-autonomous-run value;
   halting nowhere makes the orchestration its own judge. Fix: exactly two named halts —
   sanity go/no-go, and review accept/reject. See SKILL "Halt conditions".

5. **Rigidity risk.** The source run re-versioned mid-flight (changed inputs, added
   variants, fixed the harness) and stayed interpretable. Fix: re-versioning/superseded
   discipline is written as the spine (SKILL Step 8, `phase_protocol.md`), not a footnote,
   and the word "pipeline" is kept from implying a rigid conveyor.

6. **Portability.** The pattern was expressed in one runtime's primitives (a specific
   spawn API, specific model names, a per-agent effort knob). Fix: the skill is a portable
   *instruction* document; runtime primitives and model bindings live only as examples in
   `references/orchestration_template.md` and `references/tiering.md`, never in core logic.

## Ecosystem positioning

- Distinct from `delegated-review-loop` (single-artifact build-review-improve, autonomous
  panel) and `iterative-self-review` (single-answer blind verification). This skill is the
  multi-phase backbone the other two are specializations of.
- Termination block reuses the review skills' `termination:` convention and shared field
  names (`trigger`, `user_decisions`, `residual_issues`, `failure_log`), extended with
  pipeline-specific fields — not a claim of identical schema. Reference files are not
  cross-linked (marketplace bundles each skill independently).
