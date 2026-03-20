"""Check whether the configured OpenViking server is reachable."""

from __future__ import annotations

import argparse

from observatory_context import runtime


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(description="Check whether the configured OpenViking server is reachable.")


def main(argv: list[str] | None = None) -> int:
    build_parser().parse_args(argv)
    client = runtime.build_client()
    if not client.health():
        print("FAIL: OpenViking server is not reachable.")
        return 1
    status = client.get_status()
    print("PASS: OpenViking server is reachable.")
    print(status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
