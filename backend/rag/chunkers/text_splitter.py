from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.core.config.settings import settings


def split_documents(docs: List[Document]) -> List[Document]:
    """
    Découpe une liste de Documents en chunks.
    Les paramètres chunk_size et chunk_overlap viennent du .env.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""],
    )

    chunks = splitter.split_documents(docs)

    # Ajouter l'index du chunk dans les métadonnées
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i

    return chunks
