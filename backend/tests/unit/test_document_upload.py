from backend.app.services.document_upload import DocumentUploadService


class DummyRapidOCR:
    def __call__(self, img_content, **kwargs):
        return [[None, ["Hello from image OCR"], None, None]]


def test_extract_text_from_image_uses_ocr(monkeypatch):
    import rapidocr_onnxruntime

    monkeypatch.setattr(rapidocr_onnxruntime, "RapidOCR", lambda **kwargs: DummyRapidOCR())

    service = DocumentUploadService()
    text = service.extract_text("scan.png", b"not-a-real-image")

    assert "Hello from image OCR" in text
