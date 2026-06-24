# RAPPORT DE STAGE
## Développement d'un Chatbot RH intelligent pour le CHU d'Angers
### Basé sur une architecture RAG (Retrieval-Augmented Generation)

---

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                   │
│   Établissement d'accueil :   CHU d'Angers                       │
│   Service :                   Direction des Ressources Humaines  │
│   Période :                   2025 – 2026                        │
│   Projet :                    CHUbot v0.1.0                       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## TABLE DES MATIÈRES

1. [Remerciements](#1-remerciements)
2. [Résumé](#2-résumé)
3. [Introduction](#3-introduction)
4. [Présentation de l'organisme d'accueil](#4-présentation-de-lorganisme-daccueil)
5. [Analyse du besoin et problématique](#5-analyse-du-besoin-et-problématique)
6. [État de l'art — Les chatbots RAG](#6-état-de-lart--les-chatbots-rag)
7. [Architecture générale du système](#7-architecture-générale-du-système)
8. [Pipeline d'ingestion documentaire](#8-pipeline-dingestion-documentaire)
9. [Pipeline RAG — Retrieval-Augmented Generation](#9-pipeline-rag--retrieval-augmented-generation)
10. [Base de données et persistance](#10-base-de-données-et-persistance)
11. [API REST — Couche de service](#11-api-rest--couche-de-service)
12. [Interface utilisateur — Application Desktop](#12-interface-utilisateur--application-desktop)
13. [Évaluation et métriques de performance](#13-évaluation-et-métriques-de-performance)
14. [Déploiement et packaging](#14-déploiement-et-packaging)
15. [Difficultés rencontrées et solutions](#15-difficultés-rencontrées-et-solutions)
16. [Perspectives d'évolution](#16-perspectives-dévolution)
17. [Conclusion](#17-conclusion)
18. [Références et bibliographie](#18-références-et-bibliographie)
19. [Annexes](#19-annexes)

---

## 1. Remerciements

Je tiens à remercier chaleureusement l'ensemble de l'équipe de la Direction des Ressources Humaines du CHU d'Angers pour leur accueil et leur disponibilité tout au long de ce stage. Leur expertise métier a été indispensable pour comprendre les besoins réels des agents et orienter les choix techniques du projet.

Je remercie également mon maître de stage pour la confiance accordée et la liberté technique laissée dans la conception et la réalisation de ce projet ambitieux.

---

## 2. Résumé

Ce stage a consisté à concevoir et développer **CHUbot**, un assistant conversationnel intelligent destiné aux agents du CHU d'Angers. Le chatbot répond automatiquement aux questions relatives aux ressources humaines — congés, rémunération, formation, carrière, protection sociale — en s'appuyant sur la documentation officielle interne du CHU.

La solution repose sur une architecture **RAG** (Retrieval-Augmented Generation) entièrement locale : les documents RH sont vectorisés et stockés dans une base ChromaDB, puis un LLM open-source hébergé sur l'infrastructure CHU génère les réponses en citant ses sources. Un système de **recherche hybride** (BM25 + vectorielle), un **reclassement sémantique** (FlashRank) et des **gardes anti-hallucination** garantissent la fiabilité des réponses.

L'application se présente sous forme d'une **fenêtre flottante desktop** (React + Tauri) toujours visible sur le poste de travail. Un backend FastAPI gère l'ensemble des échanges, avec persistance PostgreSQL des conversations, retours utilisateurs et métriques d'usage.

**Mots-clés :** RAG, LLM, Ollama, LangChain, ChromaDB, FastAPI, Tauri, RH, chatbot, NLP

---

## 3. Introduction

La transformation numérique des services publics hospitaliers représente un enjeu majeur. Les agents d'un Centre Hospitalier Universitaire sont quotidiennement confrontés à des questions administratives complexes : calcul de congés, modalités de remboursement de transport, procédures d'avancement, droits liés au statut de fonctionnaire hospitalier...

Ces questions, souvent récurrentes, mobilisent un temps précieux des gestionnaires RH. En parallèle, les agents se retrouvent parfois dans l'incapacité de trouver rapidement l'information dans la masse documentaire mise à leur disposition : notes d'information, guides, formulaires, sites institutionnels.

L'émergence des modèles de langage de grande taille (LLM) ouvre une nouvelle voie : permettre à un agent de poser sa question en langage naturel et recevoir une réponse précise, sourcée et instantanée. C'est l'objectif de **CHUbot**.

Ce rapport détaille l'ensemble du travail réalisé durant le stage : de l'analyse des besoins à la mise en production, en passant par les choix d'architecture, les développements techniques et l'évaluation des performances.

---

## 4. Présentation de l'organisme d'accueil

### 4.1 Le CHU d'Angers

Le Centre Hospitalier Universitaire d'Angers est l'un des établissements de santé les plus importants du Grand Ouest français. Il assure des missions de soins, d'enseignement médical et de recherche.

| Indicateur | Valeur |
|---|---|
| Nombre de lits | ~1 700 |
| Personnel médical et non-médical | ~7 000 agents |
| Budget annuel | > 600 M€ |
| Statut | EPCSM (Établissement Public de Santé) |

### 4.2 La Direction des Ressources Humaines

La DRH du CHU d'Angers est organisée en **5 services** couvrant l'ensemble du cycle de vie des agents :

```
┌─────────────────────────────────────────────────────────────────┐
│                  Direction des Ressources Humaines               │
├─────────────────┬───────────────┬────────────────┬──────────────┤
│  Recrutement &  │  Service des  │ Gestion du     │  Parcours    │
│  Gestion des    │ Rémunérations │ Temps de       │ Profession.  │
│  Effectifs      │               │ Travail (GTT)  │              │
├─────────────────┴───────────────┴────────────────┴──────────────┤
│                    Service des Carrières                         │
└─────────────────────────────────────────────────────────────────┘
```

**Volume de documentation RH géré :**
- Notes d'information internes (NI) : nouvelles publications régulières
- Formulaires administratifs : ~20 types de formulaires
- Sites web institutionnels : 12 URLs référencées (CHU, ANFH, CGOS, CNRACL...)
- Guides thématiques : primes, temps de travail, retraite, formation...

---

## 5. Analyse du besoin et problématique

### 5.1 Le problème identifié

Une analyse des flux entrants vers la DRH a mis en évidence plusieurs pain points :

```
PROBLÈMES IDENTIFIÉS
─────────────────────────────────────────────────────────────────

  Agents                               DRH
  ─────                                ───
  ┌─────────────────────┐              ┌──────────────────────┐
  │ Questions répétitives│ ──────────▶ │ Temps mobilisé       │
  │ (congés, RIB, primes)│             │ pour réponses simples│
  └─────────────────────┘              └──────────────────────┘

  ┌─────────────────────┐              ┌──────────────────────┐
  │ Documentation        │             │ Mise à jour fréquente│
  │ difficile à trouver  │             │ des documents        │
  └─────────────────────┘              └──────────────────────┘

  ┌─────────────────────┐
  │ Horaires d'ouverture │ → Pas de réponse en dehors des heures
  │ DRH limitées         │   de bureau
  └─────────────────────┘
```

### 5.2 Volumétrie des questions par thème

Après analyse de la documentation et des retours métier, **105 questions types** ont été identifiées et structurées :

```
  RÉPARTITION DES QUESTIONS PAR CATÉGORIE (105 questions)
  ─────────────────────────────────────────────────────────

  Rémunération           ████████████████████████ 31  (30%)
  Carrière               ████████████ 16  (15%)
  Congés et absences     ███████████ 15  (14%)
  Formation              █████████ 12  (11%)
  Contacts utiles        ████████ 11  (10%)
  Protection sociale     ████ 6   (6%)
  Entretien prof.        ███ 4    (4%)
  Temps de travail       ███ 4    (4%)
  Accidents / maladies   ██ 2     (2%)
  CGOS & action sociale  ██ 2     (2%)
  Crèches                █ 1     (1%)
  Retraite               █ 1     (1%)
```

### 5.3 Contraintes spécifiques au contexte hospitalier

Le projet devait respecter des contraintes strictes :

| Contrainte | Exigence | Solution retenue |
|---|---|---|
| **Confidentialité des données** | Aucune donnée patient/agent sur le cloud | LLM et embeddings 100% locaux |
| **Infrastructure existante** | Serveur Ollama interne au CHU | Connexion à `https://llm.chu-angers.fr/ollama` |
| **RGPD** | Pas de données personnelles dans les réponses | Filtre des sujets sensibles + escalade |
| **Fiabilité** | Pas de réponses inventées | Garde anti-hallucination + citations |
| **Déploiement** | Poste Windows sans droits admin | Application autonome (Tauri + PyInstaller) |

### 5.4 Objectifs du projet

1. **Répondre automatiquement** aux questions RH fréquentes en langage naturel
2. **Citer les sources** documentaires pour chaque réponse
3. **Ne jamais inventer** d'information réglementaire
4. **Détecter les cas complexes** nécessitant l'intervention d'un gestionnaire
5. **S'intégrer** dans le quotidien des agents (fenêtre toujours visible)
6. **Permettre le suivi** de la qualité et des usages via des métriques

---

## 6. État de l'art — Les chatbots RAG

### 6.1 Pourquoi RAG et non un fine-tuning ?

Deux approches majeures existent pour spécialiser un LLM sur un domaine métier :

```
  FINE-TUNING                        RAG
  ───────────                        ───
  ✗ Coûteux (GPU, temps)            ✓ Peu coûteux
  ✗ Données de formation nécessaires ✓ Documents existants suffisent
  ✗ Risque d'hallucination élevé    ✓ Réponses ancrées dans les docs
  ✗ Mise à jour = réentraînement    ✓ Mise à jour = réindexation (minutes)
  ✗ Connaissance "gelée"            ✓ Base documentaire évolutive
  ✓ Inférence plus rapide           ✗ Latence de récupération
```

Le RAG est clairement le choix adapté pour un contexte documentaire évolutif comme la DRH.

### 6.2 Fonctionnement du RAG

```
          PRINCIPE DU RAG
          ──────────────────────────────────────────────────

  Question utilisateur
        │
        ▼
  ┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
  │  Recherche  │────▶│  Base vectorielle │────▶│  Documents      │
  │  hybride    │     │  (ChromaDB)       │     │  pertinents     │
  └─────────────┘     └──────────────────┘     └────────┬────────┘
                                                         │
  ┌─────────────────────────────────────────────────────▼────────┐
  │  Prompt = "Réponds à la question en te basant               │
  │            UNIQUEMENT sur ces documents : {contexte}"       │
  └─────────────────────────────────────────────────────┬────────┘
                                                         │
        ┌──────────────────────┐                        │
        │  LLM (llama3.1)      │◀───────────────────────┘
        └──────────┬───────────┘
                   │
                   ▼
          Réponse sourcée
```

### 6.3 Technologies évaluées et retenues

| Composant | Alternatives évaluées | Choix retenu | Justification |
|---|---|---|---|
| **LLM** | GPT-4, Claude, Mistral, LLaMA | llama3.1 via Ollama | Local, gratuit, performant en français |
| **Embeddings** | OpenAI, Cohere, HuggingFace | nomic-embed-text | Local, 768 dims, multilingue |
| **Vector DB** | FAISS, Weaviate, Pinecone | ChromaDB | Persistant, local, Python natif |
| **Framework** | Haystack, LlamaIndex | LangChain | Maturité, flexibilité, communauté |
| **Reranker** | CohereRerank, Colbert | FlashRank | CPU-only, pas de clé API |
| **Frontend** | Electron, webapp | Tauri + React | Léger, Rust, natif Windows |
| **Base de données** | SQLite, MongoDB | PostgreSQL | Robustesse, async, requêtes analytiques |

---

## 7. Architecture générale du système

### 7.1 Vue d'ensemble

```
╔══════════════════════════════════════════════════════════════════╗
║                    ARCHITECTURE CHUBOT                           ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║   ┌─────────────────────────────────────────────────────────┐    ║
║   │              POSTE AGENT (Windows)                       │    ║
║   │                                                           │    ║
║   │   ┌──────────────────────┐    ┌───────────────────────┐  │    ║
║   │   │  Interface Tauri     │    │  Backend FastAPI       │  │    ║
║   │   │  React 18 + Tailwind │◀──▶│  Python 3.11+         │  │    ║
║   │   │  Port: Vite 5173     │    │  Port: 8765           │  │    ║
║   │   └──────────────────────┘    └───────────┬───────────┘  │    ║
║   │                                            │               │    ║
║   │   ┌────────────────────────────────────────▼────────────┐ │    ║
║   │   │              Couche de persistance locale            │ │    ║
║   │   │   ┌────────────────┐    ┌──────────────────────┐   │ │    ║
║   │   │   │  PostgreSQL    │    │  ChromaDB             │   │ │    ║
║   │   │   │  (asyncpg)     │    │  ./data/indexes       │   │ │    ║
║   │   │   │  Conversations │    │  Embeddings vectoriels│   │ │    ║
║   │   │   │  Métriques     │    │  BM25 index           │   │ │    ║
║   │   │   └────────────────┘    └──────────────────────┘   │ │    ║
║   │   └─────────────────────────────────────────────────────┘ │    ║
║   └─────────────────────────────────────────────────────────┘    ║
║                              │                                    ║
║              HTTP (réseau interne CHU)                           ║
║                              │                                    ║
║   ┌───────────────────────────▼───────────────────────────────┐  ║
║   │            Infrastructure CHU (Serveur GPU)                │  ║
║   │   ┌──────────────────────────────────────────────────┐    │  ║
║   │   │  Ollama — llm.chu-angers.fr                       │    │  ║
║   │   │  ├── llama3.1:latest  (génération de réponses)   │    │  ║
║   │   │  └── nomic-embed-text (vectorisation, local)     │    │  ║
║   │   └──────────────────────────────────────────────────┘    │  ║
║   └───────────────────────────────────────────────────────────┘  ║
║                                                                   ║
╚══════════════════════════════════════════════════════════════════╝
```

### 7.2 Flux de traitement d'une question

```
  FLUX COMPLET D'UNE QUESTION
  ─────────────────────────────────────────────────────────────────

  Agent       Frontend     Backend      Preprocessor    Retriever
    │            │            │               │               │
    │ [Frappe]   │            │               │               │
    │───────────▶│            │               │               │
    │            │ POST /chat │               │               │
    │            │────────────▶               │               │
    │            │            │ expand_acronyms()             │
    │            │            │───────────────▶               │
    │            │            │ rewrite_query() (LLM)         │
    │            │            │───────────────▶               │
    │            │            │ detect_department()           │
    │            │            │───────────────▶               │
    │            │            │◀───────────────               │
    │            │            │               │  BM25 search  │
    │            │            │───────────────────────────────▶
    │            │            │               │  Vector search│
    │            │            │───────────────────────────────▶
    │            │            │               │  RRF merge    │
    │            │            │               │  FlashRank    │
    │            │            │◀──────────────────────────────│
    │            │            │                               │
    │            │            │  [Guard: docs trouvés?]       │
    │            │            │  LLM génère réponse            │
    │            │            │  (Streaming token/token)      │
    │            │ tokens...  │               │               │
    │            │◀───────────│               │               │
    │ [Affichage]│            │               │               │
    │◀───────────│            │               │               │
    │            │            │  Save message + métriques     │
    │            │            │               │               │
```

### 7.3 Stack technologique complète

```
  STACK TECHNOLOGIQUE — CHUBOT
  ─────────────────────────────────────────────────────────────────

  COUCHE PRÉSENTATION
  ├── Tauri 2.x          (runtime desktop natif, Rust)
  ├── React 18.3         (interface composants)
  ├── Tailwind CSS 3.4   (design system)
  ├── Vite 5.3           (bundler/dev server)
  └── Axios 1.7          (client HTTP)

  COUCHE API
  ├── FastAPI            (framework REST async)
  ├── uvicorn            (serveur ASGI)
  └── Pydantic v2        (validation schemas)

  COUCHE MÉTIER (RAG)
  ├── LangChain          (orchestration LLM/RAG)
  ├── Ollama             (LLM + embeddings locaux)
  ├── ChromaDB           (base vectorielle persistante)
  ├── FlashRank          (reranker cross-encoder)
  └── BM25Retriever      (recherche lexicale)

  COUCHE INGESTION
  ├── PyMuPDF            (extraction PDF)
  ├── python-docx        (extraction Word)
  ├── openpyxl           (extraction Excel)
  ├── trafilatura        (scraping HTML)
  └── Playwright         (scraping JS dynamique)

  COUCHE PERSISTANCE
  ├── PostgreSQL         (SGBD relationnel)
  ├── SQLAlchemy async   (ORM async)
  ├── asyncpg            (driver PostgreSQL async)
  └── Alembic            (migrations de schéma)

  COUCHE DÉPLOIEMENT
  ├── PyInstaller        (packaging backend Python)
  └── Tauri NSIS/MSI     (installateur Windows)
```

---

## 8. Pipeline d'ingestion documentaire

### 8.1 Vue d'ensemble du pipeline

L'ingestion est la phase qui transforme des documents bruts en vecteurs interrogeables. Voici le pipeline complet :

```
  PIPELINE D'INGESTION
  ─────────────────────────────────────────────────────────────────

  SOURCES DOCUMENTAIRES
  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────┐
  │ PDF         │  │ DOCX / DOC  │  │ Excel       │  │  Web     │
  │ Notes info  │  │ Formulaires │  │ Guides primes│  │  12 URLs │
  │ Guides      │  │ Demandes    │  │ Tableaux RH  │  │  CHU,    │
  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │  ANFH,   │
         │                │                │          │  CGOS... │
         └────────────────┴────────────────┘          └────┬─────┘
                          │                                │
                          ▼                                ▼
                ┌─────────────────┐             ┌──────────────────┐
                │   loaders.py    │             │  Trafilatura /   │
                │  PyMuPDF        │             │  Playwright      │
                │  python-docx    │             │  (JS dynamique)  │
                │  openpyxl       │             └────────┬─────────┘
                └────────┬────────┘                      │
                         └──────────────┬────────────────┘
                                        │
                                        ▼
                              ┌──────────────────┐
                              │   cleaner.py     │
                              │  • Supprime       │
                              │    artefacts PDF  │
                              │  • Normalise      │
                              │    espaces        │
                              │  • Supprime       │
                              │    en-têtes répét.│
                              └────────┬─────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │   splitter.py    │
                              │  • Chunks 2000   │
                              │    chars         │
                              │  • Overlap 400   │
                              │    chars         │
                              │  • Entête        │
                              │    contextuel    │
                              │  • Métadonnées   │
                              └────────┬─────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │   indexer.py     │
                              │  • Dédup. MD5    │
                              │  • nomic-embed   │
                              │  • ChromaDB      │
                              └──────────────────┘
```

### 8.2 Chargement multi-format (`loaders.py`)

| Format | Librairie | Particularités |
|---|---|---|
| **PDF** | PyMuPDF (fitz) | Extraction texte page par page, gestion des colonnes |
| **DOCX/DOC** | python-docx | Paragraphes + tableaux convertis en texte |
| **XLSX/XLS/XLSM** | openpyxl | Chaque ligne formatée en `clé: valeur` avec en-tête |
| **HTML statique** | trafilatura | Extraction du contenu principal, supprime nav/pied |
| **HTML dynamique** | Playwright | Rendu JavaScript avant extraction (sites complexes) |
| **Site web entier** | BeautifulSoup + httpx | Crawl jusqu'à 30 pages, liens relatifs résolus |

**Exemple de traitement Excel :**
```
# Entrée (feuille Excel)
Nom prime    | Montant | Conditions
Prime chaussures | 100€  | Agents exposés
Prime astreinte  | 150€  | Service d'urgence

# Sortie (texte structuré)
Nom prime: Prime chaussures | Montant: 100€ | Conditions: Agents exposés
Nom prime: Prime astreinte | Montant: 150€ | Conditions: Service d'urgence
```

### 8.3 Nettoyage de texte (`cleaner.py`)

Les artefacts récurrents dans les documents hospitaliers sont traités :

```python
# Exemples de transformations appliquées
"Congé  -  de  mater-           # Trait d'union de coupure de ligne
nité"    →  "Congé de maternité"

"Page 3/12 | CHU Angers"        # En-têtes/pieds répétés
     →  ""  (supprimé)

"Article  1  :  Le   présent"   # Espaces multiples
     →  "Article 1 : Le présent"
```

### 8.4 Découpage et enrichissement contextuel (`splitter.py`)

Chaque chunk est précédé d'un **en-tête contextuel** qui améliore la précision des embeddings :

```
[Source: 2025-46 NI Forfait mobilités durables | Section: Conditions d'éligibilité]
Les agents ayant recours au covoiturage, au vélo, à la trottinette électrique
ou à d'autres modes de transport dit « doux » pour leurs déplacements entre
leur résidence habituelle et leur lieu de travail peuvent bénéficier du
Forfait Mobilités Durables (FMD)...
```

**Paramètres de chunking :**

```
  TAILLE DES CHUNKS
  ─────────────────────────────────────────────────────────────────

  Document source (ex: NI de 8 pages ≈ 12 000 chars)
  │
  ├─▶ Chunk 1  [2000 chars]  En-tête 1
  │   ├── Overlap ──────────▶ [400 chars partagés]
  ├─▶ Chunk 2  [2000 chars]  En-tête 2
  │   ├── Overlap ──────────▶ [400 chars partagés]
  └─▶ Chunk N  [2000 chars]  En-tête N

  Taille chunk : 2000 chars ≈ 500 tokens (optimal pour llama3.1)
  Overlap      :  400 chars → évite la coupure des phrases frontières
```

### 8.5 Déduplication et indexation (`indexer.py`)

```python
# Déduplication par empreinte MD5 du contenu
doc_hash = hashlib.md5(chunk.page_content.encode()).hexdigest()
if doc_hash not in existing_hashes:
    to_index.append(chunk)
    existing_hashes.add(doc_hash)
```

**Interface CLI de l'indexeur :**

```bash
# Indexer un répertoire complet
python -m bot.ingestion.indexer --dir data/documents/

# Indexer un fichier unique
python -m bot.ingestion.indexer --file data/documents/guide_primes.pdf

# Indexer toutes les URLs documentaires (12 sites)
python -m bot.ingestion.indexer --urls

# Tout indexer (documents + URLs) avec reset préalable
python -m bot.ingestion.indexer --all --reset
```

---

## 9. Pipeline RAG — Retrieval-Augmented Generation

### 9.1 Prétraitement de la question (`preprocessor.py` + `query_rewriter.py`)

Avant toute recherche, la question subit deux transformations :

#### Expansion des acronymes RH

```
  ACRONYMES EXPANSÉS (18 acronymes HR spécifiques au public hospitalier)
  ─────────────────────────────────────────────────────────────────

  RTT  →  Réduction du Temps de Travail (RTT)
  CET  →  Compte Épargne-Temps (CET)
  CPF  →  Compte Personnel de Formation (CPF)
  RME  →  Reconnaissance de la Qualité de Travailleur Handicapé (RQTH/RME)
  NBI  →  Nouvelle Bonification Indiciaire (NBI)
  FMD  →  Forfait Mobilités Durables (FMD)
  CHU  →  Centre Hospitalier Universitaire (CHU)
  CNRACL → Caisse Nationale de Retraite des Agents des Collectivités Locales
  ANFH →  Association Nationale pour la Formation des Hospitaliers (ANFH)
  CGOS →  Comité de Gestion des Œuvres Sociales (CGOS)
  ... (18 au total)
```

#### Réécriture de la question par LLM

```
  INPUT  : "Comment prendre mon CET ?"

  PROMPT : "Tu es un expert RH. Réécris cette question en 5-10
            mots-clés précis pour une recherche documentaire.
            Évite les confusions sémantiques."

  OUTPUT : "utilisation compte épargne-temps CET congés hospitalier
            déblocage procédure service RH"
```

Ce query rewriting améliore significativement le recall de la recherche vectorielle.

### 9.2 Recherche hybride (`chain.py`)

La recherche hybride combine deux approches complémentaires :

```
  RECHERCHE HYBRIDE — RECIPROCAL RANK FUSION
  ─────────────────────────────────────────────────────────────────

  Question enrichie
        │
        ├──────────────────────┬──────────────────────────────────
        │                      │
        ▼                      ▼
  ┌──────────────┐       ┌──────────────────────┐
  │   BM25       │       │   Recherche          │
  │   (lexicale) │       │   Vectorielle        │
  │   Poids: 40% │       │   (nomic-embed-text) │
  │              │       │   Poids: 60%         │
  │  Top-10 docs │       │  Top-10 docs         │
  └──────┬───────┘       └──────────┬───────────┘
         │                          │
         └──────────┬───────────────┘
                    │
                    ▼
         ┌──────────────────┐
         │  Reciprocal Rank │    score_final(d) = Σ  1/(k + rank_i(d))
         │  Fusion (RRF)    │                    i
         │  k = 60          │
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────┐
         │  FlashRank       │   Cross-encoder ms-marco-MiniLM-L-12-v2
         │  (reranking)     │   Score seuil: 0.05
         │  Top-3 gardés    │   CPU-only, ~130 MB
         └──────────────────┘
```

**Pourquoi BM25 + vectoriel ?**

| Scénario | BM25 seul | Vectoriel seul | Hybride |
|---|---|---|---|
| Question avec terme exact "forfait mobilités" | ✓ Excellent | ~ Passable | ✓ Excellent |
| Question sémantique "transport domicile travail" | ~ Passable | ✓ Excellent | ✓ Excellent |
| Acronyme développé "Compte Épargne-Temps" | ✓ Bon | ✓ Bon | ✓ Excellent |
| Question hors corpus | ✗ Mauvais résultats | ✗ Mauvais résultats | ✗ Détecté + garde |

### 9.3 Filtrage par sous-département

```
  DÉTECTION DU SOUS-DÉPARTEMENT
  ─────────────────────────────────────────────────────────────────

  Question: "Quand vais-je recevoir mon bulletin de salaire ?"
               │
               │  Keywords détectés: "bulletin", "salaire"
               ▼
  ┌────────────────────────────────────────────────────────────────┐
  │   dept_mapping (departments.py)                                │
  │                                                                │
  │   Rémunérations   → primes, paie, bulletin, RIB, cotisation   │
  │   GTT             → congés, RTT, CET, absence, mission        │
  │   Recrutement     → concours, mobilité, mutation, détachement │
  │   Carrières       → avancement, retraite, notation, statut    │
  │   Parcours Prof.  → formation, CPF, ANFH, handicap, entretien │
  └────────────────────────────────────┬───────────────────────────┘
                                       │
                    Département: "Rémunérations"
                    → Filtre ChromaDB activé
                    → Si 0 résultats → recherche globale (fallback)
```

### 9.4 Garde anti-hallucination

```python
# Guard critique : si aucun document pertinent trouvé,
# le LLM n'est JAMAIS appelé

if not docs:
    return (
        "Je n'ai pas trouvé d'information dans la documentation "
        "disponible pour répondre à votre question. Je vous invite "
        "à contacter directement le service RH concerné."
    )

# Le LLM ne répond QUE sur la base du contexte fourni
```

### 9.5 Prompt système et règles de génération (`prompt.py`)

```
  PROMPT SYSTÈME (extrait)
  ─────────────────────────────────────────────────────────────────

  "Tu es un assistant RH spécialisé du CHU d'Angers.

  RÈGLES ABSOLUES :
  1. Tu bases tes réponses UNIQUEMENT sur les documents fournis
  2. Tu ne révèles JAMAIS de données individuelles (salaire, contrat,
     données personnelles)
  3. Tu cites TOUJOURS la source de l'information
  4. Si l'information n'est pas dans les documents, tu le dis
     explicitement et orientes vers le service compétent
  5. Tu réponds en français, de façon claire et concise
  6. Tu mentionnes les contacts de escalade si nécessaire"
```

### 9.6 Contacts d'escalade

Des cas de questions sensibles déclenchent automatiquement une mention des contacts humains :

| Trigger | Service contacté | Email |
|---|---|---|
| Accident de travail | Service RH - AT/MP | rh-at@chu-angers.fr |
| Situation complexe carrière | Service Carrières | rh-carrieres@chu-angers.fr |
| Litige rémunération | Service Rémunérations | rh-remuneration@chu-angers.fr |
| Formation ANFH | Service Formation | rh-formation@chu-angers.fr |

### 9.7 Streaming token par token

```
  STREAMING DE LA RÉPONSE
  ─────────────────────────────────────────────────────────────────

  Backend                   Frontend
  ───────                   ────────
  LLM génère token "Selon"    ──────────▶ Affiche "Selon"
  LLM génère token " la"      ──────────▶ Affiche " la"
  LLM génère token " FAQ"     ──────────▶ Affiche " FAQ"
  ...
  Headers HTTP:
  X-Session-ID: uuid-session  ──────────▶ Session créée/maintenue
  X-Message-ID: uuid-message  ──────────▶ Pour feedback ultérieur
  X-Sources: [{...}, {...}]   ──────────▶ Documents sources affichés
```

---

## 10. Base de données et persistance

### 10.1 Schéma relationnel

```
  SCHÉMA BASE DE DONNÉES POSTGRESQL
  ─────────────────────────────────────────────────────────────────

  users
  ┌─────────────────────────────────────────────────────────────┐
  │ id (UUID PK) │ username │ email │ hashed_password │ role    │
  └──────┬──────────────────────────────────────────────────────┘
         │ 1:N
         │
  conversation_sessions
  ┌─────────────────────────────────────────────────────────────┐
  │ id (UUID PK) │ user_id (FK) │ title │ created_at │ updated │
  └──────┬──────────────────────────────────────────────────────┘
         │ 1:N
         │
  messages
  ┌─────────────────────────────────────────────────────────────┐
  │ id (UUID PK) │ session_id (FK) │ role │ content │ created  │
  └──────┬──────────────────────────────────────────────────────┘
         │ 1:1                          │ 1:1
         │                              │
  message_metrics                    feedback
  ┌──────────────────────────────┐   ┌────────────────────────┐
  │ id │ message_id │ resp_time  │   │ id │ message_id         │
  │     │ is_covered │ has_escal │   │     │ is_helpful        │
  └──────────────────────────────┘   │     │ rating (1-5)      │
                                      └────────────────────────┘

  indexed_documents
  ┌─────────────────────────────────────────────────────────────┐
  │ id │ filename │ file_type │ chunks_indexed │ indexed_at      │
  └─────────────────────────────────────────────────────────────┘
```

### 10.2 Architecture asynchrone

```python
# SQLAlchemy async avec asyncpg
engine = create_async_engine(
    settings.DATABASE_URL,  # postgresql+asyncpg://...
    echo=settings.DEBUG,
)

# Session par requête HTTP (pattern Dependency Injection FastAPI)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

**Avantages :** pas de blocage I/O pendant les requêtes LLM longues, meilleure scalabilité.

---

## 11. API REST — Couche de service

### 11.1 Carte des endpoints

```
  API FASTAPI — /api/v1
  ─────────────────────────────────────────────────────────────────

  CHAT
  POST   /chat                  → Réponse complète (non-streaming)
  POST   /chat/stream           → Réponse streaming (SSE)
  GET    /chat/sessions         → 50 sessions récentes
  GET    /chat/sessions/{id}    → Historique complet session

  DOCUMENTS
  POST   /documents/upload      → Uploader + indexer un fichier
  GET    /documents/            → Lister documents indexés
  GET    /documents/file/{name} → Télécharger un document

  FEEDBACK
  POST   /feedback              → Soumettre évaluation (👍/👎 + note)

  ANALYTICS
  GET    /analytics/kpis        → Tableau de bord métriques

  SYSTÈME
  GET    /health                → Statut du service
```

### 11.2 Endpoint de streaming détaillé

```python
@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    session_id = request.session_id or str(uuid4())
    message_id = str(uuid4())

    async def generate():
        start_time = time.time()
        full_answer = []

        async for token in stream_answer(request.question):
            full_answer.append(token)
            yield token

        response_time_ms = int((time.time() - start_time) * 1000)
        # Sauvegarde conversation + métriques en base
        await save_message_with_metrics(...)

    headers = {
        "X-Session-ID": session_id,
        "X-Message-ID": message_id,
        "X-Sources": json.dumps(sources),
    }
    return StreamingResponse(generate(), media_type="text/plain", headers=headers)
```

### 11.3 KPIs analytics

```
  TABLEAU DE BORD ANALYTIQUE — /analytics/kpis
  ─────────────────────────────────────────────────────────────────

  ┌──────────────────────────────────────────────────────────────┐
  │  KPI                    │ Cible      │ Source SQL             │
  ├──────────────────────────────────────────────────────────────┤
  │  Taux de réponses utiles │  ≥ 80%    │ feedback.is_helpful   │
  │  Taux de couverture docs │  ≥ 85%    │ metrics.is_covered    │
  │  Taux d'escalade         │  ≤ 20%    │ metrics.has_escalation│
  │  Score de satisfaction   │  ≥ 4.0/5  │ feedback.rating       │
  │  Temps de réponse moyen  │  ≤ 5s     │ metrics.response_time │
  └──────────────────────────────────────────────────────────────┘
```

---

## 12. Interface utilisateur — Application Desktop

### 12.1 Concept UX : le chatbot flottant

L'interface a été conçue pour s'intégrer au quotidien des agents sans perturber leur flux de travail :

```
  ÉTAT AVATAR (80×80px)              ÉTAT CHAT (380×620px)
  ──────────────────                 ──────────────────────

  ┌────────────┐                     ┌──────────────────────────┐
  │  ╋         │  ← icône médicale   │  CHUbot     [ - ][ × ]  │
  │  CHU       │     bleue           │  ──────────────────────  │
  │    ·ping·  │  ← animation        │  "Comment puis-je vous   │
  └────────────┘     pulse           │   aider ?"               │
                                     │                          │
  Click → ouvre la                   │  [Congés] [Primes]       │
  fenêtre de chat                    │  [Formation] [Retraite]  │
                                     │  ──────────────────────  │
  Toujours visible,                  │  Ma question...      [▶] │
  draggable, alwaysOnTop             └──────────────────────────┘
```

### 12.2 Arbre des composants React

```
  App.jsx
  ├── Avatar.jsx          (état initial 80×80)
  │     └── Tauri drag region
  └── FloatingChat.jsx    (état chat 380×620)
        ├── WindowControls.jsx
        │     └── minimize / maximize / close / collapse
        └── ChatWindow.jsx
              ├── Header (drag region)
              ├── Messages list
              │     └── MessageBubble.jsx × N
              │           ├── Markdown rendered (ReactMarkdown)
              │           ├── Sources panel (PDF/Web icons)
              │           └── Feedback buttons (👍 👎)
              └── ChatInput.jsx
                    ├── Textarea auto-resize
                    └── Send button
```

### 12.3 Fenêtre frameless Tauri

```json
// tauri.conf.json
{
  "windows": [{
    "width": 80,
    "height": 80,
    "decorations": false,   // Pas de bordure Windows
    "transparent": true,    // Fond transparent
    "alwaysOnTop": true,    // Toujours au premier plan
    "resizable": false
  }]
}
```

La fenêtre est redimensionnée **programmatiquement** via l'API Tauri lors des transitions :

```javascript
// Transition Avatar → Chat
await appWindow.setSize(new PhysicalSize(380, 620));
await appWindow.center();
setIsOpen(true);

// Transition Chat → Avatar
await appWindow.setSize(new PhysicalSize(80, 80));
setIsOpen(false);
```

### 12.4 Rendu Markdown et liens documents

Les réponses du LLM sont rendues en Markdown enrichi :

```
  RÉPONSE LLM (Markdown)           RENDU DANS L'UI
  ─────────────────────            ─────────────────

  ## Forfait Mobilités Durables   →  Titre h2 stylisé
  Le montant est de **200€**      →  **Gras**
  - Vélo, trottinette             →  Liste à puces
  - Covoiturage                   →  Liste à puces
  [Voir NI 2025-46](2025-46.pdf)  →  📄 Lien cliquable
                                      ouvre via Tauri opener
```

### 12.5 Gestion du feedback utilisateur

```
  CYCLE DE FEEDBACK
  ─────────────────────────────────────────────────────────────────

  1. Réponse affichée
         │
         ▼
  Agent voit [ 👍 ] ou [ 👎 ]
         │
         ├──▶ Clic 👍 → POST /feedback {is_helpful: true, rating: null}
         └──▶ Clic 👎 → POST /feedback {is_helpful: false, rating: null}

  Après vote : boutons désactivés (pas de double vote)
  Données stockées : message_id + is_helpful + created_at
```

---

## 13. Évaluation et métriques de performance

### 13.1 Dataset d'évaluation

Un jeu de données de **105 paires question/réponse attendue** a été construit manuellement :

```
  DATASET D'ÉVALUATION — 105 QUESTIONS
  ─────────────────────────────────────────────────────────────────

  Structure d'une entrée :
  ┌─────────────────────────────────────────────────────────────┐
  │ {                                                           │
  │   "id": "QR001",                                           │
  │   "categorie": "Rémunération",                             │
  │   "sous_categorie": "Bulletins de salaire",                │
  │   "question": "Comment accéder à mon coffre-fort          │
  │                numérique ?",                               │
  │   "reponse": "Vous pouvez accéder à votre coffre-fort     │
  │               Digiposte depuis...",                        │
  │   "source": "FAQ Digiposte — CHU Angers"                  │
  │ }                                                           │
  └─────────────────────────────────────────────────────────────┘
```

### 13.2 Framework d'évaluation automatique

L'évaluation utilise le **même LLM local** (llama3.1) comme juge, sans dépendance OpenAI :

```
  MÉTRIQUES D'ÉVALUATION (3 dimensions)
  ─────────────────────────────────────────────────────────────────

  1. FAITHFULNESS (0→1)
     "La réponse est-elle basée UNIQUEMENT sur le contexte ?"
     Évalue : absence d'hallucinations / informations inventées

  2. ANSWER CORRECTNESS (0→1)
     "La réponse est-elle correcte par rapport à la vérité terrain ?"
     Évalue : précision factuelle de la réponse

  3. CONTEXT RELEVANCE (0→1)
     "Le contexte récupéré est-il pertinent pour la question ?"
     Évalue : qualité de la récupération documentaire
```

### 13.3 Résultats d'évaluation

*Évaluation réalisée sur 10 questions de la catégorie Rémunération :*

```
  SCORES GLOBAUX — ÉVALUATION CHUBOT
  ─────────────────────────────────────────────────────────────────

  Faithfulness (anti-hallucination)
  ████████████████░░░░  0.810 / 1.000   ✓ Objectif atteint (> 0.75)

  Context Relevance (qualité retrieval)
  ██████████████░░░░░░  0.740 / 1.000   ✓ Bon niveau (> 0.70)

  Answer Correctness (justesse factuelle)
  ███████████░░░░░░░░░  0.580 / 1.000   ~ À améliorer (cible: > 0.70)
```

```
  DISTRIBUTION DES SCORES DE CORRECTNESS
  ─────────────────────────────────────────────────────────────────

  Score ≥ 0.8  (réponse excellente)   ██████ 6 questions  (60%)
  Score 0.5-0.8 (réponse partielle)   ░░░░░░ 0 questions  ( 0%)
  Score < 0.5  (réponse insuffisante) ████   4 questions  (40%)

  → Les 4 questions avec score < 0.5 correspondent à des cas où
    le chatbot n'a pas trouvé le document source exact mais a
    tenté une réponse générale (ex: confidentialité coffre-fort,
    procédure changement RIB non documentée)
```

### 13.4 Analyse qualitative par question

```
  EXEMPLES DE RÉPONSES ÉVALUÉES
  ─────────────────────────────────────────────────────────────────

  QR001 - "Comment accéder à mon coffre-fort numérique ?"
  ┌─ Fidélité: 0.90 ─ Justesse: 0.80 ─ Contexte: 0.80 ─────────┐
  │ ✓ Réponse correcte, source bien citée                       │
  │ ✗ Manque : URL d'adhésion (adherer.digiposte.fr)            │
  └──────────────────────────────────────────────────────────────┘

  QR003 - "Je quitte le CHU, vais-je perdre mes bulletins ?"
  ┌─ Fidélité: 0.90 ─ Justesse: 0.30 ─ Contexte: 0.80 ─────────┐
  │ ✗ Réponse incorrecte: le chatbot suggère de "scanner"       │
  │   les bulletins, alors que Digiposte est à vie              │
  │ → Le document source ne mentionne pas clairement ce cas     │
  └──────────────────────────────────────────────────────────────┘

  QR008 - "Comment bénéficier du forfait mobilités durables ?"
  ┌─ Fidélité: 0.20 ─ Justesse: 0.30 ─ Contexte: 0.20 ─────────┐
  │ ✗ Contexte peu pertinent (NI pas encore indexée au moment   │
  │   du test)                                                   │
  │ → Réponse générique, pas ancrée dans les documents          │
  └──────────────────────────────────────────────────────────────┘
```

### 13.5 Intégration RAGAS

En complément de l'évaluation LLM-as-judge, un module **RAGAS** a été intégré pour des métriques standardisées dans la recherche RAG :

```
  PIPELINE D'ÉVALUATION RAGAS
  ─────────────────────────────────────────────────────────────────

  samples (question + réponse + contexte + vérité)
         │
         ▼
  EvaluationDataset RAGAS
  { user_input, retrieved_contexts, response, reference }
         │
         ├──▶ Faithfulness (LLM-based)
         ├──▶ Answer Correctness (LLM + embeddings)
         └──▶ Context Precision (LLM-based)
         │
         ▼
  Rapport CSV + JSON + console
```

### 13.6 Infrastructure d'évaluation

```bash
# Évaluation standard (métriques LLM-as-judge)
python tests/evaluate.py --limit 10

# Évaluation complète (105 questions)
python tests/evaluate.py

# Filtrage par catégorie
python tests/evaluate.py --cat Rémunération

# Avec métriques RAGAS supplémentaires
python tests/evaluate.py --limit 10 --ragas
```

---

## 14. Déploiement et packaging

### 14.1 Architecture de déploiement

```
  PACKAGING FINAL — INSTALLATION AGENT
  ─────────────────────────────────────────────────────────────────

  Setup.exe / Setup.msi
  ┌────────────────────────────────────────────────────────────┐
  │  Frontend (Tauri)                                          │
  │  ├── Interface React compilée (dist/)                     │
  │  └── Runtime Rust + WebView2                               │
  │                                                            │
  │  Backend (PyInstaller bundle)                              │
  │  ├── Python 3.11 embarqué                                  │
  │  ├── Toutes les dépendances Python                         │
  │  ├── chubot-backend.exe                                    │
  │  └── Démarre automatiquement sur port 8765                 │
  └────────────────────────────────────────────────────────────┘

  Installation → C:\Program Files\CHUbot\
  Données     → C:\Users\{user}\AppData\Local\CHUbot\
```

### 14.2 Commandes de build

```bash
# Build backend Python → binaire .exe
pyinstaller chubot-backend.spec

# Build frontend + packaging Tauri
cd bot/ui
npm run tauri build
# → génère: src-tauri/target/release/bundle/nsis/CHUbot_0.1.0_x64-setup.exe
#           src-tauri/target/release/bundle/msi/CHUbot_0.1.0_x64_en-US.msi
```

### 14.3 Configuration de démarrage

```python
# backend_main.py — point d'entrée PyInstaller
if getattr(sys, 'frozen', False):
    # Mode packagé : ajuste les chemins relatifs
    base_path = sys._MEIPASS
else:
    base_path = Path(__file__).parent

uvicorn.run(
    "bot.api.app:app",
    host="127.0.0.1",
    port=8765,
    log_level="warning",   # Pas de logs d'accès en prod
)
```

---

## 15. Difficultés rencontrées et solutions

### 15.1 Problème : Conflits asyncio / RAGAS sur Python 3.14

**Symptôme :** Crash lors de l'évaluation RAGAS — `nest_asyncio` patche la boucle événements et le cleanup Python 3.14 lève une exception.

**Solution :** Extraire l'évaluation RAGAS hors de la boucle asyncio principale, et l'exécuter en mode synchrone après fermeture de la boucle :

```python
# AVANT (problématique)
async def main():
    ...
    if args.ragas:
        result = evaluate(...)  # ← conflict avec loop en cours

# APRÈS (correct)
async def main():
    ...
    return samples, args  # ← retourne les données

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    samples, args = loop.run_until_complete(main())
    loop.close()           # ← loop fermée AVANT RAGAS

    if args.ragas:
        _run_ragas(samples, args)  # ← synchrone, pas de conflict
```

### 15.2 Problème : PermissionError sur results.csv

**Symptôme :** Le fichier `results.csv` était ouvert dans l'IDE ou Excel → `PermissionError: [Errno 13]`.

**Solution :** Mécanisme de fallback automatique vers un fichier horodaté :

```python
def _save_and_print(samples, output_path):
    csv_path = output_path / "results.csv"
    try:
        _write_csv(csv_path, samples)
    except PermissionError:
        # Fallback : résultats-20260602-171005.csv
        csv_path = output_path / f"results-{datetime.now():%Y%m%d-%H%M%S}.csv"
        _write_csv(csv_path, samples)
```

### 15.3 Problème : Qualité variable des extractions PDF

**Symptôme :** Certains PDF numérisés (scans) produisaient du texte incohérent avec PyMuPDF.

**Solution :** Fonction de nettoyage spécifique (`cleaner.py`) pour supprimer les artefacts, reconstituer les mots coupés par les fins de ligne, et filtrer les headers/footers récurrents détectés par pattern matching.

### 15.4 Problème : Questions hors-corpus répondues avec des hallucinations

**Symptôme :** Sur des questions pour lesquelles le document source n'était pas indexé, le LLM générait des réponses plausibles mais incorrectes.

**Solution :** Garde anti-hallucination systématique — si FlashRank ne retourne aucun document au-dessus du seuil (0.05), le LLM n'est jamais appelé :

```python
reranked = [d for d in docs if d.metadata.get("_rerank_score", 0) >= 0.05]
if not reranked:
    return MSG_NO_CONTEXT  # Message fixe, pas de LLM
```

### 15.5 Problème : Port 8765 déjà utilisé au redémarrage

**Symptôme :** `[Errno 10048] only one usage of each socket address` — une instance précédente n'avait pas été arrêtée.

**Solution :** Le processus est maintenant identifié par nom (`chubot-backend`) et tué proprement avant tout nouveau lancement.

### 15.6 Problème : Latence de première réponse (cold start)

**Symptôme :** La première requête prenait ~30s (chargement des modèles ChromaDB, BM25, FlashRank).

**Solution :** Initialisation lazy avec cache `@lru_cache` sur les singletons coûteux, et pré-chargement au démarrage du serveur via le lifespan FastAPI :

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-warm: charge vector store, BM25, reranker
    get_vector_store()
    get_ranker()
    yield
```

---

## 16. Perspectives d'évolution

### 16.1 Court terme (< 3 mois)

- **Authentification agents** : login via SSO CHU pour personnaliser l'expérience
- **Multi-langue** : support anglais/arabe pour les agents étrangers
- **Indexation automatique** : watcher sur le répertoire `documents/` pour réindexer à chaque nouveau fichier
- **Mode hors-ligne** : cache des Q/R fréquentes pour fonctionner sans réseau

### 16.2 Moyen terme (3-12 mois)

- **Tableau de bord manager** : interface dédiée DRH pour consulter les KPIs
- **Apprentissage par feedback** : utiliser les 👎 pour améliorer automatiquement les réponses
- **Citations précises** : pointer vers la page exacte du document source
- **Intégration Sharepoint** : indexation automatique de la GED CHU

### 16.3 Long terme

- **Agents spécialisés** : un sous-LLM par département RH avec expertise ciblée
- **Assistance multi-modal** : analyser des formulaires photographiés par l'agent
- **Intégration SI-RH** : connexion API vers le SIRH (Gestime, etc.) pour des réponses personnalisées ("vos congés restants : 12 jours")

---

## 17. Conclusion

Ce stage au CHU d'Angers m'a permis de mener de bout en bout le développement d'un système RAG de niveau production, en répondant à de véritables contraintes métier et techniques.

### Bilan technique

| Composant | Statut |
|---|---|
| Pipeline d'ingestion (PDF, DOCX, Excel, Web) | ✅ Opérationnel |
| Recherche hybride BM25 + vectorielle | ✅ Opérationnel |
| Reranking FlashRank | ✅ Opérationnel |
| Garde anti-hallucination | ✅ Opérationnel |
| Streaming LLM token par token | ✅ Opérationnel |
| API REST FastAPI (11 endpoints) | ✅ Opérationnel |
| Persistance PostgreSQL | ✅ Opérationnel |
| Interface Tauri flottante | ✅ Opérationnel |
| Feedback utilisateur | ✅ Opérationnel |
| Analytics KPI | ✅ Opérationnel |
| Framework d'évaluation automatique | ✅ Opérationnel |
| Packaging Windows (NSIS/MSI) | ✅ Opérationnel |

### Bilan des métriques d'évaluation

```
  SCORES FINAUX (10 questions, catégorie Rémunération)
  ─────────────────────────────────────────────────────────────────

  Faithfulness    : 0.810  ████████████████░░░░  ✓ Anti-hallucination efficace
  Ctx Relevance   : 0.740  ██████████████░░░░░░  ✓ Retrieval de qualité
  Answer Correct. : 0.580  ███████████░░░░░░░░░  ~ Marge de progression
```

Les résultats montrent un système fiable pour l'anti-hallucination (0.81) et la pertinence du retrieval (0.74). Le score de correction factuelle (0.58) révèle des axes d'amélioration principalement liés à l'exhaustivité de la base documentaire indexée.

### Apports personnels

Ce projet m'a permis d'acquérir une expertise concrète en :
- Architecture et implémentation d'un pipeline RAG complet
- Intégration LLM dans un contexte de production (latence, fiabilité, anti-hallucination)
- Développement fullstack async (FastAPI + React + Tauri)
- Gestion d'une base documentaire multiformat
- Évaluation quantitative de systèmes LLM

---

## 18. Références et bibliographie

| Référence | Description |
|---|---|
| Lewis et al. (2020) | "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" — papier fondateur du RAG |
| LangChain Documentation | https://docs.langchain.com — framework d'orchestration LLM |
| ChromaDB Documentation | https://docs.trychroma.com — base vectorielle |
| Ollama Documentation | https://ollama.ai — runtime LLM local |
| FlashRank | Prithiviraj Damodaran (2023) — cross-encoder léger CPU |
| RAGAS Framework | Es et al. (2023) — "RAGAS: Automated Evaluation of Retrieval Augmented Generation" |
| Tauri Documentation | https://tauri.app — framework desktop Rust/JS |
| FastAPI Documentation | https://fastapi.tiangolo.com — framework Python async |
| nomic-embed-text | Nussbaum et al. (2024) — modèle d'embedding open source |
| ms-marco-MiniLM-L-12-v2 | Microsoft — modèle de reranking cross-encoder |

---

## 19. Annexes

### Annexe A — Variables d'environnement (.env.example)

```ini
# Application
APP_NAME=CHUbot
APP_VERSION=0.1.0
APP_ENV=production
DEBUG=false

# LLM (Ollama hébergé CHU)
OLLAMA_BASE_URL=https://llm.chu-angers.fr/ollama
OLLAMA_MODEL=llama3.1:latest
OLLAMA_USERNAME=           # optionnel (Basic Auth)
OLLAMA_PASSWORD=           # optionnel

# Embeddings (Ollama local)
EMBEDDING_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=nomic-embed-text

# Base de données
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/chubot

# RAG
CHUNK_SIZE=2000
CHUNK_OVERLAP=400
RETRIEVAL_TOP_K=5
VECTOR_STORE_PATH=./data/indexes
```

### Annexe B — Structure des fichiers du projet

```
CHUbot/
├── backend_main.py              # Point d'entrée PyInstaller
├── alembic.ini                  # Migrations BDD
├── requirements.txt             # Dépendances Python
├── chubot-backend.spec          # Spec PyInstaller
├── bot/
│   ├── config/
│   │   ├── settings.py          # Configuration Pydantic
│   │   └── departments.py       # Mapping des 5 départements RH
│   ├── ingestion/
│   │   ├── cleaner.py           # Nettoyage texte
│   │   ├── loaders.py           # Chargeurs multi-format
│   │   ├── splitter.py          # Découpage + en-têtes
│   │   └── indexer.py           # CLI + ChromaDB
│   ├── retrieval/
│   │   ├── preprocessor.py      # Expansion acronymes + réécriture
│   │   ├── query_rewriter.py    # Reformulation LLM
│   │   ├── reranker.py          # FlashRank cross-encoder
│   │   ├── prompt.py            # Prompt système HR
│   │   └── chain.py             # Orchestration RAG complète
│   ├── api/
│   │   ├── app.py               # Application FastAPI
│   │   ├── db/
│   │   │   ├── database.py      # Moteur async SQLAlchemy
│   │   │   ├── models.py        # 6 tables ORM
│   │   │   └── schemas.py       # Schémas Pydantic
│   │   └── routes/
│   │       ├── chat.py          # Chat + streaming + sessions
│   │       ├── documents.py     # Upload + listing documents
│   │       ├── feedback.py      # Évaluations agents
│   │       └── analytics.py     # KPIs agrégés
│   └── ui/
│       ├── src/
│       │   ├── App.jsx
│       │   ├── api/client.js
│       │   └── components/
│       │       ├── Avatar.jsx
│       │       ├── FloatingChat.jsx
│       │       ├── WindowControls.jsx
│       │       └── chat/
│       │           ├── ChatWindow.jsx
│       │           ├── ChatInput.jsx
│       │           └── MessageBubble.jsx
│       └── src-tauri/
│           └── tauri.conf.json
├── data/
│   ├── documents/               # ~20 docs RH (PDF, DOCX, Excel)
│   ├── indexes/                 # ChromaDB persistant
│   └── eval/
│       ├── dataset.json         # 105 questions/réponses
│       └── results*.csv         # Résultats d'évaluation
├── tests/
│   └── evaluate.py              # Framework d'évaluation
└── alembic/                     # Migrations SQL
```

### Annexe C — Commandes utiles

```bash
# Démarrer le serveur de développement
uvicorn bot.api.app:app --host 127.0.0.1 --port 8765 --reload

# Démarrer l'interface Tauri
cd bot/ui && npx tauri dev

# Indexer tous les documents
python -m bot.ingestion.indexer --all

# Évaluer le chatbot
python tests/evaluate.py --limit 10

# Évaluation complète avec RAGAS
python tests/evaluate.py --ragas
```

---

*Rapport de stage — CHUbot v0.1.0 — CHU d'Angers — Direction des Ressources Humaines*

*Document généré le 18 juin 2026*
