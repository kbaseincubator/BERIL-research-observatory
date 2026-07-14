"""Tests for the storage backend (app.storage)."""

import pytest

from app.storage import LocalFileStorage


@pytest.fixture
def storage(tmp_path):
    return LocalFileStorage(tmp_path)


class TestLocalFileStorage:
    async def test_save_and_load_roundtrip(self, storage):
        data = b"hello, world"
        await storage.save(data, "owner/project/file.csv")
        result = await storage.load("owner/project/file.csv")
        assert result == data

    async def test_save_returns_size_bytes(self, storage):
        data = b"x" * 100
        size = await storage.save(data, "a/b/file.bin")
        assert size == 100

    async def test_save_creates_parent_dirs(self, storage, tmp_path):
        await storage.save(b"data", "deep/nested/path/file.txt")
        assert (tmp_path / "deep" / "nested" / "path" / "file.txt").exists()

    async def test_exists_true_after_save(self, storage):
        await storage.save(b"data", "a/b/c.txt")
        assert storage.exists("a/b/c.txt") is True

    async def test_exists_false_before_save(self, storage):
        assert storage.exists("no/such/file.txt") is False

    async def test_delete_removes_file(self, storage):
        await storage.save(b"data", "a/b/file.txt")
        await storage.delete("a/b/file.txt")
        assert storage.exists("a/b/file.txt") is False

    async def test_delete_nonexistent_is_noop(self, storage):
        # Should not raise
        await storage.delete("no/such/file.txt")

    async def test_save_overwrites_existing(self, storage):
        await storage.save(b"original", "a/file.txt")
        await storage.save(b"updated", "a/file.txt")
        result = await storage.load("a/file.txt")
        assert result == b"updated"

    async def test_files_are_isolated_under_root(self, storage, tmp_path):
        other = LocalFileStorage(tmp_path / "other")
        await storage.save(b"mine", "shared/path/file.txt")
        assert not other.exists("shared/path/file.txt")

    def test_root_is_resolved_to_absolute(self, tmp_path):
        s = LocalFileStorage(tmp_path)
        assert s.root.is_absolute()

    async def test_path_traversal_rejected_in_save(self, storage):
        with pytest.raises(ValueError, match="escapes storage root"):
            await storage.save(b"data", "../../outside.txt")

    async def test_path_traversal_rejected_in_load(self, storage):
        with pytest.raises(ValueError, match="escapes storage root"):
            await storage.load("../outside.txt")

    async def test_path_traversal_rejected_in_delete(self, storage):
        with pytest.raises(ValueError, match="escapes storage root"):
            await storage.delete("../../outside.txt")

    def test_path_traversal_rejected_in_exists(self, storage):
        with pytest.raises(ValueError, match="escapes storage root"):
            storage.exists("../outside.txt")

    async def test_absolute_path_rejected(self, storage):
        with pytest.raises(ValueError, match="escapes storage root"):
            await storage.save(b"data", "/tmp/evil.txt")
