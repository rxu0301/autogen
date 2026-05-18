"""뉴스 요약본 생성 서비스 (읽기용, 500~900자).

스크립트와 달리 읽기 전용 텍스트로, 뉴스 내용을 심층 분석하거나
핵심만 추출하거나 스토리텔링 형식으로 제공합니다.
"""
from __future__ import annotations

import logging
from typing import List

import httpx

from app.config import settings
from app.models.content import SummaryVersion

logger = logging.getLogger(__name__)

# 요약본 목표 글자 수: 500~900자
SUMMARY_CHARS = (500, 900)

SUMMARY_STYLES = [
    {"version": 1, "style": "심층분석형", "desc": "배경, 원인, 영향, 전망까지 상세 분석"},
    {"version": 2, "style": "핵심요약형", "desc": "5W1H 중심으로 핵심만 간결하게 정리"},
    {"version": 3, "style": "스토리텔링형", "desc": "사건의 흐름을 이야기처럼 풀어서 설명"},
]


def _build_summary_prompt(title: str, content: str, language: str = "ko") -> str:
    min_chars, max_chars = SUMMARY_CHARS
    lang_label = "한국어" if language == "ko" else "영어(English)"
    styles_desc = "\n".join(
        f"버전{s['version']} ({s['style']}): {s['desc']}" for s in SUMMARY_STYLES
    )
    return f"""너는 뉴스 요약 전문가다.
아래 뉴스를 {min_chars}~{max_chars}자 분량의 읽기용 요약본으로 작성하라.
출력 언어: {lang_label}

[뉴스 제목]
{title}

[뉴스 내용]
{content}

[작성 지침]
- 반드시 3가지 버전으로 작성
- 각 버전은 {min_chars}~{max_chars}자 (짧으면 안 됨, 충분히 길게)
- 읽기 전용 텍스트 (낭독용 아님)
- 문단 구분, 소제목 사용 가능
- 출력 언어({lang_label})로만 작성

{styles_desc}

반드시 아래 형식으로 출력하라:

[버전1 - 심층분석형]
(요약본 내용)

[버전2 - 핵심요약형]
(요약본 내용)

[버전3 - 스토리텔링형]
(요약본 내용)"""


async def _generate_with_ollama(title: str, content: str, language: str = "ko") -> List[SummaryVersion]:
    """Ollama LLM으로 요약본 생성."""
    try:
        async with httpx.AsyncClient(timeout=settings.ollama_timeout) as client:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": _build_summary_prompt(title, content, language),
                    "stream": False,
                },
            )
            resp.raise_for_status()
            raw = resp.json().get("response", "")

        return _parse_summaries(raw)

    except Exception as exc:
        logger.warning("Ollama 요약본 생성 실패: %s", exc)
        return _fallback_summaries(title, content, language)


def _parse_summaries(raw: str) -> List[SummaryVersion]:
    """LLM 응답을 파싱하여 SummaryVersion 목록으로 변환."""
    import re
    versions: List[SummaryVersion] = []

    patterns = [
        (1, "심층분석형", r"\[버전1[^\]]*\]\s*(.*?)(?=\[버전2|\Z)"),
        (2, "핵심요약형", r"\[버전2[^\]]*\]\s*(.*?)(?=\[버전3|\Z)"),
        (3, "스토리텔링형", r"\[버전3[^\]]*\]\s*(.*?)(?=\[버전4|\Z)"),
    ]

    for ver, style, pattern in patterns:
        m = re.search(pattern, raw, re.DOTALL)
        summary = m.group(1).strip() if m else ""
        if not summary:
            summary = _fallback_summary_text(ver, style)

        versions.append(SummaryVersion(
            version=ver,
            style=style,
            summary=summary,
            char_count=len(summary),
        ))

    if not versions:
        return _fallback_summaries("", "", "ko")

    return versions


