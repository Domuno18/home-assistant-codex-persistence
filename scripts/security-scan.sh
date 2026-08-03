#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .githooks/secret-patterns.sh

MODE="${1:---working-tree}"
FUND=0
TMP_DATEI=""

cleanup() {
  [ -z "$TMP_DATEI" ] || [ ! -f "$TMP_DATEI" ] || rm -f -- "$TMP_DATEI"
  return 0
}
trap cleanup EXIT

scan_working_tree() {
  echo "Security-Scan: working tree"
  if git rev-parse --git-dir >/dev/null 2>&1; then
    while IFS= read -r -d '' datei; do
      [ -f "$datei" ] || continue
      if ! scanne_datei "$datei" "$datei"; then FUND=1; fi
    done < <(git ls-files -co --exclude-standard -z)
  else
    while IFS= read -r -d '' datei; do
      if ! scanne_datei "$datei" "$datei"; then FUND=1; fi
    done < <(find . -type f -not -path './.git/*' -not -path '*/__pycache__/*' \
      -not -path './dist/*' -not -path './.venv/*' -not -name '*.pyc' -print0)
  fi
}

scan_staged() {
  git rev-parse --git-dir >/dev/null 2>&1 \
    || { echo "ERROR: --staged requires a Git repository."; exit 2; }
  echo "Security-Scan: staged content"
  while IFS= read -r -d '' datei; do
    TMP_DATEI=$(mktemp)
    git show ":$datei" > "$TMP_DATEI"
    if ! scanne_datei "$datei (staged)" "$TMP_DATEI"; then FUND=1; fi
    rm -f -- "$TMP_DATEI"
    TMP_DATEI=""
  done < <(git diff --cached --name-only --diff-filter=ACMR -z)
}

scan_history() {
  local all="$1" branch bereich
  git rev-parse -q --verify HEAD >/dev/null 2>&1 || return 0
  if [ "$all" = "all" ]; then
    bereich=(--all)
    echo "Security-Scan: complete reachable history"
  else
    branch=$(git symbolic-ref --short HEAD 2>/dev/null || echo main)
    if git rev-parse -q --verify "origin/$branch" >/dev/null 2>&1; then
      bereich=("origin/$branch..HEAD")
    else
      bereich=(HEAD)
    fi
    echo "Security-Scan: unpublished history"
  fi

  if git log --numstat --format= "${bereich[@]}" -- \
      | grep -qE '^-[[:space:]]+-[[:space:]]+'; then
    echo "  Binary file found in scanned history; clean or approve manually."
    FUND=1
  fi
  if ! git log -p "${bereich[@]}" -- | scanne_strom "Git history"; then
    FUND=1
  fi
}

case "$MODE" in
  --working-tree) scan_working_tree ;;
  --staged) scan_staged ;;
  --history) scan_history pending ;;
  --all-history) scan_history all ;;
  --all)
    scan_working_tree
    scan_history all
    ;;
  *)
    echo "Usage: $0 [--working-tree|--staged|--history|--all-history|--all]"
    exit 2
    ;;
esac

if [ "$FUND" -ne 0 ]; then
  echo "ERROR: possible secret or binary finding; do not print or bypass values."
  echo "Rotate a committed credential first, then clean history."
  exit 1
fi
echo "Security scan clean."
