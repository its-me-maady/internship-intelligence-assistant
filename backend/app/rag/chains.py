from typing import List, Optional

from app.models.chat_models import ChatMessage, ChatResponse, ChatSourceChunk
from app.rag.prompts import GROUNDED_RAG_SYSTEM_PROMPT, STANDARD_REFUSAL_MESSAGE
from app.rag.retrievers import DocumentRetriever
from app.services import llm_service
from langchain_core.documents import Document
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage


class RAGChain:
    """Orchestrates grounded conversational retrieval-augmented generation."""

    def __init__(
        self,
        retriever: Optional[DocumentRetriever] = None,
        llm: Optional[BaseChatModel] = None,
    ):
        self._retriever = retriever
        self._llm = llm

    @property
    def retriever(self) -> DocumentRetriever:
        if self._retriever is not None:
            return self._retriever
        return DocumentRetriever()

    @property
    def llm(self) -> BaseChatModel:
        if self._llm is not None:
            return self._llm
        return llm_service.get_llm()

    def format_context(self, docs: List[Document]) -> str:
        """Formats retrieved chunks into XML-delimited context."""
        formatted_chunks = []
        for doc in docs:
            meta = doc.metadata or {}
            chunk_id = meta.get("chunk_id", "unknown")
            filename = meta.get("filename", "unknown")
            page = meta.get("page_number", -1)
            page_str = f' page="{page}"' if page != -1 else ""
            formatted_chunks.append(
                f'<chunk id="{chunk_id}" source="{filename}"{page_str}>\n'
                f"{doc.page_content}\n"
                f"</chunk>"
            )
        return "\n\n".join(formatted_chunks)

    def invoke(
        self,
        query: str,
        top_k: int = 4,
        document_id: Optional[str] = None,
        chat_history: Optional[List[ChatMessage]] = None,
    ) -> ChatResponse:
        """Executes the complete grounded QA flow with citations and guardrails."""
        docs = self.retriever.retrieve(
            query=query,
            top_k=top_k,
            document_id=document_id,
        )

        # Refusal guardrail when zero chunks match
        if not docs:
            return ChatResponse(
                answer=STANDARD_REFUSAL_MESSAGE,
                is_grounded=False,
                sources=[],
            )

        context_str = self.format_context(docs)
        system_content = GROUNDED_RAG_SYSTEM_PROMPT.format(context=context_str)

        messages: List[BaseMessage] = [SystemMessage(content=system_content)]

        # Append previous conversation history
        for msg in chat_history or []:
            if msg.role.lower() in {"user", "human"}:
                messages.append(HumanMessage(content=msg.content))
            else:
                messages.append(AIMessage(content=msg.content))

        # Append current user query
        messages.append(HumanMessage(content=query))

        ai_response = self.llm.invoke(messages)
        answer_text = (
            ai_response.content
            if isinstance(ai_response.content, str)
            else str(ai_response.content)
        ).strip()

        # Check for refusal indicators
        refusal_phrases = [
            "cannot find sufficient information",
            "not enough information",
            "context does not contain",
            "insufficient information",
        ]
        is_refusal = any(
            phrase in answer_text.lower() for phrase in refusal_phrases
        ) or (answer_text == STANDARD_REFUSAL_MESSAGE)

        if is_refusal:
            return ChatResponse(
                answer=answer_text,
                is_grounded=False,
                sources=[],
            )

        # Build citation sources from retrieved chunks
        sources: List[ChatSourceChunk] = []
        for doc in docs:
            meta = doc.metadata or {}
            page_num = meta.get("page_number")
            if page_num == -1:
                page_num = None
            sources.append(
                ChatSourceChunk(
                    document_id=meta.get("document_id", ""),
                    filename=meta.get("filename", ""),
                    page_number=page_num,
                    chunk_index=meta.get("chunk_index", 0),
                    snippet=doc.page_content[:300],
                )
            )

        return ChatResponse(
            answer=answer_text,
            is_grounded=True,
            sources=sources,
        )
