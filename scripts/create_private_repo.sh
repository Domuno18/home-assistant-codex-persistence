#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

PUSH=0
REPO_NAME=""
for arg in "$@"; do
  case "$arg" in
    --push) PUSH=1 ;;
    -*) echo "Usage: $0 [repo-name] [--push]"; exit 2 ;;
    *) [ -z "$REPO_NAME" ] || { echo "Only one repository name is allowed."; exit 2; }
       REPO_NAME="$arg" ;;
  esac
done

command -v gh >/dev/null 2>&1 \
  || { echo "ERROR: GitHub CLI (gh) is missing."; exit 1; }
git rev-parse --git-dir >/dev/null 2>&1 \
  || { echo "ERROR: initialize the local Git repository first."; exit 1; }
git rev-parse -q --verify HEAD >/dev/null 2>&1 \
  || { echo "ERROR: create a validated initial commit first."; exit 1; }

git config core.hooksPath .githooks
./scripts/validate.sh
./scripts/security-scan.sh --all-history
gh auth status >/dev/null

if git remote get-url origin >/dev/null 2>&1; then
  echo "Remote origin already exists; no other repository will be created."
else
  if [ -z "$REPO_NAME" ]; then
    REPO_NAME=$(basename "$PWD" | tr ' ' '-')
  fi
  echo "Creating private GitHub repository: $REPO_NAME"
  gh repo create "$REPO_NAME" --private --source=. --remote=origin
fi

SICHTBARKEIT=$(gh repo view --json visibility --jq '.visibility')
if [ "$SICHTBARKEIT" != "PRIVATE" ]; then
  echo "ERROR: Remote visibility is '$SICHTBARKEIT', expected PRIVATE."
  exit 1
fi
echo "✔ Remote visibility confirmed: PRIVATE"

if [ "$PUSH" -eq 1 ]; then
  exec ./scripts/publish.sh
fi

echo "Nothing pushed yet. After review: ./scripts/publish.sh"
