"""
Reranking cross-encoder — second tri après retrieval initial.

Utilise FlashRank (léger, CPU, sans GPU, sans clé API) pour re-scorer
les chunks récupérés et remonter les plus pertinents en tête.

Architecture RAG Phase 2 :
  retrieval top-k → reranking → top-r (r ≤ k) → LLM
"""

from functools import lru_cache
from typing import List

from langchain_core.documents import Document


@lru_cache(maxsize=1)
def _get_ranker():
    from flashrank import Ranker
    # ms-marco-MiniLM-L-12-v2 : bon équilibre précision/vitesse, ~130 MB
    return Ranker(model_name="ms-marco-MiniLM-L-12-v2", cache_dir="./.cache/flashrank")


def rerank(query: str, docs: List[Document], top_n: int = 3) -> List[Document]:
    """Re-score les documents avec un cross-encoder et retourne les top_n.

    Si FlashRank n'est pas disponible, retourne les docs dans l'ordre original.

    Args:
        query:  question originale de l'utilisateur
        docs:   documents triés par similarité vectorielle
        top_n:  nombre de documents à conserver après reranking

    Returns:
        Liste de Documents re-triés par score cross-encoder (desc), tronquée à top_n
    """
    if not docs:
        return docs

    top_n = min(top_n, len(docs))

    try:
        from flashrank import RerankRequest

        ranker = _get_ranker()
        passages = [{"id": i, "text": doc.page_content} for i, doc in enumerate(docs)]
        request = RerankRequest(query=query, passages=passages)
        results = ranker.rerank(request)

        # results est trié desc par score ; on prend les top_n
        reranked = [docs[r["id"]] for r in results[:top_n]]
        return reranked

    except Exception:
        # FlashRank non installé ou erreur réseau au téléchargement du modèle
        return docs[:top_n]
