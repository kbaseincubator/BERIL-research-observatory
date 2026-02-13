# BERIL Observatory UI

Web interface for the BERIL Research Observatory, providing access to research projects, data collections, and shared knowledge from the KBase BER Data Lakehouse.

## Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager

Install uv if you haven't already:

```bash
# Using pip
pip install uv

# Or using the standalone installer
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Installation

1. Navigate to the UI directory:
   ```bash
   cd ui
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   uv sync
   ```

3. Activate the virtual environment:
   ```bash
   source .venv/bin/activate  # On macOS/Linux
   # Or on Windows: .venv\Scripts\activate
   ```

## Configuration

The application uses environment variables with the `BERIL_` prefix (BERIL Research Observatory). Configure the following variables:

### Required Configuration

- `BERIL_DATA_SOURCE_URL`: URL to load cached repository data from (points to the `data-cache` branch)
  ```bash
  export BERIL_DATA_SOURCE_URL="https://raw.githubusercontent.com/your-org/repo/data-cache/data_cache"
  ```

### Optional Configuration

- `BERIL_WEBHOOK_SECRET`: Secret for validating webhook requests from GitHub Actions
  ```bash
  # Generate a secure random secret
  export BERIL_WEBHOOK_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")
  ```

## Running the Application

Start the development server:

```bash
uvicorn app.main:app --reload
```

The UI will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Features

- **Projects**: Browse and explore research projects with rendered Jupyter notebooks
- **Data Collections**: View available BERDL data collections and their schemas
- **Knowledge Base**: Access shared discoveries, pitfalls, and research ideas
- **Automatic Updates**: Webhook-based data refresh when repository content changes

## Data Cache & Webhook Setup

The application can load pre-built repository data from a remote source and automatically update when notified via webhook.

### GitHub Actions Setup

1. **Add GitHub Secrets** in your repository settings (`Settings` → `Secrets and variables` → `Actions`):

   - `DATA_UPDATE_WEBHOOK_URL`: Your application's webhook endpoint
     ```
     https://your-app.com/api/webhook/data-update
     ```

   - `DATA_UPDATE_WEBHOOK_SECRET`: Shared secret for request signing (use the same value as `BERIL_WEBHOOK_SECRET`)
     ```bash
     # Generate and use the same secret for both GitHub and your app
     python -c "import secrets; print(secrets.token_hex(32))"
     ```

2. **Configure Environment Variables** on your application server:
   ```bash
   export BERIL_DATA_SOURCE_URL="https://raw.githubusercontent.com/your-org/repo/data-cache/data_cache"
   export BERIL_WEBHOOK_SECRET="<same-secret-from-github>"
   ```

### How It Works

1. When code is merged to `main`, GitHub Actions:
   - Parses all repository data (projects, docs, schemas)
   - Creates a compressed pickle file (`data.pkl.gz`) and metadata (`timestamp.json`)
   - Pushes these files to the `data-cache` branch
   - Sends a signed webhook request to your application

2. The application receives the webhook:
   - Validates the HMAC-SHA256 signature
   - Reloads data from `BERIL_DATA_SOURCE_URL`
   - Updates the "Last updated" timestamp in the footer

### Manual Data Reload

You can manually trigger a data reload by sending a POST request to the webhook endpoint:

```bash
# Without signature (if BERIL_WEBHOOK_SECRET is not set)
curl -X POST https://your-app.com/api/webhook/data-update \
  -H "Content-Type: application/json" \
  -d '{"event":"manual-reload"}'

# With signature (if BERIL_WEBHOOK_SECRET is set)
PAYLOAD='{"event":"manual-reload"}'
SECRET="your-webhook-secret"
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | sed 's/^.* //')

curl -X POST https://your-app.com/api/webhook/data-update \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: $SIGNATURE" \
  -d "$PAYLOAD"
```

## Development

The application uses:
- **FastAPI**: Web framework
- **Jinja2**: Template rendering
- **nbconvert**: Jupyter notebook rendering
- **Whoosh**: Full-text search
- **Markdown**: Documentation rendering with extensions

To add new dependencies, update `pyproject.toml` and run:

```bash
uv sync
```

## Docker Deployment

The Dockerfile is located at the repository root since the UI needs access to the entire repository (projects, docs, data directories).

### Build the Docker Image

From the repository root:

```bash
docker build -t beril-observatory-ui .
```

### Run the Container

```bash
docker run -p 8000:8000 beril-observatory-ui
```

The UI will be available at [http://localhost:8000](http://localhost:8000)

### Run with Environment Variables

If you need to pass environment variables (like auth tokens):

```bash
docker run -p 8000:8000 --env-file .env beril-observatory-ui
```

### Docker Compose

For production deployment with docker-compose (from repository root):

```yaml
version: '3.8'
services:
  ui:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
```


### Building for SPIN:
```bash
docker build \
  -t registry.nersc.gov/kbase/beril-observatory:latest \
  --platform linux/amd64 \
  --push \
  .
```
You must be logged in to NERSC to push.
```bash
docker login registry.nersc.gov
``` 
Use your NERSC username and password (no MFA)

### Deploying on SPIN
* Push a new image
* Login to SPIN at https://rancher2.nersc.spin.gov
* Go to Development -> Workflows -> Deployments
* In the `knowledge-engine` namespace, go to `beril-observatory`
* Hit the 3 dots menu on the far right, and select redeploy.
