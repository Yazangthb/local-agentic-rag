from fastapi import FastAPI

from app.openai_compat.chat import router as openai_router
from app.settings import get_settings

app = FastAPI(title="Agentic RAG API", version="0.1.0")
app.include_router(openai_router, prefix="/v1", tags=["openai-compat"])


@app.get("/healthz")
def healthz() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "chat_provider": settings.chat_provider,
        "embedding_provider": settings.embedding_provider,
    }

