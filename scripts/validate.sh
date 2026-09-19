#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

MODE="${1:-}"
case "$MODE" in
  ""|--ci|--release|--private-release) ;;
  *) echo "Usage: $0 [--ci|--release|--private-release]"; exit 2 ;;
esac

echo "Checking shell syntax…"
while IFS= read -r -d '' datei; do
  bash -n "$datei"
done < <(find scripts -type f -name '*.sh' -print0)
while IFS= read -r -d '' datei; do
  bash -n "$datei"
done < <(find .githooks -type f -print0)
bash -n release.sh

echo "Checking Python syntax…"
python3 - <<'PYTHON'
import ast
from pathlib import Path
for root in (Path("scripts"), Path("tests")):
    for path in root.rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
PYTHON

echo "Checking structure and traceability…"
if [ "$MODE" = "--release" ]; then
  python3 scripts/validate_project.py --release
elif [ "$MODE" = "--private-release" ]; then
  python3 scripts/validate_project.py --private-release
else
  python3 scripts/validate_project.py
fi

echo "Checking working tree for secrets and binary files…"
./scripts/security-scan.sh --working-tree

if git rev-parse --git-dir >/dev/null 2>&1; then
  git diff --check
  if [ "$MODE" = "--ci" ]; then
    ./scripts/security-scan.sh --all-history
  else
    ./scripts/security-scan.sh --history
  fi
fi

if find tests -type f -name 'test_*.py' -print -quit | grep -q .; then
  echo "Running Python tests…"
  python3 -m unittest discover -s tests -p 'test_*.py'
fi

echo "✔ Validation successful."
