# Evaluation Cases

`evals.json` contains 16 prompt scenarios covering language concepts, practical patterns, platform constraints, and ecosystem usage. They include both standalone explanations and applications to a supplied situation.

Assess the accuracy of the mechanism, the connection to a useful pattern, its conditions and exceptions, and the consistency of examples with the explanation. A suitable comparison is valuable when alternatives matter; not every question needs a library recommendation or a project investigation. Explanations should remain useful when workload, ownership, or target assumptions change.

Expected outputs describe the intended understanding, not fixed wording, required keywords, or a mandatory answer outline. Distinguish language/API guarantees, conditional engineering practices, and measured results. Check time-sensitive claims against sources at evaluation time. Case 16 supplies its own adoption figures; those figures are inputs to the case, not live package metrics.

These are evaluation specifications, not executed outputs or benchmark scores. No independent model-run results are recorded here. Document/example validation and actual target performance establish different things from response quality.

For practical explanations, assess whether the response connects the representative data flow, ownership, execution, and failure behavior rather than merely naming considerations. Examples should preserve the described semantics through the relevant boundary. An applicable exception needs an explanation of what changes and why, not just a warning to measure or consult documentation.

A correct short conceptual answer can remain short. Implementation-oriented explanations should be concrete enough to adapt: required features and target assumptions, the core operation, and resource completion/cleanup should be clear. Code compilation and keyword coverage alone do not establish this quality.
