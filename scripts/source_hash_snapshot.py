#!/usr/bin/env python3
"""Write SHA-256 snapshot for upstream skill sources listed in PROVENANCE.md."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

FORGE = Path(__file__).resolve().parent.parent
DEFAULT_OUT = Path("/tmp/skills-forge-source-hashes.json")
SOURCE_LINE = re.compile(r"^- Source path:\s*(.+)\s*$", re.M)
SKIP_MARKERS = frozenset({"(forge-authored)", "(none)"})
SKIP_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".wasm",
    ".bin",
    ".pyc",
}
SKIP_PARTS = {"__pycache__", ".git"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_source_roots(provenance: Path) -> list[Path]:
    roots: list[Path] = []
    text = provenance.read_text(encoding="utf-8")
    for match in SOURCE_LINE.finditer(text):
        raw = match.group(1).strip()
        if raw in SKIP_MARKERS or raw.startswith("("):
            continue
        path = Path(raw)
        if not path.is_dir():
            print(f"WARN: skipping missing source root: {raw}", file=sys.stderr)
            continue
        roots.append(path.resolve())
    return roots


def files_under(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        out[str(path.resolve())] = sha256_file(path)
    return out


def build_snapshot(roots: list[Path]) -> dict[str, dict[str, str]]:
    snap: dict[str, dict[str, str]] = {}
    for root in roots:
        key = str(root)
        snap[key] = files_under(root)
    return snap


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Output JSON path (default: {DEFAULT_OUT})",
    )
    parser.add_argument(
        "--provenance",
        type=Path,
        default=FORGE / "PROVENANCE.md",
        help="PROVENANCE file to parse",
    )
    args = parser.parse_args()
    if not args.provenance.is_file():
        print(f"Missing {args.provenance}", file=sys.stderr)
        return 1
    roots = parse_source_roots(args.provenance)
    if not roots:
        print(
            "WARN: no local upstream source roots; writing empty snapshot (forge-only checkout)",
            file=sys.stderr,
        )
        snap: dict[str, dict[str, str]] = {}
    else:
        snap = build_snapshot(roots)
    total = sum(len(v) for v in snap.values())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snap, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {total} file hashes for {len(roots)} roots → {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
