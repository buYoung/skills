# Impact Detection

Techniques for identifying side effects, consumer impact, and contract compatibility of code changes.

## Change Surface Identification

Changed entities are analyzed by role:

- **Behavioral units**: Functions, methods, handlers, jobs, workflows
- **Data contracts**: Request/response payloads, persisted schemas, serialized structures
- **Operational contracts**: Runtime entrypoints, scheduled tasks, event names, configuration keys

## Symbol Exposure Analysis

Exposure is classified by externally consumable surface:

| Exposure Type | Description | Typical Evidence |
|---------------|-------------|------------------|
| **Externally Consumable Interface** | Contracts consumed across module/service boundaries | Public exports, API descriptors, protocol definitions |
| **Module/Package Public Surface** | Symbols intended for downstream consumers | Re-export files, package entrypoint files, public manifest mappings |
| **Runtime Entrypoint Contract** | Startup, routing, eventing, or job invocation interfaces | Route maps, event registration, scheduler/worker bindings |

## Dependency Tracing

### Exact Symbol Lookup
```bash
rg -F "<symbol_name>(" .
```
- **Purpose**: Finds direct executable call sites for changed callable symbols

### Broader Reference Lookup
```bash
rg "<symbol_name>" .
```
- **Purpose**: Finds textual references when exact call patterns are insufficient

### Boundary/Entrypoint Lookup
```bash
rg "<entrypoint_or_contract_name>" .
```
- **Purpose**: Identifies where a changed contract is wired into runtime behavior

### Exposure Lookup
```bash
rg "<public_surface_indicator>.*<symbol_name>|<symbol_name>.*<public_surface_indicator>" .
```
- **Purpose**: Confirms whether changed entities are reachable from external consumers

## Consumer Counting

Consumer impact is computed in two steps:

1. **Raw Match Count**
- Count all matches from broad search to establish initial reference volume

2. **Normalized Consumer Count**
- Include: production runtime references and executable call sites
- Exclude: definition lines, comments/doc-only references, test-only references, generated files, vendor/third_party code
- Deduplicate multiple references from the same logical consumer location

> Normalized Consumer Count is the authoritative signal for impact and breaking-change severity.

## Evidence Confidence Model

| Confidence | Score Range | Characteristics |
|------------|-------------|-----------------|
| **High** | `>= 0.8` | Multiple direct executable references with call-path confirmation |
| **Medium** | `0.5 - 0.79` | References exist but aliasing/re-export/indirection leaves partial uncertainty |
| **Low** | `< 0.5` | Evidence depends on strings, reflection, dynamic dispatch, or incomplete traceability |

### Verification Status Mapping

| Verification Status | Criteria |
|---------------------|----------|
| **Verified** | High-confidence evidence with executable reference path |
| **Partially Verified** | Medium-confidence evidence with unresolved indirection |
| **Unverifiable** | Low-confidence evidence where static tracing cannot prove runtime linkage |

Unverifiable findings are included explicitly in the review report under analysis limitations.

## Impact Categories

### Direct Impact
- **Callers/Invokers**: Executable consumers that directly invoke changed behavior
- **Contract Consumers**: Components that parse, validate, or depend on changed contracts
- **Runtime Integrations**: Route/event/job bindings mapped to changed interfaces

### Indirect Impact
- **Transitive Consumers**: Callers downstream from direct consumers
- **Shared State Dependents**: Components reading or writing affected shared state
- **Operational Coupling**: Alerting, retry, caching, and fallback layers coupled to changed behavior

## Behavioral Test Coverage Check

Coverage analysis evaluates changed behavior units, not only file presence.

1. Map changed behavior units from the patch
2. Identify tests asserting those behaviors (success path, failure path, boundary conditions)
3. Classify coverage:
- **Covered**: Relevant assertions exist for changed behavior
- **Partially Covered**: Assertions exist but miss critical branch/edge path
- **Not Covered**: No relevant assertions found

### Risk Escalation for Missing Coverage

| Coverage Status | Escalation Guidance |
|-----------------|---------------------|
| **Covered** | No automatic escalation |
| **Partially Covered** | Consider one-level risk increase when change is high impact |
| **Not Covered** | Increase risk level for behavior/regression findings |

## Breaking Change Detection (Generic)

Breaking-change checks are contract-oriented and language-agnostic.

| Contract Change Type | Breaking? | Detection Signal |
|----------------------|-----------|------------------|
| **Required input increased** | Yes | New mandatory field/argument/parameter requirement |
| **Accepted value domain narrowed** | Yes | Removed valid values, stricter validation without compatibility path |
| **Output contract changed incompatibly** | Yes | Removed/renamed output fields or changed semantic guarantees |
| **Endpoint/operation signature changed** | Yes | Path/method/operation name or invocation shape changed |
| **Externally consumed member removed/renamed** | Yes | Consumer-visible symbol removed or renamed without compatibility layer |
| **Additive backward-compatible extension** | No (usually) | Optional additions preserving existing consumer behavior |

### Decision Signal

- If a breaking contract change has normalized consumers > 0, classify at least as **Critical candidate**
- Final severity considers impact magnitude, confidence, and critical-domain context

## Risk Indicators

| Indicator | Base Risk | Description |
|-----------|-----------|-------------|
| **No Behavioral Coverage** | High | Changed behavior lacks relevant tests |
| **High Normalized Consumers** | High | Change affects many runtime consumers |
| **Exposed Public Surface** | High | Change is reachable by external consumers |
| **Shared State Mutation** | High | Global or shared state semantics are modified |
| **Data Shape Change** | High | Persisted or exchanged contract changed |
| **Config Contract Change** | Medium | Runtime config keys/semantics changed |

## Analysis Limitations

Static/textual analysis has known limits:

- Dynamic invocation, reflection, and runtime plugin loading
- Indirection through aliases, generated wiring, or external orchestration
- Cross-repository consumers not present in current workspace

These are recorded as confidence reductions and/or `Unverifiable` findings.
