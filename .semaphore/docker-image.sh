#!/usr/bin/env bash
# Build one image target (worker or starter) and push it when main publishes a release.
# Usage: .semaphore/docker-image.sh <target>
set -euo pipefail

target="$1"
image="${IMAGE_PREFIX}-${target}"
release_tag=""

# The Release block uploads this artifact only when it published a new version.
# Build the release tag so the image matches the GitHub Release and its version.
if artifact pull workflow release-version >/dev/null 2>&1; then
  release_tag="v$(cat release-version)"
  git fetch --tags --quiet
  git checkout --quiet "$release_tag"
fi

docker build --target "$target" -t "${image}:build" .

if [ "${SEMAPHORE_GIT_BRANCH}" != "main" ] || [ -n "${SEMAPHORE_GIT_PR_NUMBER:-}" ]; then
  echo "Not a push to main, skipping image push"
  exit 0
fi

if [ -z "$release_tag" ]; then
  echo "No new GitHub Release, skipping image push"
  exit 0
fi

echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USERNAME" --password-stdin
for tag in "$release_tag" latest; do
  docker tag "${image}:build" "${image}:${tag}"
  docker push "${image}:${tag}"
done
