"""뉴스 요약 & 썸네일 프롬프트 생성 API 라우터."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.models.content import (
    NewsSearchRequest,
    NewsSearchResponse,
    SummaryGenerateRequest,
    SummaryGenerateResponse,
    ScriptGenerateRequest,
    ScriptGenerateResponse,
    ThumbnailPromptRequest,
    ThumbnailPromptResponse,
    SaveResultRequest,
    SaveResultResponse,
    LibraryResponse,
)
from app.services import news_service, script_service, summary_service, thumbnail_service, library_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/news", tags=["news"])


# ---------------------------------------------------------------------------
# Step 1: 뉴스 검색
# ---------------------------------------------------------------------------

@router.post(
    "/search",
    response_model=NewsSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="주제 기반 최신 뉴스 검색",
    description=(
        "주제를 입력하면 RAG를 통해 관련 최신 뉴스를 검색하고,\n"
        "3-레이어 팩트체크(출처 신뢰도 + 교차 검증 + LLM 콘텐츠 분석)를 거쳐\n"
        "신뢰도 높은 뉴스 최대 3개를 반환합니다."
    ),
)
async def search_news(req: NewsSearchRequest) -> NewsSearchResponse:
    logger.info("뉴스 검색 요청 — topic=%s", req.topic)
    try:
        news_list, filtered_count = await news_service.search_news(req.topic)
        return NewsSearchResponse(
            topic=req.topic,
            news=news_list,
            filtered_count=filtered_count,
        )
    except Exception as exc:
        logger.error("뉴스 검색 실패: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"뉴스 검색 중 오류가 발생했습니다: {exc}",
        )


# ---------------------------------------------------------------------------
# Step 2-A: 뉴스 요약본 생성
# ---------------------------------------------------------------------------

@router.post(
    "/summary",
    response_model=SummaryGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="뉴스 요약본 생성 (읽기용, 500~900자)",
    description="선택한 뉴스를 심층분석형 / 핵심요약형 / 스토리텔링형 3가지 버전으로 요약합니다.",
)
async def generate_summary(req: SummaryGenerateRequest) -> SummaryGenerateResponse:
    logger.info("요약본 생성 요청 — news_id=%s, language=%s", req.news_id, req.language)
    try:
        versions = await summary_service.generate_summaries(
            news_id=req.news_id,
            title=req.news_title,
            content=req.news_content,
            language=req.language,
        )
        return SummaryGenerateResponse(news_id=req.news_id, versions=versions)
    except Exception as exc:
        logger.error("요약본 생성 실패: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"요약본 생성 중 오류가 발생했습니다: {exc}",
        )


# ---------------------------------------------------------------------------
# Step 2-B: 뉴스 스크립트 생성
# ---------------------------------------------------------------------------

@router.post(
    "/script",
    response_model=ScriptGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="뉴스 요약 스크립트 생성",
    description="선택한 뉴스를 지정한 길이(20초/30초/1분)로 요약한 스크립트 3가지 버전을 생성합니다.",
)
async def generate_script(req: ScriptGenerateRequest) -> ScriptGenerateResponse:
    logger.info(
        "스크립트 생성 요청 — news_id=%s, duration=%s", req.news_id, req.duration
    )
    if req.duration not in ("20초", "30초", "1분"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="duration은 '20초', '30초', '1분' 중 하나여야 합니다.",
        )
    try:
        versions = await script_service.generate_scripts(
            news_id=req.news_id,
            title=req.news_title,
            content=req.news_content,
            duration=req.duration,
            language=req.language,
        )
        return ScriptGenerateResponse(
            news_id=req.news_id,
            duration=req.duration,
            versions=versions,
        )
    except Exception as exc:
        logger.error("스크립트 생성 실패: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"스크립트 생성 중 오류가 발생했습니다: {exc}",
        )


# ---------------------------------------------------------------------------
# Step 3: 썸네일 프롬프트 생성
# ---------------------------------------------------------------------------

@router.post(
    "/thumbnail",
    response_model=ThumbnailPromptResponse,
    status_code=status.HTTP_200_OK,
    summary="뉴스 썸네일 이미지 생성 프롬프트",
    description="선택한 스크립트를 바탕으로 썸네일 이미지 생성 프롬프트 3가지를 생성합니다.",
)
async def generate_thumbnail(req: ThumbnailPromptRequest) -> ThumbnailPromptResponse:
    logger.info("썸네일 프롬프트 생성 요청 — news_id=%s", req.news_id)
    try:
        prompts = await thumbnail_service.generate_thumbnail_prompts(
            news_id=req.news_id,
            title=req.news_title,
            script=req.selected_script,
            hashtags=req.hashtags,
        )
        return ThumbnailPromptResponse(news_id=req.news_id, prompts=prompts)
    except Exception as exc:
        logger.error("썸네일 프롬프트 생성 실패: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"썸네일 프롬프트 생성 중 오류가 발생했습니다: {exc}",
        )


# ---------------------------------------------------------------------------
# Step 4: 결과 저장
# ---------------------------------------------------------------------------

@router.post(
    "/save",
    response_model=SaveResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="생성 결과 저장",
    description="뉴스 요약 스크립트와 썸네일 프롬프트를 라이브러리에 저장합니다.",
)
async def save_result(req: SaveResultRequest) -> SaveResultResponse:
    logger.info("결과 저장 요청 — topic=%s, news=%s", req.topic, req.news.title)
    try:
        saved_id = await library_service.save_result(
            topic=req.topic,
            news=req.news,
            selected_script=req.selected_script,
            duration=req.duration,
            thumbnail_prompts=req.thumbnail_prompts,
            hashtags=req.hashtags,
        )
        return SaveResultResponse(id=saved_id, message="라이브러리에 저장되었습니다.")
    except Exception as exc:
        logger.error("결과 저장 실패: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"저장 중 오류가 발생했습니다: {exc}",
        )


# ---------------------------------------------------------------------------
# Step 5: 라이브러리 조회
# ---------------------------------------------------------------------------

@router.get(
    "/library",
    response_model=LibraryResponse,
    status_code=status.HTTP_200_OK,
    summary="라이브러리 조회",
    description="저장된 결과를 조회합니다. hashtag 파라미터로 필터링 가능합니다.",
)
async def get_library(
    hashtag: Optional[str] = Query(default=None, description="필터링할 해시태그 (예: #AI)"),
    limit: int = Query(default=20, ge=1, le=100, description="최대 반환 개수"),
) -> LibraryResponse:
    logger.info("라이브러리 조회 — hashtag=%s, limit=%d", hashtag, limit)
    try:
        results = await library_service.get_library(hashtag=hashtag, limit=limit)
        return LibraryResponse(
            results=results,
            total=len(results),
            hashtag_filter=hashtag,
        )
    except Exception as exc:
        logger.error("라이브러리 조회 실패: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"라이브러리 조회 중 오류가 발생했습니다: {exc}",
        )
