"""Application configuration."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Paths
    app_dir: Path = Path(__file__).parent
    ui_dir: Path = app_dir.parent
    repo_dir: Path = ui_dir.parent  # The research repository root

    # Derived paths
    @property
    def projects_dir(self) -> Path:
        return self.repo_dir / "projects"

    @property
    def docs_dir(self) -> Path:
        return self.repo_dir / "docs"

    @property
    def data_dir(self) -> Path:
        return self.repo_dir / "data"

    @property
    def templates_dir(self) -> Path:
        return self.app_dir / "templates"

    @property
    def static_dir(self) -> Path:
        return self.app_dir / "static"

    @property
    def cache_dir(self) -> Path:
        return self.ui_dir / "data"

    @property
    def cache_file(self) -> Path:
        return self.cache_dir / "cache.json"

    @property
    def search_index_dir(self) -> Path:
        return self.cache_dir / "indexdir"

    # App settings
    app_name: str = "KBase / BERIL Research Observatory"
    app_description: str = "AI-powered exploration of the KBase Data Lakehouse"
    debug: bool = False

    # Database stats (for hero display)
    total_genomes: int = 293_059
    total_species: int = 27_000
    total_genes: str = "1B+"

    class Config:
        env_prefix = "PRO_"  # BERIL Research Observatory


settings = Settings()
