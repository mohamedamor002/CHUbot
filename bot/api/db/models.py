"""
Tous les modèles SQLAlchemy du CHUbot — 6 tables.

    users                ← Comptes agents (optionnel V1, prêt pour V2)
    conversation_sessions← Sessions de conversation
    messages             ← Échanges human/assistant
    feedback             ← Retours utilisateur (is_helpful, rating 1-5)
    message_metrics      ← Métriques techniques (temps réponse, couverture, escalade)
    indexed_documents    ← Traçabilité des documents indexés
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.api.db.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Utilisateurs ──────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id:             Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username:       Mapped[str]        = mapped_column(String(50),  unique=True, index=True, nullable=False)
    email:          Mapped[str]        = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password:Mapped[str]        = mapped_column(String(255), nullable=False)
    full_name:      Mapped[str | None] = mapped_column(String(150))
    role:           Mapped[str]        = mapped_column(String(50),  default="employee")
    is_active:      Mapped[bool]       = mapped_column(Boolean,     default=True)
    created_at:     Mapped[datetime]   = mapped_column(DateTime(timezone=True), default=_now)
    updated_at:     Mapped[datetime]   = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    sessions: Mapped[list["ConversationSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


# ── Sessions de conversation ──────────────────────────────────────────────────

class ConversationSession(Base):
    __tablename__ = "conversation_sessions"

    id:         Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id:    Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    title:      Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime]   = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime]   = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    user:     Mapped["User | None"]  = relationship(back_populates="sessions")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


# ── Messages ──────────────────────────────────────────────────────────────────

class Message(Base):
    __tablename__ = "messages"

    id:         Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversation_sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    role:       Mapped[str]       = mapped_column(String(20), nullable=False)  # "human" | "assistant"
    content:    Mapped[str]       = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime]  = mapped_column(DateTime(timezone=True), default=_now)

    session:  Mapped["ConversationSession"] = relationship(back_populates="messages")
    feedback: Mapped["Feedback | None"]     = relationship(back_populates="message", uselist=False)
    metrics:  Mapped["MessageMetrics | None"] = relationship(back_populates="message", uselist=False)


# ── Feedback utilisateur ──────────────────────────────────────────────────────

class Feedback(Base):
    __tablename__ = "feedback"

    id:         Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), index=True, nullable=False)
    is_helpful: Mapped[bool]      = mapped_column(Boolean, nullable=False)
    rating:     Mapped[int | None]= mapped_column(Integer)  # 1-5
    created_at: Mapped[datetime]  = mapped_column(DateTime(timezone=True), default=_now)

    message: Mapped["Message"] = relationship(back_populates="feedback")


# ── Métriques techniques ──────────────────────────────────────────────────────

class MessageMetrics(Base):
    __tablename__ = "message_metrics"
    __table_args__ = (UniqueConstraint("message_id"),)

    id:              Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id:      Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    response_time_ms:Mapped[int | None]= mapped_column(Integer)
    is_covered:      Mapped[bool]      = mapped_column(Boolean, default=True)   # docs trouvés
    has_escalation:  Mapped[bool]      = mapped_column(Boolean, default=False)  # renvoi service
    created_at:      Mapped[datetime]  = mapped_column(DateTime(timezone=True), default=_now)

    message: Mapped["Message"] = relationship(back_populates="metrics")


# ── Documents indexés ─────────────────────────────────────────────────────────

class IndexedDocument(Base):
    __tablename__ = "indexed_documents"

    id:             Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename:       Mapped[str]       = mapped_column(String(255), nullable=False)
    file_type:      Mapped[str]       = mapped_column(String(10),  nullable=False)
    chunks_indexed: Mapped[int]       = mapped_column(Integer, nullable=False)
    indexed_at:     Mapped[datetime]  = mapped_column(DateTime(timezone=True), default=_now)
