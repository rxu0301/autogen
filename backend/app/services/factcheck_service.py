"""팩트체크 서비스 — 뉴스 신뢰도 평가 및 가짜뉴스 필터링.

3가지 레이어로 신뢰도를 평가합니다:
  Layer 1 — 출처 신뢰도: 검증된 언론사 화이트리스트 기반
  Layer 2 — 교차 검증: 복수 출처 보도 여부 확인
  Layer 3 — LLM 분석: Ollama가 내용의 과장·선동·출처 부재 등을 감지
"""
from __future__ import annotations

import logging
import re
from typing import List, Literal

import httpx

from app.config import settings
from app.models.content import NewsItem, CredibilityInfo

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Layer 1: 신뢰 언론사 화이트리스트
# ---------------------------------------------------------------------------

# 국내 주요 언론사 (공영방송, 통신사, 주요 일간지)
TRUSTED_SOURCES_KO = {
    # 공영방송
    "kbs", "mbc", "sbs", "ebs",
    "kbs뉴스", "mbc뉴스", "sbs뉴스",
    # 통신사
    "연합뉴스", "뉴시스", "뉴스1",
    # 주요 일간지
    "조선일보", "중앙일보", "동아일보", "한겨레", "경향신문",
    "한국일보", "서울신문", "국민일보", "세계일보", "문화일보",
    # 경제지
    "매일경제", "한국경제", "서울경제", "파이낸셜뉴스", "머니투데이",
    "이데일리", "헤럴드경제", "아시아경제",
    # 방송
    "jtbc", "tv조선", "채널a", "mbn", "ytn",
    "jtbc뉴스", "ytn뉴스",
}

# 해외 주요 언론사
TRUSTED_SOURCES_EN = {
    "reuters", "ap", "associated press", "bbc", "bbc news",
    "the new york times", "nyt", "the washington post",
    "the guardian", "bloomberg", "financial times", "ft",
    "the economist", "wall street journal", "wsj",
    "cnn", "nbc news", "abc news", "cbs news",
    "npr", "pbs", "time", "newsweek",
    "afp", "dpa", "kyodo news",
}

# 신뢰도 낮은 출처 패턴 (블로그, 커뮤니티 등)
UNTRUSTED_PATTERNS = [
    r"블로그", r"카페", r"커뮤니티", r"인터넷 매체",
    r"유튜브", r"youtube", r"tiktok", r"틱톡",
    r"ai 생성", r"뉴스 에이전트",  # 시뮬레이션 뉴스
]


def _check_source_trust(source: str) -> tuple[int, str]:
    """출처 신뢰도를 확인합니다.

    Returns:
        (점수 0~40, 설명)
    """
    source_lower = source.lower().strip()

    # 신뢰 출처 확인
    for trusted in TRUSTED_SOURCES_KO | TRUSTED_SOURCES_EN:
        if trusted in source_lower or source_lower in trusted:
            return 40, f"✅ 검증된 언론사 ({source})"

    # 비신뢰 패턴 확인
    for pattern in UNTRUSTED_PATTERNS:
        if re.search(pattern, source_lower):
            return 0, f"⚠️ 신뢰도 낮은 출처 ({source})"

    # 알 수 없는 출처
    return 20, f"❓ 출처 미확인 ({source})"


# ---------------------------------------------------------------------------
# Layer 2: 교차 검증 — 복수 출처 보도 여부
# ---------------------------------------------------------------------------

def _check_cross_verification(news_list: List[NewsItem], target: NewsItem) -> tuple[int, str]:
    """같은 주제를 다른 출처에서도 보도했는지 확인합니다.

    Returns:
        (점수 0~30, 설명)
    """
    # 제목에서 핵심 키워드 추출 (3글자 이상 단어)
    keywords = [w for w in re.split(r"[\s,·\-]+", target.title) if len(w) >= 3]
    if not keywords:
        return 15, "❓ 교차 검증 불가 (키워드 부족)"

    # 다른 뉴스들과 키워드 겹침 확인
    corroborating_sources = set()
    for other in news_list:
        if other.id == target.id:
            continue
        other_text = other.title + " " + other.summary
        matches = sum(1 for kw in keywords if kw in other_text)
        if matches >= 2:  # 키워드 2개 이상 겹치면 같은 사건으로 판단
            corroborating_sources.add(other.source)

    if len(corroborating_sources) >= 2:
        return 30, f"✅ {len(corroborating_sources)+1}개 출처에서 교차 확인됨"
    elif len(corroborating_sources) == 1:
        return 20, f"🔶 2개 출처에서 보도됨"
    else:
        return 10, "⚠️ 단독 보도 (교차 확인 불가)"


