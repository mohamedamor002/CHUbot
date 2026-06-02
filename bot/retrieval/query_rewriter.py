"""
Query rewriting — reformule la requête utilisateur en mots-clés précis avant le retrieval.

Technique RAG standard : au lieu de règles codées en dur, le LLM identifie
le sujet exact de la question et produit une requête de recherche optimisée,
évitant les confusions sémantiques (ex : "congé" ≠ "CET").
"""

import logging
from functools import lru_cache

from bot.config.settings import settings

log = logging.getLogger(__name__)

_REWRITE_PROMPT = """\
Tu es un assistant de recherche documentaire RH.
Reformule la question suivante en une requête de recherche précise (5 à 10 mots-clés),
ciblant EXACTEMENT le sujet demandé, sans l'élargir à des thèmes connexes.
Réponds UNIQUEMENT avec la requête reformulée. Aucune explication, aucune ponctuation finale.

Exemples :
- "comment prendre un congé ?" → "procédure demande congé annuel ordinaire pose absence"
- "je veux partir en retraite" → "départ retraite conditions âge démarches CNRACL"
- "c'est quoi la prime de service ?" → "prime de service montant calcul conditions versement"
- "comment alimenter mon CET ?" → "CET compte épargne-temps alimentation ouverture modalités"

Question : {question}
Requête :"""


@lru_cache(maxsize=1)
def _get_rewrite_llm():
    from langchain_ollama import ChatOllama
    auth = settings.ollama_auth_headers
    return ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        client_kwargs={"headers": auth} if auth else {},
        temperature=0.0,
        num_predict=40,   # suffisant pour 5-10 mots-clés
        num_ctx=512,
    )


async def rewrite_query(question: str) -> str:
    """Reformule la question en requête de recherche précise via LLM.

    Retourne la requête reformulée, ou la question originale en cas d'échec.
    """
    try:
        llm = _get_rewrite_llm()
        prompt = _REWRITE_PROMPT.format(question=question)
        msg = await llm.ainvoke(prompt)
        rewritten = (msg.content or "").strip().strip('"').strip("'")
        if rewritten:
            log.debug("query rewrite: '%s' → '%s'", question[:60], rewritten[:80])
            return rewritten
    except Exception as e:
        log.warning("query rewrite failed, using original: %s", e)
    return question
