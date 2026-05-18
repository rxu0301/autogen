"""썸네일 이미지 생성 프롬프트 서비스.

뉴스 내용을 읽고 그 장면/상황을 시각화하는 이미지 프롬프트를
3가지 아트 스타일로 생성합니다:
  버전 1 — 애니메이션 (anime / animated style)
  버전 2 — 실사/자연스러운 (photorealistic / cinematic)
  버전 3 — 카툰 (cartoon / comic style)

Pollinations.ai API로 실제 이미지를 생성합니다 (무료, 키 불필요).
"""
from __future__ import annotations

import logging
import urllib.parse
from typing import List

import httpx

from app.config import settings
from app.models.content import ThumbnailPrompt

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pollinations.ai 이미지 생성
# ---------------------------------------------------------------------------

POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"

# 스타일별 Pollinations 모델 파라미터
STYLE_MODELS = {
    "애니메이션": "flux",       # 애니메이션에 적합
    "실사":       "flux-realism",  # 실사 전용 모델
    "카툰":       "flux",       # 카툰/일러스트
}

def _make_image_url(prompt_en: str, style: str, width: int = 1280, height: int = 720) -> str:
    """Pollinations.ai 이미지 URL 생성 (16:9)."""
    encoded = urllib.parse.quote(prompt_en)
    model = STYLE_MODELS.get(style, "flux")
    return (
        f"{POLLINATIONS_BASE}/{encoded}"
        f"?width={width}&height={height}&model={model}&nologo=true&enhance=true"
    )


# ---------------------------------------------------------------------------
# 아트 스타일 정의
# ---------------------------------------------------------------------------

ART_STYLES = [
    {
        "version": 1,
        "style": "애니메이션",
        "style_en": "anime",
        "suffix_en": (
            "anime style, vibrant colors, dynamic composition, "
            "detailed background, Studio Ghibli inspired, "
            "expressive characters, cinematic anime scene, 16:9"
        ),
        "suffix_ko": "애니메이션 스타일, 선명한 색감, 역동적인 구도, 스튜디오 지브리 느낌",
    },
    {
        "version": 2,
        "style": "실사",
        "style_en": "photorealistic",
        "suffix_en": (
            "photorealistic, cinematic photography, natural lighting, "
            "high resolution, DSLR quality, documentary style, "
            "realistic textures, 8K, 16:9"
        ),
        "suffix_ko": "실사 사진 스타일, 시네마틱 조명, 다큐멘터리 느낌, 고해상도",
    },
    {
        "version": 3,
        "style": "카툰",
        "style_en": "cartoon",
        "suffix_en": (
            "cartoon style, bold outlines, flat colors, "
            "comic book illustration, expressive and fun, "
            "clean vector art, editorial cartoon, 16:9"
        ),
        "suffix_ko": "카툰/만화 스타일, 굵은 윤곽선, 플랫 컬러, 에디토리얼 일러스트",
    },
]


# ---------------------------------------------------------------------------
# LLM 프롬프트 빌더 — 뉴스 내용 → 시각 장면 묘사
# ---------------------------------------------------------------------------

def _build_thumbnail_prompt(title: str, content: str, hashtags: List[str]) -> str:
    tags_str = " ".join(hashtags[:5])
    return f"""너는 AI 이미지 생성 전문가다.
아래 뉴스를 읽고, 그 뉴스의 핵심 장면이나 상황을 시각적으로 표현하는
이미지 생성 프롬프트를 3가지 아트 스타일로 작성하라.

[뉴스 제목]
{title}

[뉴스 내용]
{content[:400]}

[관련 해시태그]
{tags_str}

[핵심 지침]
- 뉴스 내용을 읽고 그 상황/장면을 상상하여 묘사하라
- 텍스트나 글자를 프롬프트에 포함하지 말 것 (이미지 생성 AI는 텍스트 렌더링이 불가)
- 구체적인 장면, 인물, 배경, 분위기, 색감을 묘사하라
- 각 버전은 영문 프롬프트(prompt_en)와 한국어 설명(prompt_ko)을 작성
- 영문 프롬프트는 Stable Diffusion / DALL-E에 바로 입력 가능한 형태

[아트 스타일]
버전1 (애니메이션): 애니메이션/지브리 스타일로 장면 묘사
버전2 (실사): 실제 사진처럼 자연스럽고 사실적인 장면 묘사
버전3 (카툰): 만화/카툰 스타일로 장면 묘사

반드시 아래 형식으로 출력하라:

[버전1 - 애니메이션]
영문: (영문 프롬프트)
한국어: (한국어 설명)

[버전2 - 실사]
영문: (영문 프롬프트)
한국어: (한국어 설명)

[버전3 - 카툰]
영문: (영문 프롬프트)
한국어: (한국어 설명)"""


