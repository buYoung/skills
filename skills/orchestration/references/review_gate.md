# Review gate: generate as agent, judge as user

The review checkpoint (SKILL Step 6) splits one thing most loops fuse: **generating** critique and **judging** it. The orchestration may do the first. It must not do the second.

## Why the split

An orchestration that spawns its own reviewers and then accepts or rejects their findings is grading its own homework: the reviewer is part of the same system that produced the work, and the orchestrator that routed the work also rules on the verdict. The independence is cosmetic. The honest arbiter for "is this finding real, do we act on it" is the user.

This does not make the reviewers worthless — generated critique is where real blind spots surface. It means their output is **material for the user's judgment**, not a decision the orchestration executes.

## Generate: two distinct lenses

Spawn reviewers as separate sub-agents, one lens each, so one lens does not soften the other:

- **Constructive lens** — what would improve the result: gaps, weak spots, missing coverage, things worth adding. Framed as betterment.
- **Adversarial lens** — what is wrong or invalid: errors, unsupported claims, ways the result fails, reasons a conclusion should not stand. Framed to refute.

Run them as different agents (not one agent asked for "both"), because a single agent told to be both constructive and adversarial blunts the adversarial edge. Each receives the material to critique as paths, has read-only access to verify reality, and writes findings to `reviews/<lens>.md`.

Each finding must carry **evidence** — a direct quote, a path-and-line, or a reproducible observation. A finding without evidence is downgraded, not presented as fact.

## Judge: hand it to the user

The orchestration's job at the gate is to make the material *legible*, then stop:

- **May:** merge duplicate findings across lenses, drop findings that have no evidence, and rank by apparent severity for readability.
- **Must not:** mark a finding accepted or rejected, act on a finding, or proceed past the gate on its own verdict.
- **Present:** a short, readable list — one line per finding plus its evidence — not a raw dump of both reviewer documents. The user decides which findings to accept.

This is a genuine **halt**: the run does not advance past Step 6 until the user has judged. If the user accepts findings that change a run condition, that is feedback — route it through SKILL Step 8 (re-versioning), not through a silent in-place fix.

## What the orchestration may decide alone

To keep the halt from becoming friction, the orchestrator still owns the routine calls that are not judgments of *correctness*:

- whether a review checkpoint is warranted at all for a given run (low-stakes runs may skip it)
- which two (or more) lenses fit the run
- readability merging and ranking, as above

Escalate to the user only the thing that is actually theirs: **whether the findings are real and what to do about them.**

## External-reviewer caveat

A tempting way to get "independent" judgment is to send the work to an external model or service. Two failure modes to anticipate:

- **Policy blocks.** Sending internal or sensitive run material to an external tool may be refused by policy. If it is, record the block plainly and do not route around it — an external verdict obtained by circumventing a block is not a trustworthy verdict.
- **Leakage.** Even when allowed, send a summarized, evidence-bearing brief, not raw sensitive artifacts. The reviewer needs enough to judge, not the whole corpus.

If external review is blocked, the run is not stuck: the user is the arbiter regardless, and the generated internal critique plus the user's judgment is the valid path.
