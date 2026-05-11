"""Rule-based fallback content generator (no LLM required).

Used when Ollama is unavailable or when use_llm=False is requested.
Produces a structured content plan based purely on the input data.
"""

import logging

logger = logging.getLogger(__name__)


def generate_content_plan(data: dict) -> str:
    """Generate a structured shortform content plan without an LLM.

    Applies rule-based logic to produce concept suggestions, a detailed
    content structure, optimisation elements, and viral improvement tips.

    Args:
        data: Dictionary with keys: interest, goal, target_audience,
              platform, tone, duration, keywords.

    Returns:
        A formatted string containing the full content plan.
    """
    audience: str = data.get("target_audience", "").strip()
    platform: str = data.get("platform", "").strip()
    tone: str = data.get("tone", "").strip()
    duration: str = data.get("duration", "").strip()
    keywords: str = data.get("keywords", "없음").strip()

    logger.debug(
        "Generating fallback content plan — platform=%s tone=%s keywords=%s",
        platform,
        tone,
        keywords,
    )

    concepts = [
        f"콘셉트 1: '{keywords} 챌린지' - {platform}에서 쉽게 따라 할 수 있는 루틴과 즉각적 변화 강조",
        f"콘셉트 2: '데일리 경고 메시지' - {audience} 대상의 공감형 자극 카피로 빠르게 클릭 유도",
        f"콘셉트 3: '속도전 포맷' - 유머를 섞어 짧은 시간에 강렬한 에너지 전달",
    ]

    hook = (
        f"{audience}이라면 이 {duration}, 그냥 지나치면 안 된다!"
        if duration
        else f"지금 바로 확인해야 할 {keywords} 비결!"
    )

    hashtags = [
        f"#{keywords.replace(',', '').replace(' ', '')}",
        "#챌린지",
        "#숏폼",
        "#팔로워늘리기",
    ]
    if "유머" in tone:
        hashtags.append("#웃긴영상")

    content_plan = (
        f"- 콘셉트 제안 (3개)\n"
        f"{concepts[0]}\n{concepts[1]}\n{concepts[2]}\n\n"
        f"- 최종 선택 콘텐츠 상세 구성\n"
        f"선택 콘셉트: {concepts[0]}\n"
        f"훅(Hook): {hook}\n"
        f"스크립트:\n"
        f"1) 0~3초: 강렬한 훅 자막 노출.\n"
        f"2) 3~{duration or '10초'}: 핵심 동작 빠르게 시연.\n"
        f"3) 마지막: 팔로우 콜투액션.\n\n"
        f"- 최적화 요소\n"
        f"추천 해시태그: {' '.join(hashtags)}\n"
        f"썸네일 문구: {keywords} {duration} 챌린지\n"
        f"업로드 캡션: {keywords} 관련 꿀팁! 팔로우로 더 많은 정보 받기.\n\n"
        f"- 바이럴 개선 포인트\n"
        f"1. 첫 3초에 강한 질문형 훅으로 시청자 호기심을 즉각 자극합니다.\n"
        f"2. 화면 텍스트를 짧고 굵게 구성해 모바일 가독성을 높입니다.\n"
        f"3. 타겟 활동 시간대에 업로드하고 트렌드 음원을 활용합니다.\n"
    )

    logger.debug("Fallback content plan generated — chars=%d", len(content_plan))
    return content_plan
