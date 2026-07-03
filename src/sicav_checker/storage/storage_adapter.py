from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class StorageAdapter(ABC):
    @abstractmethod
    def save_bytes(self, key: str, data: bytes) -> None:
        raise NotImplementedError

    @abstractmethod
    def load_bytes(self, key: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def exists(self, key: str) -> bool:
        raise NotImplementedError

    @staticmethod
    def normalize_key(key: str | Path) -> str:
        return str(key).replace("\\", "/")
