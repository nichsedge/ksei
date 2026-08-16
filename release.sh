#!/usr/bin/env bash
set -euo pipefail

BUMP_TYPE="${1:-patch}"

echo "==> 1. Running tests..."
uv run python -m pytest

echo "==> 2. Checking git status..."
CURRENT_BRANCH=$(git branch --show-current)
if [ -z "$CURRENT_BRANCH" ]; then
  echo "Error: Not on a branch (detached HEAD). Cannot proceed."
  exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
  echo "Error: Working directory has uncommitted changes. Please commit or stash them first."
  exit 1
fi

echo "==> 3. Bumping version ($BUMP_TYPE)..."
uv version --bump "$BUMP_TYPE"
NEW_VERSION=$(grep -m1 '^version = ' pyproject.toml | cut -d'"' -f2)
TAG="v${NEW_VERSION}"

echo "==> 4. Building release artifacts..."
rm -rf ./dist
uv build

echo "==> 5. Committing and tagging release ($TAG)..."
git add pyproject.toml uv.lock
git commit -m "chore: release ${TAG}"
git tag -a "$TAG" -m "Release ${TAG}"

echo "==> 6. Publishing to PyPI..."
uv publish

echo "==> 7. Pushing branch and tag to GitHub..."
git push origin "$CURRENT_BRANCH"
git push origin "$TAG"

echo "==> 8. Creating GitHub Release..."
gh release create "$TAG" dist/* \
  --title "${TAG}" \
  --generate-notes

echo "==> Successfully published and released ${TAG}!"
