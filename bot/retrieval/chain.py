"""
Pipeline RAG online : question → pré-traitement → hybrid retrieval → reranking → LLM → réponse.

Flux conforme à l'architecture RAG (Phase 2) :
  1. Pré-traitement    : expansion acronymes + détection sous-département
  2. Hybrid retrieval  : BM25 (lexical) + ChromaDB (sémantique) avec filtre metadata
  3. Fallback          : si filtre trop restrictif → retrieval sans filtre
  4. Reranking         : cross-encoder (FlashRank) pour re-trier les chunks
  5. Guard anti-hallucination : si 0 doc → message fixe, LLM non appelé
  6. LLM               : génération contrainte au contexte
"""

import logging
import re
from functools import lru_cache
from typing import List, Optional, Tuple

log = logging.getLogger(__name__)

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from bot.config.settings import settings
from bot.config.departments import ESCALATION_CONTACTS, Department
from bot.ingestion.indexer import get_vector_store
from bot.retrieval.prompt import SYSTEM_PROMPT
from bot.retrieval.preprocessor import preprocess_query
from bot.retrieval.reranker import rerank

# Message fixe quand aucun document pertinent n'est trouvé.
# Le LLM N'EST PAS appelé → zéro risque d'hallucination.
_NO_DOCS_MESSAGE = (
    "Je ne trouve pas d'information sur ce sujet dans la base documentaire du CHU d'Angers.\n\n"
    "Pour obtenir une réponse, contactez directement le service RH concerné :\n"
    "• Carrières → Carrieres@chu-angers.fr\n"
    "• Formation continue → Formation-Continue@chu-angers.fr\n"
    "• Protection sociale → protectionsociale@chu-angers.fr\n"
    "• Retour & Maintien dans l'Emploi → Retouretmaintien@chu-angers.fr"
)

# Nombre de docs après reranking transmis au LLM (r ≤ k)
_RERANK_TOP_N: int = 3

# ── Patterns de détection post-génération ────────────────────────────────────

_ESCALATION_PATTERN = re.compile(
    r"contacter|contacter le (service|pôle|bureau)|DRH|"
    r"ressources humaines|@chu-angers|"
    + "|".join(re.escape(email) for email in ESCALATION_CONTACTS.values()),
    re.IGNORECASE,
)

_NOT_COVERED_PATTERN = re.compile(
    r"n[''e]est pas dans les documents|pas d[''i]information|"
    r"aucune information|je ne (trouve|peux|dispose|sais) pas|"
    r"non disponible|n[''a]i pas trouvé|base documentaire",
    re.IGNORECASE,
)


# ── LLM ──────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _get_llm() -> ChatOllama:
    return ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.1,
        num_ctx=4096,
        num_predict=512,
        reasoning=False,    # désactive le mode "thinking" de qwen3/deepseek
    )


@lru_cache(maxsize=1)
def _get_chain():
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{question}"),
    ])
    return prompt | _get_llm() | StrOutputParser()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _format_context(docs: List[Document]) -> str:
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


def _extract_sources(docs: List[Document]) -> List[dict]:
    seen: set = set()
    sources = []
    for doc in docs:
        name = doc.metadata.get("source_file")
        if name and name not in seen:
            seen.add(name)
            sources.append({
                "name": name,
                "url":  doc.metadata.get("source_url"),
                "type": doc.metadata.get("file_type", "pdf"),
            })
    return sources


def detect_escalation(answer: str) -> bool:
    return bool(_ESCALATION_PATTERN.search(answer))


def detect_not_covered(answer: str) -> bool:
    return bool(_NOT_COVERED_PATTERN.search(answer))


# ── BM25 (lexical) ───────────────────────────────────────────────────────────

def _build_bm25_retriever(all_docs: List[Document], k: int):
    """Construit un BM25Retriever à partir des documents ChromaDB chargés en mémoire."""
    try:
        from langchain_community.retrievers import BM25Retriever
        bm25 = BM25Retriever.from_documents(all_docs)
        bm25.k = k
        return bm25
    except Exception:
        return None


# ── Hybrid retrieval : BM25 + vecteur ────────────────────────────────────────

