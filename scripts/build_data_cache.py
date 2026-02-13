#!/usr/bin/env python
"""Build data cache script for GitHub Actions.

This script:
1. Parses all repository data using the RepositoryParser
2. Saves the RepositoryData object to a gzipped pickle file
3. Creates a timestamp.json file with metadata
"""

import gzip
import json
import pickle
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_git_commit_hash() -> str:
    """Get the current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error getting git commit hash: {e}", file=sys.stderr)
        return "unknown"


def main():
    """Main execution function."""
    # Add the ui directory to the path so we can import the app modules
    script_dir = Path(__file__).parent
    repo_dir = script_dir.parent
    ui_dir = repo_dir / "ui"
    sys.path.insert(0, str(ui_dir))

    # Import after path is set
    from app.dataloader import get_parser, REPOSITORY_DATA_FILE

    print("Starting data cache build...")
    print(f"Repository directory: {repo_dir}")

    # Parse all data
    print("Parsing repository data...")
    parser = get_parser()
    repository_data = parser.parse_all()

    # Create output directory if it doesn't exist
    output_dir = repo_dir / "data_cache"
    output_dir.mkdir(exist_ok=True)

    # Save pickle file
    pickle_path = output_dir / REPOSITORY_DATA_FILE
    print(f"Writing pickle file to {pickle_path}...")
    with gzip.open(pickle_path, "wb") as f:
        pickle.dump(repository_data, f)

    print(f"Pickle file written: {pickle_path.stat().st_size:,} bytes")

    # Get git commit hash
    commit_hash = get_git_commit_hash()

    # Create timestamp metadata
    timestamp_data = {
        "timestamp": repository_data.last_updated.isoformat() if repository_data.last_updated else datetime.now().isoformat(),
        "commit": commit_hash,
    }

    # Save timestamp file
    timestamp_path = output_dir / "timestamp.json"
    print(f"Writing timestamp file to {timestamp_path}...")
    with open(timestamp_path, "w") as f:
        json.dump(timestamp_data, f, indent=2)

    print(f"Timestamp file written with commit: {commit_hash}")
    print("\nData cache build complete!")
    print(f"  - Projects: {len(repository_data.projects)}")
    print(f"  - Discoveries: {len(repository_data.discoveries)}")
    print(f"  - Research Ideas: {len(repository_data.research_ideas)}")
    print(f"  - Collections: {len(repository_data.collections)}")
    print(f"  - Notebooks: {repository_data.total_notebooks}")
    print(f"  - Visualizations: {repository_data.total_visualizations}")
    print(f"  - Data Files: {repository_data.total_data_files}")


if __name__ == "__main__":
    main()
