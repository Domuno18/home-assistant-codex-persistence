from __future__ import annotations

import json
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
            "docs/PROJEKTAUFTRAG.md",
            "docs/ANFORDERUNGEN.md",
            "docs/DOMAENENMODELL.md",
            "docs/ARCHITEKTUR.md",
            "docs/PROJEKTSTRUKTURPLAN.md",
            "docs/TESTKONZEPT.md",
            "docs/NACHWEISMATRIX.md",
            "docs/SECURITY.md",
        )
        for relative in required:
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file())

    def test_required_optional_models_are_active(self) -> None:
        mapping = {
            "isa95": "docs/ISA95-MODELL.md",
            "mathematical_model": "docs/MATHEMATISCHES-MODELL.md",
            "external_interfaces": "docs/SCHNITTSTELLEN.md",
        }
        for flag, relative in mapping.items():
            if self.data["scope"].get(flag):
                text = (ROOT / relative).read_text(encoding="utf-8")
                with self.subTest(flag=flag):
                    self.assertNotIn("\n**Nicht anwendbar:**", text)


if __name__ == "__main__":
    unittest.main()
