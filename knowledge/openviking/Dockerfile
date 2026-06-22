FROM python:3.13-slim

# This Dockerfile builds an image that is intended for deployment on SPIN.
# It provides the following:
# * group and user management (needed to attach to a NERSC account)
# * installation of pinned versions of openviking and litellm[google]
# * the migrate-embedding script (for updating embedding models as necessary)
# * /ov directory for volume mounts
# Note that this assumes that the config file is mounted at OV_CONFIG_PATH
# (default /var/openviking/ov.conf). That will need to be set up via
# Rancher/Kubernetes (or a bind mount for docker-compose).

# Locations are parameterized so the same image works under SPIN/K8s and
# docker-compose. Override OV_CONFIG_PATH / OV_HOME at build or run time.
ARG OV_CONFIG_PATH=/var/openviking/ov.conf
ARG OV_HOME=/ov
ENV OV_CONFIG_PATH=${OV_CONFIG_PATH}
ENV OV_HOME=${OV_HOME}


# Add SPIN user id. `--home` + `--shell` give the account a real, writable
# HOME — without these, `adduser --system` defaults to HOME=/nonexistent,
# which breaks any tool that reads/writes under $HOME (e.g. the bundled
# `claude` CLI used by the chat feature hangs on its config path).
RUN addgroup --system --gid 76761 openviking
RUN adduser --system --uid 76761 \
    --home /home/ov \
    --shell /bin/bash \
    --ingroup openviking \
    ov

RUN pip install --no-cache openviking==0.3.24 litellm[google]>=1.83.12

COPY migrate-embedding ${OV_HOME}/migrate-embedding

# Pre-create the workspace dir owned by ov. A named volume mounted at
# ${OV_HOME}/workspace inherits ownership/permissions from this image
# directory; without it Docker creates the volume root as root:root and the
# ov user gets PermissionError trying to write under /ov/workspace.
RUN mkdir -p ${OV_HOME}/workspace

WORKDIR ${OV_HOME}
RUN chown -R ov:openviking ${OV_HOME}

USER ov

EXPOSE 1933
EXPOSE 8020

# Shell form so ${OV_CONFIG_PATH} is expanded from the environment at runtime;
# `exec` replaces the shell so the server (PID 1) receives OS signals directly.
CMD exec openviking-server --config ${OV_CONFIG_PATH}
