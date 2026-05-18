# CHUbot — Assistant RH du CHU d'Angers

Chatbot RAG (Retrieval-Augmented Generation) pour la Direction des Ressources Humaines du CHU d'Angers.  
Les agents internes posent leurs questions en langage naturel et obtiennent des réponses basées sur les documents RH officiels.

---

## Architecture

```
CHUbot/
├── bot/
│   ├── config/
│   │   ├── settings.py        ← Variables d'environnement (Pydantic)
│   │   └── departments.py     ← 5 sous-départements RH + emails d'escalade
│   ├── ingestion/             ← Pipeline offline (docs → chunks → vecteurs)
│   │   ├── loaders.py         ← PDF, DOCX, Excel, scraping web
│   │   ├── splitter.py        ← Découpage en chunks
│   │   └── indexer.py         ← ChromaDB + CLI d'ingestion
│   ├── retrieval/             ← Pipeline online (question → réponse)
│   │   ├── prompt.py          ← Prompt système RH (5 départements, escalade)
│   │   └── chain.py           ← Chaîne RAG : retrieval → LLM → réponse
│   ├── api/                   ← Couche HTTP (FastAPI)
│   │   ├── app.py             ← Point d'entrée
│   │   ├── db/
│   │   │   ├── database.py    ← Connexion PostgreSQL async
│   │   │   ├── models.py      ← 6 tables SQLAlchemy
│   │   │   └── schemas.py     ← Schémas Pydantic
│   │   └── routes/
│   │       ├── chat.py        ← POST /chat, /chat/stream, GET /sessions
│   │       ├── documents.py   ← Upload, liste, visualisation
│   │       ├── feedback.py    ← Retours utilisateurs
│   │       └── analytics.py   ← KPIs de performance
│   └── ui/                    ← Interface React 18 + Tailwind CSS
├── data/
│   ├── documents/             ← Fichiers sources PDF/DOCX/Excel (non versionné)
│   └── indexes/               ← Index ChromaDB (non versionné)
├── alembic/                   ← Migrations PostgreSQL
├── .env                       ← Variables d'environnement (non versionné)
└── requirements.txt
```

---

## Périmètre fonctionnel (Phase 1)

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
| Backend | FastAPI, Python 3.11+ |
| LLM | Ollama local — configurable via `.env` |
| Embeddings | Ollama `nomic-embed-text` |
| Vector Store | ChromaDB (local, persistant) |
| RAG | LangChain |
| Base de données | PostgreSQL + SQLAlchemy async |
| Frontend | React 18, Vite, Tailwind CSS |

---

## Prérequis

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- [Ollama](https://ollama.com) installé et lancé

---

## Installation

### 1. Environnement Python

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
```

### 2. Variables d'environnement

```bash
copy .env.example .env
```

Modifier `.env` :

```env
DATABASE_URL=postgresql+asyncpg://postgres:MOT_DE_PASSE@localhost:5432/chubot
OLLAMA_MODEL=qwen2.5:9b
```

### 3. Base de données

```bash
psql -U postgres -c "CREATE DATABASE chubot;"
```

Les tables sont créées automatiquement au premier démarrage.

### 4. Modèles Ollama

```bash
ollama pull qwen2.5:9b          # LLM
ollama pull nomic-embed-text    # Embeddings
```

### 5. Frontend

```bash
cd bot/ui
npm install
```

---

## Lancement

**Terminal 1 — Backend :**
```bash
.venv\Scripts\activate
uvicorn bot.api.app:app --reload
# API disponible sur http://localhost:8000
# Docs interactives : http://localhost:8000/docs
```

**Terminal 2 — Frontend :**
```bash
cd bot/ui
npm run dev
# Interface disponible sur http://localhost:5173
```

---

## Ingestion des documents

```bash
# Indexer tous les documents du dossier data/documents/
python -m bot.ingestion.indexer --dir data/documents

# Indexer un fichier unique
python -m bot.ingestion.indexer --file data/documents/guide_primes.pdf

# Indexer les URLs documentaires du rapport Phase 1
python -m bot.ingestion.indexer --urls

# Vider l'index avant de réindexer
python -m bot.ingestion.indexer --reset --dir data/documents
```

---

## Endpoints API

| Méthode | URL | Description |
|---------|-----|-------------|
| `POST` | `/api/v1/chat` | Question → réponse complète |
| `POST` | `/api/v1/chat/stream` | Question → streaming token |
| `GET`  | `/api/v1/chat/sessions` | Liste des conversations |
| `GET`  | `/api/v1/chat/sessions/{id}` | Historique d'une session |
| `POST` | `/api/v1/documents/upload` | Upload + indexation d'un fichier |
| `GET`  | `/api/v1/documents/` | Liste des documents indexés |
| `GET`  | `/api/v1/documents/file/{nom}` | Visualiser un document |
| `POST` | `/api/v1/feedback` | Soumettre un retour |
| `GET`  | `/api/v1/analytics/kpis` | KPIs de performance |
| `GET`  | `/health` | État du serveur |

---

## Structure de la base de données

| Table | Rôle |
|-------|------|
| `users` | Comptes agents (prêt pour auth V2) |
| `conversation_sessions` | Sessions de conversation |
| `messages` | Échanges human/assistant |
| `feedback` | Retours is_helpful + rating 1-5 |
| `message_metrics` | Temps de réponse, couverture, escalade |
| `indexed_documents` | Traçabilité des fichiers indexés |
