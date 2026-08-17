from __future__ import annotations

from pathlib import Path

_SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".png", ".jpg", ".jpeg"}


class DocumentUploadService:
    def validate_upload(self, filename: str) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix not in _SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported document type: {filename}. Supported types: {sorted(_SUPPORTED_EXTENSIONS)}")
        return suffix
