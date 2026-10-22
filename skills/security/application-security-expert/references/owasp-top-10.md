# OWASP Top 10 (2021)

## A01 — Broken Access Control

**Issues**: missing authz checks · IDOR · privilege escalation · CORS misconfig.

**Mitigations**: authz at every endpoint · indirect object refs · least privilege · validate CORS · test access controls.

## A02 — Cryptographic Failures

**Issues**: weak algorithms · insecure key mgmt · plaintext storage · weak SSL/TLS.

**Mitigations**: AES-256, RSA-2048+ · bcrypt/argon2 for passwords · encrypt at rest · HTTPS everywhere (TLS 1.2+) · key rotation · secure RNG.

## A03 — Injection

**Issues**: SQL · NoSQL · command · LDAP · XPath.

**Mitigations**: parameterized queries / prepared statements · validate & sanitize inputs · ORM query builders · whitelist validation · escape special chars · least-privilege DB users.

## A04 — Insecure Design

**Issues**: missing security controls · weak threat modeling · insecure defaults.

**Mitigations**: security by design · threat modeling · secure design patterns · secure defaults · documented security requirements.

## A05 — Security Misconfiguration

**Issues**: default credentials · unnecessary features · missing headers · verbose errors · outdated deps.

**Mitigations**: remove defaults · disable unused features · security headers (CSP, HSTS, X-Frame-Options) · generic errors · update deps · use config checklists.

## A06 — Vulnerable & Outdated Components

**Issues**: unpatched deps · unknown deps · outdated frameworks.

**Mitigations**: regular updates · dependency scanning · component inventory · monitor advisories · remove unused deps · package managers with security features.

## A07 — Identification & Authentication Failures

**Issues**: weak passwords · session fixation · insecure recovery · missing MFA · weak session management.

**Mitigations**: strong password policies · secure session mgmt · secure recovery · MFA · account lockout · httpOnly cookie token storage.

## A08 — Software & Data Integrity Failures

**Issues**: insecure CI/CD · unsigned updates · dependency confusion.

**Mitigations**: secure CI/CD · code signing · integrity verification · dependency pinning · package verification.

## A09 — Security Logging & Monitoring Failures

**Issues**: insufficient logging · missing security event monitoring · inadequate log retention.

**Mitigations**: log security events · monitor suspicious activity · alerting · log retention · log integrity protection · centralized logging.

## A10 — Server-Side Request Forgery (SSRF)

**Issues**: unvalidated user URLs · internal network exposure.

**Mitigations**: validate & sanitize URLs · URL allowlists · disable internal network access · network segmentation · validate responses.