async def _hybrid_search(
    query: str,
    dept: Optional[Department],
    all_docs: List[Document],
) -> List[Document]:
    """Combine BM25 (lexical) et ChromaDB (sémantique) via EnsembleRetriever.

    BM25 est particulièrement utile pour les termes exacts : numéros de
    formulaires (CERFA 12345), noms de primes, codes d'absence, etc.

    Poids : 40% BM25  +  60% vectoriel  (le vectoriel reste dominant pour
    les questions sémantiques qui représentent la majorité du trafic RH).
    """
    store = get_vector_store()
    k = settings.RETRIEVAL_TOP_K

    # ── Retriever vectoriel (avec ou sans filtre sous-département) ──
    if dept:
        try:
            vector_retriever = store.as_retriever(
                search_kwargs={"k": k, "filter": {"sous_departement": dept.id}}
            )
            probe = await vector_retriever.ainvoke(query)
            if not probe:
                vector_retriever = store.as_retriever(search_kwargs={"k": k})
        except Exception:
            vector_retriever = store.as_retriever(search_kwargs={"k": k})
    else:
        vector_retriever = store.as_retriever(search_kwargs={"k": k})

    # ── Retriever BM25 ──
    bm25_retriever = _build_bm25_retriever(all_docs, k)

    if bm25_retriever is None:
        # BM25 non disponible → fallback purement vectoriel
        return await vector_retriever.ainvoke(query)

    # ── Ensemble : fusion par Reciprocal Rank Fusion (RRF) ──
    try:
        from langchain_classic.retrievers.ensemble import EnsembleRetriever
        ensemble = EnsembleRetriever(
            retrievers=[bm25_retriever, vector_retriever],
            weights=[0.4, 0.6],
        )
        return await ensemble.ainvoke(query)
    except Exception:
        # EnsembleRetriever non disponible → fallback vectoriel
        return await vector_retriever.ainvoke(query)


async def _get_all_docs() -> List[Document]:
    """Charge tous les documents du vector store pour initialiser BM25.

    BM25 a besoin d'un corpus complet à l'initialisation ; on le charge une
    seule fois depuis ChromaDB (collection entière, sans filtre).
    """
    store = get_vector_store()
    try:
        # ChromaDB : get() sans filtre retourne toute la collection
        raw = store._collection.get(include=["documents", "metadatas"])
        docs = []
        for content, meta in zip(raw["documents"], raw["metadatas"]):
            docs.append(Document(page_content=content, metadata=meta or {}))
        return docs
    except Exception:
        return []


# ── Retrieval complet (hybrid + reranking) ───────────────────────────────────

async def _search(query: str, dept: Optional[Department]) -> List[Document]:
    """Retrieval hybride BM25+vectoriel suivi d'un reranking cross-encoder.

    Étapes :
      1. Charge le corpus complet pour BM25
      2. Hybrid retrieval top-k
      3. Reranking FlashRank → top-r

    Si la collection ChromaDB n'existe pas encore (index non initialisé),
    retourne une liste vide sans lever d'exception → le guard anti-hallucination
    renverra le message fixe à l'utilisateur.
    """
    try:
        all_docs = await _get_all_docs()
    except Exception as e:
        log.error("_get_all_docs failed: %s", e)
        return []

    try:
        if all_docs:
            docs = await _hybrid_search(query, dept, all_docs)
        else:
            store = get_vector_store()
            retriever = store.as_retriever(search_kwargs={"k": settings.RETRIEVAL_TOP_K})
            docs = await retriever.ainvoke(query)
    except Exception as e:
        log.error("retrieval failed: %s", e)
        return []

    if not docs:
        return docs

    return rerank(query, docs, top_n=_RERANK_TOP_N)


# ── API publique ──────────────────────────────────────────────────────────────

async def retrieve(question: str) -> Tuple[str, List[dict], bool]:
    """Pré-traite la question et retourne (contexte, sources, is_covered)."""
    enriched_question, detected_dept = preprocess_query(question)
    docs = await _search(enriched_question, detected_dept)
    is_covered = len(docs) > 0
    return _format_context(docs), _extract_sources(docs), is_covered


async def stream_answer(context: str, question: str, is_covered: bool = True):
    """Streaming token par token.
    Court-circuite le LLM si aucun document trouvé.
    """
    if not is_covered:
        yield _NO_DOCS_MESSAGE
        return
    async for chunk in _get_chain().astream({"context": context, "question": question}):
        yield chunk


async def ask(question: str) -> str:
    """Réponse complète (non streamée).
    Court-circuite le LLM si aucun document trouvé.
    """
    context, _, is_covered = await retrieve(question)
    if not is_covered:
        return _NO_DOCS_MESSAGE
    return await _get_chain().ainvoke({"context": context, "question": question})
