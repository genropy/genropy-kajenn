#!/bin/sh
# Build the bundles a genropy site is served from. The CI and a developer
# run the same commands.
#
#   build.sh lock <genropy tree>
#       resolve what genropy and the packages $GNR_PACKAGES require, under the
#       package list of the image and genropy/constraints.txt, and write the
#       exact versions of what the image lacks to genropy/genropy.lock
#   build.sh genropy <genropy tree> <tag>
#       the genropy bundle, pushed to $REGISTRY/genropy-bundle:<tag>
#   build.sh application <project dir> <project> <instance> <genropy bundle> <name> <tag>
#       an application bundle on top of <genropy bundle>, pushed to $REGISTRY/<name>:<tag>
#
# genropy and application print the reference by digest of what they pushed.
#
# Environment:
#   IMAGE          the genropy-kajenn image the bundles are built under
#   REGISTRY       where the bundles are pushed
#   PLATFORM       the platform of the build: the one of the image
#   GNR_PACKAGES   the genropy packages whose requirements.txt enter the bundle
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
IMAGE=${IMAGE:-ghcr.io/genropy/genropy-kajenn:latest}
REGISTRY=${REGISTRY:-ghcr.io/genropy}
PLATFORM=${PLATFORM:-linux/amd64}
GNR_PACKAGES=${GNR_PACKAGES:-adm sys}

pushed() {
    docker push -q "$1" >/dev/null
    docker inspect --format '{{index .RepoDigests 0}}' "$1"
}

case "${1:-}" in
lock)
    TREE=$(cd "$2" && pwd)
    REQUIREMENTS=""
    for package in $GNR_PACKAGES; do
        REQUIREMENTS="$REQUIREMENTS /src/genropy/projects/gnrcore/packages/$package/requirements.txt"
    done
    docker run --rm --platform "$PLATFORM" --user root --entrypoint sh \
        -v "$TREE":/src/genropy:ro -v "$HERE":/bundles "$IMAGE" -c "
        python -m pip install -q --no-cache-dir uv &&
        uv pip compile -q /src/genropy/gnrpy/pyproject.toml --extra pgsql $REQUIREMENTS \
            -c /image-packages.txt -c /bundles/genropy/constraints.txt \
            --no-header --no-annotate -o /tmp/resolved.txt &&
        python /bundles/tools/missing_packages.py /image-packages.txt /tmp/resolved.txt \
            > /bundles/genropy/genropy.lock"
    echo "$(grep -c '==' "$HERE/genropy/genropy.lock") packages in genropy/genropy.lock"
    ;;
genropy)
    TREE=$(cd "$2" && pwd)
    TARGET="$REGISTRY/genropy-bundle:$3"
    docker buildx build --load -q --platform "$PLATFORM" --provenance=false \
        --build-arg IMAGE="$IMAGE" --build-arg GNR_PACKAGES="$GNR_PACKAGES" \
        --build-context genropy="$TREE" -t "$TARGET" "$HERE/genropy" >/dev/null
    pushed "$TARGET"
    ;;
application)
    PROJECT_DIR=$(cd "$2" && pwd)
    PROJECT=$3
    INSTANCE=$4
    GENROPY_BUNDLE=$5
    TARGET="$REGISTRY/$6:$7"
    CONTEXT=$(mktemp -d)
    cp "$HERE/application/Dockerfile" "$CONTEXT/Dockerfile"
    cat > "$CONTEXT/bundle.json" <<JSON
{
  "application": "$PROJECT",
  "instance": "$INSTANCE",
  "build": "$7",
  "genropy_bundle": "$GENROPY_BUNDLE",
  "image": "$IMAGE"
}
JSON
    docker buildx build --load -q --platform "$PLATFORM" --provenance=false \
        --build-arg GENROPY_BUNDLE="$GENROPY_BUNDLE" --build-arg PROJECT="$PROJECT" \
        --build-context application="$PROJECT_DIR" -t "$TARGET" "$CONTEXT" >/dev/null
    rm -rf "$CONTEXT"
    pushed "$TARGET"
    ;;
*)
    sed -n 2,23p "$0"
    exit 2
    ;;
esac