def _fallback_summary_text(version: int, style: str, language: str = "ko") -> str:
    """단일 버전 폴백 요약본."""
    if language == "en":
        if style == "심층분석형":
            return """This news story represents a significant development in the field. According to multiple sources and expert analysis, the situation has evolved from initial reports into a more complex scenario with far-reaching implications.

Background: The events leading to this development have been building over recent months, with various stakeholders expressing concerns about potential outcomes. Industry experts have been monitoring the situation closely, noting several key indicators that suggested this outcome was possible.

Current Status: As of now, the situation continues to develop with new information emerging regularly. Authorities and relevant organizations are working to address the immediate concerns while also planning for longer-term implications.

Impact: The effects of this development are expected to be felt across multiple sectors, affecting not only direct stakeholders but also related industries and the general public. Analysts predict that adjustments will be necessary in the coming weeks and months.

Outlook: Looking ahead, experts suggest that this situation will likely serve as a catalyst for broader changes in policy and practice. Stakeholders are advised to stay informed and prepared for potential developments."""
        elif style == "핵심요약형":
            return """What: A significant development has occurred in this field, marking an important milestone.

When: The event took place recently, with effects becoming apparent immediately.

Where: The situation is centered in the relevant region/sector, with potential ripple effects elsewhere.

Who: Key stakeholders include industry leaders, regulatory bodies, and affected communities.

Why: The development stems from a combination of factors including market conditions, policy changes, and technological advances.

How: The situation unfolded through a series of events, culminating in the current state.

Significance: This development is expected to have lasting implications for the industry and related sectors, requiring attention from all stakeholders."""
        else:
            return """The story begins with an unexpected turn of events that caught many by surprise. What started as a routine situation quickly evolved into something far more significant, drawing attention from experts and observers alike.

As the situation unfolded, it became clear that this was no ordinary development. Behind the scenes, various factors had been converging, setting the stage for what would become a pivotal moment in the field.

The human element of this story cannot be overlooked. Real people, with real concerns and aspirations, found themselves at the center of events that would shape their futures and the futures of many others.

Now, as we look at where things stand, the full picture is beginning to emerge. The implications extend far beyond the immediate circumstances, touching on broader themes of change, adaptation, and progress.

The story continues to unfold, with each new development adding another layer to an already complex narrative. What happens next will depend on the choices made by key stakeholders and the broader forces at play in the field."""
    else:
        if style == "심층분석형":
            return """이번 뉴스는 해당 분야에서 중요한 전환점이 될 것으로 보입니다. 복수의 소식통과 전문가 분석에 따르면, 상황은 초기 보도에서 더욱 복잡한 양상으로 발전하며 광범위한 파급효과를 낳고 있습니다.

배경: 이번 사건으로 이어진 일련의 과정은 최근 수개월간 진행되어 왔으며, 다양한 이해관계자들이 잠재적 결과에 대한 우려를 표명해왔습니다. 업계 전문가들은 상황을 면밀히 모니터링하며 이러한 결과가 가능하다는 여러 핵심 지표를 주목해왔습니다.

현재 상황: 현재 상황은 새로운 정보가 정기적으로 나오면서 계속 전개되고 있습니다. 당국과 관련 기관들은 즉각적인 우려사항을 해결하는 동시에 장기적 영향에 대한 계획도 수립하고 있습니다.

영향: 이번 사건의 영향은 여러 부문에 걸쳐 나타날 것으로 예상되며, 직접적인 이해관계자뿐만 아니라 관련 산업과 일반 대중에게도 영향을 미칠 것입니다. 분석가들은 향후 몇 주, 몇 달 동안 조정이 필요할 것으로 예측합니다.

전망: 앞으로 전문가들은 이 상황이 정책과 관행의 광범위한 변화를 위한 촉매제 역할을 할 것으로 보고 있습니다. 이해관계자들은 잠재적 발전 상황에 대해 정보를 유지하고 대비할 것을 권고받고 있습니다."""
        elif style == "핵심요약형":
            return """무엇: 해당 분야에서 중요한 이정표가 되는 주요 사건이 발생했습니다.

언제: 최근 사건이 발생했으며, 그 영향은 즉시 나타나기 시작했습니다.

어디서: 상황은 관련 지역/부문을 중심으로 전개되고 있으며, 다른 곳으로도 파급효과가 예상됩니다.

누가: 주요 이해관계자로는 업계 리더, 규제 기관, 영향을 받는 커뮤니티가 포함됩니다.

왜: 이번 사건은 시장 상황, 정책 변화, 기술 발전 등 여러 요인이 복합적으로 작용한 결과입니다.

어떻게: 상황은 일련의 사건을 통해 전개되었으며, 현재 상태에 이르렀습니다.

의의: 이번 사건은 업계와 관련 부문에 지속적인 영향을 미칠 것으로 예상되며, 모든 이해관계자의 주의가 필요합니다."""
        else:
            return """이야기는 많은 이들을 놀라게 한 예상치 못한 전개로 시작됩니다. 일상적인 상황으로 시작된 것이 빠르게 훨씬 더 중요한 것으로 발전하며, 전문가와 관찰자들의 관심을 끌었습니다.

상황이 전개되면서, 이것이 평범한 사건이 아니라는 것이 분명해졌습니다. 무대 뒤에서는 다양한 요인들이 수렴하고 있었고, 이 분야에서 중요한 순간이 될 무대를 마련하고 있었습니다.

이 이야기의 인간적 요소를 간과할 수 없습니다. 실제 사람들이 실제 우려와 열망을 가지고, 자신과 많은 다른 이들의 미래를 형성할 사건의 중심에 서게 되었습니다.

이제 현재 상황을 보면, 전체 그림이 드러나기 시작하고 있습니다. 그 의미는 즉각적인 상황을 훨씬 넘어서, 변화, 적응, 진보라는 더 넓은 주제를 다루고 있습니다.

이야기는 계속 전개되고 있으며, 각각의 새로운 발전이 이미 복잡한 서사에 또 다른 층을 더하고 있습니다. 다음에 무슨 일이 일어날지는 주요 이해관계자들의 선택과 이 분야에서 작용하는 더 넓은 힘에 달려 있습니다."""


