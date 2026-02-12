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
- **Search**: Full-text search across projects and documentation

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
docker build -t registry.nersc.gov/kbase/beril-observatory:latest-amd64 --platform linux/amd64 --push
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
