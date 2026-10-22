#!/usr/bin/env python3
"""Link forge skills into local harness directories.

The forge checkout is the editable copy. Each harness keeps a real
skills directory and receives one symlink per skill folder. Existing
real directories are left in place. Harness-owned entries listed in
PROTECTED_NAMES are never replaced.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|$")
DOMAINS = frozenset(
    {
        "engineering",
        "architecture",
        "quality",
        "security",
        "documentation",
        "devops",
        "design",
        "productivity",
        "ai-agents",
    }
)
PROTECTED_NAMES = frozenset(
    {
        ".system",
        "air-finance-sentinel",
    }
)
# Contract for references/install-map.md. The validator fails if the
# table drops or retargets one of these rows.
REQUIRED_REPLACEMENTS: dict[str, frozenset[str]] = {
    "buscar-vagas-ti": frozenset({"skills/productivity/job-search"}),
    "pr-creator-ado": frozenset({"skills/devops/pr-creator-tr"}),
    "senior-code-reviewer": frozenset(
        {
            "skills/quality/senior-code-review-judge",
            "skills/quality/senior-code-reviewer-protocol",
        }
    ),
}


@dataclass(frozen=True)
class Harness:
    name: str
    directory: Path


@dataclass(frozen=True)
class PlannedLink:
    action: str
    skill_name: str
    link_path: Path
    target: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def harnesses() -> tuple[Harness, ...]:
    home = Path.home()
    return (
        Harness("cursor", home / ".cursor" / "skills"),
        Harness("claude", home / ".claude" / "skills"),
        Harness("codex", home / ".codex" / "skills"),
        Harness("agents", home / ".agents" / "skills"),
    )


def install_map_path(forge: Path) -> Path:
    return forge / "references" / "install-map.md"


def iter_skill_dirs(forge: Path) -> list[Path]:
    return [path.parent for path in sorted((forge / "skills").glob("*/*/SKILL.md"))]


def skill_index(forge: Path) -> tuple[dict[str, Path], list[str]]:
    index: dict[str, Path] = {}
    errors: list[str] = []
    for skill_dir in iter_skill_dirs(forge):
        name = skill_dir.name
        if KEBAB.match(name) is None:
            errors.append(f"Skill folder is not kebab-case: {skill_dir}")
        previous = index.get(name)
        if previous is not None:
            errors.append(f"Duplicate skill name {name}: {previous} and {skill_dir}")
            continue
        index[name] = skill_dir
    return index, errors


def parse_install_rows(text: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for line in text.splitlines():
        match = ROW.match(line.strip())
        if match is None:
            continue
        retired = match.group(1).strip()
        forge_skill = match.group(2).strip()
        if retired == "Retired harness name" or forge_skill == "Forge skill":
            continue
        if retired.startswith("-") or forge_skill.startswith("-"):
            continue
        rows.append((retired, forge_skill))
    return rows


def check_install_map(forge: Path) -> list[str]:
    errors: list[str] = []
    index, index_errors = skill_index(forge)
    errors.extend(index_errors)
    path = install_map_path(forge)
    if not path.is_file():
        return [*errors, f"Missing install map: {path}"]
    text = path.read_text(encoding="utf-8")
    if "air-finance-sentinel" not in text:
        errors.append("install map must record that air-finance-sentinel stays out")
    grouped: dict[str, set[str]] = {}
    for retired, forge_skill in parse_install_rows(text):
        errors.extend(validate_install_row(forge, index, retired, forge_skill))
        grouped.setdefault(retired, set()).add(forge_skill)
    for retired, expected in REQUIRED_REPLACEMENTS.items():
        actual = grouped.get(retired)
        if actual is None:
            errors.append(f"install map is missing retired name {retired}")
            continue
        if actual != set(expected):
            errors.append(
                f"install map paths for {retired} are {sorted(actual)}, expected {sorted(expected)}"
            )
    return errors


def validate_install_row(
    forge: Path,
    index: dict[str, Path],
    retired: str,
    forge_skill: str,
) -> list[str]:
    errors: list[str] = []
    if retired == "air-finance-sentinel":
        errors.append("air-finance-sentinel must not be an install replacement")
    if KEBAB.match(retired) is None:
        errors.append(f"Retired name is not kebab-case: {retired}")
    if retired in index:
        errors.append(f"Retired name {retired} is also a forge skill folder")
    parts = Path(forge_skill).parts
    if len(parts) != 3 or parts[0] != "skills" or parts[1] not in DOMAINS:
        errors.append(f"Forge skill path is outside skills/<domain>/<name>: {forge_skill}")
        return errors
    if KEBAB.match(parts[2]) is None:
        errors.append(f"Forge skill name is not kebab-case: {forge_skill}")
    skill_dir = forge / forge_skill
    if not (skill_dir / "SKILL.md").is_file():
        errors.append(f"Install map target has no SKILL.md: {forge_skill}")
    return errors


def windows_path(path: Path) -> str:
    completed = subprocess.run(
        ["wslpath", "-w", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def assert_safe_windows_arg(value: str) -> None:
    if any(token in value for token in ('"', "\n", "\r", "&", "|")):
        raise ValueError(f"Unsafe Windows path: {value}")


def link_kind(resolved_directory: Path) -> str:
    if str(resolved_directory).startswith("/mnt/"):
        return "windows"
    return "linux"


def windows_skill_target(skill_dir: Path, forge: Path, windows_root: str) -> str:
    relative = skill_dir.resolve().relative_to(forge.resolve())
    suffix = "\\".join(relative.parts)
    return windows_root.rstrip("\\") + "\\" + suffix


def expected_target(skill_dir: Path, forge: Path, kind: str, windows_root: str | None) -> str:
    if kind == "windows":
        if windows_root is None:
            raise RuntimeError("Windows harness is missing its translated forge root")
        return windows_skill_target(skill_dir, forge, windows_root)
    return str(skill_dir.resolve())


def same_target(current: str, expected: str, skill_dir: Path) -> bool:
    if current == expected:
        return True
    if current.replace("/", "\\").casefold() == expected.replace("/", "\\").casefold():
        return True
    candidate = Path(current)
    if candidate == skill_dir:
        return True
    try:
        return candidate.resolve() == skill_dir.resolve()
    except OSError:
        return False


def plan_link(link_path: Path, skill_dir: Path, target: str) -> str:
    if link_path.is_symlink():
        current = os.readlink(link_path)
        if same_target(current, target, skill_dir):
            return "unchanged"
        return "conflict-target"
    if link_path.exists():
        return "conflict-real"
    return "create"


def create_link(link_path: Path, target: str, kind: str) -> None:
    if kind == "linux":
        os.symlink(target, link_path)
        return
    link_win = windows_path(link_path)
    assert_safe_windows_arg(link_win)
    assert_safe_windows_arg(target)
    completed = subprocess.run(
        ["cmd.exe", "/c", f'mklink /D "{link_win}" "{target}"'],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(detail or f"mklink failed with status {completed.returncode}")


def plan_harness(
    harness: Harness,
    forge: Path,
    index: dict[str, Path],
) -> tuple[list[PlannedLink], list[str]]:
    planned: list[PlannedLink] = []
    errors: list[str] = []
    if not harness.directory.exists():
        return planned, [f"{harness.name}: skills directory missing: {harness.directory}"]
    resolved = harness.directory.resolve()
    kind = link_kind(resolved)
    windows_root: str | None = None
    if kind == "windows":
        try:
            windows_root = windows_path(forge)
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            return planned, [f"{harness.name}: cannot translate forge path for Windows: {exc}"]
    for name in sorted(index):
        if name in PROTECTED_NAMES:
            errors.append(f"{harness.name}: refusing to link protected name {name}")
            continue
        skill_dir = index[name]
        target = expected_target(skill_dir, forge, kind, windows_root)
        link_path = resolved / name
        action = plan_link(link_path, skill_dir, target)
        planned.append(PlannedLink(action, name, link_path, target))
    return planned, errors


def apply_planned_links(planned: list[PlannedLink], kind: str, dry_run: bool) -> list[str]:
    errors: list[str] = []
    if dry_run:
        return errors
    for item in planned:
        if item.action != "create":
            continue
        try:
            create_link(item.link_path, item.target, kind)
        except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
            errors.append(f"failed to link {item.skill_name}: {exc}")
    return errors


def print_harness_report(harness_name: str, planned: list[PlannedLink], dry_run: bool) -> None:
    counts: dict[str, int] = {}
    for item in planned:
        counts[item.action] = counts.get(item.action, 0) + 1
    prefix = "dry-run " if dry_run else ""
    summary = " ".join(f"{key}={counts[key]}" for key in sorted(counts))
    print(f"{prefix}{harness_name}: {summary or 'no skills'}")
    for item in planned:
        if not item.action.startswith("conflict"):
            continue
        print(f"  {item.action} {item.skill_name}")
    sys.stdout.flush()


def link_all(forge: Path, dry_run: bool) -> int:
    index, errors = skill_index(forge)
    map_errors = check_install_map(forge)
    for problem in map_errors:
        if problem not in errors:
            errors.append(problem)
    if errors:
        for problem in errors:
            print(f"ERROR: {problem}", file=sys.stderr)
        return 1
    failed = False
    for harness in harnesses():
        planned, harness_errors = plan_harness(harness, forge, index)
        for problem in harness_errors:
            print(f"ERROR: {problem}", file=sys.stderr)
            failed = True
        if not harness.directory.exists():
            continue
        kind = link_kind(harness.directory.resolve())
        apply_errors = apply_planned_links(planned, kind, dry_run)
        for problem in apply_errors:
            print(f"ERROR: {problem}", file=sys.stderr)
            failed = True
        print_harness_report(harness.name, planned, dry_run)
        if any(item.action.startswith("conflict") for item in planned):
            failed = True
    if failed:
        print("Link incomplete. Real directories were left in place.", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Link forge skills into local harness directories.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions without creating symlinks.",
    )
    parser.add_argument(
        "--check-repo",
        action="store_true",
        help="Validate the install map and skill names. Does not touch harness directories.",
    )
    args = parser.parse_args(argv)
    forge = repo_root()
    if args.check_repo:
        problems = check_install_map(forge)
        for problem in problems:
            print(f"ERROR: {problem}", file=sys.stderr)
        if problems:
            return 1
        index, _ = skill_index(forge)
        print(f"OK install map ({len(index)} skills)")
        return 0
    return link_all(forge, args.dry_run)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
