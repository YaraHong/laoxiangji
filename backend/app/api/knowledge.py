from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logger_handle import logger
from app.core.response import success
from app.models.knowledge_chunk import KnowledgeChunk
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


def _build_doc_response(doc, chunk_count: int = 0) -> dict:
    return {
        "id": doc.id,
        "title": doc.title,
        "file_url": doc.file_url,
        "doc_type": doc.doc_type,
        "version": doc.version,
        "status": doc.status,
        "chunk_count": chunk_count,
        "enabled": doc.enabled,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
    }


async def _count_chunks(db: AsyncSession, document_id: int) -> int:
    result = await db.execute(
        select(func.count()).select_from(KnowledgeChunk).where(
            KnowledgeChunk.document_id == document_id,
            KnowledgeChunk.enabled == True,
        )
    )
    return result.scalar() or 0


async def _batch_count_chunks(db: AsyncSession, doc_ids: list[int]) -> dict[int, int]:
    if not doc_ids:
        return {}
    result = await db.execute(
        select(KnowledgeChunk.document_id, func.count())
        .where(KnowledgeChunk.document_id.in_(doc_ids), KnowledgeChunk.enabled == True)
        .group_by(KnowledgeChunk.document_id)
    )
    return {row[0]: row[1] for row in result.all()}


@router.post("/documents")
async def upload_document_endpoint(
        file: UploadFile = File(...),
        doc_type: str = Form(...),
        db: AsyncSession = Depends(get_db),
):
    doc = await upload_document(db, file, doc_type)
    chunk_count = await _count_chunks(db, doc.id)
    logger.info("文档上传请求: id=%d, title=%s, type=%s, status=%s", doc.id, doc.title, doc_type, doc.status)
    return success(_build_doc_response(doc, chunk_count))


@router.get("/documents")
async def list_documents_endpoint(db: AsyncSession = Depends(get_db)):
    docs = await list_documents(db)
    doc_ids = [d.id for d in docs]
    chunk_count_map = await _batch_count_chunks(db, doc_ids)
    return success([
        _build_doc_response(d, chunk_count_map.get(d.id, 0))
        for d in docs
    ])


@router.post("/documents/{document_id}/embed")
async def re_embed_endpoint(document_id: int, db: AsyncSession = Depends(get_db)):
    doc = await re_embed_document(db, document_id)
    chunk_count = await _count_chunks(db, document_id)
    logger.info("文档重新向量化请求: doc_id=%d, status=%s", document_id, doc.status)
    return success({"id": doc.id, "status": doc.status, "chunk_count": chunk_count})


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
            "updated_at": f.updated_at.isoformat() if f.updated_at else None,
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
        "updated_at": faq.updated_at.isoformat() if faq.updated_at else None,
    })
