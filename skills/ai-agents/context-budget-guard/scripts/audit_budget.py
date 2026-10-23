#!/usr/bin/env python3
"""
Audit token budget for every agent-consumed markdown file.

Categories:
  - always              : .cursor/rules/*.mdc with `alwaysApply: true`
  - requestable         : .cursor/rules/*.mdc otherwise
  - skill               : .cursor/skills/*/SKILL.md, .claude/skills/*/SKILL.md,
                          skills/*/*/SKILL.md (forge domain layout)
  - reference           : .cursor/skills/**/references/*.md, .claude/skills/**/references/*.md,
                          skills/*/*/references/**/*.md
  - root                : AGENTS.md, CLAUDE.md (repo root), apps/*/DESIGN.md
  - pr_template         : .github/pull_request_template.md
  - docs_architecture   : docs/README.md, docs/glossary.md, docs/architecture/**/*.md
  - docs_module         : docs/modules/**/*.md (per backend module)
  - docs_feature        : docs/features/**/*.md (per frontend feature)
  - docs_decision       : docs/decisions/**/*.md (ADRs)
  - docs_runbook        : docs/runbooks/**/*.md (operational procedures)

`docs/_templates/`, `docs/product/`, `docs/specs/`, `docs/deploy/`, and legacy
root-level docs (e.g. `docs/lgpd-cpf-migration.md`) are intentionally excluded
from auditing — templates are stubs, legacy folders are scheduled to be
migrated into the canonical structure.

Token approximation: bytes / 3.5 (conservative for technical markdown).

Exit codes:
  0 : every file within budget (and within strict thresholds when --strict is set)
  1 : at least one HARD violation (>= ceiling) or strict-mode danger triggered
  2 : warnings present and --fail-on warn was set
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

CHARS_PER_TOKEN = 3.5

IGNORED_DIRS = {
    "node_modules",
    ".git",
    "dist",
    "build",
    ".turbo",
    ".next",
    "coverage",
    ".vercel",
    ".cache",
}


@dataclass(frozen=True)
class Budget:
    soft_tokens: int
    hard_tokens: int


BUDGETS: dict[str, Budget] = {
    "always": Budget(soft_tokens=3_500, hard_tokens=4_500),
    "requestable": Budget(soft_tokens=5_000, hard_tokens=7_000),
    "skill": Budget(soft_tokens=2_500, hard_tokens=4_000),
    "reference": Budget(soft_tokens=5_000, hard_tokens=7_000),
    "root": Budget(soft_tokens=3_000, hard_tokens=4_000),
    "pr_template": Budget(soft_tokens=2_000, hard_tokens=3_000),
    "docs_architecture": Budget(soft_tokens=3_000, hard_tokens=4_500),
    "docs_module": Budget(soft_tokens=1_500, hard_tokens=2_500),
    "docs_feature": Budget(soft_tokens=1_200, hard_tokens=2_000),
    "docs_decision": Budget(soft_tokens=1_500, hard_tokens=2_500),
    "docs_runbook": Budget(soft_tokens=2_000, hard_tokens=3_000),
}

DOCS_AUDITED_PREFIXES: tuple[str, ...] = (
    "docs/architecture/",
    "docs/modules/",
    "docs/features/",
    "docs/decisions/",
    "docs/runbooks/",
)
DOCS_AUDITED_FILES: frozenset[str] = frozenset({"docs/README.md", "docs/glossary.md"})
DOCS_EXCLUDED_PREFIXES: tuple[str, ...] = (
    "docs/_templates/",
    "docs/product/",
    "docs/specs/",
    "docs/deploy/",
)

AGGREGATE_ALWAYS_APPLY = Budget(soft_tokens=8_000, hard_tokens=10_000)

STRICT_OK_MIN_MARGIN_TOKENS = 200
STRICT_WARN_GAP_RATIO = 0.5


@dataclass
class FileEntry:
    path: Path
    category: str
    bytes_count: int
    tokens: int

    def status(self, mode: str) -> str:
        budget = BUDGETS[self.category]
        threshold = budget.hard_tokens if mode == "ceiling" else budget.soft_tokens
        if self.tokens >= budget.hard_tokens:
            return "FAIL"
        if self.tokens >= budget.soft_tokens:
            return "WARN"
        _ = threshold
        return "OK"

    def margin(self, mode: str) -> int:
        budget = BUDGETS[self.category]
        threshold = budget.hard_tokens if mode == "ceiling" else budget.soft_tokens
        return threshold - self.tokens

    def is_strict_danger(self) -> bool:
        budget = BUDGETS[self.category]
        if self.tokens >= budget.hard_tokens:
            return True
        if self.tokens >= budget.soft_tokens:
            gap = budget.hard_tokens - budget.soft_tokens
            consumed = self.tokens - budget.soft_tokens
            return consumed >= gap * STRICT_WARN_GAP_RATIO
        margin = budget.soft_tokens - self.tokens
        return margin < STRICT_OK_MIN_MARGIN_TOKENS


@dataclass
class Report:
    entries: list[FileEntry] = field(default_factory=list)
    aggregate_always: int = 0

    def by_category(self, category: str) -> list[FileEntry]:
        return [e for e in self.entries if e.category == category]

    def counts(self, mode: str) -> tuple[int, int, int]:
        ok = warn = fail = 0
        for entry in self.entries:
            status = entry.status(mode)
            if status == "OK":
                ok += 1
            elif status == "WARN":
                warn += 1
            else:
                fail += 1
        return ok, warn, fail


def estimate_tokens(byte_count: int) -> int:
    return int(byte_count / CHARS_PER_TOKEN)


def has_always_apply(text: str) -> bool:
    if not text.startswith("---"):
        return False
    end = text.find("\n---", 3)
    if end == -1:
        return False
    front_matter = text[3:end]
    for raw_line in front_matter.splitlines():
        line = raw_line.strip()
        if not line.startswith("alwaysApply"):
            continue
        _, _, value = line.partition(":")
        return value.strip().lower() == "true"
    return False


def is_ignored(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)


def iter_candidates(root: Path) -> Iterable[Path]:
    patterns = (
        ".cursor/rules/*.mdc",
        ".cursor/skills/*/SKILL.md",
        ".cursor/skills/**/references/*.md",
        ".claude/skills/*/SKILL.md",
        ".claude/skills/**/references/*.md",
        # Forge domain layout: skills/<domain>/<name>/SKILL.md
        "skills/*/*/SKILL.md",
        "skills/*/*/references/**/*.md",
    )
    seen: set[Path] = set()
    for pattern in patterns:
        for match in root.glob(pattern):
            if match.is_file() and not is_ignored(match.relative_to(root)):
                seen.add(match.resolve())
                yield match
    for name in ("AGENTS.md", "CLAUDE.md"):
        candidate = root / name
        if candidate.is_file():
            resolved = candidate.resolve()
            if resolved not in seen:
                seen.add(resolved)
                yield candidate
    for design_md in (root / "apps").glob("*/DESIGN.md"):
        if design_md.is_file() and not is_ignored(design_md.relative_to(root)):
            resolved = design_md.resolve()
            if resolved not in seen:
                seen.add(resolved)
                yield design_md
    pr_template = root / ".github" / "pull_request_template.md"
    if pr_template.is_file():
        resolved = pr_template.resolve()
        if resolved not in seen:
            seen.add(resolved)
            yield pr_template
    docs_dir = root / "docs"
    if docs_dir.is_dir():
        for md in docs_dir.rglob("*.md"):
            if not md.is_file():
                continue
            rel = md.relative_to(root).as_posix()
            if is_ignored(md.relative_to(root)):
                continue
            if any(rel.startswith(prefix) for prefix in DOCS_EXCLUDED_PREFIXES):
                continue
            if rel in DOCS_AUDITED_FILES or any(
                rel.startswith(prefix) for prefix in DOCS_AUDITED_PREFIXES
            ):
                resolved = md.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    yield md


def classify(path: Path, root: Path) -> str:
    rel = path.relative_to(root).as_posix()
    if rel in {"AGENTS.md", "CLAUDE.md"}:
        return "root"
    if rel.startswith("apps/") and rel.endswith("/DESIGN.md") and rel.count("/") == 2:
        return "root"
    if rel == ".github/pull_request_template.md":
        return "pr_template"
    if rel.startswith(".cursor/rules/") and rel.endswith(".mdc"):
        text = path.read_text(encoding="utf-8", errors="replace")
        return "always" if has_always_apply(text) else "requestable"
    if "/references/" in rel and rel.endswith(".md"):
        return "reference"
    if rel.endswith("/SKILL.md"):
        return "skill"
    if rel in DOCS_AUDITED_FILES or rel.startswith("docs/architecture/"):
        return "docs_architecture"
    if rel.startswith("docs/modules/"):
        return "docs_module"
    if rel.startswith("docs/features/"):
        return "docs_feature"
    if rel.startswith("docs/decisions/"):
        return "docs_decision"
    if rel.startswith("docs/runbooks/"):
        return "docs_runbook"
    raise ValueError(f"Unclassifiable file: {rel}")


def collect(root: Path, only: str | None) -> Report:
    report = Report()
    for path in sorted(iter_candidates(root)):
        category = classify(path, root)
        if only is not None and category != only:
            continue
        bytes_count = path.stat().st_size
        tokens = estimate_tokens(bytes_count)
        report.entries.append(
            FileEntry(
                path=path.relative_to(root),
                category=category,
                bytes_count=bytes_count,
                tokens=tokens,
            )
        )
        if category == "always":
            report.aggregate_always += tokens
    return report


CATEGORY_LABELS: dict[str, str] = {
    "always": "alwaysApply rules",
    "requestable": "agent_requestable rules",
    "skill": "SKILL.md (top level)",
    "reference": "skill references/*.md",
    "root": "root agent docs",
    "pr_template": "PR template",
    "docs_architecture": "docs/ — architecture + index + glossary",
    "docs_module": "docs/modules/*.md (backend)",
    "docs_feature": "docs/features/*.md (frontend)",
    "docs_decision": "docs/decisions/*.md (ADRs)",
    "docs_runbook": "docs/runbooks/*.md (operational)",
}


def format_table(report: Report, mode: str) -> str:
    lines: list[str] = []
    for category, label in CATEGORY_LABELS.items():
        rows = report.by_category(category)
        if not rows:
            continue
        budget = BUDGETS[category]
        threshold = budget.hard_tokens if mode == "ceiling" else budget.soft_tokens
        lines.append("")
        lines.append(
            f"=== {label}  (budget: {budget.soft_tokens} tok / ceiling: {budget.hard_tokens} tok) ==="
        )
        lines.append(
            f"{'STATUS':<6} {'TOK':>6} {'BYTES':>7} {'MARGIN':>8}  FILE"
        )
        for entry in sorted(rows, key=lambda e: e.tokens, reverse=True):
            status = entry.status(mode)
            margin = entry.margin(mode)
            margin_str = f"{margin:+d}"
            lines.append(
                f"{status:<6} {entry.tokens:>6} {entry.bytes_count:>7} {margin_str:>8}  {entry.path.as_posix()}"
            )
        _ = threshold

    lines.append("")
    lines.append(
        f"=== Aggregate alwaysApply  (budget: {AGGREGATE_ALWAYS_APPLY.soft_tokens} tok / ceiling: {AGGREGATE_ALWAYS_APPLY.hard_tokens} tok) ==="
    )
    threshold = (
        AGGREGATE_ALWAYS_APPLY.hard_tokens
        if mode == "ceiling"
        else AGGREGATE_ALWAYS_APPLY.soft_tokens
    )
    if report.aggregate_always >= AGGREGATE_ALWAYS_APPLY.hard_tokens:
        agg_status = "FAIL"
    elif report.aggregate_always >= AGGREGATE_ALWAYS_APPLY.soft_tokens:
        agg_status = "WARN"
    else:
        agg_status = "OK"
    margin = threshold - report.aggregate_always
    lines.append(
        f"{agg_status:<6} {report.aggregate_always:>6} tokens   margin {margin:+d}"
    )

    ok, warn, fail = report.counts(mode)
    lines.append("")
    lines.append(f"Summary: OK={ok}  WARN={warn}  FAIL={fail}")
    return "\n".join(lines)


def to_json(report: Report, mode: str) -> str:
    payload = {
        "mode": mode,
        "chars_per_token": CHARS_PER_TOKEN,
        "budgets": {k: {"soft": v.soft_tokens, "hard": v.hard_tokens} for k, v in BUDGETS.items()},
        "aggregate_always_apply": {
            "tokens": report.aggregate_always,
            "soft": AGGREGATE_ALWAYS_APPLY.soft_tokens,
            "hard": AGGREGATE_ALWAYS_APPLY.hard_tokens,
        },
        "files": [
            {
                "path": entry.path.as_posix(),
                "category": entry.category,
                "bytes": entry.bytes_count,
                "tokens": entry.tokens,
                "status": entry.status(mode),
                "margin": entry.margin(mode),
            }
            for entry in report.entries
        ],
    }
    ok, warn, fail = report.counts(mode)
    payload["summary"] = {"ok": ok, "warn": warn, "fail": fail}
    return json.dumps(payload, indent=2, ensure_ascii=False)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit token budget of agent-consumed markdown files."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: current working directory).",
    )
    parser.add_argument(
        "--ceiling",
        action="store_true",
        help="Compare against the hard ceiling instead of the soft budget.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="emit_json",
        help="Emit machine-readable JSON.",
    )
    parser.add_argument(
        "--only",
        choices=tuple(BUDGETS.keys()),
        help="Audit a single category.",
    )
    parser.add_argument(
        "--fail-on",
        choices=("fail", "warn"),
        default="fail",
        help="Exit non-zero when this severity is reached (default: fail).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Fail when any file enters the danger zone: WARN consuming >="
            f" {int(STRICT_WARN_GAP_RATIO * 100)}%% of the soft->hard gap, or OK"
            f" with margin < {STRICT_OK_MIN_MARGIN_TOKENS} tokens."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root: Path = args.root.resolve()
    if not root.is_dir():
        print(f"ERROR: root '{root}' is not a directory", file=sys.stderr)
        return 1

    mode = "ceiling" if args.ceiling else "soft"
    report = collect(root, args.only)

    if args.emit_json:
        print(to_json(report, mode))
    else:
        print(format_table(report, mode))

    _, warn, fail = report.counts(mode)
    aggregate_status_fail = (
        report.aggregate_always >= AGGREGATE_ALWAYS_APPLY.hard_tokens
    )
    aggregate_status_warn = (
        report.aggregate_always >= AGGREGATE_ALWAYS_APPLY.soft_tokens
        and not aggregate_status_fail
    )

    if fail > 0 or aggregate_status_fail:
        return 1

    if args.strict:
        danger_files = [e for e in report.entries if e.is_strict_danger()]
        aggregate_gap = (
            AGGREGATE_ALWAYS_APPLY.hard_tokens - AGGREGATE_ALWAYS_APPLY.soft_tokens
        )
        aggregate_consumed = max(
            0, report.aggregate_always - AGGREGATE_ALWAYS_APPLY.soft_tokens
        )
        aggregate_danger = aggregate_status_warn and (
            aggregate_consumed >= aggregate_gap * STRICT_WARN_GAP_RATIO
        )
        aggregate_margin = (
            AGGREGATE_ALWAYS_APPLY.soft_tokens - report.aggregate_always
        )
        aggregate_ok_close = (
            not aggregate_status_warn
            and aggregate_margin < STRICT_OK_MIN_MARGIN_TOKENS
        )
        if danger_files or aggregate_danger or aggregate_ok_close:
            print("", file=sys.stderr)
            print(
                "STRICT MODE: drift detected. Refactor before merging.",
                file=sys.stderr,
            )
            for entry in danger_files:
                print(
                    f"  DANGER  {entry.tokens:>6} tok  {entry.path.as_posix()}",
                    file=sys.stderr,
                )
            if aggregate_danger or aggregate_ok_close:
                print(
                    f"  DANGER  {report.aggregate_always:>6} tok  <aggregate alwaysApply>",
                    file=sys.stderr,
                )
            return 1

    if args.fail_on == "warn" and (warn > 0 or aggregate_status_warn):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
