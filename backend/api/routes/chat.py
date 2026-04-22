import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.domain.models.message import Message
from backend.domain.models.session import ConversationSession
from backend.domain.schemas.chat import ChatRequest, ChatResponse, SessionResponse
from backend.rag.retrieval.retriever import ask, get_rag_chain

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
    """Pose une question — retourne la réponse en streaming token par token."""
    conv_session = await _get_or_create_session(request.session_id, db)
    db.add(Message(session_id=conv_session.id, role="human", content=request.question))
    await db.flush()

    session_id = conv_session.id
    llm_chain = get_rag_chain()
    collected_tokens: list[str] = []

    async def token_generator():
        async for chunk in llm_chain.astream(request.question):
            collected_tokens.append(chunk)
            yield chunk

        full_answer = "".join(collected_tokens)
        async with db.begin_nested():
            db.add(Message(session_id=session_id, role="assistant", content=full_answer))

    return StreamingResponse(
        token_generator(),
        media_type="text/plain",
        headers={"X-Session-ID": str(session_id)},
    )


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
