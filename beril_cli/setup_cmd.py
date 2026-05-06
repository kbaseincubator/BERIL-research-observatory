"""beril setup — interactive onboarding wizard."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from beril_cli import config


def _find_repo_root() -> Path | None:
    """Walk up from cwd looking for PROJECT.md."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "PROJECT.md").exists():
            return parent
    return None


def _prompt(question: str, default: str = "") -> str:
    """Prompt user for input with optional default."""
    suffix = f" [{default}]" if default else ""
    answer = input(f"{question}{suffix}: ").strip()
    return answer or default


def _confirm(question: str, default: bool = True) -> bool:
    """Yes/no prompt."""
    hint = "Y/n" if default else "y/N"
    answer = input(f"{question} [{hint}]: ").strip().lower()
    if not answer:
        return default
    return answer in ("y", "yes")


def _step(number: int, label: str) -> None:
    """Print a numbered step header."""
    print(f"\n{'─' * 50}")
    print(f"  Step {number}: {label}")
    print(f"{'─' * 50}")


def run_setup() -> int:
    """Run the interactive setup wizard."""
    print()
    print("BERIL Research Observatory — Setup")
    print("=" * 50)

    # ── Step 1: Repo detection ──────────────────────
    _step(1, "Repository")

    repo_root = _find_repo_root()
    if not repo_root:
        print("  BERIL repository not found in current directory tree.")
        clone_url = "https://github.com/kbaseincubator/BERIL-research-observatory.git"
        if _confirm(f"  Clone it into {Path.cwd() / 'BERIL-research-observatory'}?"):
            print(f"  Cloning {clone_url} ...")
            result = subprocess.run(
                ["git", "clone", clone_url],
                check=False,
            )
            if result.returncode != 0:
                print("  ERROR: git clone failed. Check your network and try again.")
                return 1
            repo_root = Path.cwd() / "BERIL-research-observatory"
            os.chdir(repo_root)
            print(f"  Cloned to: {repo_root}")
        else:
            print("  To set up manually:")
            print(f"    git clone {clone_url}")
            print("    cd BERIL-research-observatory")
            print("    beril setup")
            return 1

    print(f"  Found repo at: {repo_root}")

    # ── Step 2: .env creation + credential sync ─────
    _step(2, "Environment file (.env)")

    env_path = repo_root / ".env"
    env_example = repo_root / ".env.example"

    # Ensure .env exists
    if not env_path.exists():
        if env_example.exists():
            print("  Creating .env from .env.example...")
            shutil.copy2(env_example, env_path)
        else:
            print("  Creating minimal .env...")
            env_path.write_text("")

    # Sync credentials from environment → .env
    # On JupyterHub these are the freshest source and should always overwrite .env
    _ENV_KEYS = [
        "KBASE_AUTH_TOKEN",
        "MINIO_ACCESS_KEY",
        "MINIO_SECRET_KEY",
        "MINIO_ENDPOINT_URL",
    ]
    synced = []
    for key in _ENV_KEYS:
        live_val = os.environ.get(key, "")
        if live_val:
            _update_env_var(env_path, key, live_val)
            synced.append(key)

    if synced:
        print(f"  Synced from environment: {', '.join(synced)}")

    # Check if KBASE_AUTH_TOKEN ended up set
    env_vars = _parse_env_file(env_path)
    file_token = env_vars.get("KBASE_AUTH_TOKEN", "")
    if not file_token or file_token == "YOUR_AUTH_TOKEN_HERE":
        token = _prompt(
            "  Enter your KBASE_AUTH_TOKEN (from https://narrative.kbase.us/#auth2/account)"
        )
        if token:
            _update_env_var(env_path, "KBASE_AUTH_TOKEN", token)
            print("  Token saved to .env")
        else:
            print("  WARNING: No KBASE_AUTH_TOKEN configured. BERDL commands will fail.")
            print("  Add it to .env later: KBASE_AUTH_TOKEN=your-token-here")
    else:
        print("  KBASE_AUTH_TOKEN is set.")

    # ── Step 3: BERDL environment ───────────────────
    _step(3, "BERDL environment")

    on_cluster = False
    detect_script = repo_root / "scripts" / "detect_berdl_environment.py"
    if detect_script.exists():
        result = subprocess.run(
            [sys.executable, str(detect_script)],
            capture_output=True, text=True, timeout=15, check=False,
        )
        print(result.stdout)
        if result.returncode != 0:
            print("  Some checks failed — see above for next steps.")
        # Parse location for downstream decisions
        try:
            import json
            env_info = json.loads(result.stdout)
            on_cluster = env_info.get("location") == "on-cluster"
        except (json.JSONDecodeError, ValueError):
            pass
    else:
        print("  Detection script not found, skipping.")

    # ── Step 4: Virtual environment ─────────────────
    # .venv-berdl is only needed off-cluster (for spark_connect_remote, pproxy, etc.)
    # On-cluster (JupyterHub), Spark is directly available.
    if on_cluster:
        _step(4, "BERDL client environment")
        print("  On-cluster — .venv-berdl not needed (Spark is directly available).")
    else:
        _step(4, "BERDL client environment")

        venv_path = repo_root / ".venv-berdl"
        bootstrap_script = repo_root / "scripts" / "bootstrap_client.sh"

        if venv_path.exists():
            print("  .venv-berdl already exists.")
        elif bootstrap_script.exists():
            if _confirm("  .venv-berdl not found. Bootstrap it now?"):
                print("  Running bootstrap_client.sh...")
                result = subprocess.run(
                    ["bash", str(bootstrap_script)],
                    cwd=str(repo_root), check=False,
                )
                if result.returncode != 0:
                    print(f"  ERROR: bootstrap_client.sh failed (exit {result.returncode}).")
                    print("  Fix the issue above and retry: bash scripts/bootstrap_client.sh")
                    return 1
            else:
                print("  Skipped — run later: bash scripts/bootstrap_client.sh")
        else:
            print("  Bootstrap script not found, skipping.")

    # ── Step 5: GitHub CLI ──────────────────────────
    _step(5, "GitHub CLI")

    rc = subprocess.run(
        ["gh", "auth", "status"],
        capture_output=True, text=True, check=False,
    ).returncode if shutil.which("gh") else -1

    if rc == 0:
        print("  gh is authenticated.")
    elif shutil.which("gh"):
        print("  gh is installed but not authenticated.")
        print("  Run: gh auth login")
    else:
        print("  gh is not installed.")
        print("  Install: https://cli.github.com/")

    # ── Step 6: Profile (optional) ──────────────────
    _step(6, "Profile (optional — press Enter to skip)")

    existing_cfg = config.load()
    user_cfg = existing_cfg.get("user", {})

    name = _prompt("  Your name", user_cfg.get("name", ""))
    affiliation = _prompt("  Affiliation", user_cfg.get("affiliation", ""))
    orcid = _prompt("  ORCID", user_cfg.get("orcid", ""))

    user_cfg = {}
    if name:
        user_cfg["name"] = name
    if affiliation:
        user_cfg["affiliation"] = affiliation
    if orcid:
        user_cfg["orcid"] = orcid

    # ── Step 7: Agent selection ─────────────────────
    _step(7, "Coding agent")

    agents_found: list[str] = []
    for agent in ("claude", "codex", "gemini"):
        if shutil.which(agent):
            agents_found.append(agent)

    if agents_found:
        print(f"  Detected: {', '.join(agents_found)}")
    else:
        print("  No agents detected (claude, codex, gemini).")
        print("  Install one and re-run setup, or use beril start --agent <name>.")

    default_agent = existing_cfg.get("defaults", {}).get("agent", "")
    if not default_agent and agents_found:
        default_agent = agents_found[0]

    if agents_found:
        chosen = _prompt("  Default agent", default_agent)
        if chosen not in agents_found:
            print(f"  Warning: '{chosen}' was not detected on PATH.")
    else:
        chosen = default_agent or "claude"

    # ── Step 8: BERIL Anthropic key (Google Vertex) ──
    vertex_cfg: dict = {}
    _VERTEX_CREDENTIALS = Path("/global_share/BERIL-setup/20260507_hackathon.json")
    _VERTEX_PROJECT_ID = "beril-hackathon-2026"
    _VERTEX_REGION = "global"

    if chosen == "claude" and _VERTEX_CREDENTIALS.exists():
        _step(8, "BERIL Anthropic key (Google Vertex)")
        print("  A shared BERIL Anthropic API key is available via Google Vertex.")
        print("  This lets you use Claude without a personal API key or subscription.")
        if _confirm("  Use the BERIL Anthropic key?"):
            vertex_cfg = {
                "enabled": True,
                "project_id": _VERTEX_PROJECT_ID,
                "region": _VERTEX_REGION,
                "credentials_file": str(_VERTEX_CREDENTIALS),
            }
            print("  Vertex enabled — Claude will use the shared BERIL key.")
        else:
            print("  Skipped — Claude will use your personal API key / subscription.")
    elif chosen == "claude":
        _step(8, "BERIL Anthropic key (Google Vertex)")
        print("  Shared Vertex credentials not found at expected location.")
        print("  Claude will use your personal API key / subscription.")

    # ── Save config ─────────────────────────────────
    cfg: dict = {}
    if user_cfg:
        cfg["user"] = user_cfg
    cfg["defaults"] = {"agent": chosen}
    if vertex_cfg:
        cfg["vertex"] = vertex_cfg
    config.save(cfg)
    print(f"\n  Config saved to {config.CONFIG_PATH}")

    # ── Step 9: Launch ──────────────────────────────
    _step(9, "Launch")

    if agents_found and _confirm(f"  Launch {chosen} now?"):
        print(f"\n  Starting {chosen} with /berdl_start...\n")
        binary = shutil.which(chosen)
        if binary:
            os.chdir(repo_root)
            # Inject Vertex env vars if enabled
            if chosen == "claude" and vertex_cfg.get("enabled"):
                os.environ["CLAUDE_CODE_USE_VERTEX"] = "1"
                os.environ["CLOUD_ML_REGION"] = vertex_cfg.get("region", "global")
                os.environ["ANTHROPIC_VERTEX_PROJECT_ID"] = vertex_cfg.get("project_id", "")
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = vertex_cfg.get("credentials_file", "")
                os.environ["VERTEX_REGION_CLAUDE_HAIKU_4_5"] = "us-east5"
                os.environ["ANTHROPIC_DEFAULT_HAIKU_MODEL"] = "claude-haiku-4-5@20251001"
            os.execvp(binary, [chosen, "--model", "opus", "/berdl_start"])
        else:
            print(f"  Error: '{chosen}' not found on PATH.", file=sys.stderr)
            return 1

    print("\n  Setup complete! Run 'beril start' when you're ready.\n")
    return 0


def _parse_env_file(env_path: Path) -> dict[str, str]:
    """Minimal .env parser."""
    env_vars: dict[str, str] = {}
    if not env_path.exists():
        return env_vars
    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env_vars[key.strip()] = value.strip().strip("'").strip('"')
    return env_vars


def _update_env_var(env_path: Path, key: str, value: str) -> None:
    """Update or insert a key=value pair in a .env file."""
    lines = env_path.read_text().splitlines()
    updated = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            updated = True
            break
    if not updated:
        lines.append(f"{key}={value}")
    env_path.write_text("\n".join(lines) + "\n")
