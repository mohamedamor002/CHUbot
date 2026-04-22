from functools import lru_cache

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from backend.core.config.settings import settings
from backend.rag.indexer.vector_store import get_vector_store


SYSTEM_PROMPT = """Tu es CHUbot, l'assistant RH du CHU (Centre Hospitalier Universitaire).
Tu réponds aux questions des employés en te basant uniquement sur les documents RH fournis.
Si la réponse n'est pas dans les documents, dis-le clairement sans inventer.
Réponds toujours en français, de manière concise et professionnelle.

Contexte extrait des documents RH :
{context}
"""


def _format_docs(docs) -> str:
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


@lru_cache(maxsize=1)
def get_rag_chain():
    """Construit et retourne la chaîne RAG complète."""
    llm = ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.1,
        num_ctx=2048,
        num_predict=512,
        reasoning=False,   # disable extended thinking for qwen3/qwen3.5 models
    )

    retriever = get_vector_store().as_retriever(
        search_kwargs={"k": settings.RETRIEVAL_TOP_K}
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{question}"),
    ])

    chain = (
        {"context": retriever | _format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain


async def ask(question: str) -> str:
    """Pose une question et retourne la réponse générée par Ollama."""
    chain = get_rag_chain()
    return await chain.ainvoke(question)
