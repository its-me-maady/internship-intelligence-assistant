from app.api.documents import router as documents_router
from app.config import settings
from app.services.vector_service import get_vector_store
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Backend API for Internship Intelligence Assistant — "
        "Document Analysis & Grounded RAG Platform"
    ),
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(documents_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify backend operational readiness."""
    vector_store = get_vector_store()
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "llm_model": settings.LLM_MODEL,
        "embedding_model": settings.EMBEDDING_MODEL,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "chroma_directory": settings.CHROMA_PERSIST_DIRECTORY,
        "indexed_documents_count": vector_store.get_indexed_documents_count(),
        "total_chunks_count": vector_store.get_total_chunks_count(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
