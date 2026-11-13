# syntax=docker/dockerfile:1
# The genropy bundle: genropy at one commit and the Python packages it needs
# that the genropy-kajenn image lacks. A directory tree with no operating
# system inside.
#
# Build contexts:
#   .         this folder (the lock)
#   genropy   the genropy tree at one commit, without application projects
ARG IMAGE
FROM ${IMAGE} AS build
ARG GNR_PACKAGES="adm sys"
USER root
COPY genropy.lock /src/genropy.lock
COPY --from=genropy . /src/genropy
# The lock holds exact versions of what the image lacks: nothing is resolved
# here. The bytecode is compiled now because the bundle is read-only later.
RUN python -m pip install --no-cache-dir --no-deps --target /out/python -r /src/genropy.lock \
    && python -m pip install --no-cache-dir --no-deps --target /out/python /src/genropy/gnrpy \
    && python -m compileall -q /out/python
# The lock was made for one genropy commit. It is checked against this one:
# every installed package finds what it requires, and every line of the
# requirements.txt of the genropy packages is met by the image plus the
# bundle. With no index, a requirement that is not met stops the build.
RUN export PYTHONPATH=/out/python \
    && python -m pip check \
    && for package in $GNR_PACKAGES; do \
         python -m pip install --dry-run --no-index \
             -r /src/genropy/projects/gnrcore/packages/$package/requirements.txt || exit 1; \
       done

FROM scratch
COPY --from=build /out/python /python
