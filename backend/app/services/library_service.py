"""라이브러리(저장소) 서비스 — 생성 결과를 ChromaDB에 저장하고 해시태그별로 조회합니다."""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from datetime import datetime
from typing import List, Optional

from app.config import settings
from app.models.content import SavedResult, ScriptVersion, ThumbnailPrompt, NewsItem

logger = logging.getLogger(__name__)

_chroma_client = None
_chroma_loaded = False


def _load_chroma():
    global _chroma_client, _chroma_loaded
    if _chroma_loaded:
        return _chroma_client
    try:
        import chromadb
        client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
        )
        client.heartbeat()
        _chroma_client = client
        logger.info("ChromaDB 연결 성공: %s:%s", settings.chroma_host, settings.chroma_port)
    except Exception as exc:
        logger.warning("ChromaDB 초기화 실패: %s", exc)
        _chroma_client = None
    finally:
        _chroma_loaded = True
    return _chroma_client


def _get_collection():
    client = _load_chroma()
    if client is None:
        return None
    try:
        return client.get_or_create_collection(
            name="news_library",
            metadata={"hnsw:space": "cosine"},
        )
    except Exception as exc:
        logger.warning("ChromaDB 컬렉션 접근 실패: %s", exc)
        return None


# ---------------------------------------------------------------------------
# 인메모리 폴백 저장소 (ChromaDB 미가용 시)
# ---------------------------------------------------------------------------
_memory_store: List[dict] = []


def _save_to_memory(result_dict: dict) -> None:
    _memory_store.append(result_dict)
    logger.info("인메모리 저장소에 저장 완료 (id=%s)", result_dict.get("id"))


def _load_from_memory(hashtag: Optional[str] = None) -> List[dict]:
    if not hashtag:
        return list(reversed(_memory_store))
    return [
        r for r in reversed(_memory_store)
        if hashtag in r.get("hashtags", [])
    ]


# ---------------------------------------------------------------------------
# ChromaDB 저장/조회
# ---------------------------------------------------------------------------

def _save_to_chroma_sync(result_dict: dict) -> None:
    collection = _get_collection()
    if collection is None:
        _save_to_memory(result_dict)
        return

    doc_id = result_dict["id"]
    document = f"{result_dict['news_title']} {result_dict['topic']} {' '.join(result_dict.get('hashtags', []))}"
    metadata = {
        "topic": result_dict["topic"],
        "news_title": result_dict["news_title"],
        "news_source": result_dict["news_source"],
        "published_at": result_dict["published_at"],
        "duration": result_dict["duration"],
        "hashtags": json.dumps(result_dict.get("hashtags", []), ensure_ascii=False),
        "created_at": result_dict["created_at"],
        "payload": json.dumps(result_dict, ensure_ascii=False),
    }

    try:
        collection.upsert(
            ids=[doc_id],
            documents=[document],
            metadatas=[metadata],
        )
        logger.info("ChromaDB 저장 완료 (id=%s)", doc_id)
    except Exception as exc:
        logger.warning("ChromaDB 저장 실패, 인메모리로 폴백: %s", exc)
        _save_to_memory(result_dict)


def _load_from_chroma_sync(hashtag: Optional[str] = None, limit: int = 50) -> List[dict]:
    collection = _get_collection()
    if collection is None:
        return _load_from_memory(hashtag)

    try:
        if hashtag:
            results = collection.get(
                where_document={"$contains": hashtag},
                limit=limit,
                include=["metadatas"],
            )
        else:
            results = collection.get(
                limit=limit,
                include=["metadatas"],
            )

        items = []
        for meta in (results.get("metadatas") or []):
            payload_str = meta.get("payload", "")
            if payload_str:
                try:
                    items.append(json.loads(payload_str))
                except Exception:
                    pass

        # created_at 기준 내림차순 정렬
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return items

    except Exception as exc:
        logger.warning("ChromaDB 조회 실패, 인메모리로 폴백: %s", exc)
        return _load_from_memory(hashtag)


# ---------------------------------------------------------------------------
# 공개 인터페이스
# ---------------------------------------------------------------------------

async def save_result(
    topic: str,
    news: NewsItem,
    selected_script: ScriptVersion,
    duration: str,
    thumbnail_prompts: List[ThumbnailPrompt],
    hashtags: List[str],
) -> str:
    """생성 결과를 라이브러리에 저장하고 저장 ID를 반환합니다."""
    now = datetime.now().isoformat()
    doc_id = "lib_" + hashlib.md5(f"{news.id}{now}".encode()).hexdigest()[:12]

    result_dict = {
        "id": doc_id,
        "topic": topic,
        "news_title": news.title,
        "news_source": news.source,
        "published_at": news.published_at,
        "duration": duration,
        "selected_script": selected_script.model_dump(),
        "thumbnail_prompts": [p.model_dump() for p in thumbnail_prompts],
        "hashtags": hashtags,
        "created_at": now,
    }

    await asyncio.to_thread(_save_to_chroma_sync, result_dict)
    return doc_id


async def get_library(
    hashtag: Optional[str] = None,
    limit: int = 50,
) -> List[SavedResult]:
    """라이브러리에서 저장된 결과를 조회합니다. hashtag 필터 가능."""
    raw_list = await asyncio.to_thread(_load_from_chroma_sync, hashtag, limit)

    results: List[SavedResult] = []
    for raw in raw_list:
        try:
            script_data = raw.get("selected_script", {})
            thumbnail_data = raw.get("thumbnail_prompts", [])

            results.append(SavedResult(
                id=raw["id"],
                topic=raw["topic"],
                news_title=raw["news_title"],
                news_source=raw["news_source"],
                published_at=raw["published_at"],
                duration=raw["duration"],
                selected_script=ScriptVersion(**script_data),
                thumbnail_prompts=[ThumbnailPrompt(**p) for p in thumbnail_data],
                hashtags=raw.get("hashtags", []),
                created_at=raw["created_at"],
            ))
        except Exception as exc:
            logger.warning("라이브러리 항목 파싱 실패: %s", exc)

    return results
