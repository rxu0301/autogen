"""
Bug Condition Exploration Test
==============================
Property 1: --mode content 실행 시 generate_with_llm()이 호출되는지 검증

수정 전 코드에서 FAIL → 버그 존재 증명
수정 후 코드에서 PASS → 버그 수정 확인

Validates: Requirements 1.1, 1.2, 2.1, 2.2
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

sys.path.insert(0, str(Path(__file__).parent.parent))
import generate_prompt


# ---------------------------------------------------------------------------
# Hypothesis strategy
# ---------------------------------------------------------------------------

valid_json_strategy = st.fixed_dictionaries({
    "interest": st.text(min_size=1, max_size=20).filter(str.strip),
    "goal": st.text(min_size=1, max_size=20).filter(str.strip),
    "target_audience": st.text(min_size=1, max_size=20).filter(str.strip),
    "platform": st.sampled_from(["TikTok", "Instagram", "YouTube"]),
    "tone": st.text(min_size=1, max_size=20).filter(str.strip),
    "duration": st.sampled_from(["15초", "30초", "60초"]),
    "keywords": st.text(min_size=1, max_size=20).filter(str.strip),
})


def run_main_content_mode(data: dict):
    """Ollama available 상태를 mock하고 main()을 --mode content로 실행, llm 호출 횟수 반환."""
    mock_llm = MagicMock(return_value="LLM generated content")

    with patch.object(generate_prompt, "is_ollama_available", return_value=True), \
         patch.object(generate_prompt, "generate_with_llm", mock_llm), \
         patch.object(generate_prompt, "load_json", return_value=data), \
         patch("sys.argv", ["generate_prompt.py", "--mode", "content"]), \
         patch("builtins.print"):
        generate_prompt.main()

    return mock_llm.call_count


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

class TestBugConditionUnit:

    def test_generate_with_llm_called_when_ollama_available(self):
        """Ollama 사용 가능 시 --mode content에서 generate_with_llm()이 1회 호출되어야 한다."""
        sample_data = {
            "interest": "헬스, 다이어트",
            "goal": "팔로워 증가",
            "target_audience": "20대 여성",
            "platform": "TikTok",
            "tone": "자극적 + 유머",
            "duration": "15초",
            "keywords": "뱃살, 홈트",
        }
        call_count = run_main_content_mode(sample_data)
        assert call_count == 1, (
            f"generate_with_llm() call_count={call_count} (기대값: 1)\n"
            "원인: main()의 content 분기에서 generate_with_llm()이 호출되지 않음"
        )

    def test_fallback_when_ollama_unavailable(self):
        """Ollama 미가동 시 generate_content_plan() 폴백이 실행되어야 한다."""
        mock_plan = MagicMock(return_value="fallback content")
        sample_data = {
            "interest": "요리",
            "goal": "브랜드 홍보",
            "target_audience": "30대",
            "platform": "Instagram",
            "tone": "감성적",
            "duration": "30초",
            "keywords": "레시피",
        }

        with patch.object(generate_prompt, "is_ollama_available", return_value=False), \
             patch.object(generate_prompt, "generate_content_plan", mock_plan), \
             patch.object(generate_prompt, "load_json", return_value=sample_data), \
             patch("sys.argv", ["generate_prompt.py", "--mode", "content"]), \
             patch("builtins.print"), \
             patch("sys.stderr"):
            generate_prompt.main()

        assert mock_plan.call_count == 1, "Ollama 미가동 시 generate_content_plan() 폴백이 호출되어야 함"

    def test_prompt_mode_does_not_call_llm(self):
        """--mode prompt 실행 시 generate_with_llm()은 호출되지 않아야 한다."""
        mock_llm = MagicMock(return_value="should not be called")
        sample_data = {
            "interest": "여행",
            "goal": "인지도 향상",
            "target_audience": "20대",
            "platform": "YouTube",
            "tone": "밝고 경쾌",
            "duration": "60초",
            "keywords": "배낭여행",
        }

        with patch.object(generate_prompt, "generate_with_llm", mock_llm), \
             patch.object(generate_prompt, "load_json", return_value=sample_data), \
             patch("sys.argv", ["generate_prompt.py", "--mode", "prompt"]), \
             patch("builtins.print"):
            generate_prompt.main()

        assert mock_llm.call_count == 0, "--mode prompt에서 generate_with_llm()이 호출되면 안 됨"


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------

class TestBugConditionProperty:

    @given(data=valid_json_strategy)
    @settings(max_examples=15, suppress_health_check=[HealthCheck.too_slow])
    def test_llm_always_called_for_any_valid_input(self, data: dict):
        """
        Property 1: 임의의 유효 JSON 입력 + Ollama 가용 시
        --mode content에서 generate_with_llm()이 반드시 1회 호출되어야 한다.
        """
        call_count = run_main_content_mode(data)
        assert call_count == 1, (
            f"generate_with_llm() call_count={call_count} (기대값: 1), 입력: {data}"
        )
