# Security Domains

All 17 ASVS 5.0.0 domains with code-audit-relevant requirements and cross-source mappings to API Security Top 10 2023, CheatSheet Series, and WSTG.

> **Source**: `doc/security/OWASP_Application_Security_Verification_Standard_5.0.0_en.json` (ASVS 5.0.0)
>
> Descriptions are verbatim from JSON ("Verify that" prefix removed for brevity).
>
> Documentation-only sections are listed as comments in YAML blocks.
>
> **Total: 345 requirements across 17 domains.**

## Table of Contents

- [V1 Encoding and Sanitization](#v1-encoding-and-sanitization) (30)
- [V2 Validation and Business Logic](#v2-validation-and-business-logic) (13)
- [V3 Web Frontend Security](#v3-web-frontend-security) (31)
- [V4 API and Web Service](#v4-api-and-web-service) (16)
- [V5 File Handling](#v5-file-handling) (13)
- [V6 Authentication](#v6-authentication) (47)
- [V7 Session Management](#v7-session-management) (19)
- [V8 Authorization](#v8-authorization) (13)
- [V9 Self-contained Tokens](#v9-self-contained-tokens) (7)
- [V10 OAuth and OIDC](#v10-oauth-and-oidc) (36)
- [V11 Cryptography](#v11-cryptography) (24)
- [V12 Secure Communication](#v12-secure-communication) (12)
- [V13 Configuration](#v13-configuration) (21)
- [V14 Data Protection](#v14-data-protection) (13)
- [V15 Secure Coding and Architecture](#v15-secure-coding-and-architecture) (21)
- [V16 Security Logging and Error Handling](#v16-security-logging-and-error-handling) (17)
- [V17 WebRTC](#v17-webrtc) (12)

---

## V1 Encoding and Sanitization

**30 requirements** | Sections: Encoding and Sanitization Architecture, Injection Prevention, Sanitization, Memory, String, and Unmanaged Code, Safe Deserialization

### Cross-Source Mapping

| Source | Reference |
|--------|-----------|
| API Top 10 | API7:2023 Server Side Request Forgery, API10:2023 Unsafe Consumption of APIs |
| CheatSheet | Injection_Prevention, Cross_Site_Scripting_Prevention, SQL_Injection_Prevention, DOM_based_XSS_Prevention, LDAP_Injection_Prevention, OS_Command_Injection_Defense, Query_Parameterization, Server_Side_Request_Forgery_Prevention, Deserialization, XML_External_Entity_Prevention |
| WSTG | WSTG-INPV-01 (Reflected XSS), WSTG-INPV-02 (Stored XSS), WSTG-INPV-05 (SQL Injection), WSTG-INPV-06 (LDAP Injection), WSTG-INPV-07 (XML Injection), WSTG-INPV-12 (Command Injection), WSTG-INPV-19 (SSRF) |

### Key Requirements for Code Audit

```yaml
V1.1_encoding_and_sanitization_architecture:
  - V1.1.1: [L2] input is decoded or unescaped into a canonical form only once, it is only decoded when encoded data in that form is expected, and that this is done before processing the input further, for example it is not performed after input validation or sanitization.
  - V1.1.2: [L2] the application performs output encoding and escaping either as a final step before being used by the interpreter for which it is intended or by the interpreter itself.

V1.2_injection_prevention:
  - V1.2.1: [L1] output encoding for an HTTP response, HTML document, or XML document is relevant for the context required, such as encoding the relevant characters for HTML elements, HTML attributes, HTML comments, CSS, or HTTP header fields, to avoid changing the message or document structure.
  - V1.2.2: [L1] when dynamically building URLs, untrusted data is encoded according to its context (e.g., URL encoding or base64url encoding for query or path parameters). Ensure that only safe URL protocols are permitted (e.g., disallow javascript: or data:).
  - V1.2.3: [L1] output encoding or escaping is used when dynamically building JavaScript content (including JSON), to avoid changing the message or document structure (to avoid JavaScript and JSON injection).
  - V1.2.4: [L1] data selection or database queries (e.g., SQL, HQL, NoSQL, Cypher) use parameterized queries, ORMs, entity frameworks, or are otherwise protected from SQL Injection and other database injection attacks. This is also relevant when writing stored procedures.
  - V1.2.5: [L1] the application protects against OS command injection and that operating system calls use parameterized OS queries or use contextual command line output encoding.
  - V1.2.6: [L2] the application protects against LDAP injection vulnerabilities, or that specific security controls to prevent LDAP injection have been implemented.
  - V1.2.7: [L2] the application is protected against XPath injection attacks by using query parameterization or precompiled queries.
  - V1.2.8: [L2] LaTeX processors are configured securely (such as not using the "--shell-escape" flag) and an allowlist of commands is used to prevent LaTeX injection attacks.
  - V1.2.9: [L2] the application escapes special characters in regular expressions (typically using a backslash) to prevent them from being misinterpreted as metacharacters.
  - V1.2.10: [L3] the application is protected against CSV and Formula Injection. The application must follow the escaping rules defined in RFC 4180 sections 2.6 and 2.7 when exporting CSV content. Additionally, when exporting to CSV or other spreadsheet formats (such as XLS, XLSX, or ODF), special characters (including '=', '+', '-', '@', '\t' (tab), and '\0' (null character)) must be escaped with a single quote if they appear as the first character in a field value.

V1.3_sanitization:
  - V1.3.1: [L1] all untrusted HTML input from WYSIWYG editors or similar is sanitized using a well-known and secure HTML sanitization library or framework feature.
  - V1.3.2: [L1] the application avoids the use of eval() or other dynamic code execution features such as Spring Expression Language (SpEL). Where there is no alternative, any user input being included must be sanitized before being executed.
  - V1.3.3: [L2] data being passed to a potentially dangerous context is sanitized beforehand to enforce safety measures, such as only allowing characters which are safe for this context and trimming input which is too long.
  - V1.3.4: [L2] user-supplied Scalable Vector Graphics (SVG) scriptable content is validated or sanitized to contain only tags and attributes (such as draw graphics) that are safe for the application, e.g., do not contain scripts and foreignObject.
  - V1.3.5: [L2] the application sanitizes or disables user-supplied scriptable or expression template language content, such as Markdown, CSS or XSL stylesheets, BBCode, or similar.
  - V1.3.6: [L2] the application protects against Server-side Request Forgery (SSRF) attacks, by validating untrusted data against an allowlist of protocols, domains, paths and ports and sanitizing potentially dangerous characters before using the data to call another service.
  - V1.3.7: [L2] the application protects against template injection attacks by not allowing templates to be built based on untrusted input. Where there is no alternative, any untrusted input being included dynamically during template creation must be sanitized or strictly validated.
  - V1.3.8: [L2] the application appropriately sanitizes untrusted input before use in Java Naming and Directory Interface (JNDI) queries and that JNDI is configured securely to prevent JNDI injection attacks.
  - V1.3.9: [L2] the application sanitizes content before it is sent to memcache to prevent injection attacks.
  - V1.3.10: [L2] format strings which might resolve in an unexpected or malicious way when used are sanitized before being processed.
  - V1.3.11: [L2] the application sanitizes user input before passing to mail systems to protect against SMTP or IMAP injection.
  - V1.3.12: [L3] regular expressions are free from elements causing exponential backtracking, and ensure untrusted input is sanitized to mitigate ReDoS or Runaway Regex attacks.

V1.4_memory_string_and_unmanaged_code:
  - V1.4.1: [L2] the application uses memory-safe string, safer memory copy and pointer arithmetic to detect or prevent stack, buffer, or heap overflows.
  - V1.4.2: [L2] sign, range, and input validation techniques are used to prevent integer overflows.
  - V1.4.3: [L2] dynamically allocated memory and resources are released, and that references or pointers to freed memory are removed or set to null to prevent dangling pointers and use-after-free vulnerabilities.

V1.5_safe_deserialization:
  - V1.5.1: [L1] the application configures XML parsers to use a restrictive configuration and that unsafe features such as resolving external entities are disabled to prevent XML eXternal Entity (XXE) attacks.
  - V1.5.2: [L2] deserialization of untrusted data enforces safe input handling, such as using an allowlist of object types or restricting client-defined object types, to prevent deserialization attacks. Deserialization mechanisms that are explicitly defined as insecure must not be used with untrusted input.
  - V1.5.3: [L3] different parsers used in the application for the same data type (e.g., JSON parsers, XML parsers, URL parsers), perform parsing in a consistent way and use the same character encoding mechanism to avoid issues such as JSON Interoperability vulnerabilities or different URI or file parsing behavior being exploited in Remote File Inclusion (RFI) or Server-side Request Forgery (SSRF) attacks.

```

---

## V2 Validation and Business Logic

**13 requirements** | Sections: Validation and Business Logic Documentation, Input Validation, Business Logic Security, Anti-automation

### Cross-Source Mapping

| Source | Reference |
|--------|-----------|
| API Top 10 | API4:2023 Unrestricted Resource Consumption, API6:2023 Unrestricted Access to Sensitive Business Flows |
| CheatSheet | Input_Validation, Mass_Assignment, Denial_of_Service, Bean_Validation |
| WSTG | WSTG-BUSL-01 to WSTG-BUSL-09 (Business Logic Testing), WSTG-INPV (Input Validation Testing) |

### Key Requirements for Code Audit

```yaml
# V2.1_validation_and_business_logic_documentation: (3 documentation requirements - see ASVS source)

V2.2_input_validation:
  - V2.2.1: [L1] input is validated to enforce business or functional expectations for that input. This should either use positive validation against an allow list of values, patterns, and ranges, or be based on comparing the input to an expected structure and logical limits according to predefined rules. For L1, this can focus on input which is used to make specific business or security decisions. For L2 and up, this should apply to all input.
  - V2.2.2: [L1] the application is designed to enforce input validation at a trusted service layer. While client-side validation improves usability and should be encouraged, it must not be relied upon as a security control.
  - V2.2.3: [L2] the application ensures that combinations of related data items are reasonable according to the pre-defined rules.

V2.3_business_logic_security:
  - V2.3.1: [L1] the application will only process business logic flows for the same user in the expected sequential step order and without skipping steps.
  - V2.3.2: [L2] business logic limits are implemented per the application's documentation to avoid business logic flaws being exploited.
  - V2.3.3: [L2] transactions are being used at the business logic level such that either a business logic operation succeeds in its entirety or it is rolled back to the previous correct state.
  - V2.3.4: [L2] business logic level locking mechanisms are used to ensure that limited quantity resources (such as theater seats or delivery slots) cannot be double-booked by manipulating the application's logic.
  - V2.3.5: [L3] high-value business logic flows require multi-user approval to prevent unauthorized or accidental actions. This could include but is not limited to large monetary transfers, contract approvals, access to classified information, or safety overrides in manufacturing.

V2.4_anti_automation:
  - V2.4.1: [L2] anti-automation controls are in place to protect against excessive calls to application functions that could lead to data exfiltration, garbage-data creation, quota exhaustion, rate-limit breaches, denial-of-service, or overuse of costly resources.
  - V2.4.2: [L3] business logic flows require realistic human timing, preventing excessively rapid transaction submissions.

```

---

## V3 Web Frontend Security

**31 requirements** | Sections: Web Frontend Security Documentation, Unintended Content Interpretation, Cookie Setup, Browser Security Mechanism Headers, Browser Origin Separation, External Resource Integrity, Other Browser Security Considerations

### Cross-Source Mapping

| Source | Reference |
|--------|-----------|
| API Top 10 | API8:2023 Security Misconfiguration |
| CheatSheet | Content_Security_Policy, HTTP_Headers, Clickjacking_Defense, Cross-Site_Request_Forgery_Prevention, DOM_Clobbering_Prevention, Third_Party_Javascript_Management, HTTP_Strict_Transport_Security, Unvalidated_Redirects_and_Forwards, XS_Leaks |
| WSTG | WSTG-CLNT-01 to WSTG-CLNT-13 (Client-side Testing) |

### Key Requirements for Code Audit

```yaml
# V3.1_web_frontend_security_documentation: (1 documentation requirements - see ASVS source)

V3.2_unintended_content_interpretation:
  - V3.2.1: [L1] security controls are in place to prevent browsers from rendering content or functionality in HTTP responses in an incorrect context (e.g., when an API, a user-uploaded file or other resource is requested directly). Possible controls could include: not serving the content unless HTTP request header fields (such as Sec-Fetch-\*) indicate it is the correct context, using the sandbox directive of the Content-Security-Policy header field or using the attachment disposition type in the Content-Disposition header field.
  - V3.2.2: [L1] content intended to be displayed as text, rather than rendered as HTML, is handled using safe rendering functions (such as createTextNode or textContent) to prevent unintended execution of content such as HTML or JavaScript.
  - V3.2.3: [L3] the application avoids DOM clobbering when using client-side JavaScript by employing explicit variable declarations, performing strict type checking, avoiding storing global variables on the document object, and implementing namespace isolation.

V3.3_cookie_setup:
  - V3.3.1: [L1] cookies have the 'Secure' attribute set, and if the '\__Host-' prefix is not used for the cookie name, the '__Secure-' prefix must be used for the cookie name.
  - V3.3.2: [L2] each cookie's 'SameSite' attribute value is set according to the purpose of the cookie, to limit exposure to user interface redress attacks and browser-based request forgery attacks, commonly known as cross-site request forgery (CSRF).
  - V3.3.3: [L2] cookies have the '__Host-' prefix for the cookie name unless they are explicitly designed to be shared with other hosts.
  - V3.3.4: [L2] if the value of a cookie is not meant to be accessible to client-side scripts (such as a session token), the cookie must have the 'HttpOnly' attribute set and the same value (e. g. session token) must only be transferred to the client via the 'Set-Cookie' header field.
  - V3.3.5: [L3] when the application writes a cookie, the cookie name and value length combined are not over 4096 bytes. Overly large cookies will not be stored by the browser and therefore not sent with requests, preventing the user from using application functionality which relies on that cookie.

V3.4_browser_security_mechanism_headers:
  - V3.4.1: [L1] a Strict-Transport-Security header field is included on all responses to enforce an HTTP Strict Transport Security (HSTS) policy. A maximum age of at least 1 year must be defined, and for L2 and up, the policy must apply to all subdomains as well.
  - V3.4.2: [L1] the Cross-Origin Resource Sharing (CORS) Access-Control-Allow-Origin header field is a fixed value by the application, or if the Origin HTTP request header field value is used, it is validated against an allowlist of trusted origins. When 'Access-Control-Allow-Origin: *' needs to be used, verify that the response does not include any sensitive information.
  - V3.4.3: [L2] HTTP responses include a Content-Security-Policy response header field which defines directives to ensure the browser only loads and executes trusted content or resources, in order to limit execution of malicious JavaScript. As a minimum, a global policy must be used which includes the directives object-src 'none' and base-uri 'none' and defines either an allowlist or uses nonces or hashes. For an L3 application, a per-response policy with nonces or hashes must be defined.
  - V3.4.4: [L2] all HTTP responses contain an 'X-Content-Type-Options: nosniff' header field. This instructs browsers not to use content sniffing and MIME type guessing for the given response, and to require the response's Content-Type header field value to match the destination resource. For example, the response to a request for a style is only accepted if the response's Content-Type is 'text/css'. This also enables the use of the Cross-Origin Read Blocking (CORB) functionality by the browser.
  - V3.4.5: [L2] the application sets a referrer policy to prevent leakage of technically sensitive data to third-party services via the 'Referer' HTTP request header field. This can be done using the Referrer-Policy HTTP response header field or via HTML element attributes. Sensitive data could include path and query data in the URL, and for internal non-public applications also the hostname.
  - V3.4.6: [L2] the web application uses the frame-ancestors directive of the Content-Security-Policy header field for every HTTP response to ensure that it cannot be embedded by default and that embedding of specific resources is allowed only when necessary. Note that the X-Frame-Options header field, although supported by browsers, is obsolete and may not be relied upon.
  - V3.4.7: [L3] the Content-Security-Policy header field specifies a location to report violations.
  - V3.4.8: [L3] all HTTP responses that initiate a document rendering (such as responses with Content-Type text/html), include the Cross‑Origin‑Opener‑Policy header field with the same-origin directive or the same-origin-allow-popups directive as required. This prevents attacks that abuse shared access to Window objects, such as tabnabbing and frame counting.

V3.5_browser_origin_separation:
  - V3.5.1: [L1] that, if the application does not rely on the CORS preflight mechanism to prevent disallowed cross-origin requests to use sensitive functionality, these requests are validated to ensure they originate from the application itself. This may be done by using and validating anti-forgery tokens or requiring extra HTTP header fields that are not CORS-safelisted request-header fields. This is to defend against browser-based request forgery attacks, commonly known as cross-site request forgery (CSRF).
  - V3.5.2: [L1] that, if the application relies on the CORS preflight mechanism to prevent disallowed cross-origin use of sensitive functionality, it is not possible to call the functionality with a request which does not trigger a CORS-preflight request. This may require checking the values of the 'Origin' and 'Content-Type' request header fields or using an extra header field that is not a CORS-safelisted header-field.
  - V3.5.3: [L1] HTTP requests to sensitive functionality use appropriate HTTP methods such as POST, PUT, PATCH, or DELETE, and not methods defined by the HTTP specification as "safe" such as HEAD, OPTIONS, or GET. Alternatively, strict validation of the Sec-Fetch-* request header fields can be used to ensure that the request did not originate from an inappropriate cross-origin call, a navigation request, or a resource load (such as an image source) where this is not expected.
  - V3.5.4: [L2] separate applications are hosted on different hostnames to leverage the restrictions provided by same-origin policy, including how documents or scripts loaded by one origin can interact with resources from another origin and hostname-based restrictions on cookies.
  - V3.5.5: [L2] messages received by the postMessage interface are discarded if the origin of the message is not trusted, or if the syntax of the message is invalid.
  - V3.5.6: [L3] JSONP functionality is not enabled anywhere across the application to avoid Cross-Site Script Inclusion (XSSI) attacks.
  - V3.5.7: [L3] data requiring authorization is not included in script resource responses, like JavaScript files, to prevent Cross-Site Script Inclusion (XSSI) attacks.
  - V3.5.8: [L3] authenticated resources (such as images, videos, scripts, and other documents) can be loaded or embedded on behalf of the user only when intended. This can be accomplished by strict validation of the Sec-Fetch-* HTTP request header fields to ensure that the request did not originate from an inappropriate cross-origin call, or by setting a restrictive Cross-Origin-Resource-Policy HTTP response header field to instruct the browser to block returned content.

V3.6_external_resource_integrity:
  - V3.6.1: [L3] client-side assets, such as JavaScript libraries, CSS, or web fonts, are only hosted externally (e.g., on a Content Delivery Network) if the resource is static and versioned and Subresource Integrity (SRI) is used to validate the integrity of the asset. If this is not possible, there should be a documented security decision to justify this for each resource.

V3.7_other_browser_security_considerations:
  - V3.7.1: [L2] the application only uses client-side technologies which are still supported and considered secure. Examples of technologies which do not meet this requirement include NSAPI plugins, Flash, Shockwave, ActiveX, Silverlight, NACL, or client-side Java applets.
  - V3.7.2: [L2] the application will only automatically redirect the user to a different hostname or domain (which is not controlled by the application) where the destination appears on an allowlist.
  - V3.7.3: [L3] the application shows a notification when the user is being redirected to a URL outside of the application's control, with an option to cancel the navigation.
  - V3.7.4: [L3] the application's top-level domain (e.g., site.tld) is added to the public preload list for HTTP Strict Transport Security (HSTS). This ensures that the use of TLS for the application is built directly into the main browsers, rather than relying only on the Strict-Transport-Security response header field.
  - V3.7.5: [L3] the application behaves as documented (such as warning the user or blocking access) if the browser used to access the application does not support the expected security features.

```

---

## V4 API and Web Service

**16 requirements** | Sections: Generic Web Service Security, HTTP Message Structure Validation, GraphQL, WebSocket

### Cross-Source Mapping

| Source | Reference |
|--------|-----------|
| API Top 10 | API1:2023 to API10:2023 (all 10 risks apply) |
| CheatSheet | REST_Security, REST_Assessment, GraphQL, Web_Service_Security |
| WSTG | WSTG-APIT-01 to WSTG-APIT-03 (API Testing) |

### Key Requirements for Code Audit

```yaml
V4.1_generic_web_service_security:
  - V4.1.1: [L1] every HTTP response with a message body contains a Content-Type header field that matches the actual content of the response, including the charset parameter to specify safe character encoding (e.g., UTF-8, ISO-8859-1) according to IANA Media Types, such as "text/", "/+xml" and "/xml".
  - V4.1.2: [L2] only user-facing endpoints (intended for manual web-browser access) automatically redirect from HTTP to HTTPS, while other services or endpoints do not implement transparent redirects. This is to avoid a situation where a client is erroneously sending unencrypted HTTP requests, but since the requests are being automatically redirected to HTTPS, the leakage of sensitive data goes undiscovered.
  - V4.1.3: [L2] any HTTP header field used by the application and set by an intermediary layer, such as a load balancer, a web proxy, or a backend-for-frontend service, cannot be overridden by the end-user. Example headers might include X-Real-IP, X-Forwarded-*, or X-User-ID.
  - V4.1.4: [L3] only HTTP methods that are explicitly supported by the application or its API (including OPTIONS during preflight requests) can be used and that unused methods are blocked.
  - V4.1.5: [L3] per-message digital signatures are used to provide additional assurance on top of transport protections for requests or transactions which are highly sensitive or which traverse a number of systems.

V4.2_http_message_structure_validation:
  - V4.2.1: [L2] all application components (including load balancers, firewalls, and application servers) determine boundaries of incoming HTTP messages using the appropriate mechanism for the HTTP version to prevent HTTP request smuggling. In HTTP/1.x, if a Transfer-Encoding header field is present, the Content-Length header must be ignored per RFC 2616. When using HTTP/2 or HTTP/3, if a Content-Length header field is present, the receiver must ensure that it is consistent with the length of the DATA frames.
  - V4.2.2: [L3] when generating HTTP messages, the Content-Length header field does not conflict with the length of the content as determined by the framing of the HTTP protocol, in order to prevent request smuggling attacks.
  - V4.2.3: [L3] the application does not send nor accept HTTP/2 or HTTP/3 messages with connection-specific header fields such as Transfer-Encoding to prevent response splitting and header injection attacks.
  - V4.2.4: [L3] the application only accepts HTTP/2 and HTTP/3 requests where the header fields and values do not contain any CR (\r), LF (\n), or CRLF (\r\n) sequences, to prevent header injection attacks.
  - V4.2.5: [L3] that, if the application (backend or frontend) builds and sends requests, it uses validation, sanitization, or other mechanisms to avoid creating URIs (such as for API calls) or HTTP request header fields (such as Authorization or Cookie), which are too long to be accepted by the receiving component. This could cause a denial of service, such as when sending an overly long request (e.g., a long cookie header field), which results in the server always responding with an error status.

V4.3_graphql:
  - V4.3.1: [L2] a query allowlist, depth limiting, amount limiting, or query cost analysis is used to prevent GraphQL or data layer expression Denial of Service (DoS) as a result of expensive, nested queries.
  - V4.3.2: [L2] GraphQL introspection queries are disabled in the production environment unless the GraphQL API is meant to be used by other parties.

V4.4_websocket:
  - V4.4.1: [L1] WebSocket over TLS (WSS) is used for all WebSocket connections.
  - V4.4.2: [L2] that, during the initial HTTP WebSocket handshake, the Origin header field is checked against a list of origins allowed for the application.
  - V4.4.3: [L2] that, if the application's standard session management cannot be used, dedicated tokens are being used for this, which comply with the relevant Session Management security requirements.
  - V4.4.4: [L2] dedicated WebSocket session management tokens are initially obtained or validated through the previously authenticated HTTPS session when transitioning an existing HTTPS session to a WebSocket channel.

```

---

## V5 File Handling

**13 requirements** | Sections: File Handling Documentation, File Upload and Content, File Storage, File Download

### Cross-Source Mapping

| Source | Reference |
|--------|-----------|
| API Top 10 | API4:2023 Unrestricted Resource Consumption |
| CheatSheet | File_Upload |
| WSTG | WSTG-BUSL-08 (Upload of Unexpected File Types), WSTG-BUSL-09 (Upload of Malicious Files) |

### Key Requirements for Code Audit

```yaml
# V5.1_file_handling_documentation: (1 documentation requirements - see ASVS source)

V5.2_file_upload_and_content:
  - V5.2.1: [L1] the application will only accept files of a size which it can process without causing a loss of performance or a denial of service attack.
  - V5.2.2: [L1] when the application accepts a file, either on its own or within an archive such as a zip file, it checks if the file extension matches an expected file extension and validates that the contents correspond to the type represented by the extension. This includes, but is not limited to, checking the initial 'magic bytes', performing image re-writing, and using specialized libraries for file content validation. For L1, this can focus just on files which are used to make specific business or security decisions. For L2 and up, this must apply to all files being accepted.
  - V5.2.3: [L2] the application checks compressed files (e.g., zip, gz, docx, odt) against maximum allowed uncompressed size and against maximum number of files before uncompressing the file.
  - V5.2.4: [L3] a file size quota and maximum number of files per user are enforced to ensure that a single user cannot fill up the storage with too many files, or excessively large files.
  - V5.2.5: [L3] the application does not allow uploading compressed files containing symlinks unless this is specifically required (in which case it will be necessary to enforce an allowlist of the files that can be symlinked to).
  - V5.2.6: [L3] the application rejects uploaded images with a pixel size larger than the maximum allowed, to prevent pixel flood attacks.

V5.3_file_storage:
  - V5.3.1: [L1] files uploaded or generated by untrusted input and stored in a public folder, are not executed as server-side program code when accessed directly with an HTTP request.
  - V5.3.2: [L1] when the application creates file paths for file operations, instead of user-submitted filenames, it uses internally generated or trusted data, or if user-submitted filenames or file metadata must be used, strict validation and sanitization must be applied. This is to protect against path traversal, local or remote file inclusion (LFI, RFI), and server-side request forgery (SSRF) attacks.
  - V5.3.3: [L3] server-side file processing, such as file decompression, ignores user-provided path information to prevent vulnerabilities such as zip slip.

V5.4_file_download:
  - V5.4.1: [L2] the application validates or ignores user-submitted filenames, including in a JSON, JSONP, or URL parameter and specifies a filename in the Content-Disposition header field in the response.
  - V5.4.2: [L2] file names served (e.g., in HTTP response header fields or email attachments) are encoded or sanitized (e.g., following RFC 6266) to preserve document structure and prevent injection attacks.
  - V5.4.3: [L2] files obtained from untrusted sources are scanned by antivirus scanners to prevent serving of known malicious content.

```

---

## V6 Authentication

**47 requirements** | Sections: Authentication Documentation, Password Security, General Authentication Security, Authentication Factor Lifecycle and Recovery, General Multi-factor authentication requirements, Out-of-Band authentication mechanisms, Cryptographic authentication mechanism, Authentication with an Identity Provider

### Cross-Source Mapping

| Source | Reference |
|--------|-----------|
| API Top 10 | API2:2023 Broken Authentication |
| CheatSheet | Authentication, Password_Storage, Forgot_Password, Credential_Stuffing_Prevention, Multifactor_Authentication, Session_Management, SAML_Security |
| WSTG | WSTG-ATHN-01 to WSTG-ATHN-10 (Authentication Testing) |

### Key Requirements for Code Audit

```yaml
# V6.1_authentication_documentation: (3 documentation requirements - see ASVS source)

V6.2_password_security:
  - V6.2.1: [L1] user set passwords are at least 8 characters in length although a minimum of 15 characters is strongly recommended.
  - V6.2.2: [L1] users can change their password.
  - V6.2.3: [L1] password change functionality requires the user's current and new password.
  - V6.2.4: [L1] passwords submitted during account registration or password change are checked against an available set of, at least, the top 3000 passwords which match the application's password policy, e.g. minimum length.
  - V6.2.5: [L1] passwords of any composition can be used, without rules limiting the type of characters permitted. There must be no requirement for a minimum number of upper or lower case characters, numbers, or special characters.
  - V6.2.6: [L1] password input fields use type=password to mask the entry. Applications may allow the user to temporarily view the entire masked password, or the last typed character of the password.
  - V6.2.7: [L1] "paste" functionality, browser password helpers, and external password managers are permitted.
  - V6.2.8: [L1] the application verifies the user's password exactly as received from the user, without any modifications such as truncation or case transformation.
  - V6.2.9: [L2] passwords of at least 64 characters are permitted.
  - V6.2.10: [L2] a user's password stays valid until it is discovered to be compromised or the user rotates it. The application must not require periodic credential rotation.
  - V6.2.11: [L2] the documented list of context specific words is used to prevent easy to guess passwords being created.
  - V6.2.12: [L2] passwords submitted during account registration or password changes are checked against a set of breached passwords.

V6.3_general_authentication_security:
  - V6.3.1: [L1] controls to prevent attacks such as credential stuffing and password brute force are implemented according to the application's security documentation.
  - V6.3.2: [L1] default user accounts (e.g., "root", "admin", or "sa") are not present in the application or are disabled.
  - V6.3.3: [L2] either a multi-factor authentication mechanism or a combination of single-factor authentication mechanisms, must be used in order to access the application. For L3, one of the factors must be a hardware-based authentication mechanism which provides compromise and impersonation resistance against phishing attacks while verifying the intent to authenticate by requiring a user-initiated action (such as a button press on a FIDO hardware key or a mobile phone). Relaxing any of the considerations in this requirement requires a fully documented rationale and a comprehensive set of mitigating controls.
  - V6.3.4: [L2] that, if the application includes multiple authentication pathways, there are no undocumented pathways and that security controls and authentication strength are enforced consistently.
  - V6.3.5: [L3] users are notified of suspicious authentication attempts (successful or unsuccessful). This may include authentication attempts from an unusual location or client, partially successful authentication (only one of multiple factors), an authentication attempt after a long period of inactivity or a successful authentication after several unsuccessful attempts.
  - V6.3.6: [L3] email is not used as either a single-factor or multi-factor authentication mechanism.
  - V6.3.7: [L3] users are notified after updates to authentication details, such as credential resets or modification of the username or email address.
  - V6.3.8: [L3] valid users cannot be deduced from failed authentication challenges, such as by basing on error messages, HTTP response codes, or different response times. Registration and forgot password functionality must also have this protection.

V6.4_authentication_factor_lifecycle_and_recovery:
  - V6.4.1: [L1] system generated initial passwords or activation codes are securely randomly generated, follow the existing password policy, and expire after a short period of time or after they are initially used. These initial secrets must not be permitted to become the long term password.
  - V6.4.2: [L1] password hints or knowledge-based authentication (so-called "secret questions") are not present.
  - V6.4.3: [L2] a secure process for resetting a forgotten password is implemented, that does not bypass any enabled multi-factor authentication mechanisms.
  - V6.4.4: [L2] if a multi-factor authentication factor is lost, evidence of identity proofing is performed at the same level as during enrollment.
  - V6.4.5: [L3] renewal instructions for authentication mechanisms which expire are sent with enough time to be carried out before the old authentication mechanism expires, configuring automated reminders if necessary.
  - V6.4.6: [L3] administrative users can initiate the password reset process for the user, but that this does not allow them to change or choose the user's password. This prevents a situation where they know the user's password.

V6.5_general_multi_factor_authentication_requirements:
  - V6.5.1: [L2] lookup secrets, out-of-band authentication requests or codes, and time-based one-time passwords (TOTPs) are only successfully usable once.
  - V6.5.2: [L2] that, when being stored in the application's backend, lookup secrets with less than 112 bits of entropy (19 random alphanumeric characters or 34 random digits) are hashed with an approved password storage hashing algorithm that incorporates a 32-bit random salt. A standard hash function can be used if the secret has 112 bits of entropy or more.
  - V6.5.3: [L2] lookup secrets, out-of-band authentication code, and time-based one-time password seeds, are generated using a Cryptographically Secure Pseudorandom Number Generator (CSPRNG) to avoid predictable values.
  - V6.5.4: [L2] lookup secrets and out-of-band authentication codes have a minimum of 20 bits of entropy (typically 4 random alphanumeric characters or 6 random digits is sufficient).
  - V6.5.5: [L2] out-of-band authentication requests, codes, or tokens, as well as time-based one-time passwords (TOTPs) have a defined lifetime. Out of band requests must have a maximum lifetime of 10 minutes and for TOTP a maximum lifetime of 30 seconds.
  - V6.5.6: [L3] any authentication factor (including physical devices) can be revoked in case of theft or other loss.
  - V6.5.7: [L3] biometric authentication mechanisms are only used as secondary factors together with either something you have or something you know.
  - V6.5.8: [L3] time-based one-time passwords (TOTPs) are checked based on a time source from a trusted service and not from an untrusted or client provided time.

V6.6_out_of_band_authentication_mechanisms:
  - V6.6.1: [L2] authentication mechanisms using the Public Switched Telephone Network (PSTN) to deliver One-time Passwords (OTPs) via phone or SMS are offered only when the phone number has previously been validated, alternate stronger methods (such as Time based One-time Passwords) are also offered, and the service provides information on their security risks to users. For L3 applications, phone and SMS must not be available as options.
  - V6.6.2: [L2] out-of-band authentication requests, codes, or tokens are bound to the original authentication request for which they were generated and are not usable for a previous or subsequent one.
  - V6.6.3: [L2] a code based out-of-band authentication mechanism is protected against brute force attacks by using rate limiting. Consider also using a code with at least 64 bits of entropy.
  - V6.6.4: [L3] that, where push notifications are used for multi-factor authentication, rate limiting is used to prevent push bombing attacks. Number matching may also mitigate this risk.

V6.7_cryptographic_authentication_mechanism:
  - V6.7.1: [L3] the certificates used to verify cryptographic authentication assertions are stored in a way protects them from modification.
  - V6.7.2: [L3] the challenge nonce is at least 64 bits in length, and statistically unique or unique over the lifetime of the cryptographic device.

V6.8_authentication_with_an_identity_provider:
  - V6.8.1: [L2] that, if the application supports multiple identity providers (IdPs), the user's identity cannot be spoofed via another supported identity provider (eg. by using the same user identifier). The standard mitigation would be for the application to register and identify the user using a combination of the IdP ID (serving as a namespace) and the user's ID in the IdP.
  - V6.8.2: [L2] the presence and integrity of digital signatures on authentication assertions (for example on JWTs or SAML assertions) are always validated, rejecting any assertions that are unsigned or have invalid signatures.
  - V6.8.3: [L2] SAML assertions are uniquely processed and used only once within the validity period to prevent replay attacks.
  - V6.8.4: [L2] that, if an application uses a separate Identity Provider (IdP) and expects specific authentication strength, methods, or recentness for specific functions, the application verifies this using the information returned by the IdP. For example, if OIDC is used, this might be achieved by validating ID Token claims such as 'acr', 'amr', and 'auth_time' (if present). If the IdP does not provide this information, the application must have a documented fallback approach that assumes that the minimum strength authentication mechanism was used (for example, single-factor authentication using username and password).

```

---

## V7 Session Management

**19 requirements** | Sections: Session Management Documentation, Fundamental Session Management Security, Session Timeout, Session Termination, Defenses Against Session Abuse, Federated Re-authentication

### Cross-Source Mapping

| Source | Reference |
|--------|-----------|
| API Top 10 | API2:2023 Broken Authentication |
| CheatSheet | Session_Management |
| WSTG | WSTG-SESS-01 to WSTG-SESS-09 (Session Management Testing) |

### Key Requirements for Code Audit

```yaml
# V7.1_session_management_documentation: (3 documentation requirements - see ASVS source)

V7.2_fundamental_session_management_security:
  - V7.2.1: [L1] the application performs all session token verification using a trusted, backend service.
  - V7.2.2: [L1] the application uses either self-contained or reference tokens that are dynamically generated for session management, i.e. not using static API secrets and keys.
  - V7.2.3: [L1] if reference tokens are used to represent user sessions, they are unique and generated using a cryptographically secure pseudo-random number generator (CSPRNG) and possess at least 128 bits of entropy.
  - V7.2.4: [L1] the application generates a new session token on user authentication, including re-authentication, and terminates the current session token.

V7.3_session_timeout:
  - V7.3.1: [L2] there is an inactivity timeout such that re-authentication is enforced according to risk analysis and documented security decisions.
  - V7.3.2: [L2] there is an absolute maximum session lifetime such that re-authentication is enforced according to risk analysis and documented security decisions.

V7.4_session_termination:
  - V7.4.1: [L1] when session termination is triggered (such as logout or expiration), the application disallows any further use of the session. For reference tokens or stateful sessions, this means invalidating the session data at the application backend. Applications using self-contained tokens will need a solution such as maintaining a list of terminated tokens, disallowing tokens produced before a per-user date and time or rotating a per-user signing key.
  - V7.4.2: [L1] the application terminates all active sessions when a user account is disabled or deleted (such as an employee leaving the company).
  - V7.4.3: [L2] the application gives the option to terminate all other active sessions after a successful change or removal of any authentication factor (including password change via reset or recovery and, if present, an MFA settings update).
  - V7.4.4: [L2] all pages that require authentication have easy and visible access to logout functionality.
  - V7.4.5: [L2] application administrators are able to terminate active sessions for an individual user or for all users.

V7.5_defenses_against_session_abuse:
  - V7.5.1: [L2] the application requires full re-authentication before allowing modifications to sensitive account attributes which may affect authentication such as email address, phone number, MFA configuration, or other information used in account recovery.
  - V7.5.2: [L2] users are able to view and (having authenticated again with at least one factor) terminate any or all currently active sessions.
  - V7.5.3: [L3] the application requires further authentication with at least one factor or secondary verification before performing highly sensitive transactions or operations.

V7.6_federated_re_authentication:
  - V7.6.1: [L2] session lifetime and termination between Relying Parties (RPs) and Identity Providers (IdPs) behave as documented, requiring re-authentication as necessary such as when the maximum time between IdP authentication events is reached.
  - V7.6.2: [L2] creation of a session requires either the user's consent or an explicit action, preventing the creation of new application sessions without user interaction.

```

---

## V8 Authorization

**13 requirements** | Sections: Authorization Documentation, General Authorization Design, Operation Level Authorization, Other Authorization Considerations

### Cross-Source Mapping

| Source | Reference |
|--------|-----------|
| API Top 10 | API1:2023 Broken Object Level Authorization, API3:2023 Broken Object Property Level Authorization, API5:2023 Broken Function Level Authorization |
| CheatSheet | Access_Control, Authorization, Insecure_Direct_Object_Reference_Prevention, Authorization_Testing_Automation |
| WSTG | WSTG-ATHZ-01 to WSTG-ATHZ-04 (Authorization Testing) |

### Key Requirements for Code Audit

```yaml
# V8.1_authorization_documentation: (4 documentation requirements - see ASVS source)

V8.2_general_authorization_design:
  - V8.2.1: [L1] the application ensures that function-level access is restricted to consumers with explicit permissions.
  - V8.2.2: [L1] the application ensures that data-specific access is restricted to consumers with explicit permissions to specific data items to mitigate insecure direct object reference (IDOR) and broken object level authorization (BOLA).
  - V8.2.3: [L2] the application ensures that field-level access is restricted to consumers with explicit permissions to specific fields to mitigate broken object property level authorization (BOPLA).
  - V8.2.4: [L3] adaptive security controls based on a consumer's environmental and contextual attributes (such as time of day, location, IP address, or device) are implemented for authentication and authorization decisions, as defined in the application's documentation. These controls must be applied when the consumer tries to start a new session and also during an existing session.

V8.3_operation_level_authorization:
  - V8.3.1: [L1] the application enforces authorization rules at a trusted service layer and doesn't rely on controls that an untrusted consumer could manipulate, such as client-side JavaScript.
  - V8.3.2: [L3] changes to values on which authorization decisions are made are applied immediately. Where changes cannot be applied immediately, (such as when relying on data in self-contained tokens), there must be mitigating controls to alert when a consumer performs an action when they are no longer authorized to do so and revert the change. Note that this alternative would not mitigate information leakage.
  - V8.3.3: [L3] access to an object is based on the originating subject's (e.g. consumer's) permissions, not on the permissions of any intermediary or service acting on their behalf. For example, if a consumer calls a web service using a self-contained token for authentication, and the service then requests data from a different service, the second service will use the consumer's token, rather than a machine-to-machine token from the first service, to make permission decisions.

V8.4_other_authorization_considerations:
  - V8.4.1: [L2] multi-tenant applications use cross-tenant controls to ensure consumer operations will never affect tenants with which they do not have permissions to interact.
  - V8.4.2: [L3] access to administrative interfaces incorporates multiple layers of security, including continuous consumer identity verification, device security posture assessment, and contextual risk analysis, ensuring that network location or trusted endpoints are not the sole factors for authorization even though they may reduce the likelihood of unauthorized access.

```

---

## V9 Self-contained Tokens

**7 requirements** | Sections: Token source and integrity, Token content

### Cross-Source Mapping

| Source | Reference |
|--------|-----------|
| API Top 10 | API2:2023 Broken Authentication |
| CheatSheet | JSON_Web_Token_for_Java |
| WSTG | WSTG-SESS-01 (Session Management Schema) |

### Key Requirements for Code Audit

```yaml
V9.1_token_source_and_integrity:
  - V9.1.1: [L1] self-contained tokens are validated using their digital signature or MAC to protect against tampering before accepting the token's contents.
  - V9.1.2: [L1] only algorithms on an allowlist can be used to create and verify self-contained tokens, for a given context. The allowlist must include the permitted algorithms, ideally only either symmetric or asymmetric algorithms, and must not include the 'None' algorithm. If both symmetric and asymmetric must be supported, additional controls will be needed to prevent key confusion.
  - V9.1.3: [L1] key material that is used to validate self-contained tokens is from trusted pre-configured sources for the token issuer, preventing attackers from specifying untrusted sources and keys. For JWTs and other JWS structures, headers such as 'jku', 'x5u', and 'jwk' must be validated against an allowlist of trusted sources.

V9.2_token_content:
  - V9.2.1: [L1] that, if a validity time span is present in the token data, the token and its content are accepted only if the verification time is within this validity time span. For example, for JWTs, the claims 'nbf' and 'exp' must be verified.
  - V9.2.2: [L2] the service receiving a token validates the token to be the correct type and is meant for the intended purpose before accepting the token's contents. For example, only access tokens can be accepted for authorization decisions and only ID Tokens can be used for proving user authentication.
  - V9.2.3: [L2] the service only accepts tokens which are intended for use with that service (audience). For JWTs, this can be achieved by validating the 'aud' claim against an allowlist defined in the service.
  - V9.2.4: [L2] that, if a token issuer uses the same private key for issuing tokens to different audiences, the issued tokens contain an audience restriction that uniquely identifies the intended audiences. This will prevent a token from being reused with an unintended audience. If the audience identifier is dynamically provisioned, the token issuer must validate these audiences in order to make sure that they do not result in audience impersonation.

```

---

## V10 OAuth and OIDC

**36 requirements** | Sections: Generic OAuth and OIDC Security, OAuth Client, OAuth Resource Server, OAuth Authorization Server, OIDC Client, OpenID Provider, Consent Management

### Cross-Source Mapping

| Source | Reference |
|--------|-----------|
| API Top 10 | API2:2023 Broken Authentication |
| CheatSheet | OAuth2 |
| WSTG | WSTG-ATHN-01 (Credentials Transport), WSTG-SESS-01 (Session Management) |

### Key Requirements for Code Audit

```yaml
V10.1_generic_oauth_and_oidc_security:
  - V10.1.1: [L2] tokens are only sent to components that strictly need them. For example, when using a backend-for-frontend pattern for browser-based JavaScript applications, access and refresh tokens shall only be accessible for the backend.
  - V10.1.2: [L2] the client only accepts values from the authorization server (such as the authorization code or ID Token) if these values result from an authorization flow that was initiated by the same user agent session and transaction. This requires that client-generated secrets, such as the proof key for code exchange (PKCE) 'code_verifier', 'state' or OIDC 'nonce', are not guessable, are specific to the transaction, and are securely bound to both the client and the user agent session in which the transaction was started.

V10.2_oauth_client:
  - V10.2.1: [L2] that, if the code flow is used, the OAuth client has protection against browser-based request forgery attacks, commonly known as cross-site request forgery (CSRF), which trigger token requests, either by using proof key for code exchange (PKCE) functionality or checking the 'state' parameter that was sent in the authorization request.
  - V10.2.2: [L2] that, if the OAuth client can interact with more than one authorization server, it has a defense against mix-up attacks. For example, it could require that the authorization server return the 'iss' parameter value and validate it in the authorization response and the token response.
  - V10.2.3: [L3] the OAuth client only requests the required scopes (or other authorization parameters) in requests to the authorization server.

V10.3_oauth_resource_server:
  - V10.3.1: [L2] the resource server only accepts access tokens that are intended for use with that service (audience). The audience may be included in a structured access token (such as the 'aud' claim in JWT), or it can be checked using the token introspection endpoint.
  - V10.3.2: [L2] the resource server enforces authorization decisions based on claims from the access token that define delegated authorization. If claims such as 'sub', 'scope', and 'authorization_details' are present, they must be part of the decision.
  - V10.3.3: [L2] if an access control decision requires identifying a unique user from an access token (JWT or related token introspection response), the resource server identifies the user from claims that cannot be reassigned to other users. Typically, it means using a combination of 'iss' and 'sub' claims.
  - V10.3.4: [L2] that, if the resource server requires specific authentication strength, methods, or recentness, it verifies that the presented access token satisfies these constraints. For example, if present, using the OIDC 'acr', 'amr' and 'auth_time' claims respectively.
  - V10.3.5: [L3] the resource server prevents the use of stolen access tokens or replay of access tokens (from unauthorized parties) by requiring sender-constrained access tokens, either Mutual TLS for OAuth 2 or OAuth 2 Demonstration of Proof of Possession (DPoP).

V10.4_oauth_authorization_server:
  - V10.4.1: [L1] the authorization server validates redirect URIs based on a client-specific allowlist of pre-registered URIs using exact string comparison.
  - V10.4.2: [L1] that, if the authorization server returns the authorization code in the authorization response, it can be used only once for a token request. For the second valid request with an authorization code that has already been used to issue an access token, the authorization server must reject a token request and revoke any issued tokens related to the authorization code.
  - V10.4.3: [L1] the authorization code is short-lived. The maximum lifetime can be up to 10 minutes for L1 and L2 applications and up to 1 minute for L3 applications.
  - V10.4.4: [L1] for a given client, the authorization server only allows the usage of grants that this client needs to use. Note that the grants 'token' (Implicit flow) and 'password' (Resource Owner Password Credentials flow) must no longer be used.
  - V10.4.5: [L1] the authorization server mitigates refresh token replay attacks for public clients, preferably using sender-constrained refresh tokens, i.e., Demonstrating Proof of Possession (DPoP) or Certificate-Bound Access Tokens using mutual TLS (mTLS). For L1 and L2 applications, refresh token rotation may be used. If refresh token rotation is used, the authorization server must invalidate the refresh token after usage, and revoke all refresh tokens for that authorization if an already used and invalidated refresh token is provided.
  - V10.4.6: [L2] that, if the code grant is used, the authorization server mitigates authorization code interception attacks by requiring proof key for code exchange (PKCE). For authorization requests, the authorization server must require a valid 'code_challenge' value and must not accept a 'code_challenge_method' value of 'plain'. For a token request, it must require validation of the 'code_verifier' parameter.
  - V10.4.7: [L2] if the authorization server supports unauthenticated dynamic client registration, it mitigates the risk of malicious client applications. It must validate client metadata such as any registered URIs, ensure the user's consent, and warn the user before processing an authorization request with an untrusted client application.
  - V10.4.8: [L2] refresh tokens have an absolute expiration, including if sliding refresh token expiration is applied.
  - V10.4.9: [L2] refresh tokens and reference access tokens can be revoked by an authorized user using the authorization server user interface, to mitigate the risk of malicious clients or stolen tokens.
  - V10.4.10: [L2] confidential client is authenticated for client-to-authorized server backchannel requests such as token requests, pushed authorization requests (PAR), and token revocation requests.
  - V10.4.11: [L2] the authorization server configuration only assigns the required scopes to the OAuth client.
  - V10.4.12: [L3] for a given client, the authorization server only allows the 'response_mode' value that this client needs to use. For example, by having the authorization server validate this value against the expected values or by using pushed authorization request (PAR) or JWT-secured Authorization Request (JAR).
  - V10.4.13: [L3] grant type 'code' is always used together with pushed authorization requests (PAR).
  - V10.4.14: [L3] the authorization server issues only sender-constrained (Proof-of-Possession) access tokens, either with certificate-bound access tokens using mutual TLS (mTLS) or DPoP-bound access tokens (Demonstration of Proof of Possession).
  - V10.4.15: [L3] that, for a server-side client (which is not executed on the end-user device), the authorization server ensures that the 'authorization_details' parameter value is from the client backend and that the user has not tampered with it. For example, by requiring the usage of pushed authorization request (PAR) or JWT-secured Authorization Request (JAR).
  - V10.4.16: [L3] the client is confidential and the authorization server requires the use of strong client authentication methods (based on public-key cryptography and resistant to replay attacks), such as mutual TLS ('tls_client_auth', 'self_signed_tls_client_auth') or private key JWT ('private_key_jwt').

V10.5_oidc_client:
  - V10.5.1: [L2] the client (as the relying party) mitigates ID Token replay attacks. For example, by ensuring that the 'nonce' claim in the ID Token matches the 'nonce' value sent in the authentication request to the OpenID Provider (in OAuth2 refereed to as the authorization request sent to the authorization server).
  - V10.5.2: [L2] the client uniquely identifies the user from ID Token claims, usually the 'sub' claim, which cannot be reassigned to other users (for the scope of an identity provider).
  - V10.5.3: [L2] the client rejects attempts by a malicious authorization server to impersonate another authorization server through authorization server metadata. The client must reject authorization server metadata if the issuer URL in the authorization server metadata does not exactly match the pre-configured issuer URL expected by the client.
  - V10.5.4: [L2] the client validates that the ID Token is intended to be used for that client (audience) by checking that the 'aud' claim from the token is equal to the 'client_id' value for the client.
  - V10.5.5: [L2] that, when using OIDC back-channel logout, the relying party mitigates denial of service through forced logout and cross-JWT confusion in the logout flow. The client must verify that the logout token is correctly typed with a value of 'logout+jwt', contains the 'event' claim with the correct member name, and does not contain a 'nonce' claim. Note that it is also recommended to have a short expiration (e.g., 2 minutes).

V10.6_openid_provider:
  - V10.6.1: [L2] the OpenID Provider only allows values 'code', 'ciba', 'id_token', or 'id_token code' for response mode. Note that 'code' is preferred over 'id_token code' (the OIDC Hybrid flow), and 'token' (any Implicit flow) must not be used.
  - V10.6.2: [L2] the OpenID Provider mitigates denial of service through forced logout. By obtaining explicit confirmation from the end-user or, if present, validating parameters in the logout request (initiated by the relying party), such as the 'id_token_hint'.

V10.7_consent_management:
  - V10.7.1: [L2] the authorization server ensures that the user consents to each authorization request. If the identity of the client cannot be assured, the authorization server must always explicitly prompt the user for consent.
  - V10.7.2: [L2] when the authorization server prompts for user consent, it presents sufficient and clear information about what is being consented to. When applicable, this should include the nature of the requested authorizations (typically based on scope, resource server, Rich Authorization Requests (RAR) authorization details), the identity of the authorized application, and the lifetime of these authorizations.
  - V10.7.3: [L2] the user can review, modify, and revoke consents which the user has granted through the authorization server.

```

---

## V11 Cryptography

**24 requirements** | Sections: Cryptographic Inventory and Documentation, Secure Cryptography Implementation, Encryption Algorithms, Hashing and Hash-based Functions, Random Values, Public Key Cryptography, In-Use Data Cryptography

### Cross-Source Mapping

| Source | Reference |
|--------|-----------|
| API Top 10 | API2:2023 Broken Authentication (weak crypto in auth) |
| CheatSheet | Cryptographic_Storage, Key_Management, Password_Storage |
| WSTG | WSTG-CRYP-01 to WSTG-CRYP-04 (Cryptography Testing) |

### Key Requirements for Code Audit

```yaml
# V11.1_cryptographic_inventory_and_documentation: (4 documentation requirements - see ASVS source)

V11.2_secure_cryptography_implementation:
  - V11.2.1: [L2] industry-validated implementations (including libraries and hardware-accelerated implementations) are used for cryptographic operations.
  - V11.2.2: [L2] the application is designed with crypto agility such that random number, authenticated encryption, MAC, or hashing algorithms, key lengths, rounds, ciphers and modes can be reconfigured, upgraded, or swapped at any time, to protect against cryptographic breaks. Similarly, it must also be possible to replace keys and passwords and re-encrypt data. This will allow for seamless upgrades to post-quantum cryptography (PQC), once high-assurance implementations of approved PQC schemes or standards are widely available.
  - V11.2.3: [L2] all cryptographic primitives utilize a minimum of 128-bits of security based on the algorithm, key size, and configuration. For example, a 256-bit ECC key provides roughly 128 bits of security where RSA requires a 3072-bit key to achieve 128 bits of security.
  - V11.2.4: [L3] all cryptographic operations are constant-time, with no 'short-circuit' operations in comparisons, calculations, or returns, to avoid leaking information.
  - V11.2.5: [L3] all cryptographic modules fail securely, and errors are handled in a way that does not enable vulnerabilities, such as Padding Oracle attacks.

V11.3_encryption_algorithms:
  - V11.3.1: [L1] insecure block modes (e.g., ECB) and weak padding schemes (e.g., PKCS#1 v1.5) are not used.
  - V11.3.2: [L1] only approved ciphers and modes such as AES with GCM are used.
  - V11.3.3: [L2] encrypted data is protected against unauthorized modification preferably by using an approved authenticated encryption method or by combining an approved encryption method with an approved MAC algorithm.
  - V11.3.4: [L3] nonces, initialization vectors, and other single-use numbers are not used for more than one encryption key and data-element pair. The method of generation must be appropriate for the algorithm being used.
  - V11.3.5: [L3] any combination of an encryption algorithm and a MAC algorithm is operating in encrypt-then-MAC mode.

V11.4_hashing_and_hash_based_functions:
  - V11.4.1: [L1] only approved hash functions are used for general cryptographic use cases, including digital signatures, HMAC, KDF, and random bit generation. Disallowed hash functions, such as MD5, must not be used for any cryptographic purpose.
  - V11.4.2: [L2] passwords are stored using an approved, computationally intensive, key derivation function (also known as a "password hashing function"), with parameter settings configured based on current guidance. The settings should balance security and performance to make brute-force attacks sufficiently challenging for the required level of security.
  - V11.4.3: [L2] hash functions used in digital signatures, as part of data authentication or data integrity are collision resistant and have appropriate bit-lengths. If collision resistance is required, the output length must be at least 256 bits. If only resistance to second pre-image attacks is required, the output length must be at least 128 bits.
  - V11.4.4: [L2] the application uses approved key derivation functions with key stretching parameters when deriving secret keys from passwords. The parameters in use must balance security and performance to prevent brute-force attacks from compromising the resulting cryptographic key.

V11.5_random_values:
  - V11.5.1: [L2] all random numbers and strings which are intended to be non-guessable must be generated using a cryptographically secure pseudo-random number generator (CSPRNG) and have at least 128 bits of entropy. Note that UUIDs do not respect this condition.
  - V11.5.2: [L3] the random number generation mechanism in use is designed to work securely, even under heavy demand.

V11.6_public_key_cryptography:
  - V11.6.1: [L2] only approved cryptographic algorithms and modes of operation are used for key generation and seeding, and digital signature generation and verification. Key generation algorithms must not generate insecure keys vulnerable to known attacks, for example, RSA keys which are vulnerable to Fermat factorization.
  - V11.6.2: [L3] approved cryptographic algorithms are used for key exchange (such as Diffie-Hellman) with a focus on ensuring that key exchange mechanisms use secure parameters. This will prevent attacks on the key establishment process which could lead to adversary-in-the-middle attacks or cryptographic breaks.

V11.7_in_use_data_cryptography:
  - V11.7.1: [L3] full memory encryption is in use that protects sensitive data while it is in use, preventing access by unauthorized users or processes.
  - V11.7.2: [L3] data minimization ensures the minimal amount of data is exposed during processing, and ensure that data is encrypted immediately after use or as soon as feasible.

```

---

## V12 Secure Communication

**12 requirements** | Sections: General TLS Security Guidance, HTTPS Communication with External Facing Services, General Service to Service Communication Security

### Cross-Source Mapping

| Source | Reference |
|--------|-----------|
| API Top 10 | API8:2023 Security Misconfiguration |
| CheatSheet | Transport_Layer_Security, Transport_Layer_Protection, HTTP_Strict_Transport_Security, TLS_Cipher_String, Pinning |
| WSTG | WSTG-CRYP-01 (Testing for Weak TLS/SSL) |

### Key Requirements for Code Audit

```yaml
V12.1_general_tls_security_guidance:
  - V12.1.1: [L1] only the latest recommended versions of the TLS protocol are enabled, such as TLS 1.2 and TLS 1.3. The latest version of the TLS protocol must be the preferred option.
  - V12.1.2: [L2] only recommended cipher suites are enabled, with the strongest cipher suites set as preferred. L3 applications must only support cipher suites which provide forward secrecy.
  - V12.1.3: [L2] the application validates that mTLS client certificates are trusted before using the certificate identity for authentication or authorization.
  - V12.1.4: [L3] proper certification revocation, such as Online Certificate Status Protocol (OCSP) Stapling, is enabled and configured.
  - V12.1.5: [L3] Encrypted Client Hello (ECH) is enabled in the application's TLS settings to prevent exposure of sensitive metadata, such as the Server Name Indication (SNI), during TLS handshake processes.

V12.2_https_communication_with_external_facing_services:
  - V12.2.1: [L1] TLS is used for all connectivity between a client and external facing, HTTP-based services, and does not fall back to insecure or unencrypted communications.
  - V12.2.2: [L1] external facing services use publicly trusted TLS certificates.

V12.3_general_service_to_service_communication_security:
  - V12.3.1: [L2] an encrypted protocol such as TLS is used for all inbound and outbound connections to and from the application, including monitoring systems, management tools, remote access and SSH, middleware, databases, mainframes, partner systems, or external APIs. The server must not fall back to insecure or unencrypted protocols.
  - V12.3.2: [L2] TLS clients validate certificates received before communicating with a TLS server.
  - V12.3.3: [L2] TLS or another appropriate transport encryption mechanism used for all connectivity between internal, HTTP-based services within the application, and does not fall back to insecure or unencrypted communications.
  - V12.3.4: [L2] TLS connections between internal services use trusted certificates. Where internally generated or self-signed certificates are used, the consuming service must be configured to only trust specific internal CAs and specific self-signed certificates.
  - V12.3.5: [L3] services communicating internally within a system (intra-service communications) use strong authentication to ensure that each endpoint is verified. Strong authentication methods, such as TLS client authentication, must be employed to ensure identity, using public-key infrastructure and mechanisms that are resistant to replay attacks. For microservice architectures, consider using a service mesh to simplify certificate management and enhance security.

```

---

## V13 Configuration

**21 requirements** | Sections: Configuration Documentation, Backend Communication Configuration, Secret Management, Unintended Information Leakage

### Cross-Source Mapping

| Source | Reference |
|--------|-----------|
| API Top 10 | API8:2023 Security Misconfiguration, API9:2023 Improper Inventory Management |
| CheatSheet | Docker_Security, Kubernetes_Security, Secrets_Management, Infrastructure_as_Code_Security, Vulnerable_Dependency_Management |
| WSTG | WSTG-CONF-01 to WSTG-CONF-11 (Configuration Testing) |

### Key Requirements for Code Audit

```yaml
# V13.1_configuration_documentation: (4 documentation requirements - see ASVS source)

V13.2_backend_communication_configuration:
  - V13.2.1: [L2] communications between backend application components that don't support the application's standard user session mechanism, including APIs, middleware, and data layers, are authenticated. Authentication must use individual service accounts, short-term tokens, or certificate-based authentication and not unchanging credentials such as passwords, API keys, or shared accounts with privileged access.
  - V13.2.2: [L2] communications between backend application components, including local or operating system services, APIs, middleware, and data layers, are performed with accounts assigned the least necessary privileges.
  - V13.2.3: [L2] if a credential has to be used for service authentication, the credential being used by the consumer is not a default credential (e.g., root/root or admin/admin).
  - V13.2.4: [L2] an allowlist is used to define the external resources or systems with which the application is permitted to communicate (e.g., for outbound requests, data loads, or file access). This allowlist can be implemented at the application layer, web server, firewall, or a combination of different layers.
  - V13.2.5: [L2] the web or application server is configured with an allowlist of resources or systems to which the server can send requests or load data or files from.
  - V13.2.6: [L3] where the application connects to separate services, it follows the documented configuration for each connection, such as maximum parallel connections, behavior when maximum allowed connections is reached, connection timeouts, and retry strategies.

V13.3_secret_management:
  - V13.3.1: [L2] a secrets management solution, such as a key vault, is used to securely create, store, control access to, and destroy backend secrets. These could include passwords, key material, integrations with databases and third-party systems, keys and seeds for time-based tokens, other internal secrets, and API keys. Secrets must not be included in application source code or included in build artifacts. For an L3 application, this must involve a hardware-backed solution such as an HSM.
  - V13.3.2: [L2] access to secret assets adheres to the principle of least privilege.
  - V13.3.3: [L3] all cryptographic operations are performed using an isolated security module (such as a vault or hardware security module) to securely manage and protect key material from exposure outside of the security module.
  - V13.3.4: [L3] secrets are configured to expire and be rotated based on the application's documentation.

V13.4_unintended_information_leakage:
  - V13.4.1: [L1] the application is deployed either without any source control metadata, including the .git or .svn folders, or in a way that these folders are inaccessible both externally and to the application itself.
  - V13.4.2: [L2] debug modes are disabled for all components in production environments to prevent exposure of debugging features and information leakage.
  - V13.4.3: [L2] web servers do not expose directory listings to clients unless explicitly intended.
  - V13.4.4: [L2] using the HTTP TRACE method is not supported in production environments, to avoid potential information leakage.
  - V13.4.5: [L2] documentation (such as for internal APIs) and monitoring endpoints are not exposed unless explicitly intended.
  - V13.4.6: [L3] the application does not expose detailed version information of backend components.
  - V13.4.7: [L3] the web tier is configured to only serve files with specific file extensions to prevent unintentional information, configuration, and source code leakage.

```

---

## V14 Data Protection

**13 requirements** | Sections: Data Protection Documentation, General Data Protection, Client-side Data Protection

### Cross-Source Mapping

| Source | Reference |
|--------|-----------|
| API Top 10 | API3:2023 Broken Object Property Level Authorization |
| CheatSheet | User_Privacy_Protection, Logging |
| WSTG | WSTG-CONF-09 (Testing for File Permission), WSTG-ATHN-01 (Credentials Transport) |

### Key Requirements for Code Audit

```yaml
# V14.1_data_protection_documentation: (2 documentation requirements - see ASVS source)

V14.2_general_data_protection:
  - V14.2.1: [L1] sensitive data is only sent to the server in the HTTP message body or header fields, and that the URL and query string do not contain sensitive information, such as an API key or session token.
  - V14.2.2: [L2] the application prevents sensitive data from being cached in server components, such as load balancers and application caches, or ensures that the data is securely purged after use.
  - V14.2.3: [L2] defined sensitive data is not sent to untrusted parties (e.g., user trackers) to prevent unwanted collection of data outside of the application's control.
  - V14.2.4: [L2] controls around sensitive data related to encryption, integrity verification, retention, how the data is to be logged, access controls around sensitive data in logs, privacy and privacy-enhancing technologies, are implemented as defined in the documentation for the specific data's protection level.
  - V14.2.5: [L3] caching mechanisms are configured to only cache responses which have the expected content type for that resource and do not contain sensitive, dynamic content. The web server should return a 404 or 302 response when a non-existent file is accessed rather than returning a different, valid file. This should prevent Web Cache Deception attacks.
  - V14.2.6: [L3] the application only returns the minimum required sensitive data for the application's functionality. For example, only returning some of the digits of a credit card number and not the full number. If the complete data is required, it should be masked in the user interface unless the user specifically views it.
  - V14.2.7: [L3] sensitive information is subject to data retention classification, ensuring that outdated or unnecessary data is deleted automatically, on a defined schedule, or as the situation requires.
  - V14.2.8: [L3] sensitive information is removed from the metadata of user-submitted files unless storage is consented to by the user.

V14.3_client_side_data_protection:
  - V14.3.1: [L1] authenticated data is cleared from client storage, such as the browser DOM, after the client or session is terminated. The 'Clear-Site-Data' HTTP response header field may be able to help with this but the client-side should also be able to clear up if the server connection is not available when the session is terminated.
  - V14.3.2: [L2] the application sets sufficient anti-caching HTTP response header fields (i.e., Cache-Control: no-store) so that sensitive data is not cached in browsers.
  - V14.3.3: [L2] data stored in browser storage (such as localStorage, sessionStorage, IndexedDB, or cookies) does not contain sensitive data, with the exception of session tokens.

```

---

## V15 Secure Coding and Architecture

**21 requirements** | Sections: Secure Coding and Architecture Documentation, Security Architecture and Dependencies, Defensive Coding, Safe Concurrency

### Cross-Source Mapping

| Source | Reference |
|--------|-----------|
| API Top 10 | API3:2023 Broken Object Property Level Authorization, API10:2023 Unsafe Consumption of APIs |
| CheatSheet | Secure_Product_Design, Mass_Assignment, Prototype_Pollution_Prevention, Vulnerable_Dependency_Management |
| WSTG | WSTG-INPV (Input Validation Testing), WSTG-CONF (Configuration Testing) |

### Key Requirements for Code Audit

```yaml
# V15.1_secure_coding_and_architecture_documentation: (5 documentation requirements - see ASVS source)

V15.2_security_architecture_and_dependencies:
  - V15.2.1: [L1] the application only contains components which have not breached the documented update and remediation time frames.
  - V15.2.2: [L2] the application has implemented defenses against loss of availability due to functionality which is time-consuming or resource-demanding, based on the documented security decisions and strategies for this.
  - V15.2.3: [L2] the production environment only includes functionality that is required for the application to function, and does not expose extraneous functionality such as test code, sample snippets, and development functionality.
  - V15.2.4: [L3] third-party components and all of their transitive dependencies are included from the expected repository, whether internally owned or an external source, and that there is no risk of a dependency confusion attack.
  - V15.2.5: [L3] the application implements additional protections around parts of the application which are documented as containing "dangerous functionality" or using third-party libraries considered to be "risky components". This could include techniques such as sandboxing, encapsulation, containerization or network level isolation to delay and deter attackers who compromise one part of an application from pivoting elsewhere in the application.

V15.3_defensive_coding:
  - V15.3.1: [L1] the application only returns the required subset of fields from a data object. For example, it should not return an entire data object, as some individual fields should not be accessible to users.
  - V15.3.2: [L2] where the application backend makes calls to external URLs, it is configured to not follow redirects unless it is intended functionality.
  - V15.3.3: [L2] the application has countermeasures to protect against mass assignment attacks by limiting allowed fields per controller and action, e.g., it is not possible to insert or update a field value when it was not intended to be part of that action.
  - V15.3.4: [L2] all proxying and middleware components transfer the user's original IP address correctly using trusted data fields that cannot be manipulated by the end user, and the application and web server use this correct value for logging and security decisions such as rate limiting, taking into account that even the original IP address may not be reliable due to dynamic IPs, VPNs, or corporate firewalls.
  - V15.3.5: [L2] the application explicitly ensures that variables are of the correct type and performs strict equality and comparator operations. This is to avoid type juggling or type confusion vulnerabilities caused by the application code making an assumption about a variable type.
  - V15.3.6: [L2] JavaScript code is written in a way that prevents prototype pollution, for example, by using Set() or Map() instead of object literals.
  - V15.3.7: [L2] the application has defenses against HTTP parameter pollution attacks, particularly if the application framework makes no distinction about the source of request parameters (query string, body parameters, cookies, or header fields).

V15.4_safe_concurrency:
  - V15.4.1: [L3] shared objects in multi-threaded code (such as caches, files, or in-memory objects accessed by multiple threads) are accessed safely by using thread-safe types and synchronization mechanisms like locks or semaphores to avoid race conditions and data corruption.
  - V15.4.2: [L3] checks on a resource's state, such as its existence or permissions, and the actions that depend on them are performed as a single atomic operation to prevent time-of-check to time-of-use (TOCTOU) race conditions. For example, checking if a file exists before opening it, or verifying a user’s access before granting it.
  - V15.4.3: [L3] locks are used consistently to avoid threads getting stuck, whether by waiting on each other or retrying endlessly, and that locking logic stays within the code responsible for managing the resource to ensure locks cannot be inadvertently or maliciously modified by external classes or code.
  - V15.4.4: [L3] resource allocation policies prevent thread starvation by ensuring fair access to resources, such as by leveraging thread pools, allowing lower-priority threads to proceed within a reasonable timeframe.

```

---

## V16 Security Logging and Error Handling

**17 requirements** | Sections: Security Logging Documentation, General Logging, Security Events, Log Protection, Error Handling

### Cross-Source Mapping

| Source | Reference |
|--------|-----------|
| API Top 10 | API8:2023 Security Misconfiguration (error handling) |
| CheatSheet | Logging, Logging_Vocabulary, Error_Handling |
| WSTG | WSTG-ERRH-01 (Testing for Improper Error Handling), WSTG-ERRH-02 (Testing for Stack Traces) |

### Key Requirements for Code Audit

```yaml
# V16.1_security_logging_documentation: (1 documentation requirements - see ASVS source)

V16.2_general_logging:
  - V16.2.1: [L2] each log entry includes necessary metadata (such as when, where, who, what) that would allow for a detailed investigation of the timeline when an event happens.
  - V16.2.2: [L2] time sources for all logging components are synchronized, and that timestamps in security event metadata use UTC or include an explicit time zone offset. UTC is recommended to ensure consistency across distributed systems and to prevent confusion during daylight saving time transitions.
  - V16.2.3: [L2] the application only stores or broadcasts logs to the files and services that are documented in the log inventory.
  - V16.2.4: [L2] logs can be read and correlated by the log processor that is in use, preferably by using a common logging format.
  - V16.2.5: [L2] when logging sensitive data, the application enforces logging based on the data's protection level. For example, it may not be allowed to log certain data, such as credentials or payment details. Other data, such as session tokens, may only be logged by being hashed or masked, either in full or partially.

V16.3_security_events:
  - V16.3.1: [L2] all authentication operations are logged, including successful and unsuccessful attempts. Additional metadata, such as the type of authentication or factors used, should also be collected.
  - V16.3.2: [L2] failed authorization attempts are logged. For L3, this must include logging all authorization decisions, including logging when sensitive data is accessed (without logging the sensitive data itself).
  - V16.3.3: [L2] the application logs the security events that are defined in the documentation and also logs attempts to bypass the security controls, such as input validation, business logic, and anti-automation.
  - V16.3.4: [L2] the application logs unexpected errors and security control failures such as backend TLS failures.

V16.4_log_protection:
  - V16.4.1: [L2] all logging components appropriately encode data to prevent log injection.
  - V16.4.2: [L2] logs are protected from unauthorized access and cannot be modified.
  - V16.4.3: [L2] logs are securely transmitted to a logically separate system for analysis, detection, alerting, and escalation. The aim is to ensure that if the application is breached, the logs are not compromised.

V16.5_error_handling:
  - V16.5.1: [L2] a generic message is returned to the consumer when an unexpected or security-sensitive error occurs, ensuring no exposure of sensitive internal system data such as stack traces, queries, secret keys, and tokens.
  - V16.5.2: [L2] the application continues to operate securely when external resource access fails, for example, by using patterns such as circuit breakers or graceful degradation.
  - V16.5.3: [L2] the application fails gracefully and securely, including when an exception occurs, preventing fail-open conditions such as processing a transaction despite errors resulting from validation logic.
  - V16.5.4: [L3] a "last resort" error handler is defined which will catch all unhandled exceptions. This is both to avoid losing error details that must go to log files and to ensure that an error does not take down the entire application process, leading to a loss of availability.

```

---

## V17 WebRTC

**12 requirements** | Sections: TURN Server, Media, Signaling

### Cross-Source Mapping

| Source | Reference |
|--------|-----------|
| API Top 10 | N/A (specialized domain) |
| CheatSheet | N/A |
| WSTG | N/A |

### Key Requirements for Code Audit

```yaml
V17.1_turn_server:
  - V17.1.1: [L2] the Traversal Using Relays around NAT (TURN) service only allows access to IP addresses that are not reserved for special purposes (e.g., internal networks, broadcast, loopback). Note that this applies to both IPv4 and IPv6 addresses.
  - V17.1.2: [L3] the Traversal Using Relays around NAT (TURN) service is not susceptible to resource exhaustion when legitimate users attempt to open a large number of ports on the TURN server.

V17.2_media:
  - V17.2.1: [L2] the key for the Datagram Transport Layer Security (DTLS) certificate is managed and protected based on the documented policy for management of cryptographic keys.
  - V17.2.2: [L2] the media server is configured to use and support approved Datagram Transport Layer Security (DTLS) cipher suites and a secure protection profile for the DTLS Extension for establishing keys for the Secure Real-time Transport Protocol (DTLS-SRTP).
  - V17.2.3: [L2] Secure Real-time Transport Protocol (SRTP) authentication is checked at the media server to prevent Real-time Transport Protocol (RTP) injection attacks from leading to either a Denial of Service condition or audio or video media insertion into media streams.
  - V17.2.4: [L2] the media server is able to continue processing incoming media traffic when encountering malformed Secure Real-time Transport Protocol (SRTP) packets.
  - V17.2.5: [L3] the media server is able to continue processing incoming media traffic during a flood of Secure Real-time Transport Protocol (SRTP) packets from legitimate users.
  - V17.2.6: [L3] the media server is not susceptible to the "ClientHello" Race Condition vulnerability in Datagram Transport Layer Security (DTLS) by checking if the media server is publicly known to be vulnerable or by performing the race condition test.
  - V17.2.7: [L3] any audio or video recording mechanisms associated with the media server are able to continue processing incoming media traffic during a flood of Secure Real-time Transport Protocol (SRTP) packets from legitimate users.
  - V17.2.8: [L3] the Datagram Transport Layer Security (DTLS) certificate is checked against the Session Description Protocol (SDP) fingerprint attribute, terminating the media stream if the check fails, to ensure the authenticity of the media stream.

V17.3_signaling:
  - V17.3.1: [L2] the signaling server is able to continue processing legitimate incoming signaling messages during a flood attack. This should be achieved by implementing rate limiting at the signaling level.
  - V17.3.2: [L2] the signaling server is able to continue processing legitimate signaling messages when encountering malformed signaling message that could cause a denial of service condition. This could include implementing input validation, safely handling integer overflows, preventing buffer overflows, and employing other robust error-handling techniques.

```

---
