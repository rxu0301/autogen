"""뉴스 요약 스크립트 생성 서비스.

실제 방송 낭독 기준 분량:
  20초 -> 한국어 170~230자 / 영어 65~85 words
  30초 -> 한국어 260~360자 / 영어 95~130 words
  1분  -> 한국어 550~750자 / 영어 190~260 words
"""
from __future__ import annotations

import logging
from typing import List

import httpx

from app.config import settings
from app.models.content import ScriptVersion

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 분량 설정
# ---------------------------------------------------------------------------

DURATION_CONFIG = {
    "20s": {
        "ko": {"min": 170, "max": 230},
        "en": {"min_words": 65, "max_words": 85},
        "label_ko": "20s (170~230 chars)",
        "label_en": "20 seconds (65~85 words)",
        "structure_ko": (
            "1. Hook (20~30 chars)\n"
            "2. Key facts x1~2 (100~130 chars)\n"
            "3. Closing (30~40 chars)"
        ),
        "structure_en": (
            "1. Hook (10~15 words)\n"
            "2. Key facts x1~2 (40~55 words)\n"
            "3. Closing (10~15 words)"
        ),
    },
    "30s": {
        "ko": {"min": 260, "max": 360},
        "en": {"min_words": 95, "max_words": 130},
        "label_ko": "30s (260~360 chars)",
        "label_en": "30 seconds (95~130 words)",
        "structure_ko": (
            "1. Hook (25~35 chars)\n"
            "2. Background (50~70 chars)\n"
            "3. Key facts x2~3 (120~170 chars)\n"
            "4. Closing (40~50 chars)"
        ),
        "structure_en": (
            "1. Hook (10~15 words)\n"
            "2. Background (20~30 words)\n"
            "3. Key facts x2~3 (50~70 words)\n"
            "4. Closing (10~15 words)"
        ),
    },
    "1min": {
        "ko": {"min": 550, "max": 750},
        "en": {"min_words": 190, "max_words": 260},
        "label_ko": "1min (550~750 chars)",
        "label_en": "1 minute (190~260 words)",
        "structure_ko": (
            "1. Hook (30~50 chars)\n"
            "2. Background (100~140 chars)\n"
            "3. Key facts x3~4 (200~270 chars)\n"
            "4. Expert reaction (120~160 chars)\n"
            "5. Outlook + closing (60~80 chars)"
        ),
        "structure_en": (
            "1. Hook (15~20 words)\n"
            "2. Background (40~55 words)\n"
            "3. Key facts x3~4 (80~110 words)\n"
            "4. Expert reaction (40~55 words)\n"
            "5. Outlook + closing (20~30 words)"
        ),
    },
}

# duration 입력값 -> config key 매핑
_DURATION_KEY = {
    "20s": "20s", "20초": "20s",
    "30s": "30s", "30초": "30s",
    "1min": "1min", "1분": "1min",
}

STYLES = [
    {"version": 1, "style": "informative", "style_ko": "정보형", "desc": "Objective, fact-based, 5W1H"},
    {"version": 2, "style": "emotional",   "style_ko": "감성형", "desc": "Empathetic storytelling, connects with viewers"},
    {"version": 3, "style": "impactful",   "style_ko": "자극형", "desc": "Strong hook, urgency, curiosity-driven"},
]


def _get_cfg(duration: str) -> dict:
    key = _DURATION_KEY.get(duration, "30s")
    return DURATION_CONFIG[key]


def _count(text: str, language: str) -> int:
    return len(text) if language == "ko" else len(text.split())


# ---------------------------------------------------------------------------
# 프롬프트 빌더
# ---------------------------------------------------------------------------

