import httpx
import asyncio
import json

async def test_summary():
    print("=== summary 테스트 ===")
    async with httpx.AsyncClient(timeout=90) as c:
        r = await c.post("http://localhost:8000/api/v1/news/summary", json={
            "news_id": "test_001",
            "news_title": "AI 기술 발전",
            "news_content": "AI 기술이 빠르게 발전하고 있습니다.",
            "language": "ko"
        })
        print("status:", r.status_code)
        data = r.json()
        if "versions" in data:
            for v in data["versions"]:
                style = v["style"]
                chars = len(v["summary"])
                print(f"  버전{v['version']} ({style}): {chars}자")
        else:
            print("error:", r.text[:300])

async def test_script():
    print("=== script 테스트 ===")
    async with httpx.AsyncClient(timeout=90) as c:
        r = await c.post("http://localhost:8000/api/v1/news/script", json={
            "news_id": "test_001",
            "news_title": "AI 기술 발전",
            "news_content": "AI 기술이 빠르게 발전하고 있습니다.",
            "duration": "30초",
            "language": "ko"
        })
        print("status:", r.status_code)
        data = r.json()
        if "versions" in data:
            for v in data["versions"]:
                style = v["style"]
                chars = len(v["script"])
                print(f"  버전{v['version']} ({style}): {chars}자")
        else:
            print("error:", r.text[:300])

asyncio.run(test_summary())
asyncio.run(test_script())
