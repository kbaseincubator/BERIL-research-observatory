"""Compendium CLI — ``compendium audit|build|render|quality|all``.

Foundation stub; the ``all`` end-to-end pipeline is wired in Task 10 once modules land.
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="compendium", description="Deterministic KG-centered scientific wiki")
    sub = parser.add_subparsers(dest="cmd")
    for name in ("audit", "build", "render", "quality", "all"):
        sp = sub.add_parser(name)
        sp.add_argument("--projects", nargs="*", default=None)
        sp.add_argument("--projects-dir", default="../projects")
        sp.add_argument("--out", default="out")
    args = parser.parse_args(argv)
    if not args.cmd:
        parser.print_help()
        return 0
    # Dispatch is completed in Task 10 (pipeline wiring).
    try:
        from compendium import pipeline  # noqa: WPS433
    except Exception:  # pragma: no cover - stub before Task 10
        print(f"[compendium] '{args.cmd}' not yet wired; build the pipeline (Task 10).", file=sys.stderr)
        return 2
    return pipeline.dispatch(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