def _build_script_prompt(title: str, content: str, duration: str, language: str = "ko") -> str:
    cfg = _get_cfg(duration)

    if language == "ko":
        min_c, max_c = cfg["ko"]["min"], cfg["ko"]["max"]
        label = cfg["label_ko"]
        structure = cfg["structure_ko"]
        unit = "chars"
        lang_label = "Korean"
    else:
        min_c, max_c = cfg["en"]["min_words"], cfg["en"]["max_words"]
        label = cfg["label_en"]
        structure = cfg["structure_en"]
        unit = "words"
        lang_label = "English"

    styles_desc = "\n".join(
        f"  Version{s['version']} [{s['style_ko']}]: {s['desc']}" for s in STYLES
    )

    return f"""You are a professional broadcast news script writer.
Write a news script for [{label}] duration.
Output language: {lang_label}

[News Title]
{title}

[News Content]
{content}

[REQUIRED LENGTH]
- Each version MUST be {min_c}~{max_c} {unit}
- Too short = failure. Add background, outlook, meaning to fill length.
- Too long = trim less important parts.

[Structure - follow this order]
{structure}

[3 Versions]
{styles_desc}

[Rules]
- Natural broadcast anchor speaking style
- Continuous text, no paragraph breaks
- Output in {lang_label} only

Output ONLY in this format (no extra text):

[Version1 - informative]
(script content)

[Version2 - emotional]
(script content)

[Version3 - impactful]
(script content)"""


# ---------------------------------------------------------------------------
# Ollama 생성
# ---------------------------------------------------------------------------

async def _generate_with_ollama(
    title: str, content: str, duration: str, language: str = "ko"
) -> List[ScriptVersion]:
    try:
        async with httpx.AsyncClient(timeout=settings.ollama_timeout) as client:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": _build_script_prompt(title, content, duration, language),
                    "stream": False,
                },
            )
            resp.raise_for_status()
            raw = resp.json().get("response", "")

        return _parse_scripts(raw, duration, language)

    except Exception as exc:
        logger.warning("Ollama script generation failed: %s", exc)
        return _fallback_scripts(title, content, duration, language)


def _parse_scripts(raw: str, duration: str, language: str = "ko") -> List[ScriptVersion]:
    import re
    cfg = _get_cfg(duration)
    min_c = cfg["ko"]["min"] if language == "ko" else cfg["en"]["min_words"]

    versions: List[ScriptVersion] = []
    patterns = [
        (1, "informative", "정보형", r"\[Version1[^\]]*\]\s*(.*?)(?=\[Version2|\Z)"),
        (2, "emotional",   "감성형", r"\[Version2[^\]]*\]\s*(.*?)(?=\[Version3|\Z)"),
        (3, "impactful",   "자극형", r"\[Version3[^\]]*\]\s*(.*?)(?=\[Version4|\Z)"),
    ]

    for ver, style_en, style_ko, pattern in patterns:
        m = re.search(pattern, raw, re.DOTALL)
        script = m.group(1).strip() if m else ""

        if _count(script, language) < min_c * 0.7:
            logger.warning("Script too short ver=%d count=%d min=%d, using fallback",
                           ver, _count(script, language), min_c)
            script = _build_fallback_text(ver, style_ko, duration, language, script)

        versions.append(ScriptVersion(
            version=ver,
            style=style_ko,
            script=script,
            word_count=len(script),
        ))

    if not versions:
        return _fallback_scripts("", "", duration, language)

    return versions


# ---------------------------------------------------------------------------
# 폴백 - duration별 분량 정확히 맞춤
# ---------------------------------------------------------------------------

_PADDING_KO = {
    "20s": [
        "전문가들은 상황을 주시하고 있습니다.",
        "관련 기관은 추가 조치를 검토 중입니다.",
        "앞으로의 전개가 주목됩니다.",
    ],
    "30s": [
        "전문가들은 이번 사안이 업계에 중요한 영향을 미칠 것으로 분석합니다.",
        "관련 기관은 공식 입장을 조만간 발표할 예정입니다.",
        "이해관계자들은 상황을 면밀히 주시하며 대응 방안을 마련하고 있습니다.",
        "이번 사안은 더 큰 변화의 시작점이 될 수 있다는 분석도 나옵니다.",
    ],
    "1min": [
        "전문가들은 이번 사안이 업계 전반에 걸쳐 광범위한 영향을 미칠 것으로 분석하고 있습니다.",
        "관련 기관의 공식 발표에 따르면, 이번 변화는 구조적인 전환점이 될 것으로 보입니다.",
        "이해관계자들은 다각도의 대응 방안을 마련하며 상황을 면밀히 주시하고 있습니다.",
        "업계 관계자들은 이번 사안이 기존 패러다임을 바꿀 중요한 계기가 될 것이라고 입을 모읍니다.",
        "일각에서는 파급효과에 대한 우려의 목소리도 나오고 있어 균형 잡힌 시각이 필요합니다.",
        "정부와 관련 기관은 종합적인 대책 마련에 나서고 있으며 조만간 구체적인 방향이 제시될 전망입니다.",
    ],
}

