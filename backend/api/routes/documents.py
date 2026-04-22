import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.domain.models.document import IndexedDocument
from backend.domain.schemas.document import IndexResponse
from backend.rag.loaders.document_loader import load_document, SUPPORTED_EXTENSIONS
from backend.rag.indexer.vector_store import index_documents

router = APIRouter(prefix="/documents", tags=["Documents"])

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 Mo


@router.post("/upload", response_model=IndexResponse)
async def upload_and_index(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload un fichier RH (PDF, Word, Excel), l'indexe dans ChromaDB et enregistre les métadonnées en base."""
    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté : {ext}. Formats acceptés : {list(SUPPORTED_EXTENSIONS)}",
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        content = await file.read()

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="Fichier trop volumineux (max 20 Mo)")

        tmp.write(content)
        tmp_path = tmp.name

    try:
        docs = load_document(tmp_path)
        for doc in docs:
            doc.metadata["source_file"] = file.filename

        chunks_count = index_documents(docs)

        db.add(IndexedDocument(
            filename=file.filename,
            file_type=ext.lstrip("."),
            chunks_indexed=chunks_count,
        ))
        await db.commit()

        return IndexResponse(filename=file.filename, chunks_indexed=chunks_count)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'indexation : {str(e)}")

    finally:
        Path(tmp_path).unlink(missing_ok=True)


@router.get("/", response_model=list[IndexResponse])
async def list_documents(db: AsyncSession = Depends(get_db)):
    """Liste tous les documents indexés."""
    from sqlalchemy import select
    result = await db.execute(select(IndexedDocument).order_by(IndexedDocument.indexed_at.desc()))
    docs = result.scalars().all()
    return [
        IndexResponse(filename=d.filename, chunks_indexed=d.chunks_indexed)
        for d in docs
    ]
