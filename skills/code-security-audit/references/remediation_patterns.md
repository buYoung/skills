# Remediation Patterns

Secure coding fix patterns sourced from OWASP CheatSheet Series, organized by vulnerability category. Each pattern includes language-agnostic guidance and framework-specific examples.

## Table of Contents

- [1. Injection Prevention](#1-injection-prevention)
- [2. Authentication Hardening](#2-authentication-hardening)
- [3. Authorization Enforcement](#3-authorization-enforcement)
- [4. Session Security](#4-session-security)
- [4b. CSRF Prevention](#4b-csrf-prevention)
- [5. Cryptography Best Practices](#5-cryptography-best-practices)
- [6. XSS Prevention](#6-xss-prevention)
- [7. SSRF Prevention](#7-ssrf-prevention)
- [8. File Upload Security](#8-file-upload-security)
- [9. Error Handling and Logging](#9-error-handling-and-logging)
- [10. Security Headers](#10-security-headers)
- [11. API Security](#11-api-security)
- [12. Secrets Management](#12-secrets-management)
- [13. Dependency Security](#13-dependency-security)

---

## 1. Injection Prevention

**CheatSheets**: Injection_Prevention, SQL_Injection_Prevention, Query_Parameterization, OS_Command_Injection_Defense, LDAP_Injection_Prevention

### SQL Injection

```yaml
principle: "Never concatenate user input into SQL. Use parameterized queries or ORM methods."

fix_by_language:
  javascript_node:
    - library: "pg (PostgreSQL)"
      secure: "pool.query('SELECT * FROM users WHERE id = $1', [userId])"
    - library: "mysql2"
      secure: "connection.execute('SELECT * FROM users WHERE id = ?', [userId])"
    - library: "Knex.js"
      secure: "knex('users').where('id', userId).first()"
    - library: "Prisma"
      secure: "prisma.user.findUnique({ where: { id: userId } })"

  python:
    - library: "psycopg2"
      secure: "cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))"
    - library: "SQLAlchemy"
      secure: "session.query(User).filter(User.id == user_id).first()"
    - library: "Django ORM"
      secure: "User.objects.filter(id=user_id).first()"

  java:
    - library: "JDBC"
      secure: "PreparedStatement ps = conn.prepareStatement('SELECT * FROM users WHERE id = ?'); ps.setInt(1, userId);"
    - library: "JPA/Hibernate"
      secure: "em.createQuery('SELECT u FROM User u WHERE u.id = :id', User.class).setParameter('id', userId)"
    - library: "Spring Data"
      secure: "@Query('SELECT u FROM User u WHERE u.id = :id') findById(@Param('id') Long id)"

  csharp:
    - library: "ADO.NET"
      secure: "cmd.Parameters.AddWithValue('@id', userId);"
    - library: "Entity Framework"
      secure: "context.Users.Where(u => u.Id == userId).FirstOrDefault()"

  go:
    - library: "database/sql"
      secure: "db.QueryRow('SELECT * FROM users WHERE id = $1', userId)"
    - library: "GORM"
      secure: "db.Where('id = ?', userId).First(&user)"

  php:
    - library: "PDO"
      secure: "$stmt = $pdo->prepare('SELECT * FROM users WHERE id = :id'); $stmt->execute(['id' => $userId]);"
    - library: "Eloquent"
      secure: "User::find($userId);"

  ruby:
    - library: "ActiveRecord"
      secure: "User.where(id: user_id).first"
    - library: "Sequel"
      secure: "DB[:users].where(id: user_id).first"
```

### OS Command Injection

```yaml
principle: "Avoid shell execution. Use language-native APIs or parameterized subprocess calls."

fix_by_language:
  javascript: "execFile('ping', [host]) instead of exec(`ping ${host}`)"
  python: "subprocess.run(['ping', host], shell=False)"
  java: "new ProcessBuilder('ping', host).start()"
  go: "exec.Command('ping', host).Output()"
  ruby: "Open3.capture3('ping', host)"
  php: "Use escapeshellarg($host) if shell is unavoidable"
```

---

## 2. Authentication Hardening

**CheatSheets**: Authentication, Password_Storage, Credential_Stuffing_Prevention, Forgot_Password, Multifactor_Authentication

### Password Hashing

```yaml
principle: "Use a dedicated password hashing algorithm with salt and appropriate work factor."

recommended_algorithms:
  - name: "Argon2id"
    priority: 1
    params: "m=19456 (19 MiB), t=2, p=1"
  - name: "bcrypt"
    priority: 2
    params: "cost factor >= 10 (12 recommended)"
  - name: "scrypt"
    priority: 3
    params: "N=2^17, r=8, p=1"
  - name: "PBKDF2-HMAC-SHA256"
    priority: 4
    params: "iterations >= 600,000"

fix_by_language:
  javascript: "const hash = await bcrypt.hash(password, 12)"
  python: "from passlib.hash import argon2; hash = argon2.using(rounds=4).hash(password)"
  java: "BCrypt.hashpw(password, BCrypt.gensalt(12))"
  go: "bcrypt.GenerateFromPassword([]byte(password), 12)"
  php: "password_hash($password, PASSWORD_ARGON2ID)"
  ruby: "BCrypt::Password.create(password, cost: 12)"
  csharp: "BCrypt.Net.BCrypt.HashPassword(password, workFactor: 12)"
```

### Rate Limiting on Auth Endpoints

```yaml
principle: "Apply aggressive rate limiting on login, registration, and password reset endpoints."

recommended_limits:
  login: "5 attempts per minute per IP, 10 per minute per account"
  password_reset: "3 per hour per account"
  registration: "5 per hour per IP"
  otp_verification: "5 attempts per token"

fix_by_framework:
  express: "app.use('/auth', rateLimit({ windowMs: 60000, max: 5 }))"
  django: "django-ratelimit: @ratelimit(key='ip', rate='5/m', method='POST')"
  spring: "Bucket4j or Resilience4j rate limiter"
  aspnet: "AspNetCoreRateLimit middleware"
  fastapi: "slowapi: @limiter.limit('5/minute')"
```

---

## 3. Authorization Enforcement

**CheatSheets**: Access_Control, Authorization, Insecure_Direct_Object_Reference_Prevention

### Object-Level Authorization (BOLA Prevention)

```yaml
principle: "Every data access using a user-supplied ID must verify the requester owns or has access to the resource."

patterns:
  - name: "Ownership filter"
    description: "Add owner check to every query"
    example: "SELECT * FROM orders WHERE id = :orderId AND user_id = :currentUserId"

  - name: "Policy/guard pattern"
    description: "Centralized authorization check before handler execution"
    frameworks:
      express: "middleware that loads resource and checks req.user.id === resource.ownerId"
      spring: "@PreAuthorize('#userId == authentication.principal.id')"
      django: "get_object_or_404(Order, id=order_id, user=request.user)"
      rails: "before_action :authorize_resource; current_user.orders.find(params[:id])"
      nestjs: "@UseGuards(ResourceOwnerGuard)"
      laravel: "$this->authorize('view', $order) using Policy class"
```

### Function-Level Authorization (BFLA Prevention)

```yaml
principle: "Deny by default. Every endpoint must have explicit role/permission check."

patterns:
  - name: "Route-level middleware"
    frameworks:
      express: "router.use('/admin', requireRole('admin'))"
      spring: "@Secured('ROLE_ADMIN') or SecurityFilterChain config"
      django: "@permission_required('app.admin_access')"
      rails: "before_action :require_admin, only: [:destroy, :update]"
      nestjs: "@Roles('admin') with RolesGuard"
      laravel: "Route::middleware('role:admin')->group(...)"
      aspnet: "[Authorize(Roles = 'Admin')]"

  - name: "Default deny configuration"
    description: "Framework security config denies all routes by default, explicitly opens permitted ones"
```

---

## 4. Session Security

**CheatSheet**: Session_Management

```yaml
cookie_attributes:
  Secure: "true — only transmitted over HTTPS"
  HttpOnly: "true — not accessible via JavaScript"
  SameSite: "Lax or Strict — prevents CSRF"
  Path: "/ or specific path"
  Max-Age: "reasonable session duration"
  prefix: "__Host- (strongest) or __Secure-"

fix_by_framework:
  express: |
    app.use(session({
      cookie: { secure: true, httpOnly: true, sameSite: 'lax', maxAge: 3600000 },
      name: '__Host-session'
    }))
  django: |
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_AGE = 3600
  spring: |
    server.servlet.session.cookie.secure=true
    server.servlet.session.cookie.http-only=true
    server.servlet.session.cookie.same-site=lax
  rails: |
    Rails.application.config.session_store :cookie_store,
      secure: true, httponly: true, same_site: :lax
  laravel: |
    'secure' => true, 'http_only' => true, 'same_site' => 'lax' // config/session.php

session_regeneration:
  principle: "Regenerate session ID after authentication state changes (login, privilege escalation, re-authentication) to prevent session fixation."
  fix_by_framework:
    express: "req.session.regenerate((err) => { /* restore user data to new session */ })"
    django: "request.session.cycle_key() — called automatically on login() by default"
    spring: "SessionManagementConfigurer.sessionFixation().migrateSession() (default in Spring Security)"
    rails: "reset_session in SessionsController#create"
    laravel: "Session::regenerate() or $request->session()->regenerate()"
    aspnet: "HttpContext.Session.Clear() + generate new session on login"
    flask: "session.regenerate() or clear and recreate session after login"
    fastapi: "Create new session token and invalidate old one in login handler"
```

---

## 4b. CSRF Prevention

**CheatSheets**: Cross-Site_Request_Forgery_Prevention

```yaml
principle: "Verify that state-changing requests originate from the application itself, not from a cross-origin attacker site."

defense_layers:
  layer_1_samesite_cookie:
    description: "Primary defense — prevents cookies from being sent on cross-origin requests"
    fix_by_framework:
      express: "cookie: { sameSite: 'lax' } or 'strict'"
      django: "SESSION_COOKIE_SAMESITE = 'Lax'"
      spring: "server.servlet.session.cookie.same-site=lax"
      rails: "same_site: :lax in session config"
      laravel: "'same_site' => 'lax' in config/session.php"

  layer_2_csrf_token:
    description: "Synchronizer token pattern — required when SameSite alone is insufficient (e.g., same-site subdomain attacks)"
    fix_by_framework:
      express: "app.use(csurf({ cookie: { sameSite: 'strict', httpOnly: true } }))"
      django: "CsrfViewMiddleware (enabled by default), {% csrf_token %} in forms"
      spring: "CsrfConfigurer enabled by default in Spring Security; use CsrfTokenRequestAttributeHandler"
      rails: "protect_from_forgery with: :exception (enabled by default)"
      laravel: "@csrf directive in Blade forms, VerifyCsrfToken middleware"
      aspnet: "@Html.AntiForgeryToken() + [ValidateAntiForgeryToken] on POST actions"

  layer_3_custom_header:
    description: "For AJAX/API requests — require a custom header that cannot be sent cross-origin without preflight"
    pattern: "Require X-Requested-With or custom header; verify server-side"
    note: "Effective because custom headers trigger CORS preflight, which blocks cross-origin requests"

  layer_4_origin_validation:
    description: "Verify Origin or Referer header matches expected domain"
    pattern: "Check req.headers.origin against allowlist of trusted origins"
    note: "Fallback defense; Origin header may be absent in some browser contexts"

anti_patterns:
  - "csrf_exempt on state-changing views without documented justification (Django)"
  - "CSRF protection disabled globally for convenience"
  - "GET requests performing state-changing operations"
  - "CSRF token in URL query parameter (leaks via Referer header)"
```

---

## 5. Cryptography Best Practices

**CheatSheets**: Cryptographic_Storage, Key_Management

```yaml
algorithm_selection:
  symmetric_encryption: "AES-256-GCM or ChaCha20-Poly1305 (authenticated encryption)"
  asymmetric_encryption: "RSA-2048+ (OAEP padding) or ECDH P-256+"
  signing: "ECDSA P-256, Ed25519, or RSA-2048+ PSS"
  hashing: "SHA-256, SHA-384, SHA-512, SHA-3, BLAKE2"
  password_hashing: "Argon2id, bcrypt, scrypt, PBKDF2 (see Section 2)"
  mac: "HMAC-SHA256 or KMAC"

deprecated_do_not_use:
  - "DES, 3DES, RC4, Blowfish (symmetric)"
  - "RSA < 2048 bits, DSA (asymmetric)"
  - "MD5, SHA-1 (hashing for security)"
  - "ECB mode (block cipher mode)"
  - "PKCS#1 v1.5 padding for RSA encryption"

key_management:
  - "Never hardcode keys in source code"
  - "Use environment variables, KMS (AWS KMS, GCP KMS, Azure Key Vault), or HashiCorp Vault"
  - "Rotate keys periodically; support key versioning"
  - "Use separate keys for encryption vs signing"
  - "Generate IVs/nonces using CSPRNG; never reuse"
```

---

## 6. XSS Prevention

**CheatSheets**: Cross_Site_Scripting_Prevention, DOM_based_XSS_Prevention, Content_Security_Policy

```yaml
principle: "Context-aware output encoding + Content Security Policy as defense-in-depth."

context_encoding:
  html_body: "HTML entity encoding: & < > \" '"
  html_attribute: "Attribute encoding; always quote attribute values"
  javascript: "JavaScript encoding; avoid inserting user data in script blocks"
  css: "CSS encoding for property values from user input"
  url: "URL encoding for user data in URL parameters"

framework_auto_escaping:
  react: "JSX auto-escapes by default. Avoid dangerouslySetInnerHTML."
  angular: "Templates auto-sanitize. Avoid bypassSecurityTrustHtml()."
  vue: "{{ }} auto-escapes. Avoid v-html with user input."
  django: "Templates auto-escape. Avoid |safe and {% autoescape off %}."
  rails: "ERB auto-escapes with <%=. Avoid raw() and html_safe."
  thymeleaf: "th:text auto-escapes. Avoid th:utext."

csp_recommended:
  policy: |
    Content-Security-Policy:
      default-src 'self';
      script-src 'self';
      style-src 'self' 'unsafe-inline';
      img-src 'self' data:;
      font-src 'self';
      connect-src 'self';
      frame-ancestors 'none';
      base-uri 'self';
      form-action 'self'
  notes:
    - "Avoid 'unsafe-inline' for script-src"
    - "Use nonce-based or hash-based CSP for inline scripts if needed"
    - "Report-uri or report-to for monitoring violations"

rich_text_sanitization:
  javascript: "DOMPurify.sanitize(html, { ALLOWED_TAGS: ['b', 'i', 'a', 'p'] })"
  python: "bleach.clean(html, tags=['b', 'i', 'a', 'p'])"
  java: "Jsoup.clean(html, Safelist.basic())"
  php: "HTMLPurifier with explicit allowed tags"
```

---

## 7. SSRF Prevention

**CheatSheet**: Server_Side_Request_Forgery_Prevention

```yaml
principle: "Validate and restrict all server-side requests to user-provided URLs."

defense_layers:
  layer_1_input_validation:
    - "Parse URL and validate scheme (only http/https)"
    - "Validate hostname against allowlist of permitted domains"
    - "Reject IP addresses in URL (or validate against blocklist)"

  layer_2_dns_resolution:
    - "Resolve hostname and check resulting IP"
    - "Block private ranges: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8, 169.254.0.0/16, ::1"
    - "Block cloud metadata: 169.254.169.254"
    - "Re-check after DNS resolution (DNS rebinding defense)"

  layer_3_request:
    - "Disable HTTP redirects or re-validate after redirect"
    - "Set timeout on requests"
    - "Do not return raw response body to user"

  layer_4_network:
    - "Isolate URL-fetching service in separate network segment"
    - "Firewall rules blocking internal network access from fetcher"
```

---

## 8. File Upload Security

**CheatSheet**: File_Upload

```yaml
validation_checklist:
  - "File size limit (both client-side and server-side)"
  - "File extension allowlist (not blocklist)"
  - "Content-type validation via magic bytes (file-type library)"
  - "Filename sanitization: strip path separators, limit length, generate random name"
  - "Scan uploaded files for malware (ClamAV or similar)"

storage_checklist:
  - "Store outside web root or in separate storage service (S3, GCS)"
  - "Use randomized filenames; store original name in database"
  - "Set restrictive file permissions"
  - "Serve uploaded files from separate domain (prevent cookie theft)"
  - "Set Content-Disposition: attachment for downloads"
  - "Set X-Content-Type-Options: nosniff on served files"

image_specific:
  - "Reprocess/resize images to strip embedded scripts or metadata"
  - "Validate image dimensions and reject unreasonable sizes"
```

---

## 9. Error Handling and Logging

**CheatSheets**: Error_Handling, Logging, Logging_Vocabulary

```yaml
error_handling:
  principle: "Return generic errors to users; log detailed errors server-side."
  patterns:
    - "Global exception handler that catches unhandled errors"
    - "Custom error response: { error: 'An unexpected error occurred', requestId: '...' }"
    - "Never expose: stack traces, SQL errors, internal paths, dependency versions"
    - "Fail-closed: on error, deny access rather than allow"

logging_security:
  what_to_log:
    - "Authentication events (login success/failure, logout)"
    - "Authorization failures"
    - "Input validation failures"
    - "Application errors and exceptions"
    - "Security-relevant configuration changes"

  what_not_to_log:
    - "Passwords or credentials"
    - "Session tokens or API keys"
    - "Credit card numbers or financial data"
    - "PII beyond what is necessary for the log purpose"

  log_injection_prevention:
    - "Encode log data: remove newlines, control characters"
    - "Use structured logging (JSON) instead of string concatenation"
    - "Validate log input length"

  log_format:
    fields: [timestamp, level, event_type, user_id, source_ip, request_id, message]
    example: '{"timestamp":"2025-01-01T00:00:00Z","level":"WARN","event":"AUTH_FAILURE","userId":"user123","sourceIp":"1.2.3.4","requestId":"req-abc","message":"Invalid credentials"}'
```

---

## 10. Security Headers

**CheatSheet**: HTTP_Headers

```yaml
required_headers:
  - header: "Strict-Transport-Security"
    value: "max-age=31536000; includeSubDomains"
    purpose: "Force HTTPS"

  - header: "X-Content-Type-Options"
    value: "nosniff"
    purpose: "Prevent MIME-type sniffing"

  - header: "X-Frame-Options"
    value: "DENY or SAMEORIGIN"
    purpose: "Prevent clickjacking"

  - header: "Content-Security-Policy"
    value: "default-src 'self'; script-src 'self'; ..."
    purpose: "Prevent XSS and data injection"

  - header: "Referrer-Policy"
    value: "strict-origin-when-cross-origin"
    purpose: "Control referrer leakage"

  - header: "Permissions-Policy"
    value: "camera=(), microphone=(), geolocation=()"
    purpose: "Restrict browser features"

remove_headers:
  - "X-Powered-By (framework fingerprinting)"
  - "Server (version disclosure)"

framework_setup:
  express: "app.use(helmet())"
  django: "SecurityMiddleware (built-in), django-csp"
  spring: "Spring Security HttpSecurity.headers() configuration"
  aspnet: "NWebsec or manual middleware"
  rails: "config.action_dispatch.default_headers"
  laravel: "spatie/laravel-csp, manual middleware"
```

---

## 11. API Security

**CheatSheets**: REST_Security, GraphQL, Web_Service_Security, Mass_Assignment

```yaml
rest_security:
  - "Enforce authentication on all endpoints (except public ones explicitly marked)"
  - "Content-Type validation: reject requests with mismatched content types"
  - "Response Content-Type: always set application/json for JSON APIs"
  - "Disable unused HTTP methods per endpoint"
  - "Pagination: enforce max page size, use cursor-based pagination"
  - "Rate limiting: per-user and per-IP limits"
  - "CORS: explicit origin allowlist, never wildcard with credentials"
  - "Input schema validation: use JSON Schema, Zod, Joi, or similar"

graphql_security:
  - "Disable introspection in production"
  - "Query depth limiting (max 10-15 levels)"
  - "Query complexity/cost analysis"
  - "Batch query limiting"
  - "Per-field authorization in resolvers"
  - "Persisted queries for production (reject arbitrary queries)"

anti_csrf:
  - "SameSite cookie attribute (Lax or Strict)"
  - "CSRF token for cookie-based session APIs"
  - "Custom header requirement (X-Requested-With) for AJAX APIs"
  - "Origin/Referer header validation"
```

---

## 12. Secrets Management

**CheatSheet**: Secrets_Management

```yaml
storage_hierarchy:
  - tier: "Best"
    method: "Dedicated secrets manager (AWS Secrets Manager, HashiCorp Vault, GCP Secret Manager)"
  - tier: "Good"
    method: "Environment variables injected at deployment (not in shell profile)"
  - tier: "Acceptable"
    method: ".env file excluded from VCS, restricted file permissions"
  - tier: "Unacceptable"
    method: "Hardcoded in source code, committed to git, in Dockerfile"

detection_patterns:
  - "grep -r 'password\\s*=' --include='*.{py,js,ts,java,go,rb,php,cs}' ."
  - "grep -r 'API_KEY\\|SECRET\\|TOKEN\\|PRIVATE_KEY' --include='*.{py,js,ts,java,go,rb,php,cs}' ."
  - "Check .gitignore includes .env, *.pem, *.key"
  - "Check git history for previously committed secrets (git log -p -S 'password')"

rotation:
  - "Automated rotation where supported (AWS SecretsManager rotation)"
  - "Separate secrets per environment (dev/staging/prod)"
  - "Revoke and rotate on suspected exposure"
```

---

## 13. Dependency Security

**CheatSheet**: Vulnerable_Dependency_Management

```yaml
checks:
  - "Lock file present and up to date (package-lock.json, poetry.lock, go.sum, etc.)"
  - "No known vulnerabilities: npm audit, pip-audit, mvn dependency-check, govulncheck"
  - "Dependencies from trusted registries only"
  - "Subresource Integrity (SRI) for CDN-loaded scripts"
  - "Minimal dependency footprint: remove unused packages"

automation:
  - "Dependabot or Renovate for automated update PRs"
  - "CI pipeline runs vulnerability scanner on every PR"
  - "SBOM (Software Bill of Materials) generation"

supply_chain:
  - "Verify package publisher/maintainer reputation"
  - "Pin exact versions in production (not ranges)"
  - "Review changelog before major version updates"
```
