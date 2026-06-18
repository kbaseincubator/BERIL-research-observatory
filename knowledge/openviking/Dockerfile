FROM python:3.13-slim

# This Dockerfile builds an image that is intended for deployment on SPIN.
# It provides the following:
# * group and user management (needed to attach to a NERSC account)
# * installation of pinned versions of openviking and litellm[google]
# * the migrate-embedding script (for updating embedding models as necessary)
# * /ov directory for volume mounts
# Note that this assumes that the config file is mounted at /var/openviking/ov.conf
# That will need to be set up via Rancher/Kubernetes


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

COPY migrate-embedding /ov/migrate-embedding

WORKDIR /ov
RUN chown ov:openviking /ov

USER ov

EXPOSE 1933
EXPOSE 8020

CMD ["openviking-server", "--config", "/var/openviking/ov.conf"]
