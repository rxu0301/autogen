import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.content import router as news_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "뉴스 요약 & 썸네일 프롬프트 생성 API 시작 "
        f"[env={settings.app_env}, model={settings.ollama_model}]"
    )
    yield
    logger.info("뉴스 요약 & 썸네일 프롬프트 생성 API 종료")


app = FastAPI(
    title="뉴스 숏폼 에이전트 API",
    description=(
        "주제를 입력하면 RAG로 최신 뉴스 3개를 검색하고,\n"
        "선택한 뉴스를 20초/30초/1분 분량의 요약 스크립트(3가지 버전)로 생성하며,\n"
        "썸네일 이미지 생성 프롬프트(3가지 버전)를 제공합니다.\n"
        "결과는 라이브러리에 저장되어 해시태그별로 조회할 수 있습니다."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(news_router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Root & health check
# ---------------------------------------------------------------------------

@app.get("/", tags=["root"])
async def root():
    return {
        "service": "뉴스 숏폼 에이전트 API",
        "version": "2.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
async def health():
    import httpx
    ollama_ok = False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            ollama_ok = resp.status_code == 200
    except Exception:
        pass

    return {
        "status": "ok",
        "ollama": "available" if ollama_ok else "unavailable",
        "model": settings.ollama_model,
    }
