import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="Question posée par l'employé")
    session_id: uuid.UUID | None = Field(None, description="ID de session pour continuer une conversation")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Réponse générée par le modèle")
    question: str = Field(..., description="Question originale")
    session_id: uuid.UUID = Field(..., description="ID de la session de conversation")


class MessageOut(BaseModel):
    role: str
    content: str
    created_at: datetime


class SessionResponse(BaseModel):
    session_id: uuid.UUID
    messages: list[MessageOut]
    created_at: datetime


class SessionSummary(BaseModel):
    session_id: uuid.UUID
    title: str | None
    created_at: datetime
    last_message: str | None
