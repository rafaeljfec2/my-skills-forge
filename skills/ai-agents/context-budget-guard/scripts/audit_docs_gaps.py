#!/usr/bin/env python3
"""
Audit documentation gaps — extract `[INFERRED ...]` and `[TBD ...]` markers
from canonical `docs/` tree to produce an actionable backlog.

Reuses the same audited prefixes/files as `audit_budget.py`, so legacy and
template files are excluded by construction.

Output formats:
  - text (default) : table grouped by file, with line + context
  - json           : structured for CI/dashboards
  - md             : markdown grouped by category, ready to copy as backlog

Exit codes:
  0 : completed (regardless of marker count — discovery is informational)
  2 : invalid arguments
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from audit_budget import (  # noqa: E402
    DOCS_AUDITED_FILES,
    DOCS_AUDITED_PREFIXES,
    DOCS_EXCLUDED_PREFIXES,
    IGNORED_DIRS,
)

MARKER_RE = re.compile(r"\[(INFERRED|TBD)\b([^\]]*)\]")

CATEGORIES = ("architecture", "module", "feature", "decision", "runbook")
CATEGORY_LABELS: dict[str, str] = {
    "architecture": "docs/architecture/ + index + glossary",
    "module": "docs/modules/ (backend)",
    "feature": "docs/features/ (frontend)",
    "decision": "docs/decisions/ (ADRs)",
    "runbook": "docs/runbooks/ (operational)",
}


@dataclass(frozen=True)
class Gap:
    path: Path
    line: int
    kind: str
    detail: str
    context: str
    category: str

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path.as_posix(),
            "line": self.line,
            "kind": self.kind,
            "detail": self.detail,
            "context": self.context,
            "category": self.category,
        }


def is_ignored(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)


def relative_posix(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def is_audited_doc(path: Path, root: Path) -> bool:
    rel = relative_posix(path, root)
    if any(rel.startswith(prefix) for prefix in DOCS_EXCLUDED_PREFIXES):
        return False
    if rel in DOCS_AUDITED_FILES:
        return True
    return any(rel.startswith(prefix) for prefix in DOCS_AUDITED_PREFIXES)


def classify(path: Path, root: Path) -> str:
    rel = relative_posix(path, root)
    if rel in DOCS_AUDITED_FILES or rel.startswith("docs/architecture/"):
        return "architecture"
    if rel.startswith("docs/modules/"):
        return "module"
    if rel.startswith("docs/features/"):
        return "feature"
    if rel.startswith("docs/decisions/"):
        return "decision"
    if rel.startswith("docs/runbooks/"):
        return "runbook"
    raise ValueError(f"Unclassifiable doc path: {rel}")


def iter_doc_files(root: Path) -> Iterable[Path]:
    docs_dir = root / "docs"
    if not docs_dir.is_dir():
        return
    for entry in sorted(docs_dir.rglob("*.md")):
        if not entry.is_file() or is_ignored(entry):
            continue
        if not is_audited_doc(entry, root):
            continue
        yield entry


def extract_gaps_from_file(path: Path, root: Path) -> list[Gap]:
    category = classify(path, root)
    rel_path = Path(relative_posix(path, root))
    gaps: list[Gap] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return gaps
    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        for match in MARKER_RE.finditer(raw_line):
            kind = match.group(1)
            detail = match.group(2).strip(" :—-").strip()
            context = raw_line.strip()
            if len(context) > 200:
                context = context[:197] + "..."
            gaps.append(
                Gap(
                    path=rel_path,
                    line=line_no,
                    kind=kind,
                    detail=detail,
                    context=context,
                    category=category,
                )
            )
    return gaps


def collect_gaps(root: Path, only: tuple[str, ...] | None = None) -> list[Gap]:
    selected = set(only) if only else None
    all_gaps: list[Gap] = []
    for doc in iter_doc_files(root):
        for gap in extract_gaps_from_file(doc, root):
            if selected is not None and gap.category not in selected:
                continue
            all_gaps.append(gap)
    return all_gaps


def format_text(gaps: list[Gap]) -> str:
    if not gaps:
        return "No [INFERRED]/[TBD] markers found.\n"
    lines: list[str] = []
    by_file: dict[str, list[Gap]] = {}
    for gap in gaps:
        by_file.setdefault(gap.path.as_posix(), []).append(gap)
    counts = _summary_counts(gaps)
    lines.append(
        f"Docs gaps: {counts['total']} total "
        f"(INFERRED={counts['inferred']}  TBD={counts['tbd']}) "
        f"across {len(by_file)} file(s)"
    )
    for file_path in sorted(by_file):
        items = by_file[file_path]
        lines.append("")
        lines.append(f"=== {file_path} ({len(items)})")
        for gap in items:
            tail = f" — {gap.detail}" if gap.detail else ""
            lines.append(f"  {file_path}:{gap.line}  [{gap.kind}]{tail}")
    return "\n".join(lines) + "\n"


def format_json(gaps: list[Gap]) -> str:
    counts = _summary_counts(gaps)
    by_category: dict[str, int] = {cat: 0 for cat in CATEGORIES}
    for gap in gaps:
        by_category[gap.category] += 1
    payload = {
        "summary": {
            **counts,
            "files": len({g.path.as_posix() for g in gaps}),
            "by_category": by_category,
        },
        "gaps": [gap.to_dict() for gap in gaps],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def format_md(gaps: list[Gap]) -> str:
    counts = _summary_counts(gaps)
    if not gaps:
        return "# Docs gaps\n\nNo `[INFERRED]`/`[TBD]` markers found.\n"
    lines: list[str] = []
    lines.append("# Docs gaps backlog")
    lines.append("")
    lines.append(
        f"**{counts['total']}** marker(s) "
        f"(`INFERRED={counts['inferred']}`, `TBD={counts['tbd']}`)."
    )
    by_cat: dict[str, list[Gap]] = {}
    for gap in gaps:
        by_cat.setdefault(gap.category, []).append(gap)
    for cat in CATEGORIES:
        items = by_cat.get(cat)
        if not items:
            continue
        lines.append("")
        lines.append(f"## {CATEGORY_LABELS[cat]} ({len(items)})")
        for gap in items:
            tail = f" — {gap.detail}" if gap.detail else ""
            lines.append(
                f"- [ ] `{gap.path.as_posix()}:{gap.line}` **[{gap.kind}]**{tail}"
            )
    return "\n".join(lines) + "\n"


def _summary_counts(gaps: list[Gap]) -> dict[str, int]:
    inferred = sum(1 for g in gaps if g.kind == "INFERRED")
    tbd = sum(1 for g in gaps if g.kind == "TBD")
    return {"total": len(gaps), "inferred": inferred, "tbd": tbd}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List [INFERRED]/[TBD] markers across canonical docs/ tree."
    )
    parser.add_argument("--root", default=".", help="Repo root (default: current dir).")
    parser.add_argument(
        "--format",
        choices=("text", "json", "md"),
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--only",
        action="append",
        choices=CATEGORIES,
        help="Filter by category (repeatable).",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=0,
        help="Max number of gaps to emit (0 = no limit).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    root = Path(args.root)
    only_tuple: tuple[str, ...] | None = tuple(args.only) if args.only else None
    gaps = collect_gaps(root, only=only_tuple)
    if args.max and args.max > 0:
        gaps = gaps[: args.max]
    formatters = {"text": format_text, "json": format_json, "md": format_md}
    sys.stdout.write(formatters[args.format](gaps))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
