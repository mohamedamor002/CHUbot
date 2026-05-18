"""
Cartographie des sous-départements RH du CHU d'Angers.
Source : Procès-verbal Phase 1 — Analyse des besoins (avril 2026).
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class Department:
    id: str
    name: str
    themes: List[str]
    keywords: List[str]
    escalation_email: Optional[str]
    escalation_label: str


# ── 5 sous-départements identifiés lors des ateliers ────────────────────────

DEPARTMENTS: List[Department] = [
    Department(
        id="recrutement",
        name="Recrutement & Gestion des Effectifs",
        themes=["concours", "mobilité interne"],
        keywords=[
            "concours", "postuler", "mobilité interne", "offre interne",
            "candidature", "éligible", "inscription concours", "conditions accès",
        ],
        escalation_email=None,
        escalation_label="Service Recrutement & Gestion des Effectifs",
    ),
    Department(
        id="remunerations",
        name="Service des Rémunérations",
        themes=["primes", "calendrier de paie", "remboursements transport", "bulletin de salaire"],
        keywords=[
            "prime", "salaire", "rémunération", "paie", "RIB", "bulletin",
            "remboursement transport", "abonnement train", "tramway", "bus",
            "indemnité journalière", "chômage", "attestation employeur",
        ],
        escalation_email=None,
        escalation_label="Service des Rémunérations",
    ),
    Department(
        id="gtt",
        name="Gestion du Temps de Travail",
        themes=["congés", "RTT", "absences", "missions", "missions hublot"],
        keywords=[
            "congé", "RTT", "absence", "temps de travail", "mission",
            "hublot", "droits", "justificatif", "autorisation d'absence",
        ],
        escalation_email=None,
        escalation_label="Service Gestion du Temps de Travail",
    ),
    Department(
        id="parcours",
        name="Parcours Professionnels & Accompagnement",
        themes=["formation", "protection sociale", "handicap", "RME"],
        keywords=[
            "formation", "plan de formation", "étude promotionnelle", "stage",
            "crèche", "CGOS", "action sociale", "arrêt maladie", "accident travail",
            "handicap", "FIPHFP", "aménagement poste", "reclassement", "PPR",
        ],
        escalation_email="Formation-Continue@chu-angers.fr",
        escalation_label="Service Parcours Professionnels & Accompagnement",
    ),
    Department(
        id="carrieres",
        name="Service des Carrières",
        themes=[
            "avancement de carrière", "positions statutaires", "retraites",
            "médailles", "chômage", "fin d'activité", "lignes directrices",
        ],
        keywords=[
            "avancement", "retraite", "CNRACL", "médaille", "chômage",
            "fin d'activité", "disponibilité", "position statutaire",
            "lignes directrices", "formulaire", "congé longue maladie",
        ],
        escalation_email="Carrieres@chu-angers.fr",
        escalation_label="Service des Carrières",
    ),
]

# ── Emails d'escalade par domaine (rapport § 6.3) ────────────────────────────

ESCALATION_CONTACTS = {
    "carrieres":        "Carrieres@chu-angers.fr",
    "formation":        "Formation-Continue@chu-angers.fr",
    "protection_sociale": "protectionsociale@chu-angers.fr",
    "rme_handicap":     "Retouretmaintien@chu-angers.fr",
}

# ── Sujets sensibles à exclure du périmètre (rapport § 6.2) ─────────────────

SENSITIVE_TOPICS = [
    "rémunération individuelle",
    "montant de mon salaire",
    "durée de mon contrat",
    "nature de mon contrat",
    "données personnelles",
]

# ── URLs de ressources documentaires identifiées (rapport § 5) ───────────────

DOCUMENTATION_URLS = [
    "https://www.agents-chu-angers.fr/faq-numeros-utiles/",
    "https://www.agents-chu-angers.fr/je-travaille-au-chu/droits-obligations-et-plus/ma-remuneration/",
    "https://www.agents-chu-angers.fr/formulaires-utiles/",
    "https://www.agents-chu-angers.fr/je-travaille-au-chu/droits-obligations-et-plus/mes-conges-absences-ou-disponibilites/",
    "https://www.agents-chu-angers.fr/je-travaille-au-chu/ma-carriere/ma-fin-d-activite/",
    "https://www.agents-chu-angers.fr/je-travaille-au-chu/ma-carriere/mon-avancement-de-carriere/",
    "https://www.agents-chu-angers.fr/je-travaille-au-chu/ma-carriere/ma-formation/",
    "https://www.agents-chu-angers.fr/je-travaille-au-chu/ma-protection-ma-sante/les-arrets-et-accidents/",
    "https://www.agents-chu-angers.fr/je-travaille-au-chu/ma-protection-ma-sante/handicap-au-travail/",
    "https://www.agents-chu-angers.fr/je-travaille-au-chu/vie-pratique/creches/",
    "https://www.agents-chu-angers.fr/je-travaille-au-chu/vie-sociale/cgos-action-sociale-et-culturelle/",
    "https://www.anfh.fr/",
    "https://www.cgos.info/",
    "https://www.cnracl.retraites.fr/",
]


def get_department_by_id(dept_id: str) -> Optional[Department]:
    return next((d for d in DEPARTMENTS if d.id == dept_id), None)


def detect_department(text: str) -> Optional[Department]:
    """Tente d'identifier le sous-département concerné par une question."""
    text_lower = text.lower()
    best: Optional[Department] = None
    best_score = 0
    for dept in DEPARTMENTS:
        score = sum(1 for kw in dept.keywords if kw.lower() in text_lower)
        if score > best_score:
            best_score = score
            best = dept
    return best if best_score > 0 else None
