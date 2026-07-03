from __future__ import annotations

from pathlib import Path

from sicav_checker.storage.storage_adapter import StorageAdapter


class LocalStorageAdapter(StorageAdapter):
    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def _path(self, key: str) -> Path:
        return self.root / self.normalize_key(key)

    def save_bytes(self, key: str, data: bytes) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def load_bytes(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()
