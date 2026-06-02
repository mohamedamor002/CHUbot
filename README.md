# CHUbot — Assistant RH du CHU d'Angers

Chatbot RAG (Retrieval-Augmented Generation) pour la Direction des Ressources Humaines du CHU d'Angers.  
Les agents internes posent leurs questions en langage naturel et obtiennent des réponses basées sur les documents RH officiels.

Application **desktop flottante** (Tauri) — fenêtre toujours visible, déplaçable partout sur l'écran.

---

## Architecture

```
CHUbot/
├── bot/
│   ├── config/
│   │   ├── settings.py          ← Variables d'environnement (Pydantic)
│   │   └── departments.py       ← 5 sous-départements RH + emails d'escalade
│   ├── ingestion/               ← Pipeline offline (docs → chunks → vecteurs)
│   │   ├── cleaner.py           ← Nettoyage texte brut (artefacts PDF, coupures)
│   │   ├── loaders.py           ← PDF, DOCX, Excel (clé:valeur), scraping web
│   │   ├── splitter.py          ← Chunks avec en-têtes contextuels [Source|Section]
│   │   └── indexer.py           ← ChromaDB + CLI d'ingestion
│   ├── retrieval/               ← Pipeline online (question → réponse)
│   │   ├── query_rewriter.py    ← Reformulation LLM de la requête avant retrieval
│   │   ├── preprocessor.py      ← Expansion acronymes + query rewriting
│   │   ├── reranker.py          ← Cross-encoder FlashRank (filtre par score seuil)
│   │   ├── prompt.py            ← Prompt système RH (règles de pertinence)
│   │   └── chain.py             ← RAG : hybrid retrieval → reranking → LLM
│   ├── api/                     ← Couche HTTP (FastAPI)
│   │   ├── app.py               ← Point d'entrée (port 8765)
│   │   ├── db/
│   │   │   ├── database.py      ← Connexion PostgreSQL async
│   │   │   ├── models.py        ← 6 tables SQLAlchemy
│   │   │   └── schemas.py       ← Schémas Pydantic
│   │   └── routes/
│   │       ├── chat.py          ← POST /chat, /chat/stream, GET /sessions
│   │       ├── documents.py     ← Upload, liste, visualisation
│   │       ├── feedback.py      ← Retours utilisateurs
│   │       └── analytics.py     ← KPIs de performance
│   └── ui/                      ← Interface React 18 + Tailwind CSS + Tauri
│       ├── src/                 ← Composants React (Avatar, FloatingChat, Chat)
│       └── src-tauri/           ← App desktop (Rust + config Tauri)
├── backend_main.py              ← Point d'entrée desktop (PyInstaller + uvicorn)
├── data/
│   ├── documents/               ← Fichiers sources PDF/DOCX/Excel (non versionné)
│   └── indexes/                 ← Index ChromaDB (non versionné)
├── alembic/                     ← Migrations PostgreSQL
├── .env                         ← Variables d'environnement (non versionné)
└── requirements.txt
```

---

## Périmètre fonctionnel

Le chatbot couvre les 5 sous-départements identifiés lors des ateliers (avril 2026) :

| Sous-département | Thématiques |
|---|---|
| Recrutement & Effectifs | Concours, mobilité interne |
| Service des Rémunérations | Primes, calendrier de paie, remboursements transport |
| Gestion du Temps de Travail | Congés, RTT, absences, missions |
| Parcours Professionnels | Formation, protection sociale, handicap/RME |
| Service des Carrières | Avancement, retraite, médailles, positions statutaires |

---

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Backend | FastAPI, Python 3.11+, uvicorn (port 8765) |
| LLM | Ollama — modèle configurable via `.env` |
| Embeddings | Ollama `nomic-embed-text` |
| Vector Store | ChromaDB (local, persistant) |
| RAG | LangChain — hybrid BM25 + vectoriel, reranking FlashRank |
| Base de données | PostgreSQL + SQLAlchemy async |
| Frontend web | React 18, Vite, Tailwind CSS |
| Desktop | Tauri 2 (Rust + WebView2) |

---

## Prérequis

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Ollama installé et lancé
- Rust + Cargo (pour l'app desktop uniquement)

---

## Installation

### 1. Environnement Python

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### 2. Variables d'environnement

```bash
copy .env.example .env
```

Modifier `.env` :

```env
DATABASE_URL=postgresql+asyncpg://postgres:MOT_DE_PASSE@localhost:5432/chubot
OLLAMA_MODEL=llama3.1:latest
OLLAMA_BASE_URL=https://llm.chu-angers.fr/ollama
```

### 3. Base de données

```bash
psql -U postgres -c "CREATE DATABASE chubot;"
```

Les tables sont créées automatiquement au premier démarrage.

### 4. Modèles Ollama

```bash
ollama pull nomic-embed-text    # Embeddings (local obligatoire)
```

### 5. Frontend

```bash
cd bot/ui
npm install
```

---

## Lancement — Mode Web

**Terminal 1 — Backend :**
```bash
.venv\Scripts\activate
python backend_main.py
# API disponible sur http://127.0.0.1:8765
# Docs interactives : http://127.0.0.1:8765/docs
```

**Terminal 2 — Frontend :**
```bash
cd bot/ui
npm run dev
# Interface disponible sur http://localhost:5173
```

---

## Lancement — Mode Desktop (Tauri)

**Terminal 1 — Backend :**
```bash
.venv\Scripts\activate
python backend_main.py
```

**Terminal 2 — App desktop :**
```bash
cd bot/ui
npx tauri dev
```

L'application s'ouvre comme une **icône flottante** (80×80) sur le bureau.  
Cliquer sur l'icône ouvre le chat. Cliquer sur le header le referme.  
La fenêtre peut être déplacée partout sur l'écran.

---

## Ingestion des documents

```bash
# Indexer tous les documents (avec nettoyage + chunks contextuels)
python -m bot.ingestion.indexer --reset --all

# Indexer un dossier
python -m bot.ingestion.indexer --dir data/documents

# Indexer un fichier unique
python -m bot.ingestion.indexer --file data/documents/guide_primes.pdf

# Indexer les URLs du portail agents
python -m bot.ingestion.indexer --urls
```

---

## Endpoints API

| Méthode | URL | Description |
|---------|-----|-------------|
| `POST` | `/api/v1/chat` | Question → réponse complète |
| `POST` | `/api/v1/chat/stream` | Question → streaming token par token |
| `GET`  | `/api/v1/chat/sessions` | Liste des conversations |
| `GET`  | `/api/v1/chat/sessions/{id}` | Historique d'une session |
| `POST` | `/api/v1/documents/upload` | Upload + indexation d'un fichier |
| `GET`  | `/api/v1/documents/` | Liste des documents indexés |
| `GET`  | `/api/v1/documents/file/{nom}` | Visualiser un document |
| `POST` | `/api/v1/feedback` | Soumettre un retour utilisateur |
| `GET`  | `/api/v1/analytics/kpis` | KPIs de performance |
| `GET`  | `/health` | État du serveur |

---

## Pipeline RAG

```
Question utilisateur
       ↓
  Expansion acronymes (RTT → Réduction du Temps de Travail)
       ↓
  Query rewriting LLM (reformulation précise pour retrieval)
       ↓
  Hybrid retrieval BM25 + vectoriel (ChromaDB)
       ↓
  Reranking cross-encoder FlashRank (filtre score < 0.05)
       ↓
  LLM génère la réponse (contrainte au contexte récupéré)
       ↓
  Réponse + sources
```
