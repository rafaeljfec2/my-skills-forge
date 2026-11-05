#!/usr/bin/env python3
"""Test/double memory write backend. Persists body to a local store and prints JSON."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path


def main() -> int:
    body_file = Path(os.environ["CDW_MEMORY_BODY_FILE"])
    page_path = os.environ["CDW_MEMORY_PATH"]
    key = os.environ["CDW_MEMORY_IDEMPOTENCY_KEY"]
    store = Path(os.environ.get("CDW_MEMORY_STORE", ".connexto/memory-store"))
    store.mkdir(parents=True, exist_ok=True)
    body = body_file.read_text(encoding="utf-8")
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    target = store / f"{key}.md"
    target.write_text(body, encoding="utf-8")
    meta = store / f"{key}.json"
    meta.write_text(
        json.dumps({"page_path": page_path, "page_id": key, "body_sha256": digest}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"page_path": page_path, "page_id": key, "body_sha256": digest}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
