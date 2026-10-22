# Implementation Patterns — Crypto, Secrets, Auth, Headers, Validation, LGPD

## Encryption

### Data at Rest

- Encrypt sensitive DB fields
- DB-level encryption when possible
- Encrypt file storage and backups
- AES-256 for symmetric crypto
- Proper key management (KMS/vault)

### Data in Transit

- HTTPS/TLS for all communications
- TLS 1.2+ enforced
- Certificate pinning for mobile apps
- Secure protocols (HTTPS, WSS, SFTP)
- No mixed content (HTTP/HTTPS)
- Validate SSL certificates

### Password Storage

- Never plaintext
- bcrypt / argon2 / scrypt only
- Unique salt per password
- Appropriate cost factors
- Never MD5 or SHA1 for passwords

### Examples

```typescript
import * as bcrypt from "bcrypt";

const saltRounds = 12;
const hashedPassword = await bcrypt.hash(password, saltRounds);
const isValid = await bcrypt.compare(password, hashedPassword);

import * as crypto from "crypto";

const algorithm = "aes-256-gcm";
const key = crypto.randomBytes(32);
const iv = crypto.randomBytes(16);
```

## Secrets Management

- Never commit secrets to VCS
- Environment variables for config
- Rotate secrets regularly
- Use vaults (AWS Secrets Manager, HashiCorp Vault)
- Least-privilege access
- Audit secret access

```typescript
// Bad
const API_KEY = "sk_live_1234567890";

// Good
const API_KEY = process.env.API_KEY;

// Better
const API_KEY = await secretsManager.getSecret("api-key");
```

`.env` files locally (never commit) · vaults in production · validate required secrets at startup · different secrets per env · never log secrets · secret scanning in CI/CD.

## Authentication

### Password Requirements

Minimum 8+ chars · complexity (case, numbers, symbols) · password history · account lockout after failed attempts · secure reset flow.

### Session Management

httpOnly secure cookies · session timeout · regenerate session IDs after login · CSRF tokens · secure logout · server-side encrypted storage.

### Token-Based Auth

JWT with proper expiration · refresh tokens · httpOnly cookies preferred over localStorage · validate signatures · token rotation.

## Authorization

### Access Control

RBAC by default · ABAC when needed · enforce at multiple layers · least privilege · validate on every request · whitelist approach.

### Pattern (NestJS)

```typescript
@Get(':id')
@UseGuards(JwtAuthGuard, RolesGuard)
@Roles('admin', 'user')
async getResource(@Param('id') id: string, @CurrentUser() user: User) {
  if (user.role !== 'admin' && user.id !== id) {
    throw new ForbiddenException();
  }
  return this.service.findOne(id);
}
```

## Security Headers

```typescript
app.use((req, res, next) => {
  res.setHeader("X-Content-Type-Options", "nosniff");
  res.setHeader("X-Frame-Options", "DENY");
  res.setHeader("X-XSS-Protection", "1; mode=block");
  res.setHeader("Strict-Transport-Security", "max-age=31536000; includeSubDomains");
  res.setHeader("Content-Security-Policy", "default-src 'self'");
  res.setHeader("Referrer-Policy", "strict-origin-when-cross-origin");
  next();
});
```

## Input Validation

- Validate all inputs
- Whitelist approach (allow known good)
- Sanitize data
- Validate on both client and server
- Type validation
- Length limits

```typescript
import { IsEmail, IsString, MinLength, MaxLength } from "class-validator";

export class CreateUserDto {
  @IsEmail()
  email: string;

  @IsString()
  @MinLength(8)
  @MaxLength(100)
  password: string;
}
```

## LGPD Compliance

### Principles

Purpose limitation · data minimization · accuracy · storage limitation · integrity & confidentiality · accountability.

### User Rights

Access · correction · deletion · portability · information · object to processing.

### Implementation

Consent management · privacy policy · data export · data deletion · audit access logs · encrypt personal data · retention policies.

## Dependency Security

### Process

1. Check known vulns: `npm audit`, `yarn audit`, `snyk`; monitor advisories; check CVE databases.
2. Evaluate: maintainer reputation; update frequency; dependency tree; license compatibility.
3. Update strategy: regular updates; test in staging; pin critical deps; use lock files.

### Tools

`npm audit` / `yarn audit` · Snyk · Dependabot · OWASP Dependency-Check · Retire.js.
