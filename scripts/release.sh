#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

git rev-parse -q --verify HEAD >/dev/null 2>&1 \
  || { echo "ERROR: Release requires a Git repository with a commit."; exit 1; }
[ -z "$(git status --porcelain)" ] \
  || { echo "ERROR: Release requires a clean tree."; exit 1; }
[ -f VERSION ] || { echo "ERROR: VERSION is missing."; exit 1; }

VERSION=$(tr -d '[:space:]' < VERSION)
TAG="v$VERSION"
git rev-parse -q --verify "refs/tags/$TAG" >/dev/null 2>&1 \
  && { echo "ERROR: Tag $TAG already exists."; exit 1; }
grep -qF "## $VERSION" CHANGELOG.md \
  || { echo "ERROR: CHANGELOG entry for $VERSION is missing."; exit 1; }

./scripts/validate.sh --release
./scripts/build.sh
git tag -a "$TAG" -m "Release $VERSION"

echo "✔ Local release $VERSION created with tag $TAG."
echo "  Publication requires explicit approval; push the reviewed tag separately."
