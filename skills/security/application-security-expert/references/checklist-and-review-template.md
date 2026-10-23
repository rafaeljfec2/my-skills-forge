## Security Checklist

When reviewing code for security:

- [ ] Authentication implemented correctly
- [ ] Authorization checks at all endpoints
- [ ] Input validation on all inputs
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output encoding)
- [ ] CSRF protection implemented
- [ ] Sensitive data encrypted
- [ ] Secrets not in code
- [ ] Dependencies up to date
- [ ] Security headers configured
- [ ] Error messages don't leak information
- [ ] Logging doesn't expose sensitive data
- [ ] HTTPS enforced
- [ ] Session management secure
- [ ] Password policies enforced
- [ ] LGPD compliance considered

## Security Review Template

```markdown
# Security Review: [Feature/Component]

## Authentication & Authorization

- [ ] Authentication flow secure
- [ ] Authorization checks present
- [ ] Session management secure
- [ ] Token handling secure

## Data Protection

- [ ] Sensitive data encrypted
- [ ] Secrets managed securely
- [ ] Data exposure minimized

## Input Validation

- [ ] All inputs validated
- [ ] Injection attacks prevented
- [ ] XSS prevention implemented

## Dependencies

- [ ] Dependencies scanned
- [ ] No known vulnerabilities
- [ ] Up-to-date versions

## Compliance

- [ ] LGPD requirements met
- [ ] OWASP Top 10 addressed
- [ ] Security headers configured

## Issues Found

[List security issues]

## Recommendations

[Security improvement suggestions]
```