# ---------------------------------------------------------------------------
# Layer 3: LLM 콘텐츠 분석
# ---------------------------------------------------------------------------

_FACTCHECK_PROMPT = """너는 팩트체크 전문가다. 아래 뉴스를 분석하여 신뢰도를 평가하라.

[뉴스 제목]
{title}

[뉴스 내용]
{summary}

[출처]
{source}

다음 항목을 각각 분석하라:
1. 과장/선동적 표현 여부 (예: "충격", "경악", "반드시", "무조건" 등 감정 자극 언어)
2. 구체적 수치/근거 제시 여부
3. 익명 출처 또는 "관계자에 따르면" 등 불명확한 인용 여부
4. 음모론적 주장 여부
5. 전반적 신뢰도 평가

반드시 아래 형식으로만 답하라:

과장표현: 있음/없음
구체근거: 있음/없음
익명출처: 있음/없음
음모론: 있음/없음
신뢰도점수: 0~30 (숫자만)
분석요약: (한 문장)"""


async def _check_content_with_llm(title: str, summary: str, source: str) -> tuple[int, str]:
    """Ollama LLM으로 뉴스 내용의 신뢰도를 분석합니다.

    Returns:
        (점수 0~30, 분석 요약)
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": _FACTCHECK_PROMPT.format(
                        title=title, summary=summary[:300], source=source
                    ),
                    "stream": False,
                },
            )
            resp.raise_for_status()
            raw = resp.json().get("response", "")

        return _parse_llm_factcheck(raw)

    except Exception as exc:
        logger.warning("LLM 팩트체크 실패: %s", exc)
        return _rule_based_content_check(title, summary)


def _parse_llm_factcheck(raw: str) -> tuple[int, str]:
    """LLM 팩트체크 응답을 파싱합니다."""
    score = 15  # 기본값

    # 점수 추출
    score_m = re.search(r"신뢰도점수:\s*(\d+)", raw)
    if score_m:
        score = min(30, max(0, int(score_m.group(1))))

    # 감점 요소 확인
    deductions = 0
    if re.search(r"과장표현:\s*있음", raw):
        deductions += 5
    if re.search(r"익명출처:\s*있음", raw):
        deductions += 3
    if re.search(r"음모론:\s*있음", raw):
        deductions += 10
    if re.search(r"구체근거:\s*없음", raw):
        deductions += 3

    score = max(0, score - deductions)

    # 분석 요약 추출
    summary_m = re.search(r"분석요약:\s*(.+)", raw)
    summary = summary_m.group(1).strip() if summary_m else "LLM 분석 완료"

    # 아이콘 추가
    if score >= 22:
        icon = "✅"
    elif score >= 12:
        icon = "🔶"
    else:
        icon = "🚨"

    return score, f"{icon} {summary}"


def _rule_based_content_check(title: str, summary: str) -> tuple[int, str]:
    """LLM 미가용 시 규칙 기반 콘텐츠 분석."""
    text = title + " " + summary
    score = 20
    issues = []

    # 선동적 표현 감지
    sensational = ["충격", "경악", "경고", "반드시", "무조건", "절대", "폭로",
                   "충격적", "믿을 수 없는", "전격", "긴급", "속보", "단독"]
    found_sensational = [w for w in sensational if w in text]
    if len(found_sensational) >= 2:
        score -= 8
        issues.append(f"선동적 표현 다수 ({', '.join(found_sensational[:2])})")
    elif found_sensational:
        score -= 3
        issues.append(f"선동적 표현 ({found_sensational[0]})")

    # 구체적 수치 존재 여부
    has_numbers = bool(re.search(r"\d+[%억만원명개]", text))
    if has_numbers:
        score += 3

    # 음모론 키워드
    conspiracy = ["음모", "조작", "숨겨진", "진실은", "알려지지 않은", "비밀"]
    if any(w in text for w in conspiracy):
        score -= 10
        issues.append("음모론적 표현 감지")

    score = max(0, min(30, score))

    if not issues:
        return score, "✅ 특이 사항 없음 (규칙 기반)"
    else:
        icon = "🔶" if score >= 12 else "🚨"
        return score, f"{icon} {', '.join(issues)}"


# ---------------------------------------------------------------------------
# 통합 신뢰도 평가
# ---------------------------------------------------------------------------

async def evaluate_credibility(
    news: NewsItem,
    all_news: List[NewsItem],
    use_llm: bool = True,
) -> CredibilityInfo:
    """뉴스 아이템의 종합 신뢰도를 평가합니다.

    총점 100점:
      - Layer 1 (출처 신뢰도): 40점
      - Layer 2 (교차 검증):   30점
      - Layer 3 (콘텐츠 분석): 30점
    """
    # Layer 1
    source_score, source_reason = _check_source_trust(news.source)

    # Layer 2
    cross_score, cross_reason = _check_cross_verification(all_news, news)

    # Layer 3
    if use_llm:
        content_score, content_reason = await _check_content_with_llm(
            news.title, news.summary, news.source
        )
    else:
        content_score, content_reason = _rule_based_content_check(
            news.title, news.summary
        )

    total = source_score + cross_score + content_score

    # 등급 결정
    if total >= 75:
        grade: Literal["high", "medium", "low", "unverified"] = "high"
        grade_label = "높음"
        grade_icon = "✅"
    elif total >= 50:
        grade = "medium"
        grade_label = "보통"
        grade_icon = "🔶"
    elif total >= 25:
        grade = "low"
        grade_label = "낮음"
        grade_icon = "⚠️"
    else:
        grade = "unverified"
        grade_label = "미검증"
        grade_icon = "🚨"

    logger.info(
        "팩트체크 완료 — title='%s' total=%d grade=%s",
        news.title[:30], total, grade
    )

    return CredibilityInfo(
        score=total,
        grade=grade,
        grade_label=f"{grade_icon} {grade_label}",
        source_score=source_score,
        source_reason=source_reason,
        cross_score=cross_score,
        cross_reason=cross_reason,
        content_score=content_score,
        content_reason=content_reason,
        is_filtered=total < settings.factcheck_min_score,
    )


async def filter_and_score_news(
    news_list: List[NewsItem],
) -> List[NewsItem]:
    """뉴스 목록에 신뢰도 점수를 부여하고, 기준 미달 뉴스를 필터링합니다.
    (LLM 포함 — 느림, 직접 호출 시 사용)
    """
    scored: List[NewsItem] = []

    for news in news_list:
        credibility = await evaluate_credibility(news, news_list)
        news.credibility = credibility

        if not credibility.is_filtered:
            scored.append(news)
        else:
            logger.info(
                "뉴스 필터링됨 — title='%s' score=%d (기준: %d)",
                news.title[:30], credibility.score, settings.factcheck_min_score
            )

    scored.sort(key=lambda n: n.credibility.score if n.credibility else 0, reverse=True)

    if not scored:
        logger.warning("모든 뉴스가 필터링됨 — 원본 반환 (경고 표시)")
        for news in news_list:
            if news.credibility:
                news.credibility.is_filtered = False
        return news_list

    return scored[:3]


def filter_and_score_news_fast(news_list: List[NewsItem]) -> List[NewsItem]:
    """규칙 기반 팩트체크만 사용하는 빠른 버전 (LLM 호출 없음).

    뉴스 검색 응답 속도를 위해 Layer 3 LLM 분석을 스킵하고
    Layer 1 (출처) + Layer 2 (교차검증) + 규칙 기반 콘텐츠 분석만 수행합니다.
    """
    scored: List[NewsItem] = []

    for news in news_list:
        source_score, source_reason = _check_source_trust(news.source)
        cross_score, cross_reason = _check_cross_verification(news_list, news)
        content_score, content_reason = _rule_based_content_check(news.title, news.summary)

        total = source_score + cross_score + content_score

        if total >= 75:
            grade: Literal["high", "medium", "low", "unverified"] = "high"
            grade_label, grade_icon = "높음", "✅"
        elif total >= 50:
            grade = "medium"
            grade_label, grade_icon = "보통", "🔶"
        elif total >= 25:
            grade = "low"
            grade_label, grade_icon = "낮음", "⚠️"
        else:
            grade = "unverified"
            grade_label, grade_icon = "미검증", "🚨"

        news.credibility = CredibilityInfo(
            score=total,
            grade=grade,
            grade_label=f"{grade_icon} {grade_label}",
            source_score=source_score,
            source_reason=source_reason,
            cross_score=cross_score,
            cross_reason=cross_reason,
            content_score=content_score,
            content_reason=content_reason,
            is_filtered=total < settings.factcheck_min_score,
        )

        if not news.credibility.is_filtered:
            scored.append(news)

    scored.sort(key=lambda n: n.credibility.score if n.credibility else 0, reverse=True)

    if not scored:
        for news in news_list:
            if news.credibility:
                news.credibility.is_filtered = False
        return news_list

    return scored
