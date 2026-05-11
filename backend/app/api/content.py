import logging

from fastapi import APIRouter, HTTPException, status

from app.models.content import (
    ContentRequest,
    ContentResponse,
    SimilarContentRequest,
    SimilarContentResponse,
    SimilarContentItem,
)
from app.services import ollama_service, fallback_service, vector_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content", tags=["content"])


# ---------------------------------------------------------------------------
# Content generation
# ---------------------------------------------------------------------------

@router.post(
    "/generate",
    response_model=ContentResponse,
    status_code=status.HTTP_200_OK,
    summary="숏폼 콘텐츠 생성",
    description=(
        "입력 파라미터를 기반으로 숏폼 콘텐츠를 생성합니다.\n\n"
        "- `use_llm=true`이고 Ollama가 가용 상태이면 LLM으로 생성합니다.\n"
        "- Ollama를 사용할 수 없거나 `use_llm=false`이면 규칙 기반 폴백을 사용합니다.\n"
        "- 생성된 콘텐츠는 ChromaDB에 자동 저장되며, LLM 생성 시 Pinecone에도 저장됩니다."
    ),
)
async def generate_content(req: ContentRequest) -> ContentResponse:
    """콘텐츠 생성 엔드포인트."""
    data = req.model_dump()
    logger.info(
        "Content generation request — platform=%s, goal=%s, use_llm=%s",
        req.platform,
        req.goal,
        req.use_llm,
    )

    content: str
    source: str
    model: str | None = None

    if req.use_llm and await ollama_service.is_ollama_available():
        try:
            content = await ollama_service.generate_content(data)
            source = "llm"
            model = ollama_service.settings.ollama_model
            logger.info("LLM generation succeeded, model=%s", model)
        except Exception as exc:
            logger.warning("LLM generation failed (%s), falling back to rule-based", exc)
            content = fallback_service.generate_content_plan(data)
            source = "fallback"
    else:
        if req.use_llm:
            logger.info("Ollama not available — using fallback generator")
        content = fallback_service.generate_content_plan(data)
        source = "fallback"

    # Persist to vector DBs asynchronously; failures must not affect the response.
    metadata = {
        "platform": req.platform,
        "goal": req.goal,
        "tone": req.tone,
        "source": source,
    }
    try:
        await vector_service.save_to_chroma(content, metadata)
    except Exception as exc:
        logger.warning("ChromaDB save failed (non-fatal): %s", exc)

    if source == "llm":
        try:
            await vector_service.upsert_to_pinecone(content, metadata)
        except Exception as exc:
            logger.warning("Pinecone upsert failed (non-fatal): %s", exc)

    return ContentResponse(content=content, source=source, model=model)


# ---------------------------------------------------------------------------
# Similar content search
# ---------------------------------------------------------------------------

@router.post(
    "/similar",
    response_model=SimilarContentResponse,
    status_code=status.HTTP_200_OK,
    summary="유사 콘텐츠 검색",
    description="ChromaDB에서 쿼리와 유사한 콘텐츠를 검색합니다.",
)
async def find_similar(req: SimilarContentRequest) -> SimilarContentResponse:
    """유사 콘텐츠 검색 엔드포인트."""
    logger.info("Similar content search — query=%r, top_k=%d", req.query, req.top_k)
    try:
        raw_results = await vector_service.search_chroma(req.query, req.top_k)
    except Exception as exc:
        logger.error("ChromaDB search error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="벡터 DB 검색 중 오류가 발생했습니다.",
        ) from exc

    items = [
        SimilarContentItem(
            id=r["id"],
            content=r["content"],
            distance=r["distance"],
            metadata=r.get("metadata", {}),
        )
        for r in raw_results
    ]
    return SimilarContentResponse(results=items, total=len(items))


# ---------------------------------------------------------------------------
# Health check (content-service level)
# ---------------------------------------------------------------------------

@router.get(
    "/health",
    tags=["health"],
    summary="콘텐츠 서비스 헬스 체크",
    description="Ollama 연결 상태와 사용 모델 정보를 반환합니다.",
)
async def content_health():
    """콘텐츠 서비스 헬스 체크."""
    ollama_ok = await ollama_service.is_ollama_available()
    return {
        "status": "ok",
        "ollama": {
            "available": ollama_ok,
            "model": ollama_service.settings.ollama_model,
            "base_url": ollama_service.settings.ollama_base_url,
        },
    }
