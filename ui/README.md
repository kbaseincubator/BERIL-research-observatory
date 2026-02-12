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
