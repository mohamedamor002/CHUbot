"""
Pré-traitement des requêtes utilisateur avant retrieval.

Deux transformations appliquées :
  1. Expansion des acronymes RH → améliore la similarité sémantique avec les docs
  2. Query rewriting via LLM → reformule en mots-clés précis, évite les confusions sémantiques
  3. Détection du sous-département → filtre les chunks au retrieval
"""

import re
from typing import Optional, Tuple

from bot.config.departments import Department, detect_department


# ── Acronymes RH du CHU d'Angers (rapport Phase 1) ───────────────────────────

_ACRONYMS: dict[str, str] = {
    # Temps de travail
    "RTT":    "Réduction du Temps de Travail (RTT)",
    "CET":    "Compte Épargne-Temps (CET)",
    "GTT":    "Gestion du Temps de Travail (GTT)",
    "TPT":    "Temps Partiel Thérapeutique (TPT)",
    # Formation & parcours
    "CPF":    "Compte Personnel de Formation (CPF)",
    "CEP":    "Conseil en Évolution Professionnelle (CEP)",
    "ANFH":   "Association Nationale pour la Formation permanente du personnel Hospitalier (ANFH)",
    "RME":    "Retour et Maintien dans l'Emploi (RME)",
    "PPR":    "Période de Préparation au Reclassement (PPR)",
    # Protection sociale & handicap
    "CGOS":   "Comité de Gestion des Œuvres Sociales (CGOS)",
    "FIPHFP": "Fonds pour l'Insertion des Personnes Handicapées dans la Fonction Publique (FIPHFP)",
    "AT":     "Accident du Travail (AT)",
    # Carrières & retraite
    "CNRACL": "Caisse Nationale de Retraites des Agents des Collectivités Locales (CNRACL)",
    # Institutions
    "DRH":    "Direction des Ressources Humaines (DRH)",
    "CHU":    "Centre Hospitalier Universitaire (CHU)",
    "FPH":    "Fonction Publique Hospitalière (FPH)",
    "PNM":    "Personnel Non Médical (PNM)",
    "PM":     "Personnel Médical (PM)",
}

# Pré-compile les patterns pour la performance
_ACRONYM_PATTERNS = {
    re.compile(r'\b' + re.escape(acr) + r'\b'): expansion
    for acr, expansion in _ACRONYMS.items()
}


def expand_acronyms(text: str) -> str:
    """Remplace les acronymes RH par leur forme complète.

    'Mon RTT' → 'Mon Réduction du Temps de Travail (RTT)'
    """
    result = text
    for pattern, expansion in _ACRONYM_PATTERNS.items():
        result = pattern.sub(expansion, result)
    return result


async def preprocess_query(question: str) -> Tuple[str, Optional[Department]]:
    """Prépare la requête pour le retrieval.

    Returns:
        enriched_question : requête reformulée par le LLM (acronymes expansés + rewriting)
        detected_dept     : sous-département détecté (None si non identifié)
    """
    from bot.retrieval.query_rewriter import rewrite_query

    expanded = expand_acronyms(question)
    enriched = await rewrite_query(expanded)
    dept = detect_department(question)
    return enriched, dept
