import argparse
import json
import os
import sys
from pathlib import Path

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TEMPLATE_PATH = Path(__file__).with_name("prompt_template.txt")
DEFAULT_INPUT_PATH = Path(__file__).with_name("sample_input.json")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

PROMPT_INSTRUCTIONS = """
아래 입력 정보를 사용해 숏폼 콘텐츠 생성 프롬프트를 완성하세요.
출력 형식은 다음과 같습니다:
- 콘셉트 제안 (3개)
- 최종 선택 콘텐츠 상세 구성
- 최적화 요소 (해시태그, 캡션 등)
- 바이럴 개선 포인트

중요:
- 짧고 임팩트 있게 작성
- 실제 제작 가능한 수준으로 구체화
- 트렌드 기반 사고 반영
"""


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_prompt(data: dict) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    filled = template.format(
        interest=data.get("interest", ""),
        goal=data.get("goal", ""),
        target_audience=data.get("target_audience", ""),
        platform=data.get("platform", ""),
        tone=data.get("tone", ""),
        duration=data.get("duration", ""),
        keywords=data.get("keywords", "없음"),
    )
    return f"{filled}\n\n{PROMPT_INSTRUCTIONS.strip()}\n"


def build_concepts(data: dict) -> list:
    audience = data.get("target_audience", "").strip()
    platform = data.get("platform", "").strip()
    tone = data.get("tone", "").strip()
    keywords = data.get("keywords", "").replace(" ", "")

    return [
        f"콘셉트 1: '{keywords} 15초 챌린지' - {platform}에서 쉽게 따라 할 수 있는 루틴과 즉각적 변화 강조",
        f"콘셉트 2: '데일리 경고 메시지' - {audience} 대상의 공감형 자극 카피로 빠르게 클릭 유도",
        f"콘셉트 3: '웃긴 속도전' - 유머를 섞어 짧은 시간에 강렬한 에너지 전달",
    ]


def choose_best_concept(concepts: list, data: dict) -> str:
    if "팔로워" in data.get("goal", ""):
        return concepts[0]
    if "정보" in data.get("tone", "") or "정보형" in data.get("tone", ""):
        return concepts[2]
    return concepts[1]


def generate_content_plan(data: dict) -> str:
    audience = data.get("target_audience", "").strip()
    platform = data.get("platform", "").strip()
    tone = data.get("tone", "").strip()
    duration = data.get("duration", "").strip()
    keywords = data.get("keywords", "없음").strip()

    concepts = build_concepts(data)
    selected_concept = choose_best_concept(concepts, data)
    hook = (
        f"{audience}이라면 이 15초, 그냥 지나치면 안 된다!"
        if duration and "15" in duration
        else f"지금 바로 확인해야 할 {keywords} 비결!"
    )
    script = (
        "1) 0~3초: 강렬한 훅 자막 노출.\n"
        "2) 3~10초: 핵심 동작 빠르게 2회 시연.\n"
        "3) 10~15초: 전/후 컷 + 팔로우 콜투액션."
    )
    direction = (
        "- 자막은 굵은 글씨 + 노란색 테두리로 강조\n"
        "- 빠른 줌인/줌아웃으로 템포감 유지\n"
        "- 비트에 맞춘 점프컷, 마지막 슬로우모션"
    )
    trend = (
        "- 업비트 리듬 BGM 사용\n"
        "- 챌린지 태그 스타일 삽입\n"
        "- 빠른 텍스트 스냅과 반전 컷"
    )
    hashtags = ["#숏폼", f"#{keywords.replace(',','').replace(' ','')}", "#챌린지", "#팔로워늘리기"]
    if "유머" in tone:
        hashtags.append("#웃긴영상")

    caption = (
        f"{keywords} 관련 꿀팁! 지금 바로 따라해보고 팔로우로 더 많은 정보 받기."
        if keywords and keywords != "없음"
        else "오늘 바로 도전할 수 있는 짧은 루틴!"
    )
    thumbnail = f"{keywords} 15초 챌린지" if keywords and keywords != "없음" else "15초 챌린지"

    improvements = [
        "첫 3초에 더 강한 질문형 훅으로 시청자 호기심을 즉각 자극합니다.",
        "화면 텍스트를 더 짧고 굵게 구성해 모바일 가독성을 높입니다.",
        "업로드 시간대를 타겟 활동 시간대에 맞추고 트렌드 음원을 활용합니다.",
    ]

    return (
        f"- 콘셉트 제안 (3개)\n"
        f"{concepts[0]}\n{concepts[1]}\n{concepts[2]}\n\n"
        f"- 최종 선택 콘텐츠 상세 구성\n"
        f"선택 콘셉트: {selected_concept}\n"
        f"훅(Hook): {hook}\n"
        f"스크립트:\n{script}\n"
        f"화면 연출:\n{direction}\n"
        f"BGM/트렌드 요소 제안:\n{trend}\n\n"
        f"- 최적화 요소\n"
        f"추천 해시태그: {' '.join(hashtags)}\n"
        f"썸네일 문구: {thumbnail}\n"
        f"업로드 캡션: {caption}\n\n"
        f"- 바이럴 개선 포인트\n"
        f"1. {improvements[0]}\n"
        f"2. {improvements[1]}\n"
        f"3. {improvements[2]}\n"
    )


def save_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def generate_with_llm(prompt: str) -> str:
    """Generate content using Ollama local inference engine."""
    if not REQUESTS_AVAILABLE:
        raise ImportError(
            "requests 라이브러리가 설치되지 않았습니다. "
            "Run: pip install -r requirements.txt"
        )

    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "system": (
            "You are a professional shortform content strategist. "
            "Generate engaging, creative, and platform-optimized content concepts and scripts. "
            "Always provide practical, actionable suggestions in Korean."
        ),
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            f"Ollama 서버에 연결할 수 없습니다 ({OLLAMA_BASE_URL}). "
            "Ollama가 실행 중인지 확인하세요: ollama serve"
        )
    except requests.exceptions.Timeout:
        raise TimeoutError("Ollama 응답 시간이 초과되었습니다. 모델 로딩 중일 수 있습니다.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"Ollama API 오류: {e}")


def is_ollama_available() -> bool:
    """Check if Ollama server is reachable."""
    if not REQUESTS_AVAILABLE:
        return False
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a shortform content agent prompt or content plan from input JSON."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_PATH,
        help="Path to the input JSON file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to save the generated text.",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["prompt", "content"],
        default="content",
        help="Mode: 'prompt' outputs the filled template, 'content' generates via Ollama LLM.",
    )
    parser.add_argument(
        "--fallback",
        action="store_true",
        help="Force fallback mode (skip Ollama, use rule-based generation).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = load_json(args.input)

    if args.mode == "prompt":
        output = build_prompt(data)
    else:  # mode == "content"
        if not args.fallback and is_ollama_available():
            try:
                prompt = build_prompt(data)
                output = generate_with_llm(prompt)
            except Exception as e:
                print(f"Warning: Ollama 호출 실패 — 폴백 모드로 전환합니다. ({e})", file=sys.stderr)
                output = generate_content_plan(data)
        else:
            if args.fallback:
                print("Info: --fallback 플래그로 폴백 모드 실행 중.", file=sys.stderr)
            else:
                print(
                    f"Warning: Ollama 서버({OLLAMA_BASE_URL})에 연결할 수 없습니다. "
                    "폴백 콘텐츠 기획을 사용합니다. Ollama 실행: ollama serve",
                    file=sys.stderr,
                )
            output = generate_content_plan(data)

    if args.output:
        save_text(args.output, output)
        print(f"Generated output saved to: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
