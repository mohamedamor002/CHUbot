"""
Nettoyage du texte brut extrait depuis PDF, DOCX et pages web.

Les extracteurs (PyMuPDF, trafilatura) produisent souvent :
  - Mots coupés en fin de ligne : "infor-\nmation"
  - Numéros de page isolés : "\n12\n"
  - En-têtes/pieds de page répétés sur chaque page
  - Espaces multiples, tabulations, caractères de contrôle
"""

import re


# ── Patterns de nettoyage ────────────────────────────────────────────────────

# Mots coupés par un tiret en fin de ligne (PDF)
_HYPHEN_BREAK = re.compile(r'(\w)-\n(\w)')

# Numéros de page isolés sur une ligne (1 à 4 chiffres seuls)
_PAGE_NUMBER = re.compile(r'\n\s*\d{1,4}\s*\n')

# En-têtes/pieds CHU répétés : "CHU d'Angers — DRH — 2024", "Page X sur Y"
_CHU_HEADER = re.compile(
    r'\n[^\n]{0,80}(?:CHU|DRH|chu-angers\.fr)[^\n]{0,80}\n',
    re.IGNORECASE,
)
_PAGE_X_OF_Y = re.compile(r'\n[^\n]*\bpage\s+\d+\s+(?:sur|of|\/)\s+\d+[^\n]*\n', re.IGNORECASE)

# Lignes très courtes répétitives (artefacts de tableau PDF)
_SINGLE_CHAR_LINES = re.compile(r'\n[|_\-=]{1,3}\n')

# Espaces multiples / tabulations (hors saut de ligne)
_MULTI_SPACE = re.compile(r'[ \t]{2,}')

# Plus de 2 sauts de ligne consécutifs
_EXCESS_NEWLINES = re.compile(r'\n{3,}')


def clean_text(text: str) -> str:
    """Nettoie le texte brut extrait d'un document.

    Opérations dans l'ordre :
      1. Normalise les fins de ligne (\\r\\n → \\n)
      2. Supprime les sauts de page (\\f)
      3. Recolle les mots coupés par tiret en fin de ligne
      4. Supprime les numéros de page isolés
      5. Supprime les en-têtes/pieds CHU répétés
      6. Supprime les lignes parasites (séparateurs seuls)
      7. Normalise les espaces multiples
      8. Réduit les lignes vides excessives
    """
    # 1 & 2
    text = text.replace('\r\n', '\n').replace('\r', '\n').replace('\f', '\n')

    # 3 — recollage des mots coupés : "infor-\nmation" → "information"
    text = _HYPHEN_BREAK.sub(r'\1\2', text)

    # 4
    text = _PAGE_NUMBER.sub('\n', text)

    # 5
    text = _CHU_HEADER.sub('\n', text)
    text = _PAGE_X_OF_Y.sub('\n', text)

    # 6
    text = _SINGLE_CHAR_LINES.sub('\n', text)

    # 7
    text = _MULTI_SPACE.sub(' ', text)

    # 8
    text = _EXCESS_NEWLINES.sub('\n\n', text)

    return text.strip()
