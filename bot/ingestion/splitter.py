from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from bot.config.settings import settings


def split_documents(docs: List[Document]) -> List[Document]:
    """Découpe des Documents LangChain en chunks et enrichit les métadonnées.

    Métadonnées ajoutées par chunk :
      - chunk_index      : position globale dans le batch
      - sous_departement : ID du sous-département RH détecté (peut être None)
    """
    from bot.config.departments import detect_department

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = splitter.split_documents(docs)

    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i

        # Détection du sous-département à partir du contenu du chunk
        dept = detect_department(chunk.page_content)
        if dept:
            chunk.metadata["sous_departement"] = dept.id

    return chunks
