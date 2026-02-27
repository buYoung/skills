# Audit Process

Complete step-by-step methodology for OWASP-based code security audits.

## Table of Contents

- [Phase 1: Reconnaissance](#phase-1-reconnaissance)
- [Phase 2: Scope Definition](#phase-2-scope-definition)
- [Phase 3: Domain Analysis](#phase-3-domain-analysis)
- [Phase 4: Finding Synthesis](#phase-4-finding-synthesis)
- [Phase 5: Remediation Mapping](#phase-5-remediation-mapping)
- [Phase 6: Report Generation](#phase-6-report-generation)

## Phase 1: Reconnaissance

Technology stack, architecture, and security-relevant areas are identified before any analysis.

### 1.1 Technology Stack Identification

```yaml
targets:
  - Package manifests: package.json, requirements.txt, go.mod, pom.xml, build.gradle, Gemfile, Cargo.toml, composer.json
  - Framework configs: next.config.js, nuxt.config.ts, angular.json, settings.py, application.yml, appsettings.json
  - Docker/infra: Dockerfile, docker-compose.yml, .env files, terraform/*.tf, k8s manifests
  - CI/CD: .github/workflows/*.yml, .gitlab-ci.yml, Jenkinsfile
```

### 1.2 Entry Point Mapping

```yaml
targets:
  - API routes: controllers/, routes/, handlers/, api/, endpoints/
  - Middleware: middleware/, filters/, interceptors/, guards/
  - Authentication: auth/, login, signup, token, session, oauth
  - File upload: upload, multipart, file, attachment, blob
  - External calls: http client usage, fetch, axios, requests, webhooks
```

### 1.3 Security Configuration Discovery

```yaml
targets:
  - Auth config: JWT secret/config, OAuth settings, session config, CORS policy
  - Crypto config: encryption keys, certificate paths, TLS settings
  - Security headers: helmet, CSP, HSTS, X-Frame-Options settings
  - Logging config: log levels, sensitive data masking, audit trail
  - Environment: .env, .env.example, secrets management, config injection
```

### 1.4 Data Flow Mapping

```yaml
targets:
  - User input entry: request body parsing, query params, path params, headers, cookies
  - Database interaction: ORM models, raw queries, migration files, schema definitions
  - External API calls: third-party integrations, webhook handlers, service-to-service
  - Output rendering: template engines, response serialization, HTML generation
  - File I/O: file read/write, temporary files, log files, export/import
```

## Phase 2: Scope Definition

### 2.1 ASVS Level Selection

| Level | Target | Coverage |
|-------|--------|----------|
| **L1** | All applications (minimum baseline) | ~86 requirements — essential controls |
| **L2** | Applications handling sensitive data (recommended default) | ~230 requirements — standard security |
| **L3** | Critical applications (banking, healthcare, military) | ~345 requirements — comprehensive defense |

### 2.2 Domain Applicability Matrix

Domain applicability is determined based on the technology stack discovered in Phase 1.

| Domain | Applies When |
|--------|-------------|
| V1 Encoding & Sanitization | Always |
| V2 Validation & Business Logic | Always |
| V3 Web Frontend Security | Frontend code exists (HTML, JS, templates) |
| V4 API & Web Service | API endpoints exist (REST, GraphQL, SOAP) |
| V5 File Handling | File upload/download/processing exists |
| V6 Authentication | Auth system exists |
| V7 Session Management | Session-based auth exists |
| V8 Authorization | Multi-role or resource-based access exists |
| V9 Self-contained Tokens | JWT or similar token usage exists |
| V10 OAuth & OIDC | OAuth/OIDC integration exists |
| V11 Cryptography | Encryption, hashing, or signing is used |
| V12 Secure Communication | Network communication exists |
| V13 Configuration | Always |
| V14 Data Protection | PII, financial, or health data is processed |
| V15 Secure Coding & Architecture | Always |
| V16 Logging & Error Handling | Always |
| V17 WebRTC | WebRTC functionality exists |

### 2.3 Focus Area Prioritization

Focus areas map to domains as follows:

```yaml
mapping:
  injection: [V1, V2]
  authentication: [V6, V7, V9, V10]
  authorization: [V8]
  cryptography: [V11, V12]
  api-security: [V4, V17]
  session: [V7, V9, V10]
  file-handling: [V5]
  data-protection: [V14]
  configuration: [V13, V16]
  secure-coding: [V3, V15]
```

## Phase 3: Domain Analysis

Each applicable domain follows this analysis loop:

```
For each domain:
  1. Identify relevant code files using reconnaissance data
  2. Read and analyze code against domain-specific requirements
  3. Check for known vulnerability patterns (→ vulnerability_patterns.md)
  4. Record findings with:
     - Location (file:line)
     - ASVS requirement ID
     - CWE ID
     - Severity level
     - Evidence (code snippet)
     - Confidence (confirmed / likely / possible)
```

### Analysis Priorities Per Domain

Domains are ordered by this priority for maximum early detection:

```
Priority 1 (Critical attack surface):
  → V1 Encoding & Sanitization (injection is top risk)
  → V6 Authentication (auth bypass = full compromise)
  → V8 Authorization (access control failures)

Priority 2 (High impact):
  → V4 API & Web Service
  → V11 Cryptography
  → V14 Data Protection
  → V15 Secure Coding & Architecture

Priority 3 (Standard coverage):
  → V2 Validation & Business Logic
  → V7 Session Management
  → V9 Self-contained Tokens
  → V13 Configuration
  → V16 Logging & Error Handling

Priority 4 (Specialized):
  → V3 Web Frontend Security
  → V5 File Handling
  → V10 OAuth & OIDC
  → V12 Secure Communication
  → V17 WebRTC
```

### Search Strategies Per Domain

```yaml
V1_encoding:
  search_terms: [escape, encode, sanitize, htmlspecialchars, encodeURI, DOMPurify, parameterized, prepared]
  anti_patterns: [innerHTML, dangerouslySetInnerHTML, string concatenation in queries, eval, exec]

V6_authentication:
  search_terms: [login, authenticate, password, hash, bcrypt, argon2, jwt.sign, jwt.verify, compareSync]
  anti_patterns: [plaintext password, md5, sha1 for passwords, hardcoded secrets, "alg":"none"]

V8_authorization:
  search_terms: [authorize, permission, role, guard, policy, canActivate, @Roles, isAdmin, hasPermission]
  anti_patterns: [missing auth checks on routes, client-side-only auth, direct object reference without check]

V11_cryptography:
  search_terms: [encrypt, decrypt, AES, RSA, hmac, cipher, crypto, randomBytes, generateKey]
  anti_patterns: [DES, 3DES, RC4, ECB mode, Math.random for security, hardcoded IV/key, weak key size]

V4_api:
  search_terms: [rate limit, throttle, cors, helmet, csrf, content-type validation, schema validation]
  anti_patterns: ["cors: { origin: '*' }", missing rate limit, no input size limit, verbose error response]

V2_validation:
  search_terms: [validate, validator, schema, Joi, Zod, yup, class-validator, @IsString, @IsInt]
  anti_patterns: [missing server-side validation, client-side-only validation, unchecked req.body fields]

V3_frontend:
  search_terms: [CSP, Content-Security-Policy, X-Frame-Options, frame-ancestors, SameSite, Sec-Fetch, postMessage]
  anti_patterns: [innerHTML, dangerouslySetInnerHTML, v-html, document.write, bypassSecurityTrustHtml, "unsafe-inline"]

V5_file_handling:
  search_terms: [upload, multer, multipart, file-type, magic bytes, fs.readFile, path.join, Content-Disposition]
  anti_patterns: [user filename in path, no file size limit, no extension allowlist, serve from web root]

V7_session:
  search_terms: [session, cookie, Set-Cookie, express-session, HttpOnly, Secure, SameSite, __Host-, regenerate]
  anti_patterns: [missing session regeneration on login, long session lifetime, no absolute timeout, session in URL]

V9_tokens:
  search_terms: [jwt, jsonwebtoken, jose, JWT_SECRET, token.verify, algorithms, exp, aud, iss, nbf]
  anti_patterns: ["algorithms: ['none']", missing exp check, hardcoded JWT secret, jwt.decode without verify]

V13_configuration:
  search_terms: [.env, dotenv, config, DEBUG, NODE_ENV, X-Powered-By, server header, actuator, swagger]
  anti_patterns: [DEBUG=True in production, .env committed, X-Powered-By present, actuator exposed, swagger in prod]

V14_data_protection:
  search_terms: [sensitive, PII, redact, mask, Clear-Site-Data, Cache-Control, no-store, localStorage, sessionStorage]
  anti_patterns: [password in URL, token in query string, sensitive data in logs, console.log(req.body)]

V15_secure_coding:
  search_terms: [Object.assign, spread operator, prototype, __proto__, dependency, lock file, mass assignment]
  anti_patterns: [prototype pollution, Object.assign(model, req.body), User.create(req.body), missing lock file]

V16_logging:
  search_terms: [logger, winston, pino, log4j, logging, error handler, global exception, try catch]
  anti_patterns: [stack trace in response, res.status(500).send(err), console.log(password), missing error handler]
```

## Phase 4: Finding Synthesis

### 4.1 Deduplication

Multiple source checks may flag the same underlying issue. Consolidation follows:

```
1. Group findings by file:line location
2. Merge overlapping findings into single entry
3. Keep the highest severity rating
4. Retain all cross-references (ASVS + API Top 10 + CWE + WSTG)
```

### 4.2 Cross-Source Correlation

For each finding, attach applicable references from all 4 sources:

```yaml
finding:
  asvs: "V1.2.1"                            # ASVS requirement ID
  api_top10: "API1:2023"                     # API Security risk (if applicable)
  cwe: "CWE-79"                              # CWE identifier
  wstg: "WSTG-INPV-01"                       # WSTG test scenario ID
  cheatsheet: "Cross_Site_Scripting_Prevention_Cheat_Sheet"  # Remediation source
```

### 4.3 Confidence Assessment

| Confidence | Criteria |
|------------|----------|
| **Confirmed** | Vulnerable pattern directly observed in code with exploitable context |
| **Likely** | Pattern matches known vulnerability, context strongly suggests exploitability |
| **Possible** | Suspicious pattern found, but exploitability depends on runtime context or configuration |

## Phase 5: Remediation Mapping

Each finding is paired with remediation guidance from the CheatSheet Series (→ remediation_patterns.md):

```
1. Identify the vulnerability category
2. Look up the corresponding CheatSheet
3. Extract the specific fix pattern applicable to the finding's language/framework
4. Include code-level fix example where possible
```

## Phase 6: Report Generation

The final Markdown report follows the structure in report_format.md:

```
1. Compile executive summary with statistics
2. Build findings table sorted by severity
3. Write per-domain detailed sections
4. Generate remediation roadmap (Critical → High → Medium → Low)
5. Document audit metadata (scope, limitations, methodology)
```
