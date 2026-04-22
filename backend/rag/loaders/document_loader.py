from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader
from langchain_community.document_loaders import UnstructuredExcelLoader


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".xlsm"}


def load_document(file_path: str) -> List[Document]:
    """Charge un fichier et retourne une liste de Documents LangChain."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {file_path}")

    ext = path.suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Format non supporté : {ext}. Formats acceptés : {SUPPORTED_EXTENSIONS}")

    if ext == ".pdf":
        loader = PyMuPDFLoader(str(path))

    elif ext in {".docx", ".doc"}:
        loader = Docx2txtLoader(str(path))

    elif ext in {".xlsx", ".xls", ".xlsm"}:
        loader = UnstructuredExcelLoader(str(path), mode="elements")

    docs = loader.load()

    # Ajouter le nom du fichier source dans les métadonnées
    for doc in docs:
        doc.metadata["source_file"] = path.name
        doc.metadata["file_type"] = ext.lstrip(".")

    return docs


def load_directory(dir_path: str) -> List[Document]:
    """Charge tous les fichiers supportés d'un dossier."""
    directory = Path(dir_path)

    if not directory.is_dir():
        raise NotADirectoryError(f"Dossier introuvable : {dir_path}")

    all_docs: List[Document] = []

    for file in directory.rglob("*"):
        if file.suffix.lower() in SUPPORTED_EXTENSIONS:
            try:
                docs = load_document(str(file))
                all_docs.extend(docs)
                print(f"  ✓ {file.name} ({len(docs)} page(s))")
            except Exception as e:
                print(f"  ✗ {file.name} — erreur : {e}")

    return all_docs
