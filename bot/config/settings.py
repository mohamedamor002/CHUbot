from typing import List
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
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    # Base de données PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/chubot"

    # LLM — Ollama local (aucune clé API requise)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:9b"

    # Embeddings — modèle local Ollama
    EMBEDDING_MODEL: str = "nomic-embed-text"

    # RAG — tailles en caractères (français ≈ 4 chars/token)
    # 2000 chars ≈ 500 tokens | 3200 chars ≈ 800 tokens  (cible architecture : 500-800 tokens)
    CHUNK_SIZE: int = 2000
    CHUNK_OVERLAP: int = 200
    RETRIEVAL_TOP_K: int = 5

    # Stockage vecteurs
    VECTOR_STORE_PATH: str = "./data/indexes"


settings = Settings()
