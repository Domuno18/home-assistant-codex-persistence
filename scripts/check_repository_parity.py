#!/usr/bin/env python3
"""Check product parity without copying private history into a public repository."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import stat
import subprocess


def files(root: Path, *, clean: bool) -> set[str]:
    actual = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], cwd=root, text=True).strip()
    if Path(actual).resolve() != root.resolve():
        raise ValueError("expected a repository root")
    if clean and subprocess.check_output(["git", "status", "--porcelain"], cwd=root):
        raise ValueError("release parity requires two clean committed trees")
    output = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=root)
    return {name.decode("utf-8") for name in output.split(b"\0") if name}


def normalize(name: str, body: bytes, *, private: bool) -> bytes:
    if name == "project-definition.json":
        data = json.loads(body)
        project = data["project"]
        expected = "private" if private else "public"
        if (project["repository_visibility"] != expected
                or project["public_release_allowed"] is not (not private)):
            raise ValueError("repository visibility metadata differs from its line")
        expected_name = "home-assistant-codex-persistence" + ("-private" if private else "")
        if project.pop("repository_name") != expected_name:
            raise ValueError("unexpected repository identity")
        project.pop("repository_visibility")
        project.pop("public_release_allowed")
        meta = data["meta"]
        expected_status = "private-development-archive" if private else "approved"
        if meta.pop("status") != expected_status:
            raise ValueError("unexpected publication status")
        for key in ("published_at", "release_approved_at"):
            meta.pop(key, None)
        return json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    if name == "docs/BACKLOG.md":
        text, count = re.subn(
            rb"(?m)^- \[x\] BL-008 [^\r\n]+$", b"BL-008: project origin", body)
        if count != 1:
            raise ValueError("expected one historical origin entry")
        return text
    if name == "docs/BETA-4-ACCEPTANCE.md":
        text = body
        for pattern, replacement in (
            (rb"Release commit: `[0-9a-f]{40}`", b"Release commit: <line-specific>"),
            (rb"Archive SHA-256: `[0-9a-f]{64}`", b"Archive SHA-256: <line-specific>"),
            (rb"https://github\.com/Domuno18/home-assistant-codex-persistence(?:-private)?/releases/tag/v0\.9\.0-beta\.4",
             b"<line-specific beta.4 release>"),
        ):
            text, count = re.subn(pattern, replacement, text)
            if count != 1:
                raise ValueError("expected one historical release provenance field")
        return text
    return body


def compare(private: Path, public: Path, *, clean: bool = False) -> int:
    if private.resolve() == public.resolve():
        raise ValueError("private and public repositories must be different")
    private_files, public_files = files(private, clean=clean), files(public, clean=clean)
    if private_files != public_files:
        raise ValueError("file inventories differ: " + ", ".join(sorted(private_files ^ public_files)))
    for name in sorted(private_files):
        left, right = private / name, public / name
        a, b = left.lstat(), right.lstat()
        if not stat.S_ISREG(a.st_mode) or not stat.S_ISREG(b.st_mode):
            raise ValueError("non-regular product member: " + name)
        if bool(a.st_mode & 0o111) != bool(b.st_mode & 0o111):
            raise ValueError("executable mode differs: " + name)
        if normalize(name, left.read_bytes(), private=True) != normalize(
                name, right.read_bytes(), private=False):
            raise ValueError("product content differs: " + name)
    return len(private_files)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private", type=Path, required=True)
    parser.add_argument("--public", type=Path, required=True)
    parser.add_argument("--clean", action="store_true", help="require two clean committed trees")
    args = parser.parse_args()
    try:
        count = compare(args.private, args.public, clean=args.clean)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        print("BLOCK repository parity: " + str(exc))
        return 1
    print(f"OK repository parity: {count} files; only documented provenance/metadata differences")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
