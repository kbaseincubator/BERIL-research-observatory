"""BERIL CLI — launcher and environment manager for the BERIL Research Observatory."""

import argparse
import sys

from beril_cli import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="beril",
        description="BERIL Research Observatory — setup, check, and launch your research environment.",
    )
    parser.add_argument("--version", action="version", version=f"beril {__version__}")

    sub = parser.add_subparsers(dest="command")

    # doctor
    sub.add_parser("doctor", help="Check environment health")

    # setup
    sub.add_parser("setup", help="Interactive onboarding wizard")

    # start
    start_parser = sub.add_parser("start", help="Launch a coding agent")
    start_parser.add_argument(
        "--agent",
        choices=["claude", "codex", "gemini"],
        default=None,
        help="Agent to launch (default: from config, or claude)",
    )
    start_parser.add_argument(
        "--skip-onboard",
        action="store_true",
        default=False,
        help="Skip the automatic /berdl_start onboarding prompt",
    )
    start_parser.add_argument(
        "--version",
        default=None,
        metavar="VERSION",
        help="Pin to a specific release tag (e.g. v0.3.4.5). Defaults to the latest tag.",
    )

    # user
    user_parser = sub.add_parser(
        "user",
        help="Show user identity from ~/.config/beril/config.toml",
    )
    user_parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Emit machine-readable JSON",
    )

    # state — the non-authoritative research world-model (research_state.json)
    state_parser = sub.add_parser(
        "state",
        help="Read/update the research world-model (orientation only, never gates)",
    )
    state_sub = state_parser.add_subparsers(dest="action")
    state_get = state_sub.add_parser("get", help="Print projects/<id>/research_state.json (or {})")
    state_get.add_argument("project", help="Project id")
    state_set = state_sub.add_parser("set", help="Merge orientation into research_state.json")
    state_set.add_argument("project", help="Project id")
    state_set.add_argument(
        "--json",
        dest="json",
        required=True,
        metavar="OBJ",
        help="JSON object of fields to overlay (supplied replaces, absent preserved)",
    )

    # whereami — deterministic "where am I / what's next" surface
    whereami_parser = sub.add_parser(
        "whereami",
        help="Show where a project is and the recommended next move",
    )
    whereami_parser.add_argument(
        "project",
        nargs="?",
        default=None,
        help="Project id (default: most-recently-touched non-complete project)",
    )
    whereami_parser.add_argument(
        "--reinject",
        action="store_true",
        default=False,
        help="Emit the guard-wrapped orientation block (for the SessionStart hook)",
    )
    whereami_parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Emit machine-readable JSON",
    )

    args, remaining = parser.parse_known_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "doctor":
        from beril_cli.doctor import run_doctor

        return run_doctor()

    if args.command == "setup":
        from beril_cli.setup_cmd import run_setup

        return run_setup()

    if args.command == "start":
        from beril_cli.start import run_start

        return run_start(
            agent=args.agent,
            extra_args=remaining,
            skip_onboard=args.skip_onboard,
            version=args.version,
        )

    if args.command == "user":
        from beril_cli.user_cmd import run_user

        return run_user(args)

    if args.command == "state":
        from beril_cli.state_cmd import run_state

        return run_state(args)

    if args.command == "whereami":
        from beril_cli.state_cmd import run_whereami

        return run_whereami(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
