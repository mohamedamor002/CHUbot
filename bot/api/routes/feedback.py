from fastapi import APIRouter, Depends
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.db.database import get_db
from bot.api.db.models import Feedback
from bot.api.db.schemas import FeedbackRequest

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("")
async def submit_feedback(body: FeedbackRequest, db: AsyncSession = Depends(get_db)):
    """Soumet ou remplace un feedback pour un message (un seul feedback par message)."""
    await db.execute(delete(Feedback).where(Feedback.message_id == body.message_id))
    db.add(Feedback(
        message_id=body.message_id,
        is_helpful=body.is_helpful,
        rating=body.rating,
    ))
    await db.commit()
    return {"status": "ok"}
