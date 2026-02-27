# Report Format

Detailed Markdown report structure and finding schema for code security audit output.

## Table of Contents

- [Report Structure](#report-structure)
- [Section Specifications](#section-specifications)
- [Finding Schema](#finding-schema)
- [Severity Classification](#severity-classification)
- [Report Template](#report-template)

---

## Report Structure

```
# Security Audit Report
├── Audit Metadata
├── Executive Summary
├── Findings Summary Table
├── Detailed Findings
│   ├── Critical Findings
│   ├── High Findings
│   ├── Medium Findings
│   ├── Low Findings
│   └── Informational
├── Domain Analysis
│   ├── [Domain 1] Analysis
│   ├── [Domain 2] Analysis
│   └── ...
├── Remediation Roadmap
└── Appendix
    ├── Methodology
    ├── Scope & Limitations
    └── Reference Mapping
```

---

## Section Specifications

### Audit Metadata

```yaml
fields:
  - audit_date: "Date of audit execution"
  - target: "Codebase path or repository name"
  - asvs_level: "L1 / L2 / L3"
  - focus_areas: "Specified focus domains or 'All'"
  - technology_stack: "Detected languages, frameworks, infrastructure"
  - files_analyzed: "Approximate count of security-relevant files reviewed"
  - auditor: "AI-assisted audit (OWASP 4-source methodology)"
```

### Executive Summary

```yaml
content:
  - risk_posture: "One-line overall risk assessment (Critical / High / Moderate / Low / Minimal)"
  - finding_counts: "Table of findings by severity"
  - top_risks: "Top 3-5 most critical issues in bullet points"
  - positive_observations: "Well-implemented security controls observed"
  - key_recommendation: "Single most important remediation action"
```

### Findings Summary Table

```yaml
columns:
  - id: "Sequential finding ID (F-001, F-002, ...)"
  - severity: "Critical / High / Medium / Low / Info"
  - title: "Short descriptive title"
  - domain: "ASVS domain (V1-V17)"
  - asvs_id: "Specific ASVS requirement ID"
  - cwe: "CWE identifier"
  - location: "file:line or file(s)"
  - status: "New"
sort_order: "severity DESC, then domain ASC"
```

### Detailed Findings

Each finding is a self-contained section with full context.

### Domain Analysis

Per-domain summary sections covering:

```yaml
content:
  - domain_scope: "What was checked in this domain"
  - requirements_checked: "Count and list of ASVS requirements verified"
  - pass_count: "Requirements satisfied"
  - fail_count: "Requirements not satisfied (linked to findings)"
  - not_applicable: "Requirements not applicable to this codebase"
  - notes: "Domain-specific observations"
```

### Remediation Roadmap

```yaml
content:
  - priority_1_immediate: "Critical and High findings — fix before next release"
  - priority_2_short_term: "Medium findings — address within 1-2 sprints"
  - priority_3_long_term: "Low findings and improvements — backlog items"
  - estimated_effort: "Rough effort indication per finding group"
```

### Appendix

```yaml
sections:
  methodology:
    - "OWASP ASVS 5.0.0 as verification baseline"
    - "OWASP API Security Top 10 2023 for API risk assessment"
    - "OWASP CheatSheet Series for remediation guidance"
    - "OWASP WSTG for test methodology reference"
    - "Automated code search + manual code review by AI agent"

  scope_limitations:
    - "Files/directories explicitly excluded"
    - "Domains not applicable to this codebase"
    - "Dynamic behavior not verifiable via static code review"
    - "Third-party service configurations not inspected"
    - "Runtime-only vulnerabilities requiring live testing"

  reference_mapping:
    - "Table mapping each finding to ASVS, API Top 10, CWE, WSTG IDs"
```

---

## Finding Schema

Each finding follows this structure:

```markdown
### F-{NNN}: {Title}

| Field | Value |
|-------|-------|
| **Severity** | Critical / High / Medium / Low / Info |
| **Confidence** | Confirmed / Likely / Possible |
| **CVSS** | {score} ({vector string}) — optional, include when stakeholder reporting requires standardized risk scoring |
| **ASVS** | V{X}.{Y}.{Z} — {Requirement description} |
| **CWE** | CWE-{NNN} — {CWE title} |
| **API Top 10** | API{N}:2023 — {Risk title} (if applicable) |
| **WSTG** | WSTG-{CAT}-{NN} (if applicable) |
| **Location** | `path/to/file.ext:line` |

**Description**

{What the vulnerability is and why it matters. 2-4 sentences.}

**Evidence**

\```{language}
// Vulnerable code snippet from the codebase
{code}
\```

**Impact**

{What an attacker could achieve by exploiting this. 1-3 sentences.}

**Remediation**

{Specific fix guidance with code example.}

\```{language}
// Secure code replacement
{fixed_code}
\```

**References**
- OWASP CheatSheet: {CheatSheet name}
- {Additional references}
```

---

## Severity Classification

### Severity Decision Matrix

```yaml
critical:
  criteria:
    - "Remote Code Execution (RCE)"
    - "SQL Injection with data extraction capability"
    - "Authentication bypass (complete)"
    - "Hardcoded credentials for production systems"
    - "Unrestricted file upload with execution capability"
  asvs_level: "L1 requirement failure"
  typical_cwe: [CWE-89, CWE-78, CWE-287, CWE-798, CWE-434]

high:
  criteria:
    - "Broken Object Level Authorization (BOLA)"
    - "Broken Function Level Authorization (BFLA)"
    - "SSRF with internal network access"
    - "Weak password storage (MD5/SHA1, no salt)"
    - "JWT none algorithm or weak verification"
    - "Stored XSS in privileged context"
  asvs_level: "L1 requirement failure (non-critical path) or L2 critical path"
  typical_cwe: [CWE-639, CWE-285, CWE-918, CWE-916, CWE-347, CWE-79]

medium:
  criteria:
    - "Missing security headers (CSP, HSTS)"
    - "CORS misconfiguration"
    - "Verbose error messages with stack traces"
    - "Missing rate limiting on sensitive endpoints"
    - "Reflected XSS"
    - "Mass assignment without critical field exposure"
    - "TLS verification disabled in non-critical path"
  asvs_level: "L2 requirement failure"
  typical_cwe: [CWE-693, CWE-942, CWE-209, CWE-770, CWE-79, CWE-915]

low:
  criteria:
    - "Missing security logging"
    - "Incomplete input validation (non-injection context)"
    - "Cookie without optimal attributes"
    - "Minor configuration improvements"
    - "Deprecated but not yet exploitable crypto usage"
  asvs_level: "L2 minor or L3 requirement failure"
  typical_cwe: [CWE-778, CWE-20, CWE-614, CWE-16]

info:
  criteria:
    - "Best practice recommendations"
    - "Code quality observations with indirect security impact"
    - "Dependency update suggestions"
    - "Architecture improvement notes"
  asvs_level: "L3 or beyond ASVS scope"
```

### Confidence Levels

```yaml
confirmed:
  definition: "Vulnerable pattern directly observed with exploitable context"
  evidence: "Code snippet shows injection vector + data flows from user input to sink"
  action: "Must fix"

likely:
  definition: "Pattern matches known vulnerability, context strongly suggests exploitability"
  evidence: "Vulnerable pattern present, but full data flow requires runtime verification"
  action: "Should fix; verify exploitability if needed"

possible:
  definition: "Suspicious pattern found, exploitability depends on runtime context"
  evidence: "Pattern could be vulnerable depending on framework behavior or configuration"
  action: "Investigate; fix if exploitable"
```

---

## Report Template

```markdown
# Security Audit Report

## Audit Metadata

| Field | Value |
|-------|-------|
| Date | {YYYY-MM-DD} |
| Target | {codebase path or repo} |
| ASVS Level | {L1/L2/L3} |
| Focus Areas | {domains or "All"} |
| Technology Stack | {detected stack} |
| Files Analyzed | {count} |
| Methodology | OWASP 4-source (ASVS 5.0.0 + API Top 10 2023 + CheatSheet + WSTG) |

---

## Executive Summary

**Overall Risk Posture: {Critical/High/Moderate/Low/Minimal}**

| Severity | Count |
|----------|-------|
| Critical | {n} |
| High | {n} |
| Medium | {n} |
| Low | {n} |
| Info | {n} |
| **Total** | **{N}** |

### Top Risks
1. {Most critical finding summary}
2. {Second most critical}
3. {Third most critical}

### Positive Observations
- {Well-implemented security control}
- {Good practice observed}

### Key Recommendation
{Single most impactful remediation action}

---

## Findings Summary

| ID | Severity | Title | Domain | ASVS | CWE | Location |
|----|----------|-------|--------|------|-----|----------|
| F-001 | Critical | {title} | V{X} | V{X}.{Y}.{Z} | CWE-{N} | `{file:line}` |
| F-002 | High | {title} | V{X} | V{X}.{Y}.{Z} | CWE-{N} | `{file:line}` |
| ... | ... | ... | ... | ... | ... | ... |

---

## Detailed Findings

### Critical

{Finding sections using Finding Schema}

### High

{Finding sections}

### Medium

{Finding sections}

### Low

{Finding sections}

### Informational

{Finding sections}

---

## Domain Analysis

### V{X} {Domain Name}

**Requirements Checked**: {n} / {total applicable}
**Pass**: {n} | **Fail**: {n} | **N/A**: {n}

{Domain-specific observations and notes}

{Repeat for each applicable domain}

---

## Remediation Roadmap

### Priority 1: Immediate (Critical + High)
| Finding | Effort | Description |
|---------|--------|-------------|
| F-001 | {Low/Medium/High} | {brief fix description} |

### Priority 2: Short-term (Medium)
| Finding | Effort | Description |
|---------|--------|-------------|
| F-00X | {Low/Medium/High} | {brief fix description} |

### Priority 3: Long-term (Low + Info)
| Finding | Effort | Description |
|---------|--------|-------------|
| F-00X | {Low/Medium/High} | {brief fix description} |

---

## Appendix

### Methodology
This audit was performed using the OWASP 4-source methodology:
- **ASVS 5.0.0**: Verification requirements baseline ({level})
- **API Security Top 10 2023**: API risk taxonomy
- **CheatSheet Series**: Secure coding remediation guidance
- **WSTG**: Testing methodology reference

### Scope & Limitations
- {Explicit exclusions}
- {Domains not applicable}
- {Dynamic behavior caveats}

### Cross-Reference Mapping
| Finding | ASVS | API Top 10 | CWE | WSTG | CheatSheet |
|---------|------|------------|-----|------|------------|
| F-001 | V{X}.{Y}.{Z} | API{N}:2023 | CWE-{N} | WSTG-{CAT}-{NN} | {Sheet name} |
```
