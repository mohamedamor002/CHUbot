# CHUbot — Assistant RH Intelligent

Chatbot RAG (Retrieval-Augmented Generation) pour le service RH du CHU.  
Les employés posent leurs questions en langage naturel et obtiennent des réponses basées sur les documents RH officiels.

---

## Architecture

```
CHUbot/
├── backend/                  # API FastAPI
│   ├── api/routes/           # Endpoints REST (chat, documents)
│   ├── core/                 # Configuration, base de données
│   ├── domain/               # Modèles SQLAlchemy + schémas Pydantic
│   └── rag/                  # Pipeline RAG
│       ├── loaders/          # Chargement PDF, Word, Excel
│       ├── chunkers/         # Découpage en chunks
│       ├── embeddings/       # Embeddings via Ollama
│       ├── indexer/          # ChromaDB (vector store)
│       └── retrieval/        # Chaîne LangChain + LLM Ollama
├── frontend/                 # Interface React + Tailwind CSS
│   └── src/
│       ├── api/              # Client axios
│       ├── components/
│       │   ├── chat/         # Bulles de message, input, fenêtre de chat
│       │   ├── sidebar/      # Navigation, nouvelle conversation
│       │   └── documents/    # Upload et liste des documents
│       └── App.jsx
├── scripts/                  # Scripts utilitaires
│   └── ingest_documents.py   # Ingestion batch de documents RH
├── data/
│   ├── documents/            # Fichiers sources PDF/Excel (non versionné)
│   └── indexes/              # Données ChromaDB (non versionné)
├── alembic/                  # Migrations de base de données
├── .env                      # Variables d'environnement (non versionné)
└── requirements.txt
```

---

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Backend | FastAPI, Python 3.14 |
| LLM | Ollama (local) — modèle configurable via `.env` |
| Embeddings | Ollama `nomic-embed-text` |
| Vector Store | ChromaDB (local) |
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

### 1. Cloner le projet

```bash
git clone <url-du-repo>
cd CHUbot
```

### 2. Backend — environnement Python

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configurer les variables d'environnement

```bash
cp .env.example .env
```

Modifier `.env` avec vos valeurs :

```env
DATABASE_URL=postgresql+asyncpg://postgres:VOTRE_MOT_DE_PASSE@localhost:5432/chubot
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3.5:latest
JWT_SECRET_KEY=votre-cle-secrete-256-bits
```

### 4. Créer la base de données

```bash
# Créer la base dans PostgreSQL
psql -U postgres -c "CREATE DATABASE chubot;"
```

Les tables sont créées automatiquement au démarrage du serveur.

### 5. Télécharger les modèles Ollama

```bash
ollama pull qwen3.5:latest    # LLM (configurable via OLLAMA_MODEL dans .env)
ollama pull nomic-embed-text  # Embeddings
```

### 6. Frontend — dépendances Node

```bash
cd frontend
npm install
```

---

## Lancement

Ouvrir **deux terminaux** :

**Terminal 1 — Backend :**
```bash
cd CHUbot
.venv\Scripts\activate
uvicorn backend.main:app --reload
# Disponible sur http://localhost:8000
```

**Terminal 2 — Frontend :**
```bash
cd CHUbot/frontend
npm run dev
# Disponible sur http://localhost:5173
```

---

## Utilisation

1. Ouvrir **http://localhost:5173** dans le navigateur
2. Aller dans l'onglet **Documents** (sidebar gauche)
3. Uploader un document RH (PDF, Word ou Excel, max 20 Mo)
4. Aller dans l'onglet **Conversation**
5. Poser une question en français

---

## API REST

Documentation interactive disponible sur **http://localhost:8000/docs**

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/health` | Statut du serveur |
| `POST` | `/api/v1/documents/upload` | Uploader et indexer un document |
| `GET` | `/api/v1/documents/` | Lister les documents indexés |
| `POST` | `/api/v1/chat` | Poser une question (réponse complète) |
| `POST` | `/api/v1/chat/stream` | Poser une question (streaming token par token) |
| `GET` | `/api/v1/chat/sessions/{id}` | Historique d'une session |

---

## Configuration RAG

Paramètres ajustables dans `.env` :

| Variable | Défaut | Description |
|----------|--------|-------------|
| `OLLAMA_MODEL` | `qwen3.5:latest` | Modèle LLM (plus grand = plus précis mais plus lent) |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Modèle d'embeddings |
| `CHUNK_SIZE` | `512` | Taille des chunks de documents (en tokens) |
| `CHUNK_OVERLAP` | `64` | Chevauchement entre chunks |
| `RETRIEVAL_TOP_K` | `3` | Nombre de chunks récupérés par requête |

---

## Formats de documents supportés

| Format | Extension |
|--------|-----------|
| PDF | `.pdf` |
| Word | `.docx`, `.doc` |
| Excel | `.xlsx`, `.xls`, `.xlsm` |

Taille maximale : **20 Mo** par fichier (upload via API).

---

## Ingestion batch de documents

Pour indexer plusieurs documents d'un coup sans passer par l'interface :

```bash
# Placer les fichiers dans data/documents/, puis :
python scripts/ingest_documents.py --dir data/documents

# Ou un seul fichier :
python scripts/ingest_documents.py --file chemin/vers/fichier.pdf
```

---

## Ce qui reste à implémenter

- [ ] Authentification JWT (login/register)
- [ ] Mémoire conversationnelle (historique passé au LLM)
- [ ] Suppression de documents indexés
- [ ] Dockerisation pour le déploiement
