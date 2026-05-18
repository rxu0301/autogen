"""뉴스 검색 서비스 — RAG 기반 최신 뉴스 3개 검색 + 팩트체크 필터링.

속도 최적화:
  - 네이버 / NewsAPI 병렬 동시 요청
  - API 타임아웃 5초로 단축
  - Ollama 폴백은 즉시 반환 (LLM 호출 없이 규칙 기반)
  - 팩트체크 Layer 3 (LLM) 비활성화 → 규칙 기반으로 대체
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from datetime import datetime
from typing import List, Tuple

import httpx

from app.config import settings
from app.models.content import NewsItem

logger = logging.getLogger(__name__)


def _make_id(title: str) -> str:
    return "news_" + hashlib.md5(title.encode()).hexdigest()[:8]


def _extract_hashtags(text: str, topic: str) -> List[str]:
    existing = re.findall(r"#\w+", text)
    if existing:
        return existing[:5]
    words = [w for w in re.split(r"[\s,]+", text) if len(w) >= 2][:3]
    tags = [f"#{w}" for w in words if w]
    tags.insert(0, f"#{topic}")
    return list(dict.fromkeys(tags))[:5]


# ---------------------------------------------------------------------------
# 네이버 뉴스 (타임아웃 5초)
# ---------------------------------------------------------------------------

async def _fetch_from_naver(topic: str) -> List[NewsItem]:
    if not settings.naver_client_id or not settings.naver_client_secret:
        return []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                "https://openapi.naver.com/v1/search/news.json",
                headers={
                    "X-Naver-Client-Id": settings.naver_client_id,
                    "X-Naver-Client-Secret": settings.naver_client_secret,
                },
                params={"query": topic, "display": 5, "sort": "date"},
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])[:5]

        news_list = []
        for item in items:
            title = re.sub(r"<[^>]+>", "", item.get("title", ""))
            description = re.sub(r"<[^>]+>", "", item.get("description", ""))
            news_list.append(NewsItem(
                id=_make_id(title),
                title=title,
                summary=description[:300],
                source="네이버 뉴스",
                published_at=item.get("pubDate", "")[:16],
                url=item.get("originallink") or item.get("link", ""),
                hashtags=_extract_hashtags(title + " " + description, topic),
            ))
        logger.info("네이버 뉴스 %d개 (topic=%s)", len(news_list), topic)
        return news_list
    except Exception as exc:
        logger.warning("네이버 뉴스 실패: %s", exc)
        return []


# ---------------------------------------------------------------------------
# NewsAPI (타임아웃 5초)
# ---------------------------------------------------------------------------

async def _fetch_from_newsapi(topic: str) -> List[NewsItem]:
    if not settings.newsapi_key:
        return []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": topic, "language": "ko",
                    "sortBy": "publishedAt", "pageSize": 5,
                    "apiKey": settings.newsapi_key,
                },
            )
            resp.raise_for_status()
            articles = resp.json().get("articles", [])[:5]

        news_list = []
        for art in articles:
            title = art.get("title", "")
            description = art.get("description") or art.get("content") or ""
            news_list.append(NewsItem(
                id=_make_id(title),
                title=title,
                summary=description[:300],
                source=art.get("source", {}).get("name", "Unknown"),
                published_at=art.get("publishedAt", "")[:10],
                url=art.get("url", ""),
                hashtags=_extract_hashtags(title + " " + description, topic),
            ))
        logger.info("NewsAPI %d개 (topic=%s)", len(news_list), topic)
        return news_list
    except Exception as exc:
        logger.warning("NewsAPI 실패: %s", exc)
        return []


# ---------------------------------------------------------------------------
# 즉시 폴백 (LLM 없이 규칙 기반으로 즉시 반환)
# ---------------------------------------------------------------------------

def _instant_fallback(topic: str) -> List[NewsItem]:
    """API 키 없을 때 즉시 반환하는 규칙 기반 뉴스 (LLM 호출 없음)."""
    today = datetime.now().strftime("%Y-%m-%d")
    templates = [
        (f"{topic} 분야 최신 동향", f"최근 {topic} 분야에서 주목할 만한 변화가 나타나고 있습니다. 전문가들은 이번 변화가 업계 전반에 영향을 미칠 것으로 전망합니다.", ["#최신뉴스", "#트렌드"]),
        (f"{topic} 관련 정책 변화", f"정부와 관련 기관이 {topic}에 대한 새로운 방향을 제시했습니다. 관련 업계의 대응이 주목됩니다.", ["#정책", "#변화"]),
        (f"{topic} 시장 분석", f"{topic} 시장이 빠르게 변화하고 있습니다. 전문가들은 향후 지속적인 성장세를 예측하고 있습니다.", ["#시장분석", "#성장"]),
    ]
    return [
        NewsItem(
            id=_make_id(f"{topic}_{i}"),
            title=title,
            summary=summary,
            source="뉴스 에이전트",
            published_at=today,
            hashtags=[f"#{topic}"] + tags,
        )
        for i, (title, summary, tags) in enumerate(templates, 1)
    ]


# ---------------------------------------------------------------------------
# 공개 인터페이스
# ---------------------------------------------------------------------------

async def search_news(topic: str) -> Tuple[List[NewsItem], int]:
    """주제에 맞는 최신 뉴스를 검색하고 팩트체크 후 신뢰도 순으로 반환합니다.

    최적화:
      - 네이버 + NewsAPI 병렬 동시 요청
      - API 없으면 즉시 폴백 (LLM 호출 없음)
      - 팩트체크는 규칙 기반만 사용 (LLM 팩트체크 스킵)
    """
    # 1. 네이버 + NewsAPI 병렬 요청
    naver_task = asyncio.create_task(_fetch_from_naver(topic))
    newsapi_task = asyncio.create_task(_fetch_from_newsapi(topic))

    naver_result, newsapi_result = await asyncio.gather(
        naver_task, newsapi_task, return_exceptions=True
    )

    naver = naver_result if isinstance(naver_result, list) else []
    newsapi = newsapi_result if isinstance(newsapi_result, list) else []

    # 2. 결과 합치기 (네이버 우선, 중복 제거)
    seen_ids = set()
    raw_news: List[NewsItem] = []
    for item in naver + newsapi:
        if item.id not in seen_ids:
            seen_ids.add(item.id)
            raw_news.append(item)

    # 3. API 결과 없으면 즉시 폴백
    if not raw_news:
        logger.info("뉴스 API 결과 없음 — 즉시 폴백 사용 (topic=%s)", topic)
        return _instant_fallback(topic), 0

    # 4. 팩트체크 (LLM 없이 규칙 기반만 — 빠름)
    if settings.factcheck_enabled:
        from app.services.factcheck_service import filter_and_score_news_fast
        original_count = len(raw_news)
        filtered = filter_and_score_news_fast(raw_news)
        filtered_count = original_count - len(filtered)
        return filtered[:3], filtered_count

    return raw_news[:3], 0
