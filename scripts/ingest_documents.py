"""
Ingestion batch de documents RH dans ChromaDB.

Usage :
    python scripts/ingest_documents.py --dir data/documents
    python scripts/ingest_documents.py --file chemin/vers/fichier.pdf
"""

import argparse
import sys
from pathlib import Path

# Ajouter la racine du projet au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.rag.loaders.document_loader import load_document, load_directory
from backend.rag.indexer.vector_store import index_documents


def ingest_directory(dir_path: str):
    print(f"\nChargement des documents depuis : {dir_path}")
    docs = load_directory(dir_path)

    if not docs:
        print("Aucun document trouvé.")
        return

    print(f"\nIndexation de {len(docs)} page(s) dans ChromaDB...")
    count = index_documents(docs)
    print(f"\nTermine - {count} chunks indexes.")


def ingest_file(file_path: str):
    print(f"\nChargement : {file_path}")
    docs = load_document(file_path)
    print(f"Indexation de {len(docs)} page(s)...")
    count = index_documents(docs)
    print(f"Terminé — {count} chunks indexés.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingestion de documents RH dans ChromaDB")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dir", help="Dossier contenant les PDFs")
    group.add_argument("--file", help="Fichier unique à indexer")
    args = parser.parse_args()

    if args.dir:
        ingest_directory(args.dir)
    else:
        ingest_file(args.file)
