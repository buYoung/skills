---
name: code-security-audit
description: Performs OWASP-based code security audits on any codebase. Analyzes source code against ASVS 5.0.0 verification requirements, API Security Top 10 2023 risk patterns, OWASP CheatSheet secure coding practices, and WSTG testing methodologies. Input is a codebase to review; output is a detailed Markdown security audit report. Use when the user requests a security audit, security review, vulnerability assessment, or code security analysis.
---

# Code Security Audit Capabilities

OWASP 4-source integrated code security audit system for universal codebase analysis.

## Knowledge Sources

- **OWASP ASVS 5.0.0**: 345 verification requirements across 17 security domains (L1/L2/L3)
- **OWASP API Security Top 10 2023**: 10 API-specific risk categories with code-level indicators
- **OWASP CheatSheet Series**: 109 practical secure coding cheat sheets for remediation guidance
- **OWASP WSTG (Web Security Testing Guide)**: 12 testing categories with 120+ test scenarios

## Source Roles

| Source | Role | Usage |
|--------|------|-------|
| ASVS 5.0.0 | Verification requirements baseline | Defines what to check — structured requirements per domain |
| API Security Top 10 2023 | Risk taxonomy | Defines what to look for — API-specific threat patterns |
| CheatSheet Series | Implementation guidance | Defines how to fix — secure coding patterns and practices |
| WSTG | Test methodology | Defines how to verify — concrete test scenarios per vulnerability |

## Domains

- **Input Handling** (V1, V2, V5): Encoding, sanitization, injection prevention, validation, file handling
- **Authentication & Session** (V6, V7, V9, V10): Auth mechanisms, session management, token handling, OAuth/OIDC
- **Authorization** (V8): Object-level, function-level, property-level access control
- **Cryptography** (V11, V12): Storage encryption, key management, TLS configuration
- **API Security** (V4, V17): REST/GraphQL/WebSocket/WebRTC security, rate limiting, resource consumption
- **Data Protection** (V14): Sensitive data exposure, privacy controls, client-side data
- **Configuration** (V13, V16): Security headers, CORS, error handling, logging, deployment hardening
- **Secure Coding** (V3, V15): Web frontend security, architecture patterns, defensive coding, concurrency safety

## Input Contract

| Field | Required | Description |
|-------|----------|-------------|
| **Codebase path** | Yes | The current workspace or repository the agent is operating in. Defaults to the active codebase; users may narrow scope to specific directories or files (e.g., `src/auth/`, `api/controllers/`) |
| **Audit level** | No | ASVS verification level (default: **L2**). See level definitions below |
| **Focus areas** | No | Security domains to prioritize. See focus area catalog below |
| **Tech context** | No | Language, framework, or architecture notes for targeted analysis |

### Audit Levels (OWASP ASVS 5.0.0)

| Level | Target Application | Requirements | Description |
|-------|-------------------|-------------|-------------|
| **L1** | All applications | ~86 | Essential baseline — covers critical vulnerabilities that are typically exploitable and must be addressed in every application (e.g., SQL injection, OS command injection, basic auth checks) |
| **L2** | Applications handling sensitive data (PII, financial, health) | ~230 | Standard security — includes L1 plus defense-in-depth controls such as SSRF protection, template injection prevention, secure session management, and proper cryptographic usage |
| **L3** | Mission-critical systems (banking, healthcare, military, infrastructure) | ~345 | Comprehensive defense — includes L1+L2 plus advanced controls such as formula injection prevention, full input canonicalization, and exhaustive cryptographic verification |

### Focus Area Catalog

| Focus Area | Domains | Example Checks |
|------------|---------|----------------|
| **authentication** | V6, V7, V9, V10 | Password storage, MFA, OAuth/OIDC flow, credential rotation |
| **authorization** | V8 | Object-level (BOLA), function-level, property-level access control |
| **injection** | V1, V2 | SQLi, XSS, command injection, LDAP/XPath injection, template injection, XXE |
| **cryptography** | V11, V12 | Weak algorithms, key management, TLS configuration, secret storage |
| **api-security** | V4, V17 | Rate limiting, resource consumption, REST/GraphQL/WebSocket security |
| **session** | V7, V9, V10 | Token handling, session fixation, cookie attributes, JWT validation, CSRF |
| **file-handling** | V5 | Path traversal, unrestricted upload, file type validation, storage security |
| **data-protection** | V14 | Sensitive data exposure, privacy controls, client-side data leakage |
| **configuration** | V13, V16 | Security headers, CORS, error handling, logging, deployment hardening |
| **secure-coding** | V3, V15 | Frontend security, concurrency safety, architecture patterns, defensive coding |

## Preconditions

- Codebase is accessible and readable
- Agent has file search and read capabilities
- If codebase structure cannot be determined, the agent reports limitations in the audit output

## Core Capabilities

- **Codebase Reconnaissance**: Identifies technology stack, frameworks, entry points, and security-relevant file areas
- **Domain-Scoped Analysis**: Systematically audits code across all 8 security domains
- **ASVS Requirement Verification**: Checks code against applicable ASVS 5.0.0 requirements at the specified level
- **Vulnerability Pattern Detection**: Identifies known vulnerable code patterns from the integrated knowledge base
- **Cross-Source Correlation**: Maps findings to ASVS requirements, API Top 10 risks, CheatSheet guidance, and WSTG test IDs
- **Severity Classification**: Rates findings as Critical/High/Medium/Low with evidence and confidence
- **Remediation Guidance**: Provides concrete fix patterns sourced from CheatSheet Series
- **Structured Report Generation**: Produces a comprehensive Markdown audit report

## Audit Workflow

```
1. Reconnaissance    → Identify stack, structure, entry points
2. Scope Definition  → Select applicable ASVS domains and level
3. Domain Analysis   → Audit each security domain systematically
4. Finding Synthesis → Deduplicate, correlate across sources, assign severity
5. Remediation Map   → Attach fix patterns per finding
6. Report Generation → Produce structured Markdown report
```

## Output Contract

The audit produces a Markdown report containing:

- **Executive Summary**: Overall risk posture, critical findings count, audit scope
- **Findings Table**: Each finding with severity, ASVS ID, CWE, evidence, and remediation
- **Domain Reports**: Per-domain detailed analysis with code references
- **Remediation Roadmap**: Prioritized fix recommendations
- **Audit Metadata**: Scope, level, limitations, methodology notes

## Severity Levels

| Level | Criteria |
|-------|----------|
| **Critical** | Exploitable vulnerability with direct security impact (RCE, SQLi, auth bypass, data breach) |
| **High** | Significant security weakness requiring prompt remediation (broken access control, weak crypto, SSRF) |
| **Medium** | Security concern with conditional exploitability (missing headers, verbose errors, weak validation) |
| **Low** | Defense-in-depth improvement or best practice deviation (logging gaps, minor config issues) |
| **Info** | Observation or recommendation with no direct security impact |

## Technical References

- **[audit_process.md](references/audit_process.md)**: Complete step-by-step audit methodology and reconnaissance procedures
- **[security_domains.md](references/security_domains.md)**: All 17 ASVS domains with code-audit-relevant requirements and cross-source mappings
- **[vulnerability_patterns.md](references/vulnerability_patterns.md)**: Concrete code-level vulnerability patterns organized by category
- **[remediation_patterns.md](references/remediation_patterns.md)**: Secure coding fix patterns from CheatSheet Series
- **[report_format.md](references/report_format.md)**: Detailed Markdown report structure and finding schema
