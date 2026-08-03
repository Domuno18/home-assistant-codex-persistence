#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

MODE="${1:-}"
case "$MODE" in
  ""|--ci|--release) ;;
  *) echo "Usage: $0 [--ci|--release]"; exit 2 ;;
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
PYTHON_DATEIEN=(scripts/validate_project.py)
[ ! -f scripts/create_project.py ] || PYTHON_DATEIEN+=(scripts/create_project.py)
python3 -c 'import ast, pathlib, sys; [ast.parse(pathlib.Path(p).read_text(encoding="utf-8"), filename=p) for p in sys.argv[1:]]' "${PYTHON_DATEIEN[@]}"

echo "Checking structure and traceability…"
if [ "$MODE" = "--release" ]; then
  python3 scripts/validate_project.py --release
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
