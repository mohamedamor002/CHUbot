"""Schémas Pydantic — validation des entrées/sorties de l'API."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question:   str           = Field(..., min_length=1, max_length=2000)
    session_id: uuid.UUID | None = Field(None, description="Continuer une conversation existante")


class ChatResponse(BaseModel):
    answer:     str
    question:   str
    session_id: uuid.UUID


class MessageOut(BaseModel):
    role:       str
    content:    str
    created_at: datetime


class SessionResponse(BaseModel):
    session_id: uuid.UUID
    messages:   list[MessageOut]
    created_at: datetime


class SessionSummary(BaseModel):
    session_id:   uuid.UUID
    title:        Optional[str]
    created_at:   datetime
    last_message: Optional[str]


# ── Documents ─────────────────────────────────────────────────────────────────

class IndexResponse(BaseModel):
    filename:       str
    chunks_indexed: int


# ── Feedback ──────────────────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    message_id: uuid.UUID
    is_helpful: bool
    rating:     int | None = Field(None, ge=1, le=5)


# ── Admin ─────────────────────────────────────────────────────────────────────

class UrlIngestRequest(BaseModel):
    url: str = Field(..., min_length=10, max_length=512)


class JobOut(BaseModel):
    id:             uuid.UUID
    type:           str
    source:         str
    status:         str
    chunks_indexed: int
    error_msg:      Optional[str]
    created_at:     datetime
    finished_at:    Optional[datetime]

    model_config = {"from_attributes": True}


class IndexStatsOut(BaseModel):
    total_documents: int
    total_chunks:    int
    index_size_mb:   float


class DocumentOut(BaseModel):
    id:             uuid.UUID
    filename:       str
    file_type:      str
    chunks_indexed: int
    indexed_at:     datetime

    model_config = {"from_attributes": True}
