import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.database import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_helpful: Mapped[bool] = mapped_column(Boolean, nullable=False)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1–5
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MessageMetrics(Base):
    __tablename__ = "message_metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_covered: Mapped[bool] = mapped_column(Boolean, default=True)      # docs trouvés ?
    has_escalation: Mapped[bool] = mapped_column(Boolean, default=False)  # bot redirige vers DRH ?
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
