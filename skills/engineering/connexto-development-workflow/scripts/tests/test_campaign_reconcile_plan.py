"""Plan reconciliation inserts pending sprints without rewriting history."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from connexto_workflow.campaign_plan_reconcile import reconcile_plan
from connexto_workflow.errors import ConfigError, PolicyError

TWO = """### Sprint 012 — Closure

**Feature:** CAD-012 · **Branch:** feat/cad-012-closure

1. **T1 — matrix.** AC: rows
2. **T2 — regression.** AC: green
3. **T3 — audit.** AC: review
4. **T4 — decision.** AC: partial

### Sprint 013 — Health

**Feature:** CAD-013 · **Branch:** feat/cad-013-health

1. **T1 — spec.** AC: gate
2. **T2 — guest.** AC: compile
3. **T3 — host.** AC: serial
4. **T4 — shutdown.** AC: root
"""

THREE = """### Sprint 012 — Closure

**Feature:** CAD-012 · **Branch:** feat/cad-012-closure

1. **T1 — matrix.** AC: rows
2. **T2 — regression.** AC: green
3. **T3 — audit.** AC: review
4. **T4 — decision.** AC: partial

### Sprint 025 — Assessment

**Feature:** CAD-025 · **Branch:** feat/cad-025-assessment

1. **T1 — evidence.** AC: areas
2. **T2 — regression.** AC: ci
3. **T3 — audit.** AC: fresh
4. **T4 — decision.** AC: gate

### Sprint 013 — Health

**Feature:** CAD-013 · **Branch:** feat/cad-013-health

1. **T1 — spec.** AC: gate
2. **T2 — guest.** AC: compile
3. **T3 — host.** AC: serial
4. **T4 — shutdown.** AC: root
"""

SWAPPED = """### Sprint 013 — Health

**Feature:** CAD-013 · **Branch:** feat/cad-013-health

1. **T1 — spec.** AC: gate
2. **T2 — guest.** AC: compile
3. **T3 — host.** AC: serial
4. **T4 — shutdown.** AC: root

### Sprint 012 — Closure

**Feature:** CAD-012 · **Branch:** feat/cad-012-closure

1. **T1 — matrix.** AC: rows
2. **T2 — regression.** AC: green
3. **T3 — audit.** AC: review
4. **T4 — decision.** AC: partial
"""

DUPLICATE = THREE.replace(
    "### Sprint 013 — Health",
    "### Sprint 025 — Assessment",
    1,
).replace(
    "**Feature:** CAD-013 · **Branch:** feat/cad-013-health",
    "**Feature:** CAD-025 · **Branch:** feat/cad-025-other",
    1,
)


def _write_checkpoint(repo: Path) -> Path:
    path = repo / ".connexto" / "campaigns" / "demo" / "state.json"
    path.parent.mkdir(parents=True)
    state = {
        "schema_version": 1,
        "campaign_id": "demo",
        "integration_branch": "develop",
        "release_branch": "main",
        "protected_branches": ["main"],
        "protected_shas": {"main": "abc"},
        "status": "active",
        "current_sprint": None,
        "plan_approval": {"source": "operator-attestation"},
        "blockers": [],
        "sprints": [
            {
                "number": "012",
                "title": "Closure",
                "demand_id": "CAD-012",
                "branch": "feat/cad-012-closure",
                "tasks": ["T1", "T2", "T3", "T4"],
                "status": "merged",
                "merge_sha": "merged-012",
                "historical_note": "keep",
                "reviews": {"pre-pr": {"verdict": "APPROVED"}, "post-pr": None},
            },
            {
                "number": "013",
                "title": "Health",
                "demand_id": "CAD-013",
                "branch": "feat/cad-013-health",
                "tasks": ["T1", "T2", "T3", "T4"],
                "status": "pending",
                "merge_sha": None,
                "reviews": {"pre-pr": None, "post-pr": None},
            },
        ],
    }
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return path


class ReconcilePlanTests(unittest.TestCase):
    def test_inserts_between_neighbors_and_keeps_history(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            path = _write_checkpoint(repo)
            before = json.loads(path.read_text(encoding="utf-8"))
            report = reconcile_plan(repo, "demo", THREE, dry_run=False)
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(
                [item["demand_id"] for item in saved["sprints"]],
                ["CAD-012", "CAD-025", "CAD-013"],
            )
            self.assertEqual(saved["sprints"][0], before["sprints"][0])
            self.assertEqual(saved["sprints"][2], before["sprints"][1])
            self.assertEqual(saved["sprints"][1]["status"], "pending")
            self.assertIsNone(saved["sprints"][1]["merge_sha"])
            self.assertEqual(saved["plan_approval"], before["plan_approval"])
            self.assertEqual(saved["protected_shas"], before["protected_shas"])
            self.assertEqual(report["next_eligible"], "CAD-025")
            self.assertEqual(report["insertions"][0]["after"], "CAD-012")
            self.assertEqual(report["insertions"][0]["before"], "CAD-013")

    def test_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            path = _write_checkpoint(repo)
            before = path.read_bytes()
            report = reconcile_plan(repo, "demo", THREE, dry_run=True)
            self.assertTrue(report["dry_run"])
            self.assertEqual(path.read_bytes(), before)

    def test_second_apply_does_not_rewrite(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            path = _write_checkpoint(repo)
            reconcile_plan(repo, "demo", THREE, dry_run=False)
            written = path.read_bytes()
            report = reconcile_plan(repo, "demo", THREE, dry_run=False)
            self.assertEqual(report["insertions"], [])
            self.assertEqual(path.read_bytes(), written)

    def test_invalid_plan_leaves_state(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            path = _write_checkpoint(repo)
            before = path.read_bytes()
            with self.assertRaises(ConfigError):
                reconcile_plan(repo, "demo", "no sprints\n", dry_run=False)
            self.assertEqual(path.read_bytes(), before)

    def test_duplicate_demand_id_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            path = _write_checkpoint(repo)
            before = path.read_bytes()
            with self.assertRaises(PolicyError):
                reconcile_plan(repo, "demo", DUPLICATE, dry_run=False)
            self.assertEqual(path.read_bytes(), before)

    def test_swap_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            path = _write_checkpoint(repo)
            before = path.read_bytes()
            with self.assertRaises(PolicyError):
                reconcile_plan(repo, "demo", SWAPPED, dry_run=False)
            self.assertEqual(path.read_bytes(), before)

    def test_schema_version_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            path = _write_checkpoint(repo)
            state = json.loads(path.read_text(encoding="utf-8"))
            state["schema_version"] = 2
            path.write_text(json.dumps(state) + "\n", encoding="utf-8")
            before = path.read_bytes()
            with self.assertRaises(PolicyError):
                reconcile_plan(repo, "demo", THREE, dry_run=False)
            self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
