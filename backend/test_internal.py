"""백엔드 내부에서 직접 서비스 호출 테스트"""
import asyncio
import sys
sys.path.insert(0, '.')

async def main():
    from app.config import settings
    print(f"model: {settings.ollama_model}")
    print(f"ollama_url: {settings.ollama_base_url}")
    print(f"timeout: {settings.ollama_timeout}")

    # Ollama 가용성 확인
    import httpx
    try:
        async with httpx.AsyncClient(timeout=3) as c:
            r = await c.get(f"{settings.ollama_base_url}/api/tags")
            print(f"Ollama status: {r.status_code}")
            models = [m['name'] for m in r.json().get('models', [])]
            print(f"Available models: {models}")
    except Exception as e:
        print(f"Ollama error: {e}")
        return

    # 폴백 직접 테스트 (Ollama 없이)
    from app.services.summary_service import _fallback_summaries
    from app.services.script_service import _fallback_scripts

    print("\n=== 폴백 요약본 테스트 ===")
    summaries = _fallback_summaries("AI 기술 발전", "AI 기술이 빠르게 발전하고 있습니다.", "ko")
    for s in summaries:
        print(f"  버전{s.version} ({s.style}): {len(s.summary)}자")

    print("\n=== 폴백 스크립트 테스트 ===")
    scripts = _fallback_scripts("AI 기술 발전", "AI 기술이 빠르게 발전하고 있습니다.", "30초", "ko")
    for s in scripts:
        print(f"  버전{s.version} ({s.style}): {len(s.script)}자")

    # Ollama 실제 호출 테스트 (짧은 프롬프트)
    print("\n=== Ollama 직접 호출 테스트 (짧은 프롬프트) ===")
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                f"{settings.ollama_base_url}/api/generate",
                json={"model": settings.ollama_model, "prompt": "안녕하세요. 한 문장으로 답하세요.", "stream": False}
            )
            print(f"  응답: {r.json().get('response', '')[:100]}")
    except Exception as e:
        print(f"  Ollama 호출 실패: {e}")

asyncio.run(main())
