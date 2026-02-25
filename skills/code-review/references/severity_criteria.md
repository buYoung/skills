# Severity Criteria

Classification criteria for code review findings by severity level, with confidence-aware interpretation.

## Severity Levels

## Critical

Issues with immediate high risk to system integrity, security, availability, or external contract compatibility.

| Category | Examples |
|----------|----------|
| **Security Exposure** | Injection vectors, credential leakage, authorization bypass |
| **Data Integrity Failure** | Corruption, irreversible mutation, destructive migration without safe path |
| **Availability Risk** | Crash loops, deadlock potential, unbounded resource exhaustion |
| **Externally Breaking Contract** | Incompatible changes on consumed public/runtime interfaces |
| **Rollback Gap in High-Risk Change** | No rollback/mitigation path for high-impact operational changes |

### Indicators
- Sensitive operation without required access control
- Destructive schema/data change without compatibility or rollback path
- Consumer-visible contract removed or renamed while consumers exist
- Critical monitoring/remediation controls removed during risky behavior changes

## Major

Issues that cause incorrect behavior, major reliability degradation, or high operational cost.

| Category | Examples |
|----------|----------|
| **Behavioral Defects** | Incorrect branch logic, boundary errors, invalid fallback behavior |
| **Performance Degradation** | Unbounded processing, repeated expensive operations, excessive I/O |
| **Error Handling Gaps** | Swallowed failures, incorrect retry boundaries, misclassified errors |
| **Concurrency/Race Risk** | Inconsistent shared-state access, missing synchronization strategy |
| **Observability Regression** | Loss of diagnostic context, reduced signal for incident response |
| **Configuration Semantics Drift** | Runtime config meaning changed without compatibility handling |

### Indicators
- Changed behavior lacks reliable failure-path handling
- Operationally expensive path triggered without guardrails
- Logging/metrics signal required for detection or triage is significantly reduced
- Consumer-impacting change exists but evidence or impact is below Critical threshold

## Minor

Issues affecting maintainability, readability, or medium-term quality.

| Category | Examples |
|----------|----------|
| **Maintainability** | Excessive complexity, duplicated logic, unclear module boundaries |
| **Readability** | Ambiguous naming, difficult control flow, poor local context |
| **Design Hygiene** | Tight coupling, low-cohesion utility placement |

### Indicators
- Complex change with limited local explanation
- Duplication likely to drift over time
- Readability issues that increase future defect risk

## Nit

Low-impact polish and consistency suggestions.

| Category | Examples |
|----------|----------|
| **Style Consistency** | Formatting or local style drift |
| **Naming Polish** | Naming clarity improvements with negligible behavioral impact |
| **Comment Hygiene** | Outdated comments or missing short contextual notes |

### Indicators
- Cosmetic inconsistency without runtime impact
- Minor naming or organization cleanup opportunities

## Confidence Axis

Confidence qualifies how strongly evidence supports a finding.

| Confidence Tier | Score Range | Interpretation |
|-----------------|-------------|----------------|
| **High** | `>= 0.8` | Strong direct evidence; severity can be acted on directly |
| **Medium** | `0.5 - 0.79` | Credible but partially indirect evidence; include verification notes |
| **Low** | `< 0.5` | Weak or indirect evidence; avoid automatic escalation |

## Critical vs Major Boundary Guidance

| Decision Factor | Critical Lean | Major Lean |
|-----------------|--------------|------------|
| **Data Risk** | Data loss/corruption likely or irreversible | Data inconsistency possible but recoverable |
| **Business Logic Impact** | Core transaction/authorization correctness is broken | Limited-path incorrect behavior without systemic failure |
| **Rollback/Mitigation** | No safe rollback path for high-impact change | Rollback or mitigation exists and is practical |
| **Observability Effect** | Incident detection/containment capability critically degraded | Detection degraded but still operationally manageable |

## Escalation Conditions

A Major finding is considered a `REQUEST_CHANGES` candidate when all conditions hold:

- Impacts at least one critical domain (`authentication/authorization`, `payment/billing`, `data integrity/migration`, `availability/reliability`)
- Impact is high for users, service continuity, or data correctness
- Confidence is Medium or High (`>= 0.5`)

If confidence is Low, keep the finding non-escalated and request manual verification.
