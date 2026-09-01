from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ProjectStructureTest(unittest.TestCase):
    """Safety and traceability invariants generated for every project."""

    @classmethod
    def setUpClass(cls) -> None:
        definition = ROOT / "project-definition.json"
        if not definition.exists():
            raise unittest.SkipTest("Template mode has no project definition")
        cls.data = json.loads(definition.read_text(encoding="utf-8"))

    def test_repository_publication_metadata_is_explicit(self) -> None:
        project = self.data["project"]
        self.assertIn(project["repository_visibility"], {"private", "public"})
        self.assertIsInstance(project["public_release_allowed"], bool)

    def test_core_documentation_exists(self) -> None:
        required = (
            "docs/PROJECT-CHARTER.md",
            "docs/REQUIREMENTS.md",
            "docs/DOMAIN-MODEL.md",
            "docs/ARCHITECTURE.md",
            "docs/PROJECT-PLAN.md",
            "docs/TEST-PLAN.md",
            "docs/EVIDENCE-MATRIX.md",
            "docs/SECURITY.md",
        )
        for relative in required:
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file())

    def test_required_optional_models_are_active(self) -> None:
        mapping = {
            "isa95": "docs/ISA95-MODEL.md",
            "mathematical_model": "docs/MATHEMATICAL-MODEL.md",
            "external_interfaces": "docs/INTERFACES.md",
        }
        for flag, relative in mapping.items():
            if self.data["scope"].get(flag):
                with self.subTest(flag=flag):
                    path = ROOT / relative
                    self.assertTrue(path.is_file())
                    self.assertNotIn(
                        "\n**Not applicable:**",
                        path.read_text(encoding="utf-8"),
                    )

    def test_public_docs_are_english(self) -> None:
        if self.data["project"]["repository_visibility"] != "public":
            self.skipTest("English-only documentation is a public-repository gate")

        german_markers = re.compile(
            r"[äöüÄÖÜß]|"
            r"\b(?:anforderungen|arbeitspaket|ausstehend|automatisiert|"
            r"domänenmodell|erfolgreich|geprüft|nachweismatrix|neustart|"
            r"projektauftrag|projektstrukturplan|schnittstellen|"
            r"testkonzept)\b",
            re.IGNORECASE,
        )
        for path in sorted((ROOT / "docs").rglob("*.md")):
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIsNone(german_markers.search(path.read_text(encoding="utf-8")))

    def test_backlog_separates_completed_lifecycle_evidence(self) -> None:
        backlog = (ROOT / "docs/BACKLOG.md").read_text(encoding="utf-8")
        self.assertIn("[ ] BL-001 — Complete the remaining TC-012 evidence", backlog)
        self.assertIn("[x] BL-016 — Real Studio Code Server update", backlog)
        self.assertNotIn("future regression test", backlog.lower())

    def test_obsolete_or_duplicate_docs_are_absent(self) -> None:
        obsolete = (
            "DEPLOY.md",
            "INTAKE.md",
            "RELEASE_NOTES.md",
            "docs/ARCHITEKTUR.md",
            "docs/BETRIEB.md",
            "docs/PROJEKTAUFNAHME.md",
            "docs/ISA95-MODELL.md",
            "docs/MATHEMATISCHES-MODELL.md",
            "docs/PUBLIC_BETA_ROADMAP.md",
            "docs/arbeitspakete/AP-VORLAGE.md",
            "docs/entscheidungen/ADR-VORLAGE.md",
        )
        for relative in obsolete:
            with self.subTest(relative=relative):
                self.assertFalse((ROOT / relative).exists())

    def test_relative_markdown_links_resolve(self) -> None:
        link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        for source in sorted(ROOT.rglob("*.md")):
            for target in link_pattern.findall(source.read_text(encoding="utf-8")):
                target = target.strip().strip("<>")
                if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                    continue
                path_text = target.split("#", 1)[0]
                if not path_text:
                    continue
                resolved = (source.parent / path_text).resolve()
                with self.subTest(source=source.relative_to(ROOT), target=target):
                    self.assertTrue(resolved.exists())


if __name__ == "__main__":
    unittest.main()
