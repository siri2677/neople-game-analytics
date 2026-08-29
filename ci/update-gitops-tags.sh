#!/bin/sh

set -eu

: "${GITOPS_APP_PATH:?GITOPS_APP_PATH is required}"
: "${GITOPS_ENVIRONMENT:?GITOPS_ENVIRONMENT is required (dev or prod)}"
: "${IMAGE_TAG:?IMAGE_TAG is required}"

case "$GITOPS_ENVIRONMENT" in
  dev|prod) ;;
  *)
    echo "GITOPS_ENVIRONMENT must be dev or prod" >&2
    exit 1
    ;;
esac

case "$IMAGE_TAG" in
  ''|*[!A-Za-z0-9._-]*)
    echo "IMAGE_TAG contains unsupported characters" >&2
    exit 1
    ;;
esac

update_tag() {
  workload="$1"
  file="${GITOPS_APP_PATH}/${workload}/environments/${GITOPS_ENVIRONMENT}/kustomization.yaml"
  test -f "$file" || {
    echo "Image configuration not found: $file" >&2
    exit 1
  }
  sed -i.bak -E "s/^([[:space:]]+newTag:).*/\\1 ${IMAGE_TAG}/" "$file"
  rm -f "${file}.bak"
}

update_tag api
update_tag web

echo "Updated API and Web image tags to $IMAGE_TAG"
