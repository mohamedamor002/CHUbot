from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.core.database import get_db
from backend.domain.models.message import Message
from backend.domain.models.feedback import Feedback, MessageMetrics

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/kpis")
async def get_kpis(db: AsyncSession = Depends(get_db)):

    # ── Totaux de base ────────────────────────────────────────────────────────
    total_q = (await db.execute(
        select(func.count()).where(Message.role == "human")
    )).scalar_one()

    total_assistant = (await db.execute(
        select(func.count()).where(Message.role == "assistant")
    )).scalar_one()

    # ── Feedback ──────────────────────────────────────────────────────────────
    total_feedback = (await db.execute(select(func.count(Feedback.id)))).scalar_one()

    helpful_count = (await db.execute(
        select(func.count()).where(Feedback.is_helpful == True)  # noqa: E712
    )).scalar_one()

    avg_rating = (await db.execute(
        select(func.avg(Feedback.rating)).where(Feedback.rating.isnot(None))
    )).scalar_one()

    # ── Métriques messages ────────────────────────────────────────────────────
    total_metrics = (await db.execute(select(func.count(MessageMetrics.id)))).scalar_one()

    covered_count = (await db.execute(
        select(func.count()).where(MessageMetrics.is_covered == True)  # noqa: E712
    )).scalar_one()

    escalation_count = (await db.execute(
        select(func.count()).where(MessageMetrics.has_escalation == True)  # noqa: E712
    )).scalar_one()

    avg_time_ms = (await db.execute(
        select(func.avg(MessageMetrics.response_time_ms)).where(
            MessageMetrics.response_time_ms.isnot(None)
        )
    )).scalar_one()

    # ── Calculs ───────────────────────────────────────────────────────────────
    def pct(num, den): return round(num / den * 100, 1) if den else None

    useful_rate = pct(helpful_count, total_feedback)
    coverage_rate = pct(covered_count, total_metrics)
    escalation_rate = pct(escalation_count, total_metrics)
    avg_time_s = round(avg_time_ms / 1000, 2) if avg_time_ms else None
    avg_score = round(float(avg_rating), 2) if avg_rating else None

    return {
        "total_questions": total_q,
        "total_feedback": total_feedback,
        "kpis": [
            {
                "key": "useful_response_rate",
                "label": "Taux de réponse utile",
                "value": useful_rate,
                "unit": "%",
                "target": 80,
                "direction": "higher",
            },
            {
                "key": "document_coverage_rate",
                "label": "Taux de couverture documentaire",
                "value": coverage_rate,
                "unit": "%",
                "target": None,
                "direction": "higher",
            },
            {
                "key": "escalation_rate",
                "label": "Taux d'escalade humaine",
                "value": escalation_rate,
                "unit": "%",
                "target": 20,
                "direction": "lower",
            },
            {
                "key": "satisfaction_score",
                "label": "Score de satisfaction",
                "value": avg_score,
                "unit": "/5",
                "target": 4.0,
                "direction": "higher",
            },
            {
                "key": "avg_response_time",
                "label": "Délai moyen de réponse",
                "value": avg_time_s,
                "unit": "s",
                "target": 5,
                "direction": "lower",
            },
            {
                "key": "hallucination_rate",
                "label": "Taux d'hallucination",
                "value": None,
                "unit": "%",
                "target": 5,
                "direction": "lower",
                "note": "Surveillance manuelle requise",
            },
            {
                "key": "audio_wer",
                "label": "WER module audio",
                "value": None,
                "unit": "%",
                "target": 10,
                "direction": "lower",
                "note": "Module audio non implémenté",
            },
        ],
    }
