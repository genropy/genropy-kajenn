# The genropy-kajenn image: genropy-kajenn on top of the kajenn-orchestra
# image. The last image of the chain kajenn -> kajenn-orchestra ->
# genropy-kajenn.
#
# It holds no genropy and no application. A site is served from a genropy
# tree and a project that reach the container from outside the image.
#
# The build context is dist/ holding the genropy-kajenn wheel (see
# Dockerfile.dockerignore): the release job passes the wheel it published.
#
# KAJENN_ORCHESTRA_IMAGE names the kajenn-orchestra image, by digest in the
# CI, so the base is known exactly. The packages of the base win: the wheel
# is installed with their versions as constraints, and a requirement the
# base does not meet stops the build.
#
# /image-packages.txt lists every Python package of the image with its
# version: what is built on top of this image reads it.
#
# The start command is the one of the kajenn image: `kajenn serve` on
# /app/config.py. The image carries no /app/config.py.
ARG KAJENN_ORCHESTRA_IMAGE=ghcr.io/kajenn-org/kajenn-orchestra:latest
FROM ${KAJENN_ORCHESTRA_IMAGE}

USER root
COPY dist/*.whl /tmp/wheels/
RUN pip list --format=freeze > /tmp/base-packages.txt \
    && pip install --no-cache-dir -c /tmp/base-packages.txt /tmp/wheels/*.whl \
    && pip check \
    && rm -rf /tmp/wheels /tmp/base-packages.txt \
    && pip list --format=freeze > /image-packages.txt

# gnrkajenn declares the daemon provider before the site machinery is
# imported. The image starts with `kajenn serve`, so it is declared here.
ENV GNR_DAEMON_PROVIDER=genropy-kajenn
USER kajenn
