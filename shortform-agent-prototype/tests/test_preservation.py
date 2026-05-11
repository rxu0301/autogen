"""
Preservation Property Tests
============================
Property 2: --mode prompt / --output / --input / 폴백 기존 동작 보존 검증

수정 전후 모두 PASS해야 함 (리그레션 없음 확인)

Validates: Requirements 3.1, 3.2, 3.3, 3.4
"""

import sys
import json
import tempfile
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


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

class TestPreservationUnit:

    def test_prompt_mode_outputs_build_prompt_result(self):
        """--mode prompt 실행 시 build_prompt() 결과가 출력되어야 한다."""
        sample_data = {
            "interest": "헬스",
            "goal": "팔로워 증가",
            "target_audience": "20대",
            "platform": "TikTok",
            "tone": "유머",
            "duration": "15초",
            "keywords": "홈트",
        }
        captured = []

        with patch.object(generate_prompt, "load_json", return_value=sample_data), \
             patch("sys.argv", ["generate_prompt.py", "--mode", "prompt"]), \
             patch("builtins.print", side_effect=lambda x: captured.append(x)):
            generate_prompt.main()

        expected = generate_prompt.build_prompt(sample_data)
        assert len(captured) > 0
        assert captured[0] == expected

    def test_output_file_saved_when_specified(self):
        """--output 경로 지정 시 파일이 생성되어야 한다."""
        sample_data = {
            "interest": "요리",
            "goal": "홍보",
            "target_audience": "30대",
            "platform": "Instagram",
            "tone": "감성",
            "duration": "30초",
            "keywords": "레시피",
        }

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            out_path = Path(f.name)

        with patch.object(generate_prompt, "load_json", return_value=sample_data), \
             patch.object(generate_prompt, "is_ollama_available", return_value=False), \
             patch("sys.argv", ["generate_prompt.py", "--mode", "content", "--output", str(out_path)]), \
             patch("builtins.print"), \
             patch("sys.stderr"):
            generate_prompt.main()

        assert out_path.exists()
        content = out_path.read_text(encoding="utf-8")
        assert len(content) > 0
        out_path.unlink()

    def test_input_file_loaded_correctly(self):
        """--input 경로 지정 시 해당 JSON 파일이 로딩되어야 한다."""
        sample_data = {
            "interest": "게임",
            "goal": "구독자 증가",
            "target_audience": "10대",
            "platform": "YouTube",
            "tone": "에너지틱",
            "duration": "60초",
            "keywords": "FPS",
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(sample_data, f, ensure_ascii=False)
            input_path = Path(f.name)

        captured_data = []
        original_build = generate_prompt.build_prompt

        def capture_build(data):
            captured_data.append(data)
            return original_build(data)

        with patch.object(generate_prompt, "build_prompt", side_effect=capture_build), \
             patch("sys.argv", ["generate_prompt.py", "--mode", "prompt", "--input", str(input_path)]), \
             patch("builtins.print"):
            generate_prompt.main()

        assert len(captured_data) > 0
        assert captured_data[0]["interest"] == "게임"
        input_path.unlink()

    def test_fallback_content_plan_returned_when_ollama_unavailable(self):
        """Ollama 미가동 시 generate_content_plan() 결과가 반환되어야 한다."""
        sample_data = {
            "interest": "패션",
            "goal": "판매",
            "target_audience": "20대 여성",
            "platform": "Instagram",
            "tone": "세련",
            "duration": "15초",
            "keywords": "OOTD",
        }
        captured = []

        def capture_print(*args, **kwargs):
            if "file" not in kwargs:
                captured.append(args[0] if args else "")

        with patch.object(generate_prompt, "load_json", return_value=sample_data), \
             patch.object(generate_prompt, "is_ollama_available", return_value=False), \
             patch("sys.argv", ["generate_prompt.py", "--mode", "content"]), \
             patch("builtins.print", side_effect=capture_print):
            generate_prompt.main()

        expected = generate_prompt.generate_content_plan(sample_data)
        assert len(captured) > 0
        assert captured[0] == expected


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------

class TestPreservationProperty:

    @given(data=valid_json_strategy)
    @settings(max_examples=15, suppress_health_check=[HealthCheck.too_slow])
    def test_prompt_mode_always_returns_build_prompt_result(self, data: dict):
        """
        Property 2: 임의의 유효 JSON 입력에 대해
        --mode prompt 출력이 항상 build_prompt() 결과와 동일해야 한다.
        """
        captured = []

        with patch.object(generate_prompt, "load_json", return_value=data), \
             patch("sys.argv", ["generate_prompt.py", "--mode", "prompt"]), \
             patch("builtins.print", side_effect=lambda x: captured.append(x)):
            generate_prompt.main()

        expected = generate_prompt.build_prompt(data)
        assert len(captured) > 0
        assert captured[0] == expected, f"--mode prompt 출력이 build_prompt() 결과와 다름. 입력: {data}"

    @given(data=valid_json_strategy)
    @settings(max_examples=15, suppress_health_check=[HealthCheck.too_slow])
    def test_fallback_always_returns_content_plan(self, data: dict):
        """
        Property 2: Ollama 미가동 시 임의 입력에 대해
        항상 generate_content_plan() 결과가 반환되어야 한다.
        """
        captured = []

        def capture_print(*args, **kwargs):
            if "file" not in kwargs:
                captured.append(args[0] if args else "")

        with patch.object(generate_prompt, "load_json", return_value=data), \
             patch.object(generate_prompt, "is_ollama_available", return_value=False), \
             patch("sys.argv", ["generate_prompt.py", "--mode", "content"]), \
             patch("builtins.print", side_effect=capture_print):
            generate_prompt.main()

        expected = generate_prompt.generate_content_plan(data)
        assert len(captured) > 0
        assert captured[0] == expected, f"폴백 출력이 generate_content_plan() 결과와 다름. 입력: {data}"
