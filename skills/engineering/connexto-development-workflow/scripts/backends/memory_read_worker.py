#!/usr/bin/env python3
"""Test/double memory read backend. Reads from the local store populated by memory_write_worker."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def main() -> int:
    key = os.environ["CDW_MEMORY_IDEMPOTENCY_KEY"]
    store = Path(os.environ.get("CDW_MEMORY_STORE", ".connexto/memory-store"))
    target = store / f"{key}.md"
    if not target.is_file():
        print(f"missing stored page for {key}", file=sys.stderr)
        return 1
    sys.stdout.write(target.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
