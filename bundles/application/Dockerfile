# syntax=docker/dockerfile:1
# An application bundle: built on top of a genropy bundle named by digest, it
# adds the project and its manifest. One digest identifies the pair.
#
# Build contexts:
#   .             a folder holding bundle.json
#   application   the project folder (packages, instances, sites)
ARG GENROPY_BUNDLE
FROM ${GENROPY_BUNDLE}
ARG PROJECT
COPY --from=application . /projects/${PROJECT}
COPY bundle.json /bundle.json
