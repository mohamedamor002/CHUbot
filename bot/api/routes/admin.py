"""
Routes d'administration CHUbot — /api/admin

Endpoints :
  GET    /api/admin/              → Interface web (HTML)
  POST   /api/admin/documents/upload  → Upload + indexation en arrière-plan
  POST   /api/admin/urls/add          → Ajout URL + indexation en arrière-plan
  GET    /api/admin/jobs              → Liste des jobs (les 50 derniers)
  GET    /api/admin/jobs/{id}         → Détail d'un job
  GET    /api/admin/documents         → Liste des documents indexés
  DELETE /api/admin/documents/{id}    → Supprime un document (DB + ChromaDB)
  GET    /api/admin/index/stats       → Statistiques de l'index vectoriel

Sécurité : toutes les routes (sauf GET /) exigent l'en-tête X-Admin-Key.
"""

import ipaddress
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.db.database import get_db, AsyncSessionLocal
from bot.api.db.models import IndexedDocument, IngestionJob
from bot.api.db.schemas import (
    DocumentOut, IndexStatsOut, JobOut, UrlIngestRequest,
)
from bot.config.settings import settings
from bot.ingestion.loaders import load_file, load_url, SUPPORTED_EXTENSIONS
from bot.ingestion.indexer import index_documents, get_vector_store

router = APIRouter(prefix="/admin", tags=["Admin"])

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 Mo

# Signatures magiques des formats acceptés (magic bytes)
_MAGIC: dict[bytes, str] = {
    b"%PDF":     "pdf",
    b"PK\x03\x04": "docx/xlsx",  # ZIP → DOCX, XLSX, XLSM
    b"\xd0\xcf\x11\xe0": "xls/doc",  # Compound Document → XLS, DOC
}

_PRIVATE_NETS = [
    ipaddress.IPv4Network("10.0.0.0/8"),
    ipaddress.IPv4Network("172.16.0.0/12"),
    ipaddress.IPv4Network("192.168.0.0/16"),
    ipaddress.IPv4Network("127.0.0.0/8"),
    ipaddress.IPv4Network("169.254.0.0/16"),
    ipaddress.IPv4Network("0.0.0.0/8"),
]


# ── Auth ─────────────────────────────────────────────────────────────────────

async def verify_admin(x_admin_key: str = Header(..., alias="X-Admin-Key")):
    if x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Clé admin invalide")


# ── Validation ───────────────────────────────────────────────────────────────

def _check_mime(header: bytes, filename: str) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(400, f"Extension non supportée : {ext}")
    for magic, _ in _MAGIC.items():
        if header.startswith(magic):
            return
    raise HTTPException(400, "Le contenu du fichier ne correspond pas à un format autorisé")


def _check_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(400, "Seuls http et https sont autorisés")
    hostname = parsed.hostname or ""
    if not hostname:
        raise HTTPException(400, "URL invalide")
    if hostname.lower() in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        raise HTTPException(400, "Les URLs localhost ne sont pas autorisées")
    try:
        ip = ipaddress.ip_address(hostname)
        for net in _PRIVATE_NETS:
            if ip in net:
                raise HTTPException(400, f"Adresse IP privée non autorisée : {hostname}")
    except ValueError:
        pass  # hostname DNS → OK


# ── Tâches de fond ───────────────────────────────────────────────────────────

async def _ingest_file_task(job_id: uuid.UUID, tmp_path: str, original_name: str) -> None:
    async with AsyncSessionLocal() as db:
        job = await db.get(IngestionJob, job_id)
        job.status = "running"
        await db.commit()
        try:
            docs = load_file(tmp_path)
            for d in docs:
                d.metadata["source_file"] = original_name
            n = index_documents(docs)
            job.status = "done"
            job.chunks_indexed = n
            job.finished_at = datetime.now(timezone.utc)
            db.add(IndexedDocument(
                filename=original_name,
                file_type=Path(original_name).suffix.lstrip(".").lower(),
                chunks_indexed=n,
            ))
        except Exception as exc:
            job.status = "error"
            job.error_msg = str(exc)
            job.finished_at = datetime.now(timezone.utc)
        finally:
            Path(tmp_path).unlink(missing_ok=True)
        await db.commit()


