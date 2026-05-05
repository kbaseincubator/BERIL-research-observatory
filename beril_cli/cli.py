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

        return run_start(agent=args.agent, extra_args=remaining, skip_onboard=args.skip_onboard)

    return 0


if __name__ == "__main__":
    sys.exit(main())
