from __future__ import annotations

import hashlib
import json
from pathlib import Path


Manifest = dict[str, dict[str, str]]


def build_manifest(target_sources: dict[str, list[Path]], repo_root: Path) -> Manifest:
    manifest: Manifest = {}
    for target_uri, paths in sorted(target_sources.items()):
        manifest[target_uri] = {
            path.relative_to(repo_root).as_posix(): _sha256(path) for path in sorted(paths)
        }
    return manifest


def changed_targets(old: Manifest, new: Manifest) -> list[str]:
    return sorted(target for target, files in new.items() if old.get(target) != files)


def removed_targets(old: Manifest, new: Manifest) -> list[str]:
    return sorted(set(old) - set(new))


def load_manifest(path: Path) -> Manifest:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def save_manifest(path: Path, manifest: Manifest) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
