#!/usr/bin/env bash
# Mirror the workspace `senior-code-reviewer` skill into the four mirror nodes:
#
#   1. workspace .cursor/skills/senior-code-reviewer/  ← SOURCE-OF-TRUTH (this dir)
#   2. workspace .claude/skills/senior-code-reviewer/  ← local mirror (kept identical)
#   3. ~/.cursor/skills/senior-code-reviewer/          ← global Cursor mirror
#   4. ~/.claude/skills/senior-code-reviewer/          ← global Claude mirror (only if parent exists)
#
# Usage:
#   bash .cursor/skills/senior-code-reviewer/references/sync-global.sh           # mirror
#   bash .cursor/skills/senior-code-reviewer/references/sync-global.sh --check   # dry-run; exits non-zero on drift
#
# Safe to re-run.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
SRC="${REPO_ROOT}/.cursor/skills/senior-code-reviewer"

CHECK_ONLY=0
[[ "${1:-}" == "--check" ]] && CHECK_ONLY=1

if [[ ! -d "${SRC}" ]]; then
  echo "ERROR: workspace source not found at ${SRC}" >&2
  exit 1
fi

DESTINATIONS=(
  "${REPO_ROOT}/.claude/skills/senior-code-reviewer"
  "${HOME}/.cursor/skills/senior-code-reviewer"
)
[[ -d "${HOME}/.claude/skills" ]] && DESTINATIONS+=("${HOME}/.claude/skills/senior-code-reviewer")

drift=0
for DST in "${DESTINATIONS[@]}"; do
  if [[ ${CHECK_ONLY} -eq 1 ]]; then
    if [[ ! -d "${DST}" ]]; then
      echo "DRIFT: ${DST} missing"
      drift=1
      continue
    fi
    if ! diff -rq --no-dereference "${SRC}" "${DST}" >/dev/null 2>&1; then
      echo "DRIFT: ${DST} differs from ${SRC}"
      diff -rq "${SRC}" "${DST}" || true
      drift=1
    else
      echo "OK: ${DST}"
    fi
  else
    mkdir -p "${DST}"
    rsync -a --delete --exclude '.git' "${SRC}/" "${DST}/"
    echo "MIRRORED: ${SRC} -> ${DST}"
  fi
done

if [[ ${CHECK_ONLY} -eq 1 ]]; then
  if [[ ${drift} -ne 0 ]]; then
    echo "FAIL: one or more mirrors drifted; run without --check to repair" >&2
    exit 2
  fi
  echo "VERIFIED: all mirrors byte-identical with workspace source"
else
  for DST in "${DESTINATIONS[@]}"; do
    diff -rq "${SRC}" "${DST}" >/dev/null && echo "VERIFIED: ${DST}"
  done
fi
