"""
Gestion de l'index vectoriel ChromaDB + CLI d'ingestion.

Usage en ligne de commande :
    python -m bot.ingestion.indexer --dir data/documents
    python -m bot.ingestion.indexer --file data/documents/guide_primes.pdf
    python -m bot.ingestion.indexer --urls   (indexe toutes les URLs du rapport)
    python -m bot.ingestion.indexer --reset  (vide la collection avant d'indexer)
"""

import argparse
import hashlib
import sys
from functools import lru_cache
from pathlib import Path
from typing import List

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

from bot.config.settings import settings
from bot.config.departments import DOCUMENTATION_URLS

COLLECTION_NAME = "chubot_hr_docs"


# ── Embeddings ────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(
        model=settings.EMBEDDING_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
    )


# ── Vecteur store ─────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_vector_store() -> Chroma:
    """Retourne l'instance ChromaDB persistante (singleton)."""
    Path(settings.VECTOR_STORE_PATH).mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embeddings(),
        persist_directory=settings.VECTOR_STORE_PATH,
    )


def _chunk_id(chunk: Document) -> str:
    """ID déterministe (MD5) basé sur le contenu + source — évite les doublons."""
    key = chunk.page_content + chunk.metadata.get("source_file", "")
    return hashlib.md5(key.encode()).hexdigest()


def index_documents(docs: List[Document]) -> int:
    """Découpe et indexe des documents dans ChromaDB (sans doublons). Retourne le nombre de chunks."""
    from bot.ingestion.splitter import split_documents

    chunks = split_documents(docs)

    # Déduplication intra-batch : si deux chunks ont le même ID (contenu identique),
    # on ne garde que le premier — ChromaDB refuse les IDs en double dans un même appel.
    seen: dict[str, Document] = {}
    for chunk in chunks:
        cid = _chunk_id(chunk)
        if cid not in seen:
            seen[cid] = chunk

    unique_chunks = list(seen.values())
    unique_ids    = list(seen.keys())
    dropped       = len(chunks) - len(unique_chunks)

    get_vector_store().add_documents(unique_chunks, ids=unique_ids)
    msg = f"  [OK] {len(unique_chunks)} chunks indexés"
    if dropped:
        msg += f" ({dropped} doublons ignorés)"
    print(msg)
    return len(unique_chunks)


def reset_index() -> None:
    """Vide toute la collection et supprime les fichiers sur disque (réindexation propre)."""
    import shutil
    try:
        get_vector_store().delete_collection()
    except Exception:
        pass
    get_vector_store.cache_clear()
    get_embeddings.cache_clear()

    # Supprime les fichiers physiques pour éviter les conflits de version ChromaDB
    index_path = Path(settings.VECTOR_STORE_PATH)
    if index_path.exists():
        try:
            shutil.rmtree(index_path)
        except PermissionError:
            print("  [WARN] Fichiers verrouillés — arrêtez le serveur uvicorn puis relancez --reset")
            sys.exit(1)
        index_path.mkdir(parents=True)
    print("  [OK] Index ChromaDB supprimé et répertoire recréé")


# ── CLI ───────────────────────────────────────────────────────────────────────

def _cli():
    parser = argparse.ArgumentParser(
        description="Ingestion de documents RH dans ChromaDB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dir",   metavar="DOSSIER", help="Indexe tous les fichiers d'un dossier")
    group.add_argument("--file",  metavar="FICHIER",  help="Indexe un fichier unique")
    group.add_argument("--urls",  action="store_true", help="Indexe les URLs documentaires du rapport")
    group.add_argument("--all",   action="store_true", help="Indexe data/documents/ + toutes les URLs du rapport")
    parser.add_argument("--reset", action="store_true", help="Vide la collection avant d'indexer")
    args = parser.parse_args()

    if args.reset:
        reset_index()

    from bot.ingestion.loaders import load_file, load_directory, load_urls

    docs: List[Document] = []

    if args.dir:
        print(f"\nChargement depuis : {args.dir}")
        docs = load_directory(args.dir)
    elif args.file:
        print(f"\nChargement : {args.file}")
        docs = load_file(args.file)
    elif args.urls:
        print(f"\nScraping de {len(DOCUMENTATION_URLS)} URLs du rapport...")
        docs = load_urls(DOCUMENTATION_URLS)
    else:  # --all
        print("\n[1/2] Chargement des fichiers depuis data/documents/")
        docs = load_directory("data/documents")
        print(f"\n[2/2] Scraping de {len(DOCUMENTATION_URLS)} URLs du rapport...")
        docs += load_urls(DOCUMENTATION_URLS)

    if not docs:
        print("Aucun document chargé.")
        sys.exit(0)

    print(f"\nIndexation de {len(docs)} document(s)...")
    total = index_documents(docs)
    print(f"\nTerminé — {total} chunks indexés dans ChromaDB (doublons ignorés).")


if __name__ == "__main__":
    _cli()
