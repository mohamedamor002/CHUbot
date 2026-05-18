from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.db.database import get_db
from bot.api.db.models import Message, Feedback, MessageMetrics

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/kpis")
async def get_kpis(db: AsyncSession = Depends(get_db)):
    """KPIs de performance du chatbot RH."""

    def pct(num, den):
        return round(num / den * 100, 1) if den else None

    # Totaux
    total_q = (await db.execute(select(func.count()).where(Message.role == "human"))).scalar_one()

    # Feedback
    total_fb  = (await db.execute(select(func.count(Feedback.id)))).scalar_one()
    helpful   = (await db.execute(select(func.count()).where(Feedback.is_helpful == True))).scalar_one()  # noqa: E712
    avg_rating = (await db.execute(select(func.avg(Feedback.rating)).where(Feedback.rating.isnot(None)))).scalar_one()

    # Métriques
    total_metrics  = (await db.execute(select(func.count(MessageMetrics.id)))).scalar_one()
    covered        = (await db.execute(select(func.count()).where(MessageMetrics.is_covered == True))).scalar_one()  # noqa: E712
    escalated      = (await db.execute(select(func.count()).where(MessageMetrics.has_escalation == True))).scalar_one()  # noqa: E712
    avg_time_ms    = (await db.execute(select(func.avg(MessageMetrics.response_time_ms)).where(MessageMetrics.response_time_ms.isnot(None)))).scalar_one()

    return {
        "total_questions": total_q,
        "total_feedback":  total_fb,
        "kpis": [
            {
                "key":       "useful_response_rate",
                "label":     "Taux de réponse utile",
                "value":     pct(helpful, total_fb),
                "unit":      "%",
                "target":    80,
                "direction": "higher",
            },
            {
                "key":       "document_coverage_rate",
                "label":     "Taux de couverture documentaire",
                "value":     pct(covered, total_metrics),
                "unit":      "%",
                "target":    None,
                "direction": "higher",
            },
            {
                "key":       "escalation_rate",
                "label":     "Taux d'escalade humaine",
                "value":     pct(escalated, total_metrics),
                "unit":      "%",
                "target":    20,
                "direction": "lower",
            },
            {
                "key":       "satisfaction_score",
                "label":     "Score de satisfaction",
                "value":     round(float(avg_rating), 2) if avg_rating else None,
                "unit":      "/5",
                "target":    4.0,
                "direction": "higher",
            },
            {
                "key":       "avg_response_time",
                "label":     "Délai moyen de réponse",
                "value":     round(avg_time_ms / 1000, 2) if avg_time_ms else None,
                "unit":      "s",
                "target":    5,
                "direction": "lower",
            },
        ],
    }
