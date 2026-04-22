"""
Web scraper pour le site CHU Angers.

- Pages statiques (agents-chu-angers.fr) : trafilatura pour extraction du contenu principal
- Pages JavaScript (mstaff.co) : Playwright (navigateur headless Chromium)
"""

import time
from typing import List
from urllib.parse import urljoin, urlparse

import requests
import trafilatura
from bs4 import BeautifulSoup
from langchain_core.documents import Document

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


# ── Extraction statique (trafilatura) ─────────────────────────────────────────

def _scrape_static(url: str) -> str | None:
    """Extrait le contenu principal d'une page statique via trafilatura."""
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()

    text = trafilatura.extract(
        response.text,
        include_links=True,
        include_tables=True,
        include_images=False,
        no_fallback=False,
        favor_precision=False,   # favorise le rappel (plus de contenu)
        deduplicate=True,
    )
    return text


# ── Extraction JavaScript (Playwright) ───────────────────────────────────────

def _scrape_js(url: str, wait_seconds: int = 3) -> str | None:
    """Extrait le contenu d'une page rendue en JavaScript via Playwright."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=30000)
        time.sleep(wait_seconds)  # attendre le rendu JS

        html = page.content()
        browser.close()

    return trafilatura.extract(
        html,
        include_links=True,
        include_tables=True,
        include_images=False,
        deduplicate=True,
    )


# ── Découverte de sous-pages ──────────────────────────────────────────────────

def _find_subpages(base_url: str, max_pages: int = 30) -> List[str]:
    """Trouve les sous-pages internes d'un site."""
    base_domain = urlparse(base_url).netloc
    visited = set()
    to_visit = [base_url]
    found = []

    while to_visit and len(found) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)

        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if "text/html" not in r.headers.get("Content-Type", ""):
                continue
            found.append(url)

            soup = BeautifulSoup(r.text, "lxml")
            for a in soup.find_all("a", href=True):
                href = urljoin(url, a["href"]).split("#")[0].split("?")[0]
                if (
                    urlparse(href).netloc == base_domain
                    and href not in visited
                    and href not in to_visit
                    and not href.endswith((".pdf", ".docx", ".xlsx", ".jpg", ".png"))
                ):
                    to_visit.append(href)
        except Exception:
            continue

    return found


# ── API publique ──────────────────────────────────────────────────────────────

def load_url(url: str, use_js: bool = False) -> List[Document]:
    """Scrape une URL et retourne une liste de Documents LangChain."""
    try:
        text = _scrape_js(url) if use_js else _scrape_static(url)
    except Exception as e:
        raise RuntimeError(f"Erreur scraping {url}: {e}") from e

    if not text or len(text.strip()) < 100:
        return []

    # Titre de la page
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")
        title = soup.title.get_text(strip=True) if soup.title else urlparse(url).path
    except Exception:
        title = urlparse(url).path

    return [Document(
        page_content=text,
        metadata={
            "source_file": title,
            "source_url": url,
            "file_type": "web",
        }
    )]


def load_site(base_url: str, max_pages: int = 30, use_js: bool = False) -> List[Document]:
    """Crawle un site entier à partir d'une URL de base."""
    print(f"  Découverte des sous-pages de {base_url}...")
    urls = _find_subpages(base_url, max_pages=max_pages)
    print(f"  {len(urls)} pages trouvées")

    all_docs: List[Document] = []
    for url in urls:
        try:
            docs = load_url(url, use_js=use_js)
            if docs:
                all_docs.extend(docs)
                print(f"    ✓ {url}")
            else:
                print(f"    ⚠ {url} (contenu vide)")
        except Exception as e:
            print(f"    ✗ {url} — {e}")

    return all_docs


def load_urls(urls: List[str], use_js: bool = False) -> List[Document]:
    """Scrape une liste d'URLs spécifiques."""
    all_docs: List[Document] = []
    for url in urls:
        try:
            docs = load_url(url, use_js=use_js)
            all_docs.extend(docs)
            status = f"{len(docs)} doc(s)" if docs else "contenu vide"
            print(f"  ✓ {url} ({status})")
        except Exception as e:
            print(f"  ✗ {url} — {e}")
    return all_docs
