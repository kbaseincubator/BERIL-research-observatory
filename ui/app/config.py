"""Application configuration."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_settings = None


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Test-only settings. These should be left False unless running tests.
    test_skip_lifespan: bool = False

    # Image info. Only used for health endpoint when present
    git_commit: str | None = None
    build_date: str | None = None

    # Paths
    app_dir: Path = Path(__file__).parent
    ui_dir: Path = app_dir.parent
    repo_dir: Path = ui_dir.parent  # The research repository root

    # Lakehouse source — picks which LakehouseSource implementation is active
    # at startup and on the webhook. "git" reproduces the legacy git-clone flow
    # (see Git data source configuration below). Future values: "berdl".
    lakehouse_source: str = "git"

    # Where lakehouse sources materialize their project tree on disk. Defaults
    # match the legacy data_repo_path so existing deployments keep working
    # without setting anything new. Mount a persistent volume here in production
    # so a restart doesn't require re-downloading.
    lakehouse_cache_dir: Path = Path("/tmp/beril_lakehouse_cache")

    # Git data source configuration (consumed by GitLegacyLakehouse).
    data_repo_url: str | None = None  # Git repository URL
    data_repo_branch: str = "data-cache"  # Branch to checkout
    data_repo_path: Path = Path("/tmp/beril_data_cache")  # Local clone path
    force_local_data: bool = False

    # BERDL MinIO lakehouse source configuration (consumed by BERDLLakehouse).
    # The service-account access/secret keys are read from env (BERIL_BERDL_MINIO_*)
    # in prod via a Kubernetes secret; locally they live in .env. Both are
    # required when lakehouse_source="berdl"; sync() raises on startup otherwise.
    # See PR-2 (BERDLLakehouse) for the contract.
    berdl_minio_endpoint: str = "https://minio.berdl.kbase.us"
    berdl_minio_access_key: str | None = None
    berdl_minio_secret_key: str | None = None
    berdl_minio_bucket: str = "cdm-lake"
    # The submit skill writes here; this is the path the lakehouse source reads.
    # Trailing slash matters for the S3 list_objects_v2 prefix to scope correctly.
    berdl_projects_prefix: str = "tenant-general-warehouse/microbialdiscoveryforge/projects/"
    # Optional HTTPS proxy for off-cluster dev (e.g. http://host.docker.internal:8123).
    # In prod (beril.kbase.us), leave unset so direct connectivity is used.
    berdl_https_proxy: str | None = None
    # S3 addressing style. "path" (endpoint/bucket/key) is what MinIO and Ceph
    # RadosGW both expect; "virtual" (bucket.endpoint/key) is AWS-S3's default
    # and what boto3 sometimes guesses from the endpoint URL. Pin to "path" so
    # the same client code works against either backend without surprises.
    berdl_s3_addressing_style: str = "path"

    plotly_cdn_url: str = "https://cdn.plot.ly/plotly-3.4.0.min.js"

    # Webhook configuration
    webhook_secret: str | None = None

    # ORCiD OAuth2 configuration
    orcid_client_id: str | None = None
    orcid_client_secret: str | None = None
    orcid_redirect_root: str = "http://localhost:8000"  # expected not to end with a slash
    orcid_redirect_path: str = "/auth/orcid/callback"  # expects to be prepended with slash
    orcid_base_url: str = "https://orcid.org"  # Use https://sandbox.orcid.org for development

    # Auth token providers — comma-separated names of TokenProvider plugins to
    # enable in addition to ORCiD identity. Currently only "kbase" is supported.
    # Empty by default, so dev deployments get ORCiD-only behavior.
    auth_token_providers: str = ""

    # Name of the cookie KBase auth writes to the shared *.kbase.us domain.
    # Read on every request by KBaseTokenProvider when the provider is enabled.
    kbase_auth_cookie: str = "kbase_session_backup"
    kbase_auth_url: str = "https://ci.kbase.us/services/auth"
    kbase_auth_mfa: bool = True

    # Session configuration
    session_secret_key: str = "change-me-in-production"  # Signs session cookies

    # database info
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "beril_user"
    db_password: str | None = None
    db_name: str = "beril"

    # User project file storage (filesystem)
    user_projects_root: Path = ui_dir / "user_projects"

    # Chat configuration
    chat_config_path: Path = ui_dir / "config" / "chat_providers.yaml"
    chat_max_concurrent_turns_per_user: int = 3

    # Derived paths
    @property
    def db_url(self) -> str:
        if self.db_password is None:
            raise ValueError("BERIL_DB_PASSWORD is not set — cannot construct database URL")
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def orcid_redirect_uri(self) -> str:
        return self.orcid_redirect_root + self.orcid_redirect_path

    @property
    def auth_token_providers_list(self) -> list[str]:
        return [p.strip() for p in self.auth_token_providers.split(",") if p.strip()]

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
    app_name: str = "Microbial Discovery Forge"
    app_description: str = (
        "AI co-scientist and research observatory for BERDL-scale microbial discovery"
    )
    debug: bool = False

    # Database stats (for hero display)
    total_genomes: int = 293_059
    total_species: int = 27_000
    total_genes: str = "1B+"

    model_config = SettingsConfigDict(
        env_prefix="BERIL_",  # BERIL Research Observatory
        # Resolve .env relative to the repo root (two levels up from this file)
        env_file=str(Path(__file__).parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        # pydantic-settings 2.x defaults to "forbid"; the repo's .env contains
        # non-BERIL_ vars (KBASE_AUTH_TOKEN, JLAB_API_TOKEN, etc.) that are not
        # part of the app settings and must be ignored.
        extra="ignore",
    )


def get_settings():
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
