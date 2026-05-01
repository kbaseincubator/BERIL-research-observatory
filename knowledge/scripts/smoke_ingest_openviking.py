from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from observatory_context.config import ContextConfig
from observatory_context.openviking_client import create_client
from observatory_context.query import format_find_text


DEFAULT_TARGET_URI = "viking://resources/smoke/openviking_context/"
SMOKE_FILENAME = "OPENVIKING_SMOKE.md"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a tiny OpenViking ingestion smoke test")
    parser.add_argument("--target-uri", default=DEFAULT_TARGET_URI)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--keep", action="store_true", help="Keep the smoke target after the test")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = ContextConfig.from_env()
    smoke_dir = config.staging_dir / "smoke"
    smoke_dir.mkdir(parents=True, exist_ok=True)
    smoke_path = smoke_dir / SMOKE_FILENAME
    smoke_path.write_text(
        "\n".join(
            [
                "# BERIL OpenViking smoke test",
                "",
                "This temporary document verifies local OpenViking ingestion.",
                "Unique marker: beril-openviking-smoke-context-layer.",
            ]
        ),
        encoding="utf-8",
    )

    client = create_client(config)
    try:
        client.add_resource(
            path=str(smoke_path),
            to=args.target_uri,
            reason="BERIL OpenViking smoke test",
            wait=False,
        )
        client.wait_processed(timeout=args.timeout)

        smoke_uri = f"{args.target_uri.rstrip('/')}/{SMOKE_FILENAME}"
        print(client.read(smoke_uri))
        print()
        print(
            format_find_text(
                client.find(
                    query="beril openviking smoke context layer",
                    target_uri=args.target_uri,
                    limit=3,
                )
            )
        )

        if not args.keep:
            client.rm(args.target_uri, recursive=True)
    finally:
        client.close()


if __name__ == "__main__":
    main()
