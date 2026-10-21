#!/usr/bin/env bash

# Build one image target (worker or starter) and push it tagged with the version.
# Usage: .semaphore/docker-image.sh <target>
set -euo pipefail

target="$1"
image="${IMAGE_PREFIX}-${target}"

docker build --target "$target" -t "${image}:build" .

if [ "${SEMAPHORE_GIT_BRANCH}" != "main" ] || [ -n "${SEMAPHORE_GIT_PR_NUMBER:-}" ]; then
  echo "Not a push to main, skipping image push"
  exit 0
fi

# Same computation as the Release block, so the image tag matches the GitHub Release.
# semantic-release needs the full history and tags to compute the next version.
git fetch --unshallow --tags --quiet || git fetch --tags --quiet
next="$(uv run --locked semantic-release version --print)"
last="$(uv run --locked semantic-release version --print-last-released)"

if [ "$next" = "$last" ]; then
  echo "No fix/feat commits since v${last}, skipping image push"
  exit 0
fi

echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USERNAME" --password-stdin
for tag in "v${next}" latest; do
  docker tag "${image}:build" "${image}:${tag}"
  docker push "${image}:${tag}"
done
