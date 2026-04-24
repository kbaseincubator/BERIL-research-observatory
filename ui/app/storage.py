"""Storage backend abstraction for user-uploaded project files."""

import asyncio
from pathlib import Path
from typing import Protocol


class StorageBackend(Protocol):
    async def save(self, data: bytes, path: str) -> int: ...
    async def load(self, path: str) -> bytes: ...
    async def delete(self, path: str) -> None: ...
    def exists(self, path: str) -> bool: ...


class LocalFileStorage:
    """Stores files under a root directory on the local filesystem.

    All path arguments are relative to the root, e.g. "<owner_id>/<slug>/<filename>".
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def _full_path(self, path: str) -> Path:
        full = (self.root / path).resolve()
        if not full.is_relative_to(self.root):
            raise ValueError(f"Path escapes storage root: {path!r}")
        return full

    async def save(self, data: bytes, path: str) -> int:
        """Write data to path, creating parent directories as needed. Returns size in bytes."""
        full = self._full_path(path)
        await asyncio.to_thread(full.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(full.write_bytes, data)
        return len(data)

    async def load(self, path: str) -> bytes:
        """Read and return the file contents at path."""
        full = self._full_path(path)
        return await asyncio.to_thread(full.read_bytes)

    async def delete(self, path: str) -> None:
        """Delete the file at path. No-ops if the file does not exist."""
        full = self._full_path(path)
        await asyncio.to_thread(_unlink_if_exists, full)

    def exists(self, path: str) -> bool:
        return self._full_path(path).exists()


def _unlink_if_exists(p: Path) -> None:
    try:
        p.unlink()
    except FileNotFoundError:
        pass
