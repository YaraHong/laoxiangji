import os
import tempfile
from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    UnstructuredWordDocumentLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger_handle import logger
from app.core.milvus import get_collection
from app.core.minio_client import download_file, upload_file
from app.core.model_factory import openai_client
from app.models.faq import FAQ
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import KnowledgeDocument
from app.services.text_cleaner import clean_document_text

DOC_TYPE_MAP = {
    "加盟政策": "加盟政策",
    "FAQ": "FAQ",
    "招商话术": "招商话术",
    "培训支持": "培训支持",
    "门店模型": "门店模型",
}

_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)


def _get_loader(file_path: str, file_name: str):
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    if ext == "pdf":
        return PyPDFLoader(file_path)
    elif ext == "docx":
        return UnstructuredWordDocumentLoader(file_path)
    elif ext == "md":
        return UnstructuredMarkdownLoader(file_path)
    else:
        return TextLoader(file_path, encoding="utf-8")


async def _process_document(
        save_name: str,
        title: str,
        doc_type: str,
        doc: KnowledgeDocument,
        db: AsyncSession
) -> None:
    suffix = f".{save_name.rsplit('.', 1)[-1]}" if "." in save_name else ""
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        data = download_file(save_name)
        tmp.write(data)
        tmp_path = tmp.name

    try:
        loader = _get_loader(tmp_path, save_name)
        raw_docs = loader.load()
        logger.info("文档解析完成: %s, pages=%d", save_name, len(raw_docs))

        all_chunks = _splitter.split_documents(raw_docs)
        logger.info("文档分块完成: %s, chunks=%d", save_name, len(all_chunks))

        chunk_count = 0
        if all_chunks:
            col = get_collection()

            texts = [clean_document_text(c.page_content) for c in all_chunks]
            # 过滤掉清理后为空的chunk
            texts = [t for t in texts if t]
            vectors: list[list] = []
            batch_size = 20
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_vectors = openai_client.embeddings.create(
                    model='Qwen/Qwen3-Embedding-8B',
                    input=batch,
                    encoding_format="float"
                )
                vectors.extend(batch_vectors)
                logger.debug(
                    "Embedding 批次 %d/%d 完成", i // batch_size + 1, (len(texts) + batch_size - 1) // batch_size
                )

            for i, text in enumerate(texts):
                chunk = KnowledgeChunk(
                    document_id=doc.id,
                    chunk_index=i,
                    content=text[:4096],
                    token_count=len(text),
                    milvus_pk=f"doc{doc.id}_chunk{i}",
                )
                db.add(chunk)

            columns = [
                [doc.id] * len(texts),
                list(range(len(texts))),
                [text[:4096] for text in texts],
                [title[:512]] * len(texts),
                [doc_type[:64]] * len(texts),
                vectors,
            ]
            col.insert(columns)
            col.flush()

            chunk_count = len(texts)

        doc.status = "ready"
        logger.info("文档处理完成: id=%d, title=%s, chunks=%d", doc.id, title, chunk_count)
    finally:
        os.unlink(tmp_path)


async def upload_document(db: AsyncSession, file: UploadFile, doc_type: str):
    if doc_type not in DOC_TYPE_MAP:
        raise HTTPException(status_code=400, detail=f"无效的文档类型: {doc_type}")

    safe_name = file.filename or "unnamed"
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    save_name = f"{ts}_{safe_name}"

    content_bytes = await file.read()

    upload_file(save_name, content_bytes, file.content_type or "application/octet-stream")

    title = safe_name.rsplit(".", 1)[0] if "." in safe_name else safe_name
    doc = KnowledgeDocument(
        title=title,
        file_url=save_name,
        doc_type=doc_type,
        status="processing",
    )
    db.add(doc)
    await db.flush()

    try:
        await _process_document(save_name, title, doc_type, doc, db)
    except Exception as e:
        logger.exception("文档处理失败: %s", save_name)
        doc.status = "error"
        doc.title = f"{title} (error: {str(e)[:100]})"

    await db.commit()
    await db.refresh(doc)
    return doc


async def list_documents(db: AsyncSession) -> list[KnowledgeDocument]:
    result = await db.execute(
        select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc())
    )
    return list(result.scalars().all())


async def re_embed_document(db: AsyncSession, doc_id: int) -> KnowledgeDocument:
    result = await db.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    if not doc.file_url:
        raise HTTPException(status_code=400, detail="文档无文件路径，无法重新向量化")

    col = get_collection()
    col.delete(f'doc_id == {doc_id}')
    col.flush()

    from sqlalchemy import update as sql_update
    await db.execute(
        sql_update(KnowledgeChunk)
        .where(KnowledgeChunk.document_id == doc_id)
        .values(enabled=False)
    )

    doc.status = "processing"
    await db.flush()

    try:
        await _process_document(doc.file_url, doc.title, doc.doc_type, doc, db)
    except Exception as e:
        logger.exception("文档重新向量化失败: doc_id=%d", doc_id)
        doc.status = "error"

    await db.commit()
    await db.refresh(doc)
    return doc


async def toggle_document(db: AsyncSession, doc_id: int, enabled: bool) -> KnowledgeDocument:
    result = await db.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    doc.enabled = enabled
    await db.commit()
    await db.refresh(doc)
    return doc


async def list_faq(db: AsyncSession) -> list[FAQ]:
    result = await db.execute(
        select(FAQ).where(FAQ.enabled == True).order_by(FAQ.priority.desc())
    )
    return list(result.scalars().all())


async def create_faq(
        db: AsyncSession, question: str, answer: str, category: str = "通用", priority: int = 0
) -> FAQ:
    faq = FAQ(question=question, answer=answer, category=category, priority=priority)
    db.add(faq)
    await db.commit()
    await db.refresh(faq)
    return faq
