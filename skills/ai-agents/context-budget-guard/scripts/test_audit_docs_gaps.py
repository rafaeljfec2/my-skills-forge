"""Unit tests for audit_docs_gaps.py — extraction + filtering + output formats."""

from __future__ import annotations

import json as _json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from audit_docs_gaps import (  # noqa: E402
    classify,
    collect_gaps,
    extract_gaps_from_file,
    format_json,
    format_md,
    format_text,
    iter_doc_files,
)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestAuditDocsGapsExtraction(unittest.TestCase):
    """Verify markers are extracted with correct line, kind, detail, context."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_extracts_inferido_with_detail(self) -> None:
        target = self.root / "docs" / "modules" / "auth.md"
        write_file(target, "# Auth\n\nLogin issues a cookie [INFERRED — confirm: TTL].\n")

        gaps = extract_gaps_from_file(target, self.root)

        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0].kind, "INFERRED")
        self.assertEqual(gaps[0].line, 3)
        self.assertEqual(gaps[0].detail, "confirm: TTL")
        self.assertIn("Login issues a cookie", gaps[0].context)
        self.assertEqual(gaps[0].category, "module")

    def test_extracts_tbd_without_detail(self) -> None:
        target = self.root / "docs" / "features" / "clients.md"
        write_file(target, "# Clients\n[TBD]\n")

        gaps = extract_gaps_from_file(target, self.root)

        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0].kind, "TBD")
        self.assertEqual(gaps[0].detail, "")
        self.assertEqual(gaps[0].category, "feature")

    def test_multiple_markers_on_same_line(self) -> None:
        target = self.root / "docs" / "architecture" / "esocial.md"
        write_file(target, "Line with [INFERRED] and [TBD: motivation].\n")

        gaps = extract_gaps_from_file(target, self.root)

        self.assertEqual(len(gaps), 2)
        self.assertEqual({g.kind for g in gaps}, {"INFERRED", "TBD"})
        self.assertTrue(all(g.line == 1 for g in gaps))

    def test_long_context_truncated(self) -> None:
        long_line = "x" * 250 + " [TBD]"
        target = self.root / "docs" / "decisions" / "0001-rls.md"
        write_file(target, long_line + "\n")

        gaps = extract_gaps_from_file(target, self.root)

        self.assertEqual(len(gaps), 1)
        self.assertLessEqual(len(gaps[0].context), 200)
        self.assertTrue(gaps[0].context.endswith("..."))

    def test_no_markers_returns_empty(self) -> None:
        target = self.root / "docs" / "runbooks" / "db-migration.md"
        write_file(target, "No markers here.\n")

        gaps = extract_gaps_from_file(target, self.root)

        self.assertEqual(gaps, [])


class TestAuditDocsGapsScope(unittest.TestCase):
    """Verify only audited paths are scanned; templates and legacy excluded."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_iter_includes_canonical_subfolders(self) -> None:
        write_file(self.root / "docs" / "README.md", "# r\n")
        write_file(self.root / "docs" / "glossary.md", "# g\n")
        write_file(self.root / "docs" / "architecture" / "overview.md", "# a\n")
        write_file(self.root / "docs" / "modules" / "auth.md", "# m\n")
        write_file(self.root / "docs" / "features" / "clients.md", "# f\n")
        write_file(self.root / "docs" / "decisions" / "0001-rls.md", "# d\n")
        write_file(self.root / "docs" / "runbooks" / "db.md", "# rb\n")

        discovered = {p.relative_to(self.root).as_posix() for p in iter_doc_files(self.root)}

        self.assertEqual(
            discovered,
            {
                "docs/README.md",
                "docs/glossary.md",
                "docs/architecture/overview.md",
                "docs/modules/auth.md",
                "docs/features/clients.md",
                "docs/decisions/0001-rls.md",
                "docs/runbooks/db.md",
            },
        )

    def test_iter_excludes_templates_and_legacy(self) -> None:
        write_file(self.root / "docs" / "_templates" / "module.md", "[TBD]\n")
        write_file(self.root / "docs" / "product" / "legacy.md", "[TBD]\n")
        write_file(self.root / "docs" / "specs" / "old.md", "[TBD]\n")
        write_file(self.root / "docs" / "deploy" / "aws.md", "[TBD]\n")
        write_file(self.root / "docs" / "modules" / "real.md", "[TBD]\n")

        discovered = {p.relative_to(self.root).as_posix() for p in iter_doc_files(self.root)}

        self.assertEqual(discovered, {"docs/modules/real.md"})

    def test_classify_per_subfolder(self) -> None:
        cases = {
            "docs/README.md": "architecture",
            "docs/glossary.md": "architecture",
            "docs/architecture/auth.md": "architecture",
            "docs/modules/auth.md": "module",
            "docs/features/clients.md": "feature",
            "docs/decisions/0001.md": "decision",
            "docs/runbooks/db.md": "runbook",
        }
        for rel, expected in cases.items():
            target = self.root / rel
            write_file(target, "stub\n")
            self.assertEqual(classify(target, self.root), expected, msg=rel)


class TestAuditDocsGapsFiltersAndFormats(unittest.TestCase):
    """Verify --only filter + format outputs are well-formed."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        write_file(self.root / "docs" / "modules" / "auth.md", "[INFERRED — TTL]\n")
        write_file(self.root / "docs" / "features" / "clients.md", "[TBD]\n")
        write_file(
            self.root / "docs" / "architecture" / "esocial.md",
            "[INFERRED]\n[TBD: motivation]\n",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_collect_all(self) -> None:
        gaps = collect_gaps(self.root)
        self.assertEqual(len(gaps), 4)

    def test_only_filter_single_category(self) -> None:
        gaps = collect_gaps(self.root, only=("module",))
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0].category, "module")

    def test_only_filter_multiple_categories(self) -> None:
        gaps = collect_gaps(self.root, only=("module", "feature"))
        categories = {g.category for g in gaps}
        self.assertEqual(categories, {"module", "feature"})

    def test_format_text_groups_by_file(self) -> None:
        gaps = collect_gaps(self.root)
        out = format_text(gaps)
        self.assertIn("Docs gaps: 4 total", out)
        self.assertIn("=== docs/modules/auth.md", out)
        self.assertIn("docs/architecture/esocial.md:1  [INFERRED]", out)
        self.assertIn("docs/architecture/esocial.md:2  [TBD]", out)

    def test_format_json_emits_summary_and_gaps(self) -> None:
        gaps = collect_gaps(self.root)
        payload = _json.loads(format_json(gaps))
        self.assertEqual(payload["summary"]["total"], 4)
        self.assertEqual(payload["summary"]["inferred"], 2)
        self.assertEqual(payload["summary"]["tbd"], 2)
        self.assertEqual(payload["summary"]["files"], 3)
        self.assertEqual(payload["summary"]["by_category"]["architecture"], 2)
        self.assertEqual(len(payload["gaps"]), 4)
        for entry in payload["gaps"]:
            for required in ("path", "line", "kind", "detail", "context", "category"):
                self.assertIn(required, entry)

    def test_format_md_groups_by_category_and_uses_checkboxes(self) -> None:
        gaps = collect_gaps(self.root)
        out = format_md(gaps)
        self.assertIn("# Docs gaps backlog", out)
        self.assertIn("## docs/modules/ (backend) (1)", out)
        self.assertIn("## docs/features/ (frontend) (1)", out)
        self.assertIn("## docs/architecture/ + index + glossary (2)", out)
        self.assertIn("- [ ] `docs/modules/auth.md:1` **[INFERRED]** — TTL", out)


if __name__ == "__main__":
    unittest.main()
