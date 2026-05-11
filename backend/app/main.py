import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.content import router as content_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown lifecycle."""
    logger.info(
        "Starting Shortform Content Agent API "
        f"[env={settings.app_env}, model={settings.ollama_model}]"
    )
    yield
    logger.info("Shutting down Shortform Content Agent API")


app = FastAPI(
    title="Shortform Content Agent API",
    description=(
        "숏폼 콘텐츠 생성 에이전트 — Ollama 로컬 LLM + Pinecone + ChromaDB\n\n"
        "콘텐츠 생성 요청을 받아 Ollama LLM으로 숏폼 콘텐츠를 생성하고, "
        "벡터 DB에 저장·검색하는 API 서버입니다."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(content_router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Root & health check
# ---------------------------------------------------------------------------

@app.get("/", tags=["root"], summary="API 루트")
async def root():
    """API 서버 기본 정보를 반환합니다."""
    return {
        "service": "Shortform Content Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["health"], summary="서버 헬스 체크")
async def health_check():
    """서버 상태를 확인합니다. Ollama 연결 여부도 함께 반환합니다."""
    from app.services.ollama_service import is_ollama_available

    ollama_ok = await is_ollama_available()
    return {
        "status": "ok",
        "env": settings.app_env,
        "ollama": {
            "available": ollama_ok,
            "base_url": settings.ollama_base_url,
            "model": settings.ollama_model,
        },
    }
