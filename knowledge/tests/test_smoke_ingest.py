import os
from pathlib import Path

from observatory_context.smoke import latest_project_dirs


def test_latest_project_dirs_returns_five_most_recent(tmp_path: Path) -> None:
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()

    for index, name in enumerate(("alpha", "beta", "gamma", "delta", "epsilon", "zeta")):
        project_dir = projects_dir / name
        project_dir.mkdir()
        timestamp = 1_700_000_000 + index
        os.utime(project_dir, (timestamp, timestamp))

    assert [path.name for path in latest_project_dirs(projects_dir, 5)] == [
        "zeta",
        "epsilon",
        "delta",
        "gamma",
        "beta",
    ]