def _fallback_summaries(title: str, content: str, language: str = "ko") -> List[SummaryVersion]:
    """Ollama 실패 시 규칙 기반 요약본 생성."""
    base = content[:600] if content else title

    if language == "en":
        summaries = [
            SummaryVersion(
                version=1, style="심층분석형",
                summary=f"In-depth Analysis:\n\n{base}\n\nThis development represents a significant shift in the field. Experts suggest that the implications will be felt across multiple sectors, requiring careful attention from stakeholders. The situation continues to evolve, with new information emerging regularly.",
                char_count=len(base) + 200,
            ),
            SummaryVersion(
                version=2, style="핵심요약형",
                summary=f"Key Summary:\n\n{base}\n\nMain points: This event marks an important milestone. Stakeholders are advised to monitor developments closely. Further updates are expected in the coming days.",
                char_count=len(base) + 150,
            ),
            SummaryVersion(
                version=3, style="스토리텔링형",
                summary=f"The Story:\n\n{base}\n\nAs events unfolded, it became clear that this was more than a routine development. The human element cannot be overlooked, as real people find themselves at the center of changes that will shape the future.",
                char_count=len(base) + 180,
            ),
        ]
    else:
        summaries = [
            SummaryVersion(
                version=1, style="심층분석형",
                summary=f"심층 분석:\n\n{base}\n\n이번 사건은 해당 분야에서 중요한 전환점이 될 것으로 보입니다. 전문가들은 그 영향이 여러 부문에 걸쳐 나타날 것으로 예상하며, 이해관계자들의 세심한 주의가 필요하다고 조언합니다. 상황은 계속 전개되고 있으며, 새로운 정보가 정기적으로 나오고 있습니다.",
                char_count=len(base) + 150,
            ),
            SummaryVersion(
                version=2, style="핵심요약형",
                summary=f"핵심 요약:\n\n{base}\n\n주요 포인트: 이번 사건은 중요한 이정표입니다. 이해관계자들은 상황 전개를 면밀히 모니터링할 것을 권고받고 있습니다. 추가 업데이트가 곧 예상됩니다.",
                char_count=len(base) + 120,
            ),
            SummaryVersion(
                version=3, style="스토리텔링형",
                summary=f"이야기:\n\n{base}\n\n사건이 전개되면서, 이것이 일상적인 사건 이상이라는 것이 분명해졌습니다. 실제 사람들이 미래를 형성할 변화의 중심에 서 있다는 인간적 요소를 간과할 수 없습니다.",
                char_count=len(base) + 130,
            ),
        ]
    return summaries


# ---------------------------------------------------------------------------
# 공개 인터페이스
# ---------------------------------------------------------------------------

async def generate_summaries(
    news_id: str,
    title: str,
    content: str,
    language: str = "ko",
) -> List[SummaryVersion]:
    """뉴스 요약본 3가지 버전을 생성합니다 (500~900자)."""
    logger.info("요약본 생성 시작 — news_id=%s, language=%s", news_id, language)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            ollama_ok = resp.status_code == 200
    except Exception:
        ollama_ok = False

    if ollama_ok:
        return await _generate_with_ollama(title, content, language)
    else:
        logger.info("Ollama 미가용 — 폴백 요약본 생성")
        return _fallback_summaries(title, content, language)
