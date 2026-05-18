"""뉴스 요약 & 썸네일 프롬프트 생성 서비스 — Pydantic 모델 정의."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Step 1: 뉴스 검색 + 팩트체크
# ---------------------------------------------------------------------------

class NewsSearchRequest(BaseModel):
    """주제 기반 뉴스 검색 요청."""
    topic: str = Field(..., min_length=1, max_length=200, description="검색할 주제")

    model_config = {
        "json_schema_extra": {"example": {"topic": "인공지능"}}
    }


class CredibilityInfo(BaseModel):
    """뉴스 신뢰도 평가 결과."""
    score: int = Field(..., description="종합 신뢰도 점수 (0~100)")
    grade: Literal["high", "medium", "low", "unverified"] = Field(..., description="신뢰도 등급")
    grade_label: str = Field(..., description="신뢰도 등급 레이블 (예: ✅ 높음)")
    # Layer 1: 출처
    source_score: int = Field(..., description="출처 신뢰도 점수 (0~40)")
    source_reason: str = Field(..., description="출처 신뢰도 설명")
    # Layer 2: 교차 검증
    cross_score: int = Field(..., description="교차 검증 점수 (0~30)")
    cross_reason: str = Field(..., description="교차 검증 설명")
    # Layer 3: 콘텐츠 분석
    content_score: int = Field(..., description="콘텐츠 분석 점수 (0~30)")
    content_reason: str = Field(..., description="콘텐츠 분석 설명")
    # 필터링 여부
    is_filtered: bool = Field(default=False, description="신뢰도 기준 미달로 필터링됨")


class NewsItem(BaseModel):
    """뉴스 아이템."""
    id: str = Field(..., description="뉴스 고유 ID")
    title: str = Field(..., description="뉴스 제목")
    summary: str = Field(..., description="뉴스 요약")
    source: str = Field(..., description="출처")
    published_at: str = Field(..., description="발행일")
    url: Optional[str] = Field(default=None, description="원문 URL")
    hashtags: List[str] = Field(default_factory=list, description="관련 해시태그")
    credibility: Optional[CredibilityInfo] = Field(default=None, description="신뢰도 평가 결과")


class NewsSearchResponse(BaseModel):
    """뉴스 검색 응답 — 최대 3개."""
    topic: str
    news: List[NewsItem] = Field(..., description="검색된 뉴스 목록 (신뢰도 순 정렬, 최대 3개)")
    filtered_count: int = Field(default=0, description="신뢰도 기준 미달로 제외된 뉴스 수")


# ---------------------------------------------------------------------------
# Step 2-A: 뉴스 요약본 생성 (읽기용, 500~900자)
# ---------------------------------------------------------------------------

class SummaryGenerateRequest(BaseModel):
    """뉴스 요약본 생성 요청."""
    news_id: str = Field(..., description="선택한 뉴스 ID")
    news_title: str = Field(..., description="뉴스 제목")
    news_content: str = Field(..., description="뉴스 본문/요약")
    language: str = Field(default="ko", description="출력 언어: 'ko' | 'en'")


class SummaryVersion(BaseModel):
    """요약본 버전."""
    version: int = Field(..., description="버전 번호 (1~3)")
    style: str = Field(..., description="스타일 (심층분석형 / 핵심요약형 / 스토리텔링형)")
    summary: str = Field(..., description="요약본 본문 (500~900자)")
    char_count: int = Field(..., description="글자 수")


class SummaryGenerateResponse(BaseModel):
    """요약본 생성 응답 — 3가지 버전."""
    news_id: str
    versions: List[SummaryVersion]


# ---------------------------------------------------------------------------
# Step 2-B: 뉴스 스크립트 생성 (낭독용)
# ---------------------------------------------------------------------------

class ScriptGenerateRequest(BaseModel):
    """뉴스 요약 스크립트 생성 요청."""
    news_id: str = Field(..., description="선택한 뉴스 ID")
    news_title: str = Field(..., description="뉴스 제목")
    news_content: str = Field(..., description="뉴스 본문/요약")
    duration: str = Field(..., description="영상 길이: '20초' | '30초' | '1분'")
    language: str = Field(default="ko", description="출력 언어: 'ko' (한국어) | 'en' (영어)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "news_id": "news_001",
                "news_title": "AI가 의료 진단 정확도 95% 달성",
                "news_content": "...",
                "duration": "30초",
            }
        }
    }


class ScriptVersion(BaseModel):
    """요약 스크립트 버전."""
    version: int = Field(..., description="버전 번호 (1~3)")
    style: str = Field(..., description="스타일 설명 (예: 정보형, 감성형, 자극형)")
    script: str = Field(..., description="요약 스크립트 본문")
    word_count: int = Field(..., description="단어/글자 수")


class ScriptGenerateResponse(BaseModel):
    """요약 스크립트 생성 응답 — 3가지 버전."""
    news_id: str
    duration: str
    versions: List[ScriptVersion] = Field(..., description="3가지 스크립트 버전")


# ---------------------------------------------------------------------------
# Step 3: 썸네일 프롬프트 생성
# ---------------------------------------------------------------------------

class ThumbnailPromptRequest(BaseModel):
    """썸네일 이미지 생성 프롬프트 요청."""
    news_id: str = Field(..., description="뉴스 ID")
    news_title: str = Field(..., description="뉴스 제목")
    selected_script: str = Field(..., description="선택된 요약 스크립트")
    hashtags: List[str] = Field(default_factory=list, description="관련 해시태그")

    model_config = {
        "json_schema_extra": {
            "example": {
                "news_id": "news_001",
                "news_title": "AI가 의료 진단 정확도 95% 달성",
                "selected_script": "AI가 드디어 의사를 넘어섰습니다...",
                "hashtags": ["#AI", "#의료", "#기술"],
            }
        }
    }


class ThumbnailPrompt(BaseModel):
    """썸네일 프롬프트 버전."""
    version: int = Field(..., description="버전 번호 (1~3)")
    style: str = Field(..., description="이미지 스타일 (예: 뉴스 브레이킹, 미니멀, 임팩트)")
    prompt_en: str = Field(..., description="영문 이미지 생성 프롬프트")
    prompt_ko: str = Field(..., description="한국어 프롬프트 설명")
    image_url: Optional[str] = Field(default=None, description="생성된 썸네일 이미지 URL")


class ThumbnailPromptResponse(BaseModel):
    """썸네일 프롬프트 생성 응답 — 3가지 버전."""
    news_id: str
    prompts: List[ThumbnailPrompt] = Field(..., description="3가지 썸네일 프롬프트")


# ---------------------------------------------------------------------------
# Step 4: 결과 저장 & 라이브러리
# ---------------------------------------------------------------------------

class SaveResultRequest(BaseModel):
    """생성 결과 저장 요청."""
    topic: str = Field(..., description="검색 주제")
    news: NewsItem = Field(..., description="선택된 뉴스")
    selected_script: ScriptVersion = Field(..., description="선택된 스크립트")
    duration: str = Field(..., description="선택된 영상 길이")
    thumbnail_prompts: List[ThumbnailPrompt] = Field(..., description="썸네일 프롬프트 목록")
    hashtags: List[str] = Field(default_factory=list, description="해시태그 목록")


class SavedResult(BaseModel):
    """저장된 결과 아이템."""
    id: str = Field(..., description="저장 ID")
    topic: str
    news_title: str
    news_source: str
    published_at: str
    duration: str
    selected_script: ScriptVersion
    thumbnail_prompts: List[ThumbnailPrompt]
    hashtags: List[str]
    created_at: str


class LibraryResponse(BaseModel):
    """라이브러리 조회 응답."""
    results: List[SavedResult]
    total: int
    hashtag_filter: Optional[str] = None


class SaveResultResponse(BaseModel):
    """저장 응답."""
    id: str
    message: str
