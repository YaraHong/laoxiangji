from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logger_handle import logger
from app.core.response import success
from app.schemas.knowledge import FAQCreate, ToggleDocumentRequest
from app.services.knowledge_service import (
    create_faq,
    list_documents,
    list_faq,
    re_embed_document,
    toggle_document,
    upload_document,
)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post("/documents")
async def upload_document_endpoint(
        file: UploadFile = File(...),
        doc_type: str = Form(...),
        db: AsyncSession = Depends(get_db),
):
    doc = await upload_document(db, file, doc_type)
    logger.info("文档上传请求: id=%d, title=%s, type=%s, status=%s", doc.id, doc.title, doc_type, doc.status)
    return success({
        "id": doc.id, "title": doc.title, "file_name": doc.file_name,
        "doc_type": doc.doc_type, "version": doc.version, "status": doc.status,
        "chunk_count": doc.chunk_count, "enabled": doc.enabled,
        "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
    })


@router.get("/documents")
async def list_documents_endpoint(db: AsyncSession = Depends(get_db)):
    docs = await list_documents(db)
    return success([
        {
            "id": d.id, "title": d.title, "file_name": d.file_name,
            "doc_type": d.doc_type, "version": d.version, "status": d.status,
            "chunk_count": d.chunk_count, "enabled": d.enabled,
            "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
        }
        for d in docs
    ])


@router.post("/documents/{document_id}/embed")
async def re_embed_endpoint(document_id: int, db: AsyncSession = Depends(get_db)):
    doc = await re_embed_document(db, document_id)
    logger.info("文档重新向量化请求: doc_id=%d, status=%s", document_id, doc.status)
    return success({"id": doc.id, "status": doc.status, "chunk_count": doc.chunk_count})


@router.put("/documents/{document_id}")
async def toggle_document_endpoint(
        document_id: int, request: ToggleDocumentRequest, db: AsyncSession = Depends(get_db)
):
    doc = await toggle_document(db, document_id, request.enabled)
    return success({"id": doc.id, "enabled": doc.enabled})


@router.get("/faq")
async def list_faq_endpoint(db: AsyncSession = Depends(get_db)):
    faqs = await list_faq(db)
    return success([
        {
            "id": f.id, "question": f.question, "answer": f.answer,
            "category": f.category, "priority": f.priority, "enabled": f.enabled,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in faqs
    ])


@router.post("/faq")
async def create_faq_endpoint(request: FAQCreate, db: AsyncSession = Depends(get_db)):
    faq = await create_faq(
        db, question=request.question, answer=request.answer,
        category=request.category, priority=request.priority,
    )
    return success({
        "id": faq.id, "question": faq.question, "answer": faq.answer,
        "category": faq.category, "priority": faq.priority, "enabled": faq.enabled,
        "created_at": faq.created_at.isoformat() if faq.created_at else None,
    })
