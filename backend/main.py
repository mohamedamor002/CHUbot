from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.core.config.settings import settings
from backend.core.database import create_tables, engine
from backend.api.routes import chat, documents
import backend.domain.models  # noqa: F401 — enregistre les modèles auprès de Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Démarrage
    await create_tables()
    print(f"[START] {settings.APP_NAME} v{settings.APP_VERSION} started")
    print(f"   LLM model : {settings.OLLAMA_MODEL} via {settings.OLLAMA_BASE_URL}")
    print(f"   Database  : PostgreSQL")
    yield
    # Arrêt
    await engine.dispose()
    print("[STOP] Server shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(chat.router, prefix=settings.API_PREFIX)
app.include_router(documents.router, prefix=settings.API_PREFIX)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "env": settings.APP_ENV,
        "llm": settings.OLLAMA_MODEL,
    }
