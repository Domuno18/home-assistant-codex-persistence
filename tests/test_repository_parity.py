"""TC-032: equal product sources; limited historical metadata exceptions."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("parity", ROOT / "scripts/check_repository_parity.py")
parity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(parity)


class RepositoryParityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.private = Path(self.temp.name) / "private"
        self.public = Path(self.temp.name) / "public"
        for root, private in ((self.private, True), (self.public, False)):
            root.mkdir()
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "scripts").mkdir()
            (root / "scripts/product.py").write_text("print('synthetic')\n")
            (root / "VERSION").write_text("synthetic-version\n")
            (root / "docs").mkdir()
            (root / "docs/BACKLOG.md").write_text(
                "- [x] BL-008 - " + ("Private origin" if private else "Neutral origin") + "\nShared rules\n")
            data = {"meta": {"status": "private-development-archive" if private else "approved",
                             "confirmed": True},
                    "project": {"repository_name": "home-assistant-codex-persistence" + ("-private" if private else ""),
                                "repository_visibility": "private" if private else "public",
                                "public_release_allowed": not private, "goal": "Same product"}}
            (root / "project-definition.json").write_text(json.dumps(data))

    def test_explicit_origin_and_metadata_differences_pass(self):
        self.assertEqual(parity.compare(self.private, self.public), 4)

    def test_code_version_shared_docs_and_inventory_drift_block(self):
        for name in ("scripts/product.py", "VERSION", "docs/BACKLOG.md", "project-definition.json"):
            with self.subTest(name=name):
                path = self.public / name
                old = path.read_bytes()
                if name.endswith(".json"):
                    data = json.loads(old); data["project"]["goal"] = "Different product"
                    path.write_text(json.dumps(data))
                else:
                    path.write_bytes(old + b"unintended change\n")
                with self.assertRaises(ValueError):
                    parity.compare(self.private, self.public)
                path.write_bytes(old)
        (self.public / "extra.py").write_text("extra")
        with self.assertRaises(ValueError):
            parity.compare(self.private, self.public)

    def test_clean_gate_same_root_wrong_line_and_symlink_block(self):
        with self.assertRaises(ValueError):
            parity.compare(self.private, self.public, clean=True)
        with self.assertRaises(ValueError):
            parity.compare(self.private, self.private)
        with self.assertRaises(ValueError):
            parity.compare(self.public, self.private)
        target = self.public / "scripts/product.py"
        target.unlink(); target.symlink_to(self.private / "scripts/product.py")
        with self.assertRaises(ValueError):
            parity.compare(self.private, self.public)

    def test_historical_release_exceptions_leave_behavior_text_compared(self):
        for root, private in ((self.private, True), (self.public, False)):
            repository = "home-assistant-codex-persistence" + ("-private" if private else "")
            digit = "a" if private else "b"
            (root / "docs/BETA-4-ACCEPTANCE.md").write_text(
                f"Release commit: `{digit * 40}`.\nArchive SHA-256: `{digit * 64}`.\n"
                f"https://github.com/Domuno18/{repository}/releases/tag/v0.9.0-beta.4\nSame evidence\n")
        self.assertEqual(parity.compare(self.private, self.public), 5)
        path = self.public / "docs/BETA-4-ACCEPTANCE.md"
        path.write_text(path.read_text().replace("Same evidence", "Unsupported claim"))
        with self.assertRaises(ValueError):
            parity.compare(self.private, self.public)


if __name__ == "__main__":
    unittest.main()
