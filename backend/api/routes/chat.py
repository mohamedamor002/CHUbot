import json
import time
import uuid
import re

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.domain.models.message import Message
from backend.domain.models.session import ConversationSession
from backend.domain.models.feedback import MessageMetrics
from backend.domain.schemas.chat import ChatRequest, ChatResponse, SessionResponse, SessionSummary
from backend.rag.retrieval.retriever import ask, retrieve, stream_answer

_ESCALATION_PATTERN = re.compile(
    r"contacter|contacter le (service|pôle|bureau)|DRH|drh-|"
    r"ressources humaines|pole (politique|social)|@chu-angers",
    re.IGNORECASE,
)
_NOT_COVERED_PATTERN = re.compile(
    r"n['']est pas dans les documents|pas d['']information|"
    r"aucune information|je ne (trouve|peux|dispose|sais) pas|"
    r"non disponible|n['']ai pas trouvé",
    re.IGNORECASE,
)

router = APIRouter(prefix="/chat", tags=["Chat"])


async def _get_or_create_session(
    session_id: uuid.UUID | None, db: AsyncSession
) -> ConversationSession:
    """Récupère une session existante ou en crée une nouvelle."""
    if session_id:
        session = await db.get(ConversationSession, session_id)
        if session:
            return session

    session = ConversationSession()
    db.add(session)
    await db.flush()
    return session


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Pose une question — retourne la réponse du modèle RAG et persiste l'échange."""
    try:
        conv_session = await _get_or_create_session(request.session_id, db)

        answer = await ask(request.question)

        db.add(Message(session_id=conv_session.id, role="human", content=request.question))
        db.add(Message(session_id=conv_session.id, role="assistant", content=answer))

        return ChatResponse(
            answer=answer,
            question=request.question,
            session_id=conv_session.id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération : {str(e)}")


@router.post("/stream")
async def chat_stream(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Pose une question — streaming avec tracking des métriques."""
    conv_session = await _get_or_create_session(request.session_id, db)
    db.add(Message(session_id=conv_session.id, role="human", content=request.question))
    await db.flush()

    session_id = conv_session.id
    assistant_msg_id = uuid.uuid4()

    t_start = time.monotonic()
    context, sources, is_covered = await retrieve(request.question)
    collected_tokens: list[str] = []

    async def token_generator():
        async for chunk in stream_answer(context, request.question):
            collected_tokens.append(chunk)
            yield chunk

        # Sauvegarde après streaming — dans try/except pour ne jamais bloquer le stream
        try:
            elapsed_ms = int((time.monotonic() - t_start) * 1000)
            full_answer = "".join(collected_tokens)
            has_escalation = bool(_ESCALATION_PATTERN.search(full_answer))
            covered = is_covered and not bool(_NOT_COVERED_PATTERN.search(full_answer))

            async with db.begin_nested():
                db.add(Message(id=assistant_msg_id, session_id=session_id, role="assistant", content=full_answer))
                db.add(MessageMetrics(
                    message_id=assistant_msg_id,
                    response_time_ms=elapsed_ms,
                    is_covered=covered,
                    has_escalation=has_escalation,
                ))
        except Exception as e:
            print(f"[WARN] Erreur sauvegarde message assistant : {e}")

    return StreamingResponse(
        token_generator(),
        media_type="text/plain",
        headers={
            "X-Session-ID": str(session_id),
            "X-Message-ID": str(assistant_msg_id),
            "X-Sources": json.dumps(sources),
            "Access-Control-Expose-Headers": "X-Session-ID, X-Message-ID, X-Sources",
        },
    )


@router.get("/sessions", response_model=list[SessionSummary])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    """Liste toutes les sessions avec leur premier message comme titre."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(ConversationSession)
        .options(selectinload(ConversationSession.messages))
        .order_by(ConversationSession.created_at.desc())
        .limit(50)
    )
    sessions = result.scalars().all()

    summaries = []
    for s in sessions:
        first_human = next((m.content for m in s.messages if m.role == "human"), None)
        last_human = next((m.content for m in reversed(s.messages) if m.role == "human"), None)
        summaries.append(SessionSummary(
            session_id=s.id,
            title=s.title or (first_human[:60] if first_human else "Conversation"),
            created_at=s.created_at,
            last_message=last_human,
        ))
    return summaries


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Récupère l'historique d'une session de conversation."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(ConversationSession)
        .where(ConversationSession.id == session_id)
        .options(selectinload(ConversationSession.messages))
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")

    return SessionResponse(
        session_id=session.id,
        messages=[
            {"role": m.role, "content": m.content, "created_at": m.created_at}
            for m in session.messages
        ],
        created_at=session.created_at,
    )
