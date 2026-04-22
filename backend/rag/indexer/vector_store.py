from pathlib import Path
from typing import List
from functools import lru_cache

from langchain_chroma import Chroma
from langchain_core.documents import Document

from backend.core.config.settings import settings
from backend.rag.embeddings.embedder import get_embeddings

COLLECTION_NAME = "chubot_hr_docs"


@lru_cache(maxsize=1)
def get_vector_store() -> Chroma:
    """Retourne l'instance ChromaDB (créée une seule fois)."""
    Path(settings.VECTOR_STORE_PATH).mkdir(parents=True, exist_ok=True)

    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embeddings(),
        persist_directory=settings.VECTOR_STORE_PATH,
    )


def index_documents(docs: List[Document]) -> int:
    """
    Ajoute des documents dans ChromaDB.
    Retourne le nombre de chunks indexés.
    """
    from backend.rag.chunkers.text_splitter import split_documents

    chunks = split_documents(docs)
    vector_store = get_vector_store()
    vector_store.add_documents(chunks)

    print(f"  ✓ {len(chunks)} chunks indexés dans ChromaDB")
    return len(chunks)


def delete_collection() -> None:
    """Supprime toute la collection (réindexation complète)."""
    store = get_vector_store()
    store.delete_collection()
    get_vector_store.cache_clear()
    print("  ✓ Collection ChromaDB supprimée")
