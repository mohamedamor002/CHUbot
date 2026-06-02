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

# Seuil minimum de pertinence : un document en dessous est ignoré comme source.
# FlashRank ms-marco produit des scores généralement entre -5 et +5 (non bornés à 1).
# 0.0 = neutre ; les documents hors-sujet tombent souvent en négatif ou très proche de 0.
_SCORE_THRESHOLD: float = 0.05


@lru_cache(maxsize=1)
def _get_ranker():
    from flashrank import Ranker
    # ms-marco-MiniLM-L-12-v2 : bon équilibre précision/vitesse, ~130 MB
    return Ranker(model_name="ms-marco-MiniLM-L-12-v2", cache_dir="./.cache/flashrank")


def rerank(query: str, docs: List[Document], top_n: int = 3) -> List[Document]:
    """Re-score les documents avec un cross-encoder et retourne les top_n pertinents.

    Les documents dont le score cross-encoder est inférieur à _SCORE_THRESHOLD sont
    exclus, même s'ils sont dans les top_n — cela évite d'afficher des sources
    hors-sujet quand le retrieval n'a pas trouvé de documents vraiment pertinents.

    Si FlashRank n'est pas disponible, retourne les docs dans l'ordre original.
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

        reranked = []
        for r in results[:top_n]:
            score = r.get("score", 0.0)
            if score >= _SCORE_THRESHOLD:
                doc = docs[r["id"]]
                doc.metadata["_rerank_score"] = round(float(score), 4)
                reranked.append(doc)

        return reranked

    except Exception:
        return docs[:top_n]
