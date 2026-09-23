from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, Response, UploadFile

from backend.app.models.document import Document, ProcessingStatus
from backend.app.services.document_status import document_detail_fields
from backend.app.services.document_store import document_store
from backend.app.services.document_upload import DocumentUploadService

router = APIRouter(prefix="/api/v1/projects", tags=["documents"])

def _serialize_document(document: Document) -> Dict[str, Any]:
    return {
        "id": document.document_id,
        "filename": document.filename,
        "file_type": document.file_type,
        "status": document.status.value,
        "uploaded_at": document.uploaded_at,
        "updated_at": document.updated_at,
        "failure_reason": document.failure_reason,
    }


def _get_document(project_id: str, document_id: str) -> Document:
    document = document_store.get(project_id, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return document


@router.post("/{project_id}/documents", status_code=202)
async def upload_document(project_id: str, file: UploadFile, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    service = DocumentUploadService()
    try:
        suffix = service.validate_upload(file.filename or "")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    content = await file.read()
    text = service.extract_text(file.filename or "", content)
    timestamp = datetime.now(timezone.utc).isoformat()
    document = Document(
        document_id=str(uuid4()),
        filename=file.filename or "untitled",
        file_type=suffix.removeprefix("."),
        status=ProcessingStatus.QUEUED,
        project_id=project_id,
        uploaded_at=timestamp,
        updated_at=timestamp,
    )
    document_store.add(document)
    document_store.store_file(document.document_id, content)
    document_store.update_status(document, ProcessingStatus.QUEUED)
    background_tasks.add_task(document_store.process, document, text)
    return _serialize_document(document)


@router.get("/{project_id}/documents/{document_id}/file")
async def get_document_file(project_id: str, document_id: str) -> Response:
    document = _get_document(project_id, document_id)
    file_bytes = document_store.get_file(project_id, document_id)
    if file_bytes is None:
        raise HTTPException(status_code=404, detail="Document file not found.")

    extension = document.file_type.lower()
    mime_map = {
        "pdf": "application/pdf",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "txt": "text/plain",
        "md": "text/markdown",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    media_type = mime_map.get(extension, "application/octet-stream")
    return Response(content=file_bytes, media_type=media_type, headers={"Content-Disposition": f'inline; filename="{document.filename}"'})


@router.delete("/{project_id}/documents/{document_id}")
async def delete_document(project_id: str, document_id: str) -> Dict[str, Any]:
    if not document_store.delete(project_id, document_id):
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"deleted": True, "document_id": document_id}


@router.get("/{project_id}/documents")
async def list_documents(project_id: str) -> List[Dict[str, Any]]:
    return [_serialize_document(document) for document in document_store.list(project_id)]


@router.get("/{project_id}/documents/{document_id}")
async def get_document(project_id: str, document_id: str) -> Dict[str, Any]:
    document = _get_document(project_id, document_id)
    detail = document_detail_fields(document)
    return {
        **_serialize_document(document),
        "status": detail["status"],
        "failure_category": detail["failure_category"],
        "has_low_confidence_content": detail["has_low_confidence_content"],
        "element_count": document.element_count,
        "element_counts_by_type": {
            element_type: sum(
                element.element_type == element_type
                for element in document.elements
            )
            for element_type in {element.element_type for element in document.elements}
        },
    }


@router.get("/{project_id}/documents/{document_id}/elements")
async def list_document_elements(project_id: str, document_id: str) -> List[Dict[str, Any]]:
    document = _get_document(project_id, document_id)
    return [
        {
            "id": element.element_id,
            "element_type": element.element_type,
            "page_number": element.page_number,
            "raw_text": element.raw_text,
            "confidence": element.confidence,
            "confidence_reason": element.confidence_reason,
        }
        for element in document.elements
    ]

