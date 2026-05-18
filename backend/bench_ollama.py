import httpx, asyncio, time

async def bench():
    async with httpx.AsyncClient(timeout=120) as c:
        start = time.time()
        print("qwen3.5:4b 속도 측정 중...")
        r = await c.post("http://localhost:11434/api/generate", json={
            "model": "qwen3.5:4b",
            "prompt": "Say hello in one word.",
            "stream": False
        })
        elapsed = time.time() - start
        resp = r.json().get("response", "")
        print(f"응답시간: {elapsed:.1f}초")
        print(f"응답: {resp[:80]}")

asyncio.run(bench())