# ---------------------------------------------------------------------------
# LLM 생성
# ---------------------------------------------------------------------------

async def _generate_with_ollama(
    title: str, content: str, hashtags: List[str]
) -> List[ThumbnailPrompt]:
    try:
        async with httpx.AsyncClient(timeout=settings.ollama_timeout) as client:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": _build_thumbnail_prompt(title, content, hashtags),
                    "stream": False,
                },
            )
            resp.raise_for_status()
            raw = resp.json().get("response", "")

        return _parse_prompts(raw, title, content, hashtags)

    except Exception as exc:
        logger.warning("Ollama 썸네일 프롬프트 생성 실패: %s", exc)
        return _fallback_prompts(title, content, hashtags)


def _parse_prompts(
    raw: str, title: str, content: str, hashtags: List[str]
) -> List[ThumbnailPrompt]:
    import re
    prompts: List[ThumbnailPrompt] = []

    patterns = [
        (1, "애니메이션", r"\[버전1[^\]]*\]\s*(.*?)(?=\[버전2|\Z)"),
        (2, "실사",       r"\[버전2[^\]]*\]\s*(.*?)(?=\[버전3|\Z)"),
        (3, "카툰",       r"\[버전3[^\]]*\]\s*(.*?)(?=\[버전4|\Z)"),
    ]

    for ver, style, pattern in patterns:
        m = re.search(pattern, raw, re.DOTALL)
        block = m.group(1).strip() if m else ""

        en_m = re.search(r"영문:\s*(.+?)(?=한국어:|$)", block, re.DOTALL)
        ko_m = re.search(r"한국어:\s*(.+?)(?=\[버전|\Z)", block, re.DOTALL)

        base_en = en_m.group(1).strip() if en_m else ""
        prompt_ko = ko_m.group(1).strip() if ko_m else ""

        if not base_en:
            base_en = _fallback_scene_en(title, content, style)
        if not prompt_ko:
            prompt_ko = _fallback_scene_ko(title, content, style)

        # 아트 스타일 suffix 추가
        art = next((a for a in ART_STYLES if a["style"] == style), ART_STYLES[ver - 1])
        prompt_en = f"{base_en}, {art['suffix_en']}"

        prompts.append(ThumbnailPrompt(
            version=ver,
            style=style,
            prompt_en=prompt_en,
            prompt_ko=f"{prompt_ko} ({art['suffix_ko']})",
        ))

    if not prompts:
        return _fallback_prompts(title, content, hashtags)

    return prompts


# ---------------------------------------------------------------------------
# 폴백 — 뉴스 내용 기반 장면 묘사 규칙
# ---------------------------------------------------------------------------

