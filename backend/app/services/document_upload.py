from __future__ import annotations

from io import BytesIO
from pathlib import Path

_SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".png", ".jpg", ".jpeg"}


class DocumentUploadService:
    def validate_upload(self, filename: str) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix not in _SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported document type: {filename}. Supported types: {sorted(_SUPPORTED_EXTENSIONS)}")
        return suffix

    def _extract_image_text(self, file_content: bytes) -> str:
        try:
            from rapidocr_onnxruntime import RapidOCR
        except Exception:
            return ""

        try:
            ocr = RapidOCR()
            results = ocr(file_content)
            if not results:
                return ""

            lines: list[str] = []
            for row in results:
                if not isinstance(row, (list, tuple)) or len(row) < 2:
                    continue
                text = row[1]
                if isinstance(text, str) and text.strip():
                    lines.append(text.strip())
                elif isinstance(text, (list, tuple)):
                    cleaned = " ".join(str(part).strip() for part in text if str(part).strip())
                    if cleaned:
                        lines.append(cleaned)
            return "\n\n".join(lines).strip()
        except Exception:
            return ""

    def extract_text(self, filename: str, file_content: bytes) -> str:
        suffix = Path(filename).suffix.lower()

        if suffix in {".txt", ".md"}:
            return file_content.decode("utf-8", errors="ignore").strip()

        if suffix in {".png", ".jpg", ".jpeg"}:
            text = self._extract_image_text(file_content)
            if text:
                return text
            return ""

        if suffix == ".pdf":
            try:
                from pypdf import PdfReader

                reader = PdfReader(BytesIO(file_content))
                pages = []
                for page in reader.pages:
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        pages.append(page_text.strip())
                text = "\n\n".join(pages)
                if text.strip():
                    return text.strip()
            except Exception:
                pass

            try:
                from unstructured.partition.pdf import partition_pdf

                elements = partition_pdf(file=file_content)
                text_chunks = [getattr(element, "text", "") for element in elements if getattr(element, "text", "").strip()]
                text = "\n\n".join(text_chunks)
                if text.strip():
                    return text.strip()
            except Exception:
                pass

            return ""

        return ""
