import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.db.database import get_db
from bot.api.db.models import IndexedDocument
from bot.api.db.schemas import IndexResponse
from bot.ingestion.loaders import load_file, SUPPORTED_EXTENSIONS
from bot.ingestion.indexer import index_documents

router = APIRouter(prefix="/documents", tags=["Documents"])

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 Mo
DOCUMENTS_DIR = Path("data/documents")

MIME_TYPES = {
    ".pdf":  "application/pdf",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xlsm": "application/vnd.ms-excel.sheet.macroEnabled.12",
    ".xls":  "application/vnd.ms-excel",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc":  "application/msword",
}


@router.post("/upload", response_model=IndexResponse)
async def upload_and_index(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload un fichier RH, l'indexe dans ChromaDB et trace les métadonnées."""
    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté : {ext}. Acceptés : {list(SUPPORTED_EXTENSIONS)}",
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="Fichier trop volumineux (max 20 Mo)")
        tmp.write(content)
        tmp_path = tmp.name

    try:
        docs = load_file(tmp_path)
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
        raise HTTPException(status_code=500, detail=f"Erreur indexation : {str(e)}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@router.get("/", response_model=list[IndexResponse])
async def list_documents(db: AsyncSession = Depends(get_db)):
    """Liste tous les documents indexés (du plus récent au plus ancien)."""
    result = await db.execute(
        select(IndexedDocument).order_by(IndexedDocument.indexed_at.desc())
    )
    return [
        IndexResponse(filename=d.filename, chunks_indexed=d.chunks_indexed)
        for d in result.scalars().all()
    ]


@router.get("/file/{filename}")
async def serve_document(filename: str):
    """Sert un fichier source depuis data/documents/ (visualisation navigateur)."""
    safe_path = (DOCUMENTS_DIR / filename).resolve()
    if not str(safe_path).startswith(str(DOCUMENTS_DIR.resolve())):
        raise HTTPException(status_code=400, detail="Chemin invalide")
    if not safe_path.exists():
        raise HTTPException(status_code=404, detail="Fichier introuvable")

    ext = safe_path.suffix.lower()
    return Response(
        content=safe_path.read_bytes(),
        media_type=MIME_TYPES.get(ext, "application/octet-stream"),
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