async def _ingest_url_task(job_id: uuid.UUID, url: str) -> None:
    async with AsyncSessionLocal() as db:
        job = await db.get(IngestionJob, job_id)
        job.status = "running"
        await db.commit()
        try:
            docs = load_url(url)
            if not docs:
                raise ValueError("Aucun contenu extrait de cette URL")
            for d in docs:
                d.metadata["source_url"] = url
            n = index_documents(docs)
            job.status = "done"
            job.chunks_indexed = n
            job.finished_at = datetime.now(timezone.utc)
            db.add(IndexedDocument(
                filename=url,
                file_type="url",
                chunks_indexed=n,
            ))
        except Exception as exc:
            job.status = "error"
            job.error_msg = str(exc)
            job.finished_at = datetime.now(timezone.utc)
        await db.commit()


# ── Interface web ─────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def admin_ui():
    html_path = Path(__file__).resolve().parent.parent / "static" / "admin.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


# ── Endpoints API ─────────────────────────────────────────────────────────────

@router.post("/documents/upload", response_model=JobOut,
             dependencies=[Depends(verify_admin)])
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload un fichier et lance son indexation en arrière-plan."""
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "Fichier trop volumineux (max 20 Mo)")
    _check_mime(content[:8], file.filename)

    ext = Path(file.filename).suffix.lower()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp.write(content)
    tmp.close()

    job = IngestionJob(type="file", source=file.filename)
    db.add(job)
    await db.commit()
    await db.refresh(job)

    background_tasks.add_task(_ingest_file_task, job.id, tmp.name, file.filename)
    return job


@router.post("/urls/add", response_model=JobOut,
             dependencies=[Depends(verify_admin)])
async def add_url(
    body: UrlIngestRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Ajoute une URL et lance son scraping + indexation en arrière-plan."""
    _check_url(body.url)

    job = IngestionJob(type="url", source=body.url)
    db.add(job)
    await db.commit()
    await db.refresh(job)

    background_tasks.add_task(_ingest_url_task, job.id, body.url)
    return job


@router.get("/jobs", response_model=list[JobOut],
            dependencies=[Depends(verify_admin)])
async def list_jobs(db: AsyncSession = Depends(get_db)):
    """50 jobs les plus récents (tri du plus récent au plus ancien)."""
    result = await db.execute(
        select(IngestionJob).order_by(IngestionJob.created_at.desc()).limit(50)
    )
    return result.scalars().all()


@router.get("/jobs/{job_id}", response_model=JobOut,
            dependencies=[Depends(verify_admin)])
async def get_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    job = await db.get(IngestionJob, job_id)
    if not job:
        raise HTTPException(404, "Job introuvable")
    return job


@router.get("/documents", response_model=list[DocumentOut],
            dependencies=[Depends(verify_admin)])
async def list_documents(db: AsyncSession = Depends(get_db)):
    """Liste tous les documents indexés (du plus récent au plus ancien)."""
    result = await db.execute(
        select(IndexedDocument).order_by(IndexedDocument.indexed_at.desc())
    )
    return result.scalars().all()


@router.delete("/documents/{doc_id}", dependencies=[Depends(verify_admin)])
async def delete_document(doc_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Supprime un document de la DB et retire ses chunks de ChromaDB."""
    doc = await db.get(IndexedDocument, doc_id)
    if not doc:
        raise HTTPException(404, "Document introuvable")

    # Suppression dans ChromaDB par filtre sur source_file ou source_url
    try:
        vs = get_vector_store()
        collection = vs._collection
        # Tente les deux métadonnées possibles
        for key in ("source_file", "source_url"):
            collection.delete(where={key: doc.filename})
    except Exception:
        pass  # Non bloquant — ChromaDB peut déjà ne plus avoir ces chunks

    await db.delete(doc)
    await db.commit()
    return {"deleted": str(doc_id), "filename": doc.filename}


@router.get("/index/stats", response_model=IndexStatsOut,
            dependencies=[Depends(verify_admin)])
async def index_stats(db: AsyncSession = Depends(get_db)):
    """Statistiques globales : nombre de documents, de chunks, taille du dossier."""
    total_docs = await db.scalar(select(func.count()).select_from(IndexedDocument))
    total_chunks = await db.scalar(
        select(func.sum(IndexedDocument.chunks_indexed)).select_from(IndexedDocument)
    ) or 0

    index_path = Path(settings.VECTOR_STORE_PATH)
    size_bytes = sum(f.stat().st_size for f in index_path.rglob("*") if f.is_file()) \
        if index_path.exists() else 0

    return IndexStatsOut(
        total_documents=total_docs or 0,
        total_chunks=int(total_chunks),
        index_size_mb=round(size_bytes / (1024 * 1024), 2),
    )
