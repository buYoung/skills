# Evaluation Cases

`evals.json` holds six prompts that cover a managed MySQL upgrade, a PostgreSQL vacuum and plan diagnosis, a MongoDB to Amazon DocumentDB move, Redis latency with a Redis or Valkey decision, a DynamoDB key redesign, and a MySQL version outside the covered range.

Expected outputs describe the judgment and evidence a good answer contains, not wording or a fixed outline. Check version and lifecycle claims against the references and the vendor pages at evaluation time, because support dates and managed-service offerings change. An answer that asks for missing facts, such as the exact server version, can be correct when the decision depends on them.

Assess whether the answer:

- establishes the product, deployment, and version, and handles a version outside the covered range explicitly;
- collects evidence before changing anything and names the commands or metrics that produce it;
- marks risky statements (locks, rewrites, restarts, failovers, deletions) and gives a rehearsal or rollback;
- keeps documented guarantees, version defaults, observed results, and inference apart.

Each case's `expectations` are the assertions used for grading. In the 2026-11-27 run (one run per configuration), cases 2 and 5 passed every assertion with and without the skill, so they do not yet separate the two. Candidates for sharper assertions: for case 2, recommending a plain `VACUUM` and explaining that a held xmin horizon does not by itself stop `last_autovacuum` from advancing; for case 5, keeping not-yet-deleted expired items out of the latest-50 query with a key condition rather than a filter applied after `Limit`.