# 뉴스 키워드 → 장면 매핑
_SCENE_KEYWORDS = {
    # 기술/AI
    ("ai", "인공지능", "로봇", "자동화", "딥러닝", "머신러닝"): {
        "scene_en": "a glowing humanoid robot and human shaking hands in a futuristic city, neon lights, digital data streams flowing around them",
        "scene_ko": "미래 도시에서 빛나는 로봇과 인간이 악수하는 장면, 네온 불빛, 디지털 데이터 흐름",
    },
    # 경제/금융
    ("경제", "주식", "금융", "시장", "투자", "코인", "비트코인", "달러"): {
        "scene_en": "a dramatic stock market trading floor with rising and falling graphs, intense traders, golden light, financial charts",
        "scene_ko": "주식 거래소 바닥에서 급등락하는 그래프와 긴장한 트레이더들, 황금빛 조명",
    },
    # 환경/기후
    ("기후", "환경", "탄소", "온난화", "태풍", "홍수", "산불", "지진"): {
        "scene_en": "a dramatic landscape showing the contrast between a lush green forest and a barren wasteland, stormy sky, environmental crisis",
        "scene_ko": "울창한 숲과 황폐한 땅의 극적인 대비, 폭풍우 하늘, 환경 위기 장면",
    },
    # 정치/사회
    ("정치", "선거", "대통령", "국회", "정부", "외교", "전쟁", "평화"): {
        "scene_en": "a grand government building with flags waving, crowd of people gathered in a public square, dramatic sky, political atmosphere",
        "scene_ko": "깃발이 펄럭이는 정부 청사, 광장에 모인 군중, 극적인 하늘, 정치적 분위기",
    },
    # 의료/건강
    ("의료", "병원", "백신", "치료", "건강", "바이러스", "코로나", "암"): {
        "scene_en": "a modern hospital corridor with doctors in white coats rushing, blue and white lighting, medical equipment, sense of urgency",
        "scene_ko": "현대 병원 복도에서 달려가는 의사들, 파란 조명, 의료 장비, 긴박한 분위기",
    },
    # 우주/과학
    ("우주", "로켓", "위성", "nasa", "달", "화성", "천문"): {
        "scene_en": "a rocket launching into a starry night sky, bright exhaust flames, vast cosmos, Earth visible in the background",
        "scene_ko": "별이 가득한 밤하늘로 발사되는 로켓, 밝은 화염, 광활한 우주, 배경의 지구",
    },
    # 스포츠
    ("스포츠", "축구", "야구", "올림픽", "월드컵", "선수", "경기"): {
        "scene_en": "an athlete in peak performance moment, stadium lights blazing, crowd cheering, motion blur, triumphant expression",
        "scene_ko": "최고의 순간을 맞이한 선수, 경기장 조명, 환호하는 관중, 모션 블러, 승리의 표정",
    },
}

_DEFAULT_SCENE = {
    "scene_en": "a dramatic news scene with people in the foreground, city skyline in the background, golden hour lighting, sense of importance and urgency",
    "scene_ko": "전경의 사람들과 도시 스카이라인 배경의 극적인 뉴스 장면, 황금빛 조명, 중요성과 긴박감",
}


def _detect_scene(title: str, content: str) -> dict:
    """뉴스 제목/내용에서 적합한 장면을 감지합니다."""
    text = (title + " " + content).lower()
    for keywords, scene in _SCENE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return scene
    return _DEFAULT_SCENE


def _fallback_scene_en(title: str, content: str, style: str) -> str:
    scene = _detect_scene(title, content)
    return scene["scene_en"]


def _fallback_scene_ko(title: str, content: str, style: str) -> str:
    scene = _detect_scene(title, content)
    return scene["scene_ko"]


def _fallback_prompts(title: str, content: str, hashtags: List[str]) -> List[ThumbnailPrompt]:
    """Ollama 실패 시 키워드 기반 장면 묘사 프롬프트 생성."""
    scene = _detect_scene(title, content)
    prompts = []

    for art in ART_STYLES:
        prompt_en = f"{scene['scene_en']}, {art['suffix_en']}"
        prompt_ko = f"{scene['scene_ko']} ({art['suffix_ko']})"
        prompts.append(ThumbnailPrompt(
            version=art["version"],
            style=art["style"],
            prompt_en=prompt_en,
            prompt_ko=prompt_ko,
        ))

    return prompts


# ---------------------------------------------------------------------------
# 공개 인터페이스
# ---------------------------------------------------------------------------

async def generate_thumbnail_prompts(
    news_id: str,
    title: str,
    script: str,
    hashtags: List[str],
) -> List[ThumbnailPrompt]:
    """뉴스 내용을 시각화하는 썸네일 프롬프트 3가지(애니메이션/실사/카툰)를 생성합니다."""
    logger.info("썸네일 프롬프트 생성 시작 — news_id=%s", news_id)

    # Ollama 가용성 확인
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            ollama_ok = resp.status_code == 200
    except Exception:
        ollama_ok = False

    if ollama_ok:
        prompts = await _generate_with_ollama(title, script, hashtags)
    else:
        logger.info("Ollama 미가용 — 키워드 기반 장면 묘사 프롬프트 생성")
        prompts = _fallback_prompts(title, script, hashtags)

    # Pollinations 이미지 URL 첨부 (스타일별 모델 적용)
    for p in prompts:
        p.image_url = _make_image_url(p.prompt_en, p.style)
        logger.debug("이미지 URL 생성 — style=%s url=%s", p.style, p.image_url[:80])

    return prompts