_PADDING_EN = {
    "20s": [
        "Experts are closely monitoring the situation.",
        "Authorities are reviewing additional measures.",
        "Further developments are expected soon.",
    ],
    "30s": [
        "Experts say this will have significant implications for the industry.",
        "Relevant authorities are expected to release an official statement soon.",
        "Stakeholders are preparing their responses as the situation unfolds.",
        "Analysts note this could mark the beginning of a broader shift.",
    ],
    "1min": [
        "Experts suggest this development will have far-reaching implications across the entire industry.",
        "According to official statements, this represents a fundamental structural shift.",
        "Stakeholders from various sectors are preparing comprehensive response strategies.",
        "Industry insiders agree this could serve as a pivotal moment for changing existing paradigms.",
        "Some voices have raised concerns about potential ripple effects, calling for a balanced perspective.",
        "Government agencies are working on countermeasures, with specific directions expected soon.",
    ],
}


def _build_fallback_text(
    version: int, style: str, duration: str, language: str, existing: str = ""
) -> str:
    cfg = _get_cfg(duration)
    dur_key = _DURATION_KEY.get(duration, "30s")

    if language == "ko":
        min_c, max_c = cfg["ko"]["min"], cfg["ko"]["max"]
    else:
        min_c, max_c = cfg["en"]["min_words"], cfg["en"]["max_words"]

    padding_pool = (_PADDING_KO if language == "ko" else _PADDING_EN).get(dur_key, [])

    if language == "ko":
        openings = {
            "정보형": "안녕하세요. 오늘의 주요 뉴스입니다. ",
            "감성형": "여러분, 오늘 꼭 알아야 할 소식이 있습니다. ",
            "자극형": "지금 바로 주목해야 할 뉴스입니다! ",
        }
        closings = {
            "정보형": " 앞으로의 상황을 계속 전해드리겠습니다.",
            "감성형": " 이 변화가 우리에게 어떤 의미인지 함께 생각해봐요.",
            "자극형": " 지금 바로 확인하세요!",
        }
    else:
        openings = {
            "정보형": "Here is today's top story. ",
            "감성형": "This is a story that matters to all of us. ",
            "자극형": "You need to hear this right now! ",
        }
        closings = {
            "정보형": " We will continue to follow this developing story.",
            "감성형": " Let us reflect on what this means for all of us.",
            "자극형": " Stay informed and don't be left behind!",
        }

    opening = openings.get(style, openings.get("정보형", ""))
    closing = closings.get(style, closings.get("정보형", ""))
    text = opening + (existing if existing else "")

    for pad in padding_pool:
        if _count(text + closing, language) >= min_c:
            break
        text += " " + pad

    idx = 0
    while _count(text + closing, language) < min_c and padding_pool:
        text += " " + padding_pool[idx % len(padding_pool)]
        idx += 1

    text += closing

    if language == "ko" and len(text) > max_c:
        text = text[:max_c]

    return text


def _fallback_scripts(
    title: str, content: str, duration: str, language: str = "ko"
) -> List[ScriptVersion]:
    base = (title + ". " + content) if content else title
    scripts = []
    for s in STYLES:
        script = _build_fallback_text(s["version"], s["style_ko"], duration, language, base)
        scripts.append(ScriptVersion(
            version=s["version"],
            style=s["style_ko"],
            script=script,
            word_count=len(script),
        ))
    return scripts


# ---------------------------------------------------------------------------
# 공개 인터페이스
# ---------------------------------------------------------------------------

async def generate_scripts(
    news_id: str,
    title: str,
    content: str,
    duration: str,
    language: str = "ko",
) -> List[ScriptVersion]:
    """뉴스 요약 스크립트 3가지 버전을 생성합니다."""
    logger.info("Script generation start - news_id=%s, duration=%s, language=%s",
                news_id, duration, language)

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            ollama_ok = resp.status_code == 200
    except Exception:
        ollama_ok = False

    if ollama_ok:
        return await _generate_with_ollama(title, content, duration, language)
    else:
        logger.info("Ollama unavailable - using fallback (duration=%s)", duration)
        return _fallback_scripts(title, content, duration, language)
