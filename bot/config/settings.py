import base64
from typing import Dict, List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "CHUbot"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # API
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,tauri://localhost,http://tauri.localhost"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    # Base de données SQLite (fichier local, aucun serveur requis)
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/chubot.db"

    # LLM — Ollama hébergé OVH
    OLLAMA_BASE_URL: str = "https://llm.chu-angers.fr/ollama"
    OLLAMA_MODEL: str = "llama3.1:latest"
    OLLAMA_AUTH_USER: str = ""
    OLLAMA_AUTH_PASSWORD: str = ""

    @property
    def ollama_auth_headers(self) -> Dict[str, str]:
        if self.OLLAMA_AUTH_USER and self.OLLAMA_AUTH_PASSWORD:
            token = base64.b64encode(
                f"{self.OLLAMA_AUTH_USER}:{self.OLLAMA_AUTH_PASSWORD}".encode()
            ).decode()
            return {"Authorization": f"Basic {token}"}
        return {}

    # Embeddings — modèle local Ollama (nomic-embed-text non dispo sur OVH)
    EMBEDDING_MODEL: str = "nomic-embed-text"
    EMBEDDING_BASE_URL: str = "http://localhost:11434"

    # RAG — tailles en caractères (français ≈ 4 chars/token)
    # 2000 chars ≈ 500 tokens | 3200 chars ≈ 800 tokens  (cible architecture : 500-800 tokens)
    CHUNK_SIZE: int = 2000
    CHUNK_OVERLAP: int = 400
    RETRIEVAL_TOP_K: int = 5

    # Stockage vecteurs
    VECTOR_STORE_PATH: str = "./data/indexes"

    # Admin — clé d'accès à l'interface d'administration
    ADMIN_API_KEY: str = "changeme-admin-secret"


settings = Settings()
