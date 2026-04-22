"""
Ingestion des pages web du site CHU Angers dans ChromaDB.

Stratégie :
  - agents-chu-angers.fr → crawl complet du site (HTML statique, trafilatura)
  - mstaff.co            → rendu JavaScript via Playwright (Chromium headless)

Usage :
    python scripts/ingest_web.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.rag.loaders.web_loader import load_site, load_urls
from backend.rag.indexer.vector_store import index_documents

# Pages mstaff (JavaScript — nécessite Playwright)
MSTAFF_URLS = [
    "https://chu-angers.mstaff.co/offers",
    "https://chu-angers.mstaff.co/mobility",
]

if __name__ == "__main__":
    all_docs = []

    # ── 1. Crawl complet du site agents-chu-angers.fr ─────────────────────────
    print("\n[1/2] Crawl du site agents-chu-angers.fr (statique)...")
    docs = load_site(
        "https://www.agents-chu-angers.fr/",
        max_pages=60,
        use_js=False,
    )
    print(f"  → {len(docs)} pages extraites")
    all_docs.extend(docs)

    # ── 2. Pages mstaff (JavaScript) ─────────────────────────────────────────
    print("\n[2/2] Scraping mstaff.co (JavaScript / Playwright)...")
    docs = load_urls(MSTAFF_URLS, use_js=True)
    print(f"  → {len(docs)} pages extraites")
    all_docs.extend(docs)

    # ── Indexation ────────────────────────────────────────────────────────────
    if not all_docs:
        print("\nAucun contenu extrait.")
        sys.exit(1)

    print(f"\nIndexation de {len(all_docs)} document(s) dans ChromaDB...")
    count = index_documents(all_docs)
    print(f"\nTerminé — {count} chunks indexés.")
