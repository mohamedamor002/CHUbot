from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bot.config.settings import settings
from bot.api.db.database import create_tables, engine
import bot.api.db.models  # noqa: F401 — enregistre tous les modèles auprès de Base
from bot.api.routes import chat, documents, feedback, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    print(f"[START] {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"        LLM  : {settings.OLLAMA_MODEL} — {settings.OLLAMA_BASE_URL}")
    print(f"        DB   : PostgreSQL")
    print(f"        Index: {settings.VECTOR_STORE_PATH}")
    yield
    await engine.dispose()
    print("[STOP]  Serveur arrêté")


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

app.include_router(chat.router,      prefix=settings.API_PREFIX)
app.include_router(documents.router, prefix=settings.API_PREFIX)
app.include_router(feedback.router,  prefix=settings.API_PREFIX)
app.include_router(analytics.router, prefix=settings.API_PREFIX)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "app":    settings.APP_NAME,
        "version": settings.APP_VERSION,
        "llm":    settings.OLLAMA_MODEL,
    }
