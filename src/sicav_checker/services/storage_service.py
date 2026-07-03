from __future__ import annotations

import json
from pathlib import Path

from sicav_checker.core.logging import log_stage
from sicav_checker.domain.models import FinancialDocument
from sicav_checker.exceptions import StorageError
from sicav_checker.storage.local_storage import LocalStorageAdapter
from sicav_checker.storage.minio_storage import MinioStorageAdapter
from sicav_checker.storage.storage_adapter import StorageAdapter


class StorageService:
    """Persists canonical documents behind a storage adapter boundary."""

    def __init__(self, adapter: StorageAdapter | None = None, extracted_dir: Path = Path("data/extracted_json"), backend: str = "local") -> None:
        self.extracted_dir = extracted_dir
        if adapter is not None:
            self.adapter = adapter
        elif backend == "minio":
            self.adapter = MinioStorageAdapter()
        else:
            self.adapter = LocalStorageAdapter(".")

    def save_document(self, document: FinancialDocument, key: str | None = None) -> Path | None:
        if document.document_year is None:
            raise StorageError("Cannot save a document without a year")
        storage_key = key or str(self.extracted_dir / f"{document.document_year}.json")
        with log_stage("save_document", key=storage_key):
            payload = json.dumps(document.model_dump(mode="json"), indent=2, ensure_ascii=False).encode("utf-8")
            self.adapter.save_bytes(storage_key, payload)
            return Path(storage_key) if isinstance(self.adapter, LocalStorageAdapter) else None

    def save_documents(self, documents: list[FinancialDocument]) -> list[Path | None]:
        return [self.save_document(document) for document in documents]

    def load_documents(self) -> list[FinancialDocument]:
        with log_stage("load_documents", extracted_dir=str(self.extracted_dir)):
            if not self.extracted_dir.exists():
                return []
            documents: list[FinancialDocument] = []
            for path in sorted(self.extracted_dir.glob("*.json")):
                try:
                    documents.append(FinancialDocument(**json.loads(path.read_text(encoding="utf-8"))))
                except OSError as exc:
                    raise StorageError(str(exc)) from exc
            return sorted(documents, key=lambda document: document.document_year or 0)