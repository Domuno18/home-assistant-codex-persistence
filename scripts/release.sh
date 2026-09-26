#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

MODE="${1:-}"
case "$MODE" in
  "") VALIDATE_MODE="--release" ;;
  --private) VALIDATE_MODE="--private-release" ;;
  *) echo "Usage: $0 [--private]"; exit 2 ;;
esac

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

./scripts/validate.sh "$VALIDATE_MODE"
[ -n "${HACP_PEER_REPO:-}" ] \
  || { echo "ERROR: Set HACP_PEER_REPO to the other reviewed repository checkout."; exit 1; }
if [ "$MODE" = --private ]; then
  python3 scripts/check_repository_parity.py --private "$PWD" --public "$HACP_PEER_REPO" --clean
else
  python3 scripts/check_repository_parity.py --private "$HACP_PEER_REPO" --public "$PWD" --clean
fi
./scripts/build.sh
git tag -a "$TAG" -m "Release $VERSION"

echo "✔ Local release $VERSION created with tag $TAG."
echo "  Publication is separate; follow docs/RELEASES.md."
