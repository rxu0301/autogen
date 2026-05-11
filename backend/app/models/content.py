from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ContentRequest(BaseModel):
    """콘텐츠 생성 요청 모델."""

    interest: str = Field(..., min_length=1, max_length=200, description="사용자 관심사")
    goal: str = Field(..., min_length=1, max_length=200, description="콘텐츠 목적")
    target_audience: str = Field(..., min_length=1, max_length=200, description="타겟 시청자")
    platform: str = Field(
        ...,
        description="플랫폼 (TikTok, Instagram, YouTube 등)",
        examples=["TikTok", "Instagram", "YouTube"],
    )
    tone: str = Field(..., min_length=1, max_length=100, description="콘텐츠 톤 (예: 유머, 정보, 감성)")
    duration: str = Field(..., min_length=1, max_length=50, description="영상 길이 (예: 15초, 30초, 1분)")
    keywords: Optional[str] = Field(default="없음", max_length=500, description="참고 키워드 (쉼표 구분)")
    use_llm: bool = Field(default=True, description="Ollama LLM 사용 여부. False이면 규칙 기반 폴백 사용")

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        allowed = {"TikTok", "Instagram", "YouTube", "Shorts", "Reels"}
        if v not in allowed:
            # Accept any value but normalise known aliases
            aliases = {
                "tiktok": "TikTok",
                "instagram": "Instagram",
                "youtube": "YouTube",
                "shorts": "Shorts",
                "reels": "Reels",
            }
            normalised = aliases.get(v.lower())
            if normalised:
                return normalised
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "interest": "헬스, 다이어트",
                "goal": "팔로워 증가",
                "target_audience": "20~30대 직장인",
                "platform": "TikTok",
                "tone": "유머",
                "duration": "30초",
                "keywords": "홈트, 다이어트, 챌린지",
                "use_llm": True,
            }
        }
    }


class SimilarContentRequest(BaseModel):
    """유사 콘텐츠 검색 요청 모델."""

    query: str = Field(..., min_length=1, max_length=500, description="검색 쿼리 텍스트")
    top_k: int = Field(default=5, ge=1, le=20, description="반환할 최대 결과 수")


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class ContentResponse(BaseModel):
    """콘텐츠 생성 응답 모델."""

    content: str = Field(..., description="생성된 콘텐츠 텍스트")
    source: str = Field(..., description="생성 소스: 'llm' (Ollama) 또는 'fallback' (규칙 기반)")
    model: Optional[str] = Field(default=None, description="사용된 LLM 모델명 (LLM 사용 시)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "콘셉트 1: ...\n훅: ...\n스크립트: ...",
                "source": "llm",
                "model": "llama3",
            }
        }
    }


class SimilarContentItem(BaseModel):
    """유사 콘텐츠 검색 결과 항목."""

    id: str = Field(..., description="콘텐츠 고유 ID (MD5 해시)")
    content: str = Field(..., description="저장된 콘텐츠 텍스트")
    distance: float = Field(..., description="벡터 거리 (낮을수록 유사)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="저장 시 첨부된 메타데이터")


class SimilarContentResponse(BaseModel):
    """유사 콘텐츠 검색 응답 모델."""

    results: List[SimilarContentItem] = Field(default_factory=list)
    total: int = Field(..., description="반환된 결과 수")


class TrendItem(BaseModel):
    """트렌드 콘텐츠 항목 (Pinecone 검색 결과)."""

    id: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
