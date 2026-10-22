"""Unit tests for audit_budget.py — coverage of apps/*/DESIGN.md discovery + classification."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import json as _json  # noqa: E402

from audit_budget import (  # noqa: E402
    classify,
    collect,
    format_table,
    iter_candidates,
    to_json,
)


def write_file(path: Path, content: str = "stub content\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestAuditBudgetDesignMd(unittest.TestCase):
    """Verify apps/*/DESIGN.md is discovered and classified as `root`."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_apps_web_design_md_is_discovered(self) -> None:
        target = self.root / "apps" / "web" / "DESIGN.md"
        write_file(target, "# DESIGN.md\nstub\n")

        discovered = {p.resolve() for p in iter_candidates(self.root)}

        self.assertIn(target.resolve(), discovered)

    def test_apps_web_design_md_classified_as_root(self) -> None:
        target = self.root / "apps" / "web" / "DESIGN.md"
        write_file(target, "# DESIGN.md\nstub\n")

        category = classify(target, self.root)

        self.assertEqual(category, "root")

    def test_apps_admin_design_md_is_discovered(self) -> None:
        target = self.root / "apps" / "admin" / "DESIGN.md"
        write_file(target, "# Admin DESIGN.md\n")

        discovered = {p.resolve() for p in iter_candidates(self.root)}
        self.assertIn(target.resolve(), discovered)
        self.assertEqual(classify(target, self.root), "root")

    def test_apps_web_design_md_respects_root_budget(self) -> None:
        write_file(self.root / "apps" / "web" / "DESIGN.md", "# DESIGN.md\n" * 20)

        report = collect(self.root, only=None)
        design_entries = [
            e
            for e in report.entries
            if e.path.as_posix() == "apps/web/DESIGN.md"
        ]

        self.assertEqual(len(design_entries), 1)
        self.assertEqual(design_entries[0].category, "root")
        self.assertGreater(design_entries[0].tokens, 0)

    def test_non_design_md_in_apps_not_matched(self) -> None:
        write_file(self.root / "apps" / "web" / "README.md", "# Readme\n")
        write_file(self.root / "apps" / "web" / "src" / "DESIGN.md", "# nested\n")
        write_file(self.root / "apps" / "web" / "design.md", "# lowercase\n")

        discovered = {p.relative_to(self.root).as_posix() for p in iter_candidates(self.root)}

        self.assertNotIn("apps/web/README.md", discovered)
        self.assertNotIn("apps/web/src/DESIGN.md", discovered)
        self.assertNotIn("apps/web/design.md", discovered)

    def test_existing_patterns_still_work(self) -> None:
        write_file(self.root / "AGENTS.md", "# Agents\n")
        write_file(self.root / "CLAUDE.md", "# Claude\n")
        write_file(
            self.root / ".github" / "pull_request_template.md", "# PR template\n"
        )
        write_file(
            self.root / ".cursor" / "rules" / "sample.mdc",
            "---\ndescription: x\n---\n# Sample\n",
        )
        write_file(
            self.root / ".cursor" / "skills" / "demo" / "SKILL.md",
            "# Skill\n",
        )
        write_file(
            self.root / ".cursor" / "skills" / "demo" / "references" / "ref.md",
            "# Ref\n",
        )

        discovered = {p.relative_to(self.root).as_posix() for p in iter_candidates(self.root)}

        for expected in (
            "AGENTS.md",
            "CLAUDE.md",
            ".github/pull_request_template.md",
            ".cursor/rules/sample.mdc",
            ".cursor/skills/demo/SKILL.md",
            ".cursor/skills/demo/references/ref.md",
        ):
            self.assertIn(expected, discovered, f"expected {expected} to be discovered")


class TestAuditBudgetDocsFolder(unittest.TestCase):
    """Verify docs/ canonical structure is discovered + classified per sub-folder."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_docs_readme_classified_as_architecture(self) -> None:
        target = self.root / "docs" / "README.md"
        write_file(target, "# Docs index\n")

        discovered = {p.resolve() for p in iter_candidates(self.root)}
        self.assertIn(target.resolve(), discovered)
        self.assertEqual(classify(target, self.root), "docs_architecture")

    def test_docs_glossary_classified_as_architecture(self) -> None:
        target = self.root / "docs" / "glossary.md"
        write_file(target, "# Glossary\n")

        discovered = {p.resolve() for p in iter_candidates(self.root)}
        self.assertIn(target.resolve(), discovered)
        self.assertEqual(classify(target, self.root), "docs_architecture")

    def test_docs_architecture_files_classified(self) -> None:
        target = self.root / "docs" / "architecture" / "multi-tenancy.md"
        write_file(target, "# Multi-tenancy\n")

        discovered = {p.resolve() for p in iter_candidates(self.root)}
        self.assertIn(target.resolve(), discovered)
        self.assertEqual(classify(target, self.root), "docs_architecture")

    def test_docs_module_files_classified(self) -> None:
        target = self.root / "docs" / "modules" / "auth.md"
        write_file(target, "# Auth module\n")

        discovered = {p.resolve() for p in iter_candidates(self.root)}
        self.assertIn(target.resolve(), discovered)
        self.assertEqual(classify(target, self.root), "docs_module")

    def test_docs_feature_files_classified(self) -> None:
        target = self.root / "docs" / "features" / "settings.md"
        write_file(target, "# Settings feature\n")

        discovered = {p.resolve() for p in iter_candidates(self.root)}
        self.assertIn(target.resolve(), discovered)
        self.assertEqual(classify(target, self.root), "docs_feature")

    def test_docs_decision_files_classified(self) -> None:
        target = self.root / "docs" / "decisions" / "0001-rls-strategy.md"
        write_file(target, "# ADR\n")

        discovered = {p.resolve() for p in iter_candidates(self.root)}
        self.assertIn(target.resolve(), discovered)
        self.assertEqual(classify(target, self.root), "docs_decision")

    def test_docs_runbook_files_classified(self) -> None:
        target = self.root / "docs" / "runbooks" / "cert-rotation.md"
        write_file(target, "# Cert rotation\n")

        discovered = {p.resolve() for p in iter_candidates(self.root)}
        self.assertIn(target.resolve(), discovered)
        self.assertEqual(classify(target, self.root), "docs_runbook")

    def test_docs_templates_excluded(self) -> None:
        write_file(self.root / "docs" / "_templates" / "module.md", "# template\n")
        write_file(self.root / "docs" / "_templates" / "feature.md", "# template\n")

        discovered = {p.relative_to(self.root).as_posix() for p in iter_candidates(self.root)}

        self.assertNotIn("docs/_templates/module.md", discovered)
        self.assertNotIn("docs/_templates/feature.md", discovered)

    def test_docs_legacy_folders_not_audited(self) -> None:
        write_file(self.root / "docs" / "product" / "legacy.md", "# legacy\n")
        write_file(self.root / "docs" / "specs" / "security" / "SEC-001.md", "# legacy\n")
        write_file(self.root / "docs" / "deploy" / "aws.md", "# legacy\n")
        write_file(self.root / "docs" / "lgpd-cpf-migration.md", "# legacy\n")
        write_file(self.root / "docs" / "notifications-channel-decision.md", "# legacy\n")

        discovered = {p.relative_to(self.root).as_posix() for p in iter_candidates(self.root)}

        self.assertNotIn("docs/product/legacy.md", discovered)
        self.assertNotIn("docs/specs/security/SEC-001.md", discovered)
        self.assertNotIn("docs/deploy/aws.md", discovered)
        self.assertNotIn("docs/lgpd-cpf-migration.md", discovered)
        self.assertNotIn("docs/notifications-channel-decision.md", discovered)

    def test_docs_budgets_per_subfolder(self) -> None:
        write_file(self.root / "docs" / "modules" / "small.md", "# tiny\n")
        write_file(self.root / "docs" / "architecture" / "overview.md", "# overview\n" * 100)

        report = collect(self.root, only=None)
        by_path = {e.path.as_posix(): e for e in report.entries}

        self.assertIn("docs/modules/small.md", by_path)
        self.assertEqual(by_path["docs/modules/small.md"].category, "docs_module")
        self.assertIn("docs/architecture/overview.md", by_path)
        self.assertEqual(by_path["docs/architecture/overview.md"].category, "docs_architecture")


class TestAuditBudgetReportingForDocsCategories(unittest.TestCase):
    """Verify format_table()/to_json() emit sections + entries for new docs_* categories."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        write_file(self.root / "docs" / "architecture" / "overview.md", "# arch\n")
        write_file(self.root / "docs" / "modules" / "auth.md", "# mod\n")
        write_file(self.root / "docs" / "features" / "clients.md", "# feat\n")
        write_file(self.root / "docs" / "decisions" / "0001-rls.md", "# adr\n")
        write_file(self.root / "docs" / "runbooks" / "db-migration.md", "# rb\n")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_format_table_includes_all_docs_sections(self) -> None:
        report = collect(self.root, only=None)
        table = format_table(report, mode="soft")

        self.assertIn("docs/ — architecture + index + glossary", table)
        self.assertIn("docs/modules/*.md (backend)", table)
        self.assertIn("docs/features/*.md (frontend)", table)
        self.assertIn("docs/decisions/*.md (ADRs)", table)
        self.assertIn("docs/runbooks/*.md (operational)", table)
        self.assertIn("docs/architecture/overview.md", table)
        self.assertIn("docs/runbooks/db-migration.md", table)

    def test_to_json_emits_budgets_and_entries_for_docs_categories(self) -> None:
        report = collect(self.root, only=None)
        payload = _json.loads(to_json(report, mode="soft"))

        for cat in (
            "docs_architecture",
            "docs_module",
            "docs_feature",
            "docs_decision",
            "docs_runbook",
        ):
            self.assertIn(cat, payload["budgets"])
            self.assertIn("soft", payload["budgets"][cat])
            self.assertIn("hard", payload["budgets"][cat])

        files_by_path = {f["path"]: f for f in payload["files"]}
        self.assertEqual(
            files_by_path["docs/decisions/0001-rls.md"]["category"], "docs_decision"
        )
        self.assertEqual(
            files_by_path["docs/runbooks/db-migration.md"]["category"], "docs_runbook"
        )


if __name__ == "__main__":
    unittest.main()
