from __future__ import annotations

from typing import Any

from .config import ContextConfig


def create_client(config: ContextConfig) -> Any:
    import openviking as ov

    client = ov.SyncHTTPClient(
        url=config.openviking_url,
        api_key=config.openviking_api_key,
    )
    client.initialize()
    return client
