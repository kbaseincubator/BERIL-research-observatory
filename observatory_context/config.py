from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_OPENVIKING_URL = "http://127.0.0.1:1933"
PROJECTS_TARGET_URI = "viking://resources/projects/"
DOCS_TARGET_URI = "viking://resources/docs/"


@dataclass(frozen=True)
class ContextConfig:
    repo_root: Path
    openviking_url: str = DEFAULT_OPENVIKING_URL
    openviking_api_key: str | None = None

    @classmethod
    def from_env(cls, repo_root: Path | None = None) -> "ContextConfig":
        root = repo_root or Path(__file__).resolve().parents[1]
        return cls(
            repo_root=root,
            openviking_url=os.getenv("OPENVIKING_URL", DEFAULT_OPENVIKING_URL),
            openviking_api_key=os.getenv("OPENVIKING_API_KEY"),
        )

    def __post_init__(self) -> None:
        object.__setattr__(self, "repo_root", Path(self.repo_root))

    @property
    def projects_dir(self) -> Path:
        return self.repo_root / "projects"

    @property
    def docs_dir(self) -> Path:
        return self.repo_root / "docs"

    @property
    def staging_dir(self) -> Path:
        return self.repo_root / "knowledge" / "staging"

    @property
    def state_dir(self) -> Path:
        return self.repo_root / "knowledge" / "state"
