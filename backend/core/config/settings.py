from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "CHUbot"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # API
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/chubot"

    # Auth / JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Ollama
    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:9b"

    # Embeddings (modèle Ollama local — ex: nomic-embed-text, mxbai-embed-large)
    EMBEDDING_MODEL: str = "nomic-embed-text"

    # RAG
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    RETRIEVAL_TOP_K: int = 5

    # Vector Store
    VECTOR_STORE_TYPE: str = "chroma"
    VECTOR_STORE_PATH: str = "./data/indexes"


settings = Settings()
