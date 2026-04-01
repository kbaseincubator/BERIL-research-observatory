# Microbial Discovery Forge UI

Web interface for the Microbial Discovery Forge — an AI co-scientist and research observatory for BERDL-scale microbial discovery. Provides access to research projects, data collections, skills, and shared knowledge from the KBase BER Data Lakehouse.

## Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- PostgreSQL 14 or higher (for the user database)

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

Copy `.env.example` to `.env` at the repository root and fill in the values. All variables use the `BERIL_` prefix.

### Required

| Variable | Description |
|---|---|
| `BERIL_DB_PASSWORD` | PostgreSQL password — app will not start without this |
| `BERIL_SESSION_SECRET_KEY` | Signs session cookies — generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `BERIL_ORCID_CLIENT_ID` | ORCiD OAuth2 client ID |
| `BERIL_ORCID_CLIENT_SECRET` | ORCiD OAuth2 client secret |

### Database

| Variable | Default | Description |
|---|---|---|
| `BERIL_DB_HOST` | `localhost` | PostgreSQL host (use service name in Kubernetes/SPIN) |
| `BERIL_DB_PORT` | `5432` | PostgreSQL port |
| `BERIL_DB_USER` | `beril_user` | PostgreSQL username |
| `BERIL_DB_PASSWORD` | *(required)* | PostgreSQL password |
| `BERIL_DB_NAME` | `beril` | PostgreSQL database name |

### ORCiD OAuth2

| Variable | Default | Description |
|---|---|---|
| `BERIL_ORCID_BASE_URL` | `https://orcid.org` | Use `https://sandbox.orcid.org` for development |
| `BERIL_ORCID_CLIENT_ID` | — | From ORCiD developer tools |
| `BERIL_ORCID_CLIENT_SECRET` | — | From ORCiD developer tools |
| `BERIL_ORCID_REDIRECT_ROOT` | `http://localhost:8000` | Use `127.0.0.1` not `localhost` — ORCiD blocks `localhost` |
| `BERIL_ORCID_REDIRECT_PATH` | `/auth/orcid/callback` | Callback path |

### Data / Git sync

| Variable | Default | Description |
|---|---|---|
| `BERIL_DATA_REPO_URL` | — | Git repository URL to clone/pull data from |
| `BERIL_DATA_REPO_BRANCH` | `data-cache` | Branch to checkout |
| `BERIL_DATA_REPO_PATH` | `/tmp/beril_data_cache` | Local clone path |
| `BERIL_WEBHOOK_SECRET` | — | HMAC secret for validating GitHub webhook requests |

## Running the Application

1. **Set up the database.** The app creates tables automatically on first start using SQLAlchemy's `create_all`. Ensure PostgreSQL is running and `BERIL_DB_PASSWORD` (and other `BERIL_DB_*` vars) are set.

   For local development with Docker:
   ```bash
   docker run --name pg -e POSTGRES_PASSWORD=mypassword -d -p 5432:5432 postgres:18
   # Then in psql (connect with: psql -h 127.0.0.1 -U postgres):
   # CREATE USER beril_user WITH PASSWORD 'mypassword';
   # CREATE DATABASE beril OWNER beril_user;
   ```

2. **Start the development server:**
   ```bash
   uvicorn app.main:app --reload
   ```

The UI will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000)

> **Note:** Use `127.0.0.1`, not `localhost` — ORCiD OAuth2 and asyncpg both have issues with `localhost` on some systems.

## Features

- **AI Co-Scientist**: Research loop methodology (Plan → Run → Learn → Reuse)
- **Projects**: Browse and explore research projects with rendered Jupyter notebooks
- **Data Collections**: View available BERDL data collections and their schemas
- **Skills**: Browse reusable AI co-scientist skills
- **Knowledge Base**: Access shared discoveries, pitfalls, performance tips, and research ideas
- **Community**: Contributor profiles with project and collection linkage
- **User Accounts**: ORCiD-based login with persistent user profiles and project ownership stored in PostgreSQL
- **Automatic Updates**: Webhook-based data refresh when repository content changes

## Data Cache & Webhook Setup

