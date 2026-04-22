from functools import lru_cache

from langchain_ollama import OllamaEmbeddings

from backend.core.config.settings import settings


@lru_cache(maxsize=1)
def get_embeddings() -> OllamaEmbeddings:
    """
    Retourne le modèle d'embeddings via Ollama (aucun téléchargement HuggingFace).
    Le modèle doit être disponible localement : ollama pull <EMBEDDING_MODEL>
    """
    return OllamaEmbeddings(
        model=settings.EMBEDDING_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
    )
