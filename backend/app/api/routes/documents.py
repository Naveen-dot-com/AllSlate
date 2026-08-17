from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, UploadFile

from backend.app.models.document import Document, ProcessingStatus
from backend.app.services.document_upload import DocumentUploadService

router = APIRouter(prefix="/api/v1/projects", tags=["documents"])


def _project_documents() -> Dict[str, List[Document]]:
    return {"demo": []}


@router.post("/{project_id}/documents")
async def upload_document(project_id: str, file: UploadFile) -> Dict[str, Any]:
    service = DocumentUploadService()
    try:
        service.validate_upload(file.filename or "")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    document = Document(
        document_id=f"doc-{project_id}-{len(_project_documents().get(project_id, []))}",
        filename=file.filename or "untitled",
        file_type=(file.filename or "").split(".")[-1].lower() or "unknown",
        status=ProcessingStatus.UPLOADED,
        project_id=project_id,
    )
    return {
        "id": document.document_id,
        "filename": document.filename,
        "file_type": document.file_type,
        "status": document.status.value,
        "uploaded_at": document.uploaded_at,
    }


@router.get("/{project_id}/documents")
async def list_documents(project_id: str) -> List[Dict[str, Any]]:
    return [{"id": "demo-doc", "filename": "sample.pdf", "file_type": "pdf", "status": ProcessingStatus.UPLOADED.value, "uploaded_at": "now"}]


@router.get("/{project_id}/documents/{document_id}")
async def get_document(project_id: str, document_id: str) -> Dict[str, Any]:
    return {
        "id": document_id,
        "filename": "sample.pdf",
        "file_type": "pdf",
        "status": ProcessingStatus.STORED.value,
        "element_count": 1,
        "element_counts_by_type": {"text": 1},
    }
