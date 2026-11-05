"""Redact credential-shaped text before it is written to evidence."""

from __future__ import annotations

import re

_ASSIGNMENT = re.compile(
    r"(?i)\b(api[_-]?key|token|password|secret|authorization)\b(\s*[:=]\s*)(\S+)"
)
_AKIA = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
_PRIVATE = re.compile(
    r"-----BEGIN (?:RSA |OPENSSH |EC |OPENPGP )?PRIVATE KEY-----"
    r"[\s\S]*?"
    r"-----END (?:RSA |OPENSSH |EC |OPENPGP )?PRIVATE KEY-----"
)


def redact(text: str) -> str:
    """Replace secret-shaped substrings. Surrounding labels stay so logs remain readable."""
    cleaned = _PRIVATE.sub("[REDACTED_PRIVATE_KEY]", text)
    cleaned = _AKIA.sub("[REDACTED]", cleaned)
    return _ASSIGNMENT.sub(lambda match: f"{match.group(1)}{match.group(2)}[REDACTED]", cleaned)


def contains_secret(text: str) -> bool:
    """True when text still carries a credential-shaped value."""
    return bool(_ASSIGNMENT.search(text) or _AKIA.search(text) or _PRIVATE.search(text))
