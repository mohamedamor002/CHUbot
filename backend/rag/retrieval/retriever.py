from functools import lru_cache
from typing import List, Tuple

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

from backend.core.config.settings import settings
from backend.rag.indexer.vector_store import get_vector_store


SYSTEM_PROMPT = """Tu es CHUbot, l'assistant RH du CHU (Centre Hospitalier Universitaire).
Tu réponds aux questions des employés en te basant uniquement sur les documents RH fournis.
Si la réponse n'est pas dans les documents, dis-le clairement sans inventer.
Réponds toujours en français, de manière concise et professionnelle.

Contexte extrait des documents RH :
{context}
"""


def _format_docs(docs: List[Document]) -> str:
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


def _extract_sources(docs: List[Document]) -> List[dict]:
    seen = set()
    sources = []
    for doc in docs:
        name = doc.metadata.get("source_file")
        if name and name not in seen:
            seen.add(name)
            sources.append({
                "name": name,
                "url": doc.metadata.get("source_url"),        # None pour les PDFs
                "type": doc.metadata.get("file_type", "pdf"), # "web" ou "pdf"
            })
    return sources


@lru_cache(maxsize=1)
def _get_llm():
    return ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.1,
        num_ctx=2048,
        num_predict=512,
        reasoning=False,
    )


@lru_cache(maxsize=1)
def _get_generation_chain():
    """Chaîne prompt → LLM → parser (sans retriever)."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{question}"),
    ])
    return prompt | _get_llm() | StrOutputParser()


def get_retriever():
    return get_vector_store().as_retriever(
        search_kwargs={"k": settings.RETRIEVAL_TOP_K}
    )


async def retrieve(question: str) -> Tuple[str, List[dict], bool]:
    """Retourne (context formaté, sources, is_covered)."""
    docs = await get_retriever().ainvoke(question)
    is_covered = len(docs) > 0
    return _format_docs(docs), _extract_sources(docs), is_covered


async def stream_answer(context: str, question: str):
    """Générateur async de tokens LLM."""
    chain = _get_generation_chain()
    async for chunk in chain.astream({"context": context, "question": question}):
        yield chunk


async def ask(question: str) -> str:
    context, _, __ = await retrieve(question)
    chain = _get_generation_chain()
    return await chain.ainvoke({"context": context, "question": question})