The application uses a git-based approach to load and automatically update repository data without restarts.

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
   export BERIL_DATA_REPO_URL="https://github.com/kbaseincubator/BERIL-research-observatory.git"
   export BERIL_DATA_REPO_BRANCH="data-cache"  # Optional, defaults to "data-cache"
   export BERIL_WEBHOOK_SECRET="<same-secret-from-github>"
   ```

### How It Works

1. **On application startup:**
   - App clones the `data-cache` branch to `/tmp/beril-data-cache` (or configured path)
   - If repo already exists, runs `git pull` to get latest changes
   - Loads data from `data_cache/data.pkl.gz` in the cloned repo

2. **When code is merged to `main`, GitHub Actions:**
   - Parses all repository data (projects, docs, schemas)
   - Creates a compressed pickle file (`data.pkl.gz`) and metadata (`timestamp.json`)
   - Pushes these files to the `data-cache` branch
   - Sends a signed webhook request to your application

3. **The application receives the webhook:**
   - Validates the HMAC-SHA256 signature
   - Runs `git pull` to fetch latest changes from the `data-cache` branch
   - Reloads data from the updated pickle file
   - Updates the "Last updated" timestamp in the footer

**Benefits:**
- ✅ **Instant updates** - No CDN cache lag (unlike raw.githubusercontent.com)
- ✅ **Fast** - Shallow git clone, only ~70KB of data currently
- ✅ **No restarts needed** - Webhook triggers reload in ~1-2 seconds
- ✅ **Free** - Uses GitHub for storage, no external infrastructure

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
- **SQLAlchemy** (async): ORM and database access
- **asyncpg**: Async PostgreSQL driver
- **aiosqlite**: In-memory SQLite driver (used in tests only)
- **Authlib**: ORCiD OAuth2 login
- **nbconvert**: Jupyter notebook rendering
- **Whoosh**: Full-text search
- **Markdown**: Documentation rendering with extensions

To add new dependencies, update `pyproject.toml` and run:

```bash
uv sync
```

### Running tests

Tests use an in-memory SQLite database and do not require a running PostgreSQL instance:

```bash
uv run pytest
```

## Docker Deployment

The Dockerfile is located at the repository root since the UI needs access to the entire repository (projects, docs, data directories).

### Build the Docker Image

From the repository root:

```bash
docker build -t microbial-discovery-forge .
```

### Run the Container

```bash
docker run -p 8000:8000 microbial-discovery-forge
```

The UI will be available at [http://localhost:8000](http://localhost:8000)

### Run with Environment Variables

If you need to pass environment variables (like auth tokens):

```bash
docker run -p 8000:8000 --env-file .env microbial-discovery-forge
```

### Docker Compose

For deployment with docker-compose (from repository root):

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
    depends_on:
      - postgres

  postgres:
    image: postgres:18
    environment:
      POSTGRES_USER: beril_user
      POSTGRES_PASSWORD: changeme
      POSTGRES_DB: beril
    volumes:
      - pgdata:/var/lib/postgresql/18/docker
    restart: unless-stopped
    # Uncomment for local development to allow psql/GUI access from the host.
    # Do not expose in production.
    # ports:
    #   - "5432:5432"

volumes:
  pgdata:
```

In `.env`, set the following:
* `BERIL_DB_USER` must match `POSTGRES_USER`
* `BERIL_DB_PASSWORD` must match `POSTGRES_PASSWORD`
* `BERIL_DB_NAME` must match `POSTGRES_DB`
* `BERIL_DB_HOST=postgres` (the service name) rather than `localhost`. This works for both local and production use.


### Building for SPIN:
You must be logged in to push images to the NERSC registry.
```bash
docker login registry.nersc.gov
``` 
Use your NERSC username and password (no MFA)

```bash
docker build \
  -t registry.nersc.gov/kbase/beril-observatory:develop \
  --platform linux/amd64 \
  --push \
  .
```

### Deploying on SPIN
* Push a new image
* Login to SPIN at https://rancher2.nersc.spin.gov
* Go to Development -> Workflows -> Deployments
* In the `knowledge-engine` namespace, go to `beril-develop`
* Hit the 3 dots menu on the far right, and select redeploy.

### SPIN configuration
We need a few pieces set up for running this on SPIN at NERSC. SPIN uses Rancher 2 for
deployment, so if you know that pipeline, this should be familiar. If not, here's a 
source for some SPIN documentation: https://docs.nersc.gov/services/spin/

