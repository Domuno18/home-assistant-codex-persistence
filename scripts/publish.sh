#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

git remote get-url origin >/dev/null 2>&1 \
  || { echo "ERROR: origin is missing; run create_private_repo.sh first."; exit 1; }
command -v gh >/dev/null 2>&1 \
  || { echo "ERROR: GitHub CLI (gh) is missing."; exit 1; }

SICHTBARKEIT=$(gh repo view --json visibility --jq '.visibility')
[ "$SICHTBARKEIT" = "PRIVATE" ] \
  || { echo "ERROR: Publication requires a confirmed PRIVATE repository."; exit 1; }

./scripts/validate.sh
./scripts/security-scan.sh --all-history
BRANCH=$(git symbolic-ref --short HEAD)
git push -u origin "$BRANCH" --follow-tags
echo "✔ Branch and annotated release tags published."
