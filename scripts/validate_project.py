#!/usr/bin/env python3
"""Validate structural invariants of Projektvorlage_20 or a generated project."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "README.md",
    "AGENTS.md",
    "PROJECT-PROFILE.md",
    "docs/PROJEKTAUFTRAG.md",
    "docs/ANFORDERUNGEN.md",
    "docs/DOMAENENMODELL.md",
    "docs/ARCHITEKTUR.md",
    "docs/PROJEKTSTRUKTURPLAN.md",
    "docs/TESTKONZEPT.md",
    "docs/NACHWEISMATRIX.md",
    "docs/SECURITY.md",
    "scripts/security-scan.sh",
    "scripts/validate.sh",
    ".githooks/pre-commit",
    ".githooks/pre-push",
)
TRACE_IDS = ("US-001", "AC-001", "REQ-F-001", "DOM-R-001", "AP-100", "TC-001")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--release",
        action="store_true",
        help="Freigabestatus und offene Platzhalter als harte Gates prüfen",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    warnings: list[str] = []

    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            errors.append(f"Pflichtdatei fehlt: {relative}")

    definition_path = ROOT / "project-definition.json"
    if not definition_path.exists():
        print("Strukturprüfung: Vorlagenmodus (Platzhalter sind erlaubt).")
    else:
        try:
            data = json.loads(definition_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"project-definition.json ungültig: {exc}")
            data = {}

        project = data.get("project", {})
        scope = data.get("scope", {})
        visibility = str(project.get("repository_visibility", "")).lower()
        if visibility != "private":
            errors.append("Repository-Vorgabe muss private sein.")
        if project.get("public_release_allowed") is not False:
            errors.append("Öffentliche Freigabe darf nicht implizit aktiviert sein.")

        for key, relative in (
            ("isa95", "docs/ISA95-MODELL.md"),
            ("mathematical_model", "docs/MATHEMATISCHES-MODELL.md"),
            ("external_interfaces", "docs/SCHNITTSTELLEN.md"),
        ):
            path = ROOT / relative
            if scope.get(key) and (
                not path.exists()
                or "\n**Nicht anwendbar:**" in path.read_text(encoding="utf-8")
            ):
                errors.append(f"{relative} ist laut Intake erforderlich.")

        docs_text = "\n".join(
            path.read_text(encoding="utf-8", errors="replace")
            for path in ROOT.rglob("*.md")
        )
        if "{{" in docs_text:
            errors.append("Nicht gerenderte {{...}}-Platzhalter in der Dokumentation.")

        for trace_id in TRACE_IDS:
            if trace_id not in docs_text:
                errors.append(f"Traceability-Basis fehlt: {trace_id}")

        open_pattern = re.compile(r"\bOFFEN(?:-|\s*\()")
        relevant_files = [
            ROOT / "PROJECT-PROFILE.md",
            ROOT / "docs/PROJEKTAUFTRAG.md",
            ROOT / "docs/ANFORDERUNGEN.md",
            ROOT / "docs/DOMAENENMODELL.md",
            ROOT / "docs/ARCHITEKTUR.md",
            ROOT / "docs/PROJEKTSTRUKTURPLAN.md",
            ROOT / "docs/TESTKONZEPT.md",
            ROOT / "docs/NACHWEISMATRIX.md",
        ]
        unresolved = [
            str(path.relative_to(ROOT))
            for path in relevant_files
            if path.exists() and open_pattern.search(path.read_text(encoding="utf-8"))
        ]
        if unresolved:
            message = "Offene Pflichtangaben: " + ", ".join(unresolved)
            if args.release:
                errors.append(message)
            else:
                warnings.append(message)

        if args.release and data.get("meta", {}).get("status") != "approved":
            errors.append(
                "Release benötigt meta.status = approved in project-definition.json."
            )

    for warning in warnings:
        print(f"WARNUNG: {warning}")
    for error in errors:
        print(f"FEHLER: {error}", file=sys.stderr)

    if errors:
        return 1
    print("Struktur- und Traceability-Prüfung OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
