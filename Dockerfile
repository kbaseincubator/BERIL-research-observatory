# Use Python 3.11 slim image
FROM python:3.11-slim

# Add SPIN user id
RUN addgroup --system --gid 76761 beril_app
RUN adduser --system --uid 76761 beril

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

# Install dependencies using uv
RUN uv pip install --system --no-cache -e ui/

# Copy all necessary repository directories
COPY projects ./projects
COPY docs ./docs
COPY data ./data
COPY ui/config ./ui/config

# Expose port 8000
EXPOSE 8000

# Set working directory to UI for running the app
WORKDIR /repo/ui

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
