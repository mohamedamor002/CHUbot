"""
Ingestion des pages web du site CHU Angers dans ChromaDB.

Stratégie :
  - agents-chu-angers.fr → crawl complet du site (HTML statique, trafilatura)
  - agents-chu-angers.fr/formulaires-utiles/ → téléchargement des fichiers .docx/.pdf liés
  - mstaff.co            → rendu JavaScript via Playwright (Chromium headless)

Usage :
    python scripts/ingest_web.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.rag.loaders.web_loader import load_site, load_urls, download_linked_docs
from backend.rag.loaders.document_loader import load_directory
from backend.rag.indexer.vector_store import index_documents

DOCS_DIR = Path(__file__).parent.parent / "data" / "documents"

# Pages mstaff (JavaScript — nécessite Playwright)
MSTAFF_URLS = [
    "https://chu-angers.mstaff.co/offers",
    "https://chu-angers.mstaff.co/mobility",
]

# Pages avec fichiers téléchargeables (.docx, .pdf)
FORMULAIRE_PAGES = [
    "https://www.agents-chu-angers.fr/formulaires-utiles/",
]

if __name__ == "__main__":
    all_docs = []

    # ── 1. Téléchargement des formulaires .docx/.pdf ──────────────────────────
    print("\n[1/3] Téléchargement des formulaires (agents-chu-angers.fr)...")
    downloaded_files = []
    for page_url in FORMULAIRE_PAGES:
        print(f"  Page : {page_url}")
        files = download_linked_docs(page_url, save_dir=DOCS_DIR)
        downloaded_files.extend(files)
    print(f"  -> {len(downloaded_files)} fichier(s) telecharges dans {DOCS_DIR}")

    # Indexer les fichiers téléchargés s'il y en a
    if downloaded_files:
        print(f"  Indexation des fichiers telecharges...")
        file_docs = load_directory(str(DOCS_DIR))
        if file_docs:
            count = index_documents(file_docs)
            print(f"  -> {count} chunks indexes depuis les fichiers locaux")

    # ── 2. Crawl complet du site agents-chu-angers.fr ─────────────────────────
    print("\n[2/3] Crawl du site agents-chu-angers.fr (statique)...")
    docs = load_site(
        "https://www.agents-chu-angers.fr/",
        max_pages=60,
        use_js=False,
    )
    print(f"  -> {len(docs)} pages extraites")
    all_docs.extend(docs)

    # ── 3. Pages mstaff (JavaScript) ─────────────────────────────────────────
    print("\n[3/3] Scraping mstaff.co (JavaScript / Playwright)...")
    docs = load_urls(MSTAFF_URLS, use_js=True)
    print(f"  -> {len(docs)} pages extraites")
    all_docs.extend(docs)

    # ── Indexation des pages web ──────────────────────────────────────────────
    if not all_docs:
        print("\nAucun contenu web extrait.")
        sys.exit(1)

    print(f"\nIndexation de {len(all_docs)} page(s) web dans ChromaDB...")
    count = index_documents(all_docs)
    print(f"\nTermine - {count} chunks indexes.")
