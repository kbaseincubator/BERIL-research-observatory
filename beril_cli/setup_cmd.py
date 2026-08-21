"""beril setup — interactive onboarding wizard."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from beril_cli import auth_store, config
from beril_cli.auth_cmd import run_login
from beril_cli.detect import detect_user_identity, print_jupyterhub_path_hint
from beril_cli.start import announce_omp_session, claude_defaults, omp_defaults


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


def _dashboard_api(repo_root: Path):
    """Borrow the dashboard's own proxy probe rather than reimplementing it.

    `tools/dashboard.py` is stdlib-only and cannot import from here — it runs under
    a bare `python3` in the pod — so the dependency goes this way round. It also
    means the wizard checks live mode with exactly the function the dashboard gates
    on, so "setup worked" and "the dashboard will start" cannot disagree.
    """
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    try:
        from tools.dashboard import RESTART_STEPS, jupyter_python, proxy_enabled
    except Exception:
        return None, None, ()
    return proxy_enabled, jupyter_python, RESTART_STEPS


def _install_server_proxy(repo_root: Path, assume_yes: bool = False) -> int:
    """Install and enable jupyter-server-proxy for this user, then say what next.

    Targets ``--user`` (``~/.local``) deliberately. On this image ``/opt/conda``
    is an *overlay* mount — writable, and reverted on every pod restart — while
    ``$HOME`` is a persistent volume. So ``--user`` is both the only target that
    survives and the only one a non-admin should be writing to. It also means
    this is a once-per-*user* cost, not once per pod.

    Never run implicitly. It mutates the user's environment and its last step
    restarts their server, so it only ever happens because someone typed it.
    """
    proxy_enabled, jupyter_python, restart_steps = _dashboard_api(repo_root)
    if proxy_enabled is None:
        print("  Could not read tools/dashboard.py in this checkout — skipping.")
        return 1

    if proxy_enabled():
        print("jupyter-server-proxy is already enabled — nothing to do.")
        print("If live mode still is not working, restart your server:")
        for step in restart_steps:
            print(f"  - {step}")
        return 0

    python = jupyter_python()
    if python is None:
        print(
            "Could not find the interpreter your Jupyter server runs on: no "
            "`jupyter` on PATH.\nRun this from a terminal inside JupyterHub, where "
            "it resolves to the server's own environment.",
            file=sys.stderr,
        )
        return 1

    steps = [
        [python, "-m", "pip", "install", "--user", "jupyter-server-proxy"],
        # Usually redundant: the pip install drops its own enable file into
        # <userbase>/etc/jupyter/jupyter_server_config.d/. Kept because it is
        # cheap and it covers the case where that drop-in did not land.
        [shutil.which("jupyter") or "jupyter", "server", "extension", "enable",
         "--user", "jupyter_server_proxy"],
    ]

    print("This will run, as your user:\n")
    for step in steps:
        print(f"  {' '.join(step)}")
    print("\nThen you will need to:\n")
    for item in restart_steps:
        print(f"  - {item}")

    if not assume_yes:
        if not sys.stdin.isatty():
            print("\nNot a terminal — re-run with --yes to proceed non-interactively.")
            return 1
        if input("\n  Proceed? [y/N] ").strip().lower() not in ("y", "yes"):
            print("  Skipped — the dashboard stays a snapshot. Re-run `beril setup`")
            print("  any time to turn it on.")
            return 1

    for step in steps:
        print(f"\n$ {' '.join(step)}")
        try:
            result = subprocess.run(step, check=False)
        except OSError as exc:
            print(f"could not run {step[0]}: {exc}", file=sys.stderr)
            return 1
        if result.returncode != 0:
            print(f"\nFailed: {' '.join(step)}", file=sys.stderr)
            return result.returncode

    # Verified through the same probe the dashboard gates on, so "setup worked"
    # and "the dashboard will start" cannot disagree.
    if not proxy_enabled():
        print(
            "\nInstalled, but the extension still does not read as enabled.\n"
            "Report this with the output above — it is not a case we have seen.",
            file=sys.stderr,
        )
        return 1

    print("\n" + "=" * 64)
    print("Installed and enabled. Two steps left, and this is the only time:")
    for item in restart_steps:
        print(f"  - {item}")
    print("=" * 64)
    return 0




def _run_login_step() -> None:
    """Log in to BERIL (which also links OpenViking) as part of setup.

    Best-effort, mirroring how ``beril login`` treats its own OpenViking
    linking: setup must complete even if login is skipped or fails, so a bad
    token, an unreachable server, or a non-interactive shell only warns. The
    user can always run ``beril login`` later.

    Skips entirely when a valid login already exists — re-running setup should
    not force a re-auth of someone who is already logged in.
    """
    base_url = config.get_base_url()

    record = auth_store.load()
    if record is not None:
        name = record.display_name or record.orcid_id
        print(f"  Already logged in as {name} on {record.base_url}.")
        print("  Run `beril login` any time to re-authenticate or switch servers.")
        return

    print(f"  Log in to BERIL ({base_url}) — this also links OpenViking so the")
    print("  knowledge-context tools work without extra setup.")

    # run_login() with no token prompts via getpass, which needs a real
    # terminal. Off a TTY (CI, piped input) that would hang, so point the user
    # at the manual command and move on.
    if not sys.stdin.isatty():
        print("  Not a terminal — run `beril login` yourself once setup finishes.")
        return

    if not _confirm("  Log in now?"):
        print("  Skipped — run `beril login` later to enable OpenViking.")
        return

    # run_login handles its own prompting, validation, and OV linking, and
    # prints its own success/failure lines. A non-zero return is not fatal to
    # setup — just note it and continue.
    try:
        rc = run_login()
    except (EOFError, KeyboardInterrupt):
        print("\n  Login cancelled — run `beril login` later.")
        return
    if rc != 0:
        print("  Login did not complete — run `beril login` later to finish.")


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
    # S3_* are the names a current BERDL pod injects; MINIO_* are their historical
    # spelling and are absent on current images. Both are listed so onboarding works
    # on either, and so a pod that still has the old names is not silently skipped.
    _ENV_KEYS = [
        "KBASE_AUTH_TOKEN",
        "S3_ACCESS_KEY",
        "S3_SECRET_KEY",
        "S3_ENDPOINT_URL",
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
        print(
            "  To get a KBASE_AUTH_TOKEN: sign in at https://hub.berdl.kbase.us, spawn a\n"
            "  server, and in a notebook run:\n"
            "      import os\n"
            "      print(os.environ.get('KBASE_AUTH_TOKEN'))\n"
            "  Delete the cell output immediately after copying the token. Saved outputs\n"
            "  live in the notebook file and can be shared or committed by accident.\n"
            "  The token lasts 14 days. Signing out of KBase revokes it immediately rather\n"
            "  than at its stated expiry, so do not sign out while a run is in flight.\n"
            "  Note: narrative.kbase.us shows a 'Developer Tokens' tab only to accounts\n"
            "  holding the DevToken role, and BERDL uses Login tokens, so that page is not\n"
            "  the route here."
        )
        token = _prompt("  Enter your KBASE_AUTH_TOKEN (leave blank to configure later)")
        if token:
            _update_env_var(env_path, "KBASE_AUTH_TOKEN", token)
            print("  Token saved to .env")
        else:
            print("  WARNING: No KBASE_AUTH_TOKEN configured. BERDL commands will fail.")
            print("  Add it to .env later: KBASE_AUTH_TOKEN=your-token-here")
    else:
        print("  KBASE_AUTH_TOKEN is set.")

    # ── Step 3: BERIL login (+ OpenViking) ──────────
    _step(3, "BERIL login")
    _run_login_step()

    # ── Step 4: BERDL environment ───────────────────
    _step(4, "BERDL environment")

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

    # ── Step 5: Virtual environment ─────────────────
    # .venv-berdl is only needed off-cluster (for spark_connect_remote, pproxy, etc.)
    # On-cluster (JupyterHub), Spark is directly available.
    if on_cluster:
        _step(5, "BERDL client environment")
        print("  On-cluster — .venv-berdl not needed (Spark is directly available).")
    else:
        _step(5, "BERDL client environment")

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

    # ── Step 6: GitHub CLI ──────────────────────────
    _step(6, "GitHub CLI")

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

    # ── Step 7: Profile (optional) ──────────────────
    _step(7, "Profile (optional — press Enter to skip)")

    existing_cfg = config.load()
    user_cfg = existing_cfg.get("user", {})

    detected = detect_user_identity()
    auto_filled = [k for k in ("name", "affiliation", "orcid") if detected.get(k) and not user_cfg.get(k)]
    if auto_filled:
        print(
            "  Auto-detected from JupyterHub / ORCID — press Enter to accept or type to override."
        )

    name = _prompt("  Your name", user_cfg.get("name") or detected.get("name", ""))
    affiliation = _prompt("  Affiliation", user_cfg.get("affiliation") or detected.get("affiliation", ""))
    orcid = _prompt("  ORCID", user_cfg.get("orcid") or detected.get("orcid", ""))

    user_cfg = {}
    if name:
        user_cfg["name"] = name
    if affiliation:
        user_cfg["affiliation"] = affiliation
    if orcid:
        user_cfg["orcid"] = orcid

    # ── Step 8: Agent selection ─────────────────────
    _step(8, "Coding agent")

    agents_found: list[str] = []
    for agent in config.SUPPORTED_AGENTS:
        if shutil.which(agent):
            agents_found.append(agent)

    if agents_found:
        print(f"  Detected: {', '.join(agents_found)}")
    else:
        print(f"  No agents detected ({', '.join(config.SUPPORTED_AGENTS)}).")
        print("  Install one and re-run setup, or use beril start --agent <name>.")

    default_agent = existing_cfg.get("defaults", {}).get("agent", "")
    if not default_agent and agents_found:
        default_agent = agents_found[0]

    if agents_found:
        chosen = _prompt("  Default agent", default_agent)
        if chosen not in agents_found:
            print(f"  Warning: '{chosen}' was not detected on PATH.")
    else:
        chosen = default_agent or config.DEFAULT_AGENT

    # ── Step 9: BERIL Anthropic key (Google Vertex) ──
    vertex_cfg: dict = {}
    _VERTEX_CREDENTIALS = Path("/global_share/BERIL-setup/20260507_hackathon.json")
    _VERTEX_PROJECT_ID = "beril-hackathon-2026"
    _VERTEX_REGION = "global"

    if chosen == "claude" and _VERTEX_CREDENTIALS.exists():
        _step(9, "BERIL Anthropic key (Google Vertex)")
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
        _step(9, "BERIL Anthropic key (Google Vertex)")
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

    # ── Step 10: Live dashboard ─────────────────────
    _step(10, "Live dashboard (optional)")

    print("  While a project runs, the status line links to a dashboard page.")
    print("  Without jupyter-server-proxy that page is a snapshot: it renders")
    print("  fully but does not update itself. Installing it is once per user —")
    print("  $HOME persists, so it survives every later pod restart.")
    _install_server_proxy(repo_root)

    # ── Step 11: Launch ─────────────────────────────
    _step(11, "Launch")

    if agents_found and _confirm(f"  Launch {chosen} now?"):
        print(f"\n  Starting {chosen} with /berdl_start...\n")
        print_jupyterhub_path_hint(repo_root)
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
            # The same session directory `beril start` gives omp, so a session begun
            # from the wizard is as collectable as one begun later (start.py::omp_defaults).
            session_flags = omp_defaults(chosen, [], repo_root)
            announce_omp_session(session_flags)
            flags = claude_defaults(chosen, [])
            os.execvp(binary, [chosen, *flags, *session_flags, "/berdl_start"])
        else:
            print(f"  Error: '{chosen}' not found on PATH.", file=sys.stderr)
            return 1

    print("\n  Setup complete! Run 'beril start' when you're ready.\n")
    print_jupyterhub_path_hint(repo_root)
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
