FROM python:3.11-slim

# Add SPIN user id. `--home` + `--shell` give the account a real, writable
# HOME — without these, `adduser --system` defaults to HOME=/nonexistent,
# which breaks any tool that reads/writes under $HOME (e.g. the bundled
# `claude` CLI used by the chat feature hangs on its config path).
RUN addgroup --system --gid 76761 beril_app
RUN adduser --system --uid 76761 \
    --home /home/beril \
    --shell /bin/bash \
    --ingroup beril_app \
    beril

# Create public directory with proper permissions for beril user to write config
RUN mkdir -p /tmp/beril_data_cache && \
    chown beril:beril_app /tmp/beril_data_cache && \
    chmod 755 /tmp/beril_data_cache

# Set working directory to the repository root
WORKDIR /repo

# Install git
RUN apt-get update && \
    apt-get install -y git

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy UI application files for dependency installation
COPY ui/pyproject.toml ui/pyproject.toml
COPY ui/app ui/app
COPY ui/alembic ui/alembic
COPY ui/alembic.ini ui/alembic.ini

# Install dependencies using uv
RUN uv pip install --system --no-cache -e ui/

# Copy all necessary repository directories
COPY projects ./projects
COPY docs ./docs
COPY data ./data
COPY atlas ./atlas
COPY ui/config ./ui/config

# Expose port 8000
EXPOSE 8000

# Set working directory to UI for running the app
WORKDIR /repo/ui

USER beril

ARG GIT_COMMIT
ARG BUILD_DATE
ENV BERIL_GIT_COMMIT=${GIT_COMMIT}
ENV BERIL_BUILD_DATE=${BUILD_DATE}

# Run the application
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips=\"*\""]
