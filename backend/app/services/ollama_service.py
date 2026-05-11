"""Ollama LLM integration service layer.

Provides async functions to check Ollama availability and generate
shortform content via the Ollama REST API (/api/generate endpoint).
"""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a professional shortform content strategist. "
    "Generate engaging, creative, and platform-optimized content concepts and scripts. "
    "Always provide practical, actionable suggestions in Korean."
)

PROMPT_TEMPLATE = """너는 개인 맞춤형 숏폼 콘텐츠 생성 에이전트다.
사용자의 관심사, 목적, 플랫폼 특성을 반영해 바이럴 가능성이 높은 숏폼 콘텐츠를 생성한다.

[입력 정보]
- 사용자 관심사: {interest}
- 콘텐츠 목적: {goal}
- 타겟 시청자: {target_audience}
- 플랫폼: {platform}
- 콘텐츠 톤: {tone}
- 길이: {duration}
- 참고 키워드: {keywords}

[작업]
1. 콘텐츠 콘셉트 3개 제안
2. 가장 효과적인 1개 선택 후 상세 구성 (훅, 스크립트, 화면 연출, BGM)
3. 플랫폼 최적화 요소 (해시태그 5~10개, 썸네일 문구, 업로드 캡션)
4. 바이럴 개선 포인트 3개

짧고 임팩트 있게, 실제 제작 가능한 수준으로 작성하라."""


def _build_prompt(data: dict) -> str:
    """Build the LLM prompt string from input data dict."""
    return PROMPT_TEMPLATE.format(
        interest=data.get("interest", ""),
        goal=data.get("goal", ""),
        target_audience=data.get("target_audience", ""),
        platform=data.get("platform", ""),
        tone=data.get("tone", ""),
        duration=data.get("duration", ""),
        keywords=data.get("keywords", "없음"),
    )


async def is_ollama_available() -> bool:
    """Check whether the Ollama server is reachable.

    Returns True if the /api/tags endpoint responds with HTTP 200,
    False for any connection error, timeout, or non-200 status.
    """
    url = f"{settings.ollama_base_url}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            available = response.status_code == 200
            logger.debug(
                "Ollama availability check — url=%s status=%d available=%s",
                url,
                response.status_code,
                available,
            )
            return available
    except httpx.ConnectError:
        logger.debug("Ollama not reachable at %s (connection refused)", url)
        return False
    except httpx.TimeoutException:
        logger.debug("Ollama availability check timed out at %s", url)
        return False
    except Exception as exc:  # pragma: no cover
        logger.warning("Unexpected error checking Ollama availability: %s", exc)
        return False


async def generate_content(data: dict) -> str:
    """Generate shortform content via Ollama's /api/generate endpoint.

    Builds a prompt from *data*, sends it to the configured Ollama model,
    and returns the generated text string.

    Args:
        data: Dictionary with keys: interest, goal, target_audience,
              platform, tone, duration, keywords.

    Returns:
        The generated content text from Ollama.

    Raises:
        httpx.ConnectError: If the Ollama server is unreachable.
        httpx.TimeoutException: If the request exceeds ollama_timeout seconds.
        httpx.HTTPStatusError: If Ollama returns a non-2xx HTTP status.
        ValueError: If the Ollama response does not contain a 'response' field.
    """
    prompt = _build_prompt(data)
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "stream": False,
    }

    url = f"{settings.ollama_base_url}/api/generate"
    logger.info(
        "Calling Ollama — url=%s model=%s",
        url,
        settings.ollama_model,
    )

    try:
        async with httpx.AsyncClient(timeout=float(settings.ollama_timeout)) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()

        result = response.json()
        generated_text: str = result.get("response", "")

        if not generated_text:
            logger.warning("Ollama returned an empty 'response' field for model=%s", settings.ollama_model)
            raise ValueError(
                f"Ollama returned an empty response for model '{settings.ollama_model}'. "
                "The model may not be loaded or the prompt was rejected."
            )

        logger.info(
            "Ollama generation succeeded — model=%s chars=%d",
            settings.ollama_model,
            len(generated_text),
        )
        return generated_text

    except httpx.ConnectError as exc:
        logger.error(
            "Cannot connect to Ollama at %s: %s",
            settings.ollama_base_url,
            exc,
        )
        raise
    except httpx.TimeoutException as exc:
        logger.error(
            "Ollama request timed out after %ds (model=%s): %s",
            settings.ollama_timeout,
            settings.ollama_model,
            exc,
        )
        raise
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Ollama API returned HTTP %d for model=%s: %s",
            exc.response.status_code,
            settings.ollama_model,
            exc,
        )
        raise
