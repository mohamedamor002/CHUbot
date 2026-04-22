import uuid
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.domain.models.feedback import Feedback

router = APIRouter(prefix="/feedback", tags=["Feedback"])


class FeedbackRequest(BaseModel):
    message_id: uuid.UUID
    is_helpful: bool
    rating: int | None = Field(None, ge=1, le=5)


@router.post("")
async def submit_feedback(body: FeedbackRequest, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, delete

    # Un seul feedback par message
    await db.execute(delete(Feedback).where(Feedback.message_id == body.message_id))
    db.add(Feedback(
        message_id=body.message_id,
        is_helpful=body.is_helpful,
        rating=body.rating,
    ))
    await db.commit()
    return {"status": "ok"}
