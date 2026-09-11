from app.models.chat_models import ChatRequest, ChatResponse
from app.rag.chains import RAGChain
from fastapi import APIRouter

router = APIRouter(tags=["Chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Grounded conversational RAG chat query",
    description=(
        "Executes a grounded conversational query against uploaded internship "
        "document chunks with strict anti-hallucination guardrails and citations."
    ),
)
async def chat_query(request: ChatRequest) -> ChatResponse:
    """Processes conversational query and returns grounded answer with citations."""
    chain = RAGChain()
    return chain.invoke(
        query=request.query,
        top_k=request.top_k,
        document_id=request.document_id,
        chat_history=request.chat_history,
    )
