import re
from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from bot.config.settings import settings

# Patterns de titres de section dans les documents RH
_SECTION_TITLE = re.compile(
    r'^(?:[IVX]+\.|[0-9]+[\.\)]\s|ARTICLE\s|CHAPITRE\s|§\s?)'
    r'|^[A-ZÀÂÉÈÊËÎÏÔÙÛÜ][A-ZÀÂÉÈÊËÎÏÔÙÛÜ\s\-]{4,}$',
    re.MULTILINE,
)


def _source_label(metadata: dict) -> str:
    """Produit un label lisible à partir du nom de fichier source."""
    name = metadata.get("source_file", "")
    # Retire extension et remplace tirets/underscores par espaces
    label = Path(name).stem.replace("-", " ").replace("_", " ")
    sheet = metadata.get("sheet")
    if sheet:
        label += f" — {sheet}"
    return label.strip()


def _detect_section(content: str) -> str | None:
    """Détecte la première ligne ressemblant à un titre de section."""
    for line in content.splitlines()[:5]:
        line = line.strip()
        if 5 < len(line) < 90 and _SECTION_TITLE.match(line):
            return line
    return None


def _add_context_header(chunk: Document) -> Document:
    """Préfixe chaque chunk avec son document source et sa section détectée.

    Avant :
        "Les agents ont droit à 25 jours de congé annuel..."
    Après :
        "[Source: Guide des conges | Section: CONGE ANNUEL]
        Les agents ont droit à 25 jours de congé annuel..."

    Ce préfixe améliore la précision des embeddings : le modèle sait
    d'où vient l'information même si le chunk est court ou ambigu.
    Le préfixe est stocké dans page_content (utilisé pour l'embedding)
    mais aussi dans les métadonnées pour le débogage.
    """
    source = _source_label(chunk.metadata)
    section = _detect_section(chunk.page_content)

    if section:
        header = f"[Source: {source} | Section: {section}]"
    else:
        header = f"[Source: {source}]"

    chunk.metadata["context_header"] = header
    chunk.page_content = f"{header}\n{chunk.page_content}"
    return chunk


def split_documents(docs: List[Document]) -> List[Document]:
    """Découpe des Documents LangChain en chunks contextualisés.

    Étapes :
      1. Découpage RecursiveCharacterTextSplitter
      2. Ajout d'un en-tête contextuel [Source | Section] sur chaque chunk
      3. Détection du sous-département RH
      4. Numérotation des chunks
    """
    from bot.config.departments import detect_department

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = splitter.split_documents(docs)

    for i, chunk in enumerate(chunks):
        chunk = _add_context_header(chunk)
        chunk.metadata["chunk_index"] = i
        dept = detect_department(chunk.page_content)
        if dept:
            chunk.metadata["sous_departement"] = dept.id
        chunks[i] = chunk

    return chunks
