#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

git rev-parse -q --verify HEAD >/dev/null 2>&1 \
  || { echo "ERROR: Build requires a commit."; exit 1; }
[ -z "$(git status --porcelain)" ] \
  || { echo "ERROR: Build requires a clean committed tree."; exit 1; }
[ -f VERSION ] || { echo "ERROR: VERSION is missing."; exit 1; }

VERSION=$(tr -d '[:space:]' < VERSION)
NAME=$(basename "$PWD" | tr ' ' '-' | tr -cd '[:alnum:]_.-')
[ -n "$NAME" ] || { echo "ERROR: invalid project name for artifact."; exit 1; }

./scripts/security-scan.sh --all-history
mkdir -p dist
ARTEFAKT="dist/$NAME-$VERSION.tar.gz"
MANIFEST="dist/$NAME-$VERSION.manifest.txt"

[ ! -e "$ARTEFAKT" ] || { echo "ERROR: artifact already exists: $ARTEFAKT"; exit 1; }
git archive --format=tar.gz --output="$ARTEFAKT" HEAD
{
  echo "project=$NAME"
  echo "version=$VERSION"
  echo "commit=$(git rev-parse HEAD)"
  echo "created_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "source=tracked-files-from-HEAD"
  sha256sum "$ARTEFAKT"
} > "$MANIFEST"

echo "✔ Build: $ARTEFAKT"
echo "  Manifest: $MANIFEST"
