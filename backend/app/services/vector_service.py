"""
Vector DB service — Pinecone (cloud) + ChromaDB (local)

- Pinecone: 트렌드/바이럴 콘텐츠 임베딩 저장 및 유사도 검색
- ChromaDB: 로컬 콘텐츠 히스토리 저장

Both ChromaDB and Pinecone clients are synchronous; all blocking calls are
wrapped with ``asyncio.to_thread()`` so the FastAPI event loop is never blocked.
Clients and the embedding model are initialised lazily and cached as module-level
singletons to avoid reloading the ~90 MB sentence-transformer model on every
request.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
from typing import List, Optional

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singletons (lazy-initialised on first use)
# ---------------------------------------------------------------------------

_embedder = None          # SentenceTransformer instance
_chroma_client = None     # chromadb.HttpClient instance
_pinecone_client = None   # pinecone.Pinecone instance

_embedder_loaded: bool = False
_chroma_loaded: bool = False
_pinecone_loaded: bool = False


def _load_embedder():
    """Load the sentence-transformer model (blocking, called via to_thread)."""
    global _embedder, _embedder_loaded
    if _embedder_loaded:
        return _embedder
    try:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("임베딩 모델 로드 완료: all-MiniLM-L6-v2")
    except Exception as exc:
        logger.warning("임베딩 모델 로드 실패 (sentence-transformers 미설치?): %s", exc)
        _embedder = None
    finally:
        _embedder_loaded = True
    return _embedder


def _load_chroma():
    """Connect to ChromaDB (blocking, called via to_thread)."""
    global _chroma_client, _chroma_loaded
    if _chroma_loaded:
        return _chroma_client
    try:
        import chromadb
        client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
        )
        # Probe the server so we fail fast if it is unreachable.
        client.heartbeat()
        _chroma_client = client
        logger.info(
            "ChromaDB 연결 성공: %s:%s", settings.chroma_host, settings.chroma_port
        )
    except Exception as exc:
        logger.warning(
            "ChromaDB 초기화 실패 (%s:%s): %s",
            settings.chroma_host,
            settings.chroma_port,
            exc,
        )
        _chroma_client = None
    finally:
        _chroma_loaded = True
    return _chroma_client


def _load_pinecone():
    """Connect to Pinecone (blocking, called via to_thread)."""
    global _pinecone_client, _pinecone_loaded
    if _pinecone_loaded:
        return _pinecone_client
    if not settings.pinecone_api_key:
        logger.info("PINECONE_API_KEY 미설정 — Pinecone 연동을 건너뜁니다.")
        _pinecone_loaded = True
        return None
    try:
        from pinecone import Pinecone
        _pinecone_client = Pinecone(api_key=settings.pinecone_api_key)
        logger.info("Pinecone 클라이언트 초기화 완료 (index: %s)", settings.pinecone_index_name)
    except Exception as exc:
        logger.warning("Pinecone 초기화 실패: %s", exc)
        _pinecone_client = None
    finally:
        _pinecone_loaded = True
    return _pinecone_client


# ---------------------------------------------------------------------------
# ChromaDB collection name
# ---------------------------------------------------------------------------

CHROMA_COLLECTION = "content_history"


# ---------------------------------------------------------------------------
# ChromaDB operations
# ---------------------------------------------------------------------------

async def save_to_chroma(content: str, metadata: dict) -> None:
    """ChromaDB에 콘텐츠와 메타데이터를 저장합니다.

    MD5 해시를 문서 ID로 사용하여 중복 저장을 방지합니다.
    ChromaDB를 사용할 수 없는 경우 경고 로그를 남기고 조용히 건너뜁니다.

    Args:
        content: 저장할 텍스트 콘텐츠.
        metadata: 콘텐츠와 함께 저장할 메타데이터 딕셔너리.
    """
    def _sync_save() -> None:
        client = _load_chroma()
        embedder = _load_embedder()
        if client is None or embedder is None:
            logger.warning("ChromaDB 또는 임베딩 모델을 사용할 수 없어 저장을 건너뜁니다.")
            return
        try:
            collection = client.get_or_create_collection(CHROMA_COLLECTION)
            doc_id = hashlib.md5(content.encode()).hexdigest()
            vector: List[float] = embedder.encode(content).tolist()
            collection.upsert(
                ids=[doc_id],
                embeddings=[vector],
                documents=[content],
                metadatas=[metadata],
            )
            logger.debug("ChromaDB 저장 완료: id=%s", doc_id)
        except Exception as exc:
            logger.error("ChromaDB 저장 실패: %s", exc)
            raise

    await asyncio.to_thread(_sync_save)


async def search_chroma(query: str, top_k: int = 5) -> List[dict]:
    """ChromaDB에서 쿼리와 유사한 콘텐츠를 검색합니다.

    ChromaDB를 사용할 수 없는 경우 빈 리스트를 반환합니다.

    Args:
        query: 유사도 검색에 사용할 쿼리 문자열.
        top_k: 반환할 최대 결과 수.

    Returns:
        각 결과를 ``{"id", "content", "distance", "metadata"}`` 형태의
        딕셔너리로 담은 리스트.
    """
    def _sync_search() -> List[dict]:
        client = _load_chroma()
        embedder = _load_embedder()
        if client is None or embedder is None:
            logger.warning("ChromaDB 또는 임베딩 모델을 사용할 수 없어 검색을 건너뜁니다.")
            return []
        try:
            collection = client.get_or_create_collection(CHROMA_COLLECTION)
            vector: List[float] = embedder.encode(query).tolist()
            results = collection.query(
                query_embeddings=[vector],
                n_results=top_k,
            )
            items: List[dict] = []
            for i, doc in enumerate(results["documents"][0]):
                items.append(
                    {
                        "id": results["ids"][0][i],
                        "content": doc,
                        "distance": results["distances"][0][i],
                        "metadata": results["metadatas"][0][i],
                    }
                )
            logger.debug("ChromaDB 검색 완료: %d건 반환", len(items))
            return items
        except Exception as exc:
            logger.error("ChromaDB 검색 실패: %s", exc)
            raise

    return await asyncio.to_thread(_sync_search)


# ---------------------------------------------------------------------------
# Pinecone operations
# ---------------------------------------------------------------------------

async def upsert_to_pinecone(content: str, metadata: dict) -> None:
    """Pinecone에 콘텐츠 임베딩을 upsert합니다.

    MD5 해시를 벡터 ID로 사용하여 중복 저장을 방지합니다.
    Pinecone API 키가 설정되지 않은 경우 조용히 건너뜁니다.

    Args:
        content: 임베딩할 텍스트 콘텐츠.
        metadata: 벡터와 함께 저장할 메타데이터 딕셔너리.
    """
    def _sync_upsert() -> None:
        pc = _load_pinecone()
        embedder = _load_embedder()
        if pc is None:
            # API 키 미설정 또는 초기화 실패 — 이미 경고 로그가 남겨짐
            return
        if embedder is None:
            logger.warning("임베딩 모델을 사용할 수 없어 Pinecone upsert를 건너뜁니다.")
            return
        try:
            index = pc.Index(settings.pinecone_index_name)
            vector: List[float] = embedder.encode(content).tolist()
            doc_id = hashlib.md5(content.encode()).hexdigest()
            index.upsert(
                vectors=[
                    {
                        "id": doc_id,
                        "values": vector,
                        "metadata": metadata,
                    }
                ]
            )
            logger.debug("Pinecone upsert 완료: id=%s", doc_id)
        except Exception as exc:
            logger.error("Pinecone upsert 실패: %s", exc)
            raise

    await asyncio.to_thread(_sync_upsert)


async def search_pinecone(query: str, top_k: int = 5) -> List[dict]:
    """Pinecone에서 쿼리와 유사한 벡터를 검색합니다.

    Pinecone API 키가 설정되지 않은 경우 빈 리스트를 반환합니다.

    Args:
        query: 유사도 검색에 사용할 쿼리 문자열.
        top_k: 반환할 최대 결과 수.

    Returns:
        각 결과를 ``{"id", "score", "metadata"}`` 형태의 딕셔너리로 담은 리스트.
    """
    def _sync_search() -> List[dict]:
        pc = _load_pinecone()
        embedder = _load_embedder()
        if pc is None or embedder is None:
            return []
        try:
            index = pc.Index(settings.pinecone_index_name)
            vector: List[float] = embedder.encode(query).tolist()
            results = index.query(vector=vector, top_k=top_k, include_metadata=True)
            return [
                {"id": m.id, "score": m.score, "metadata": m.metadata}
                for m in results.matches
            ]
        except Exception as exc:
            logger.error("Pinecone 검색 실패: %s", exc)
            raise

    return await asyncio.to_thread(_sync_search)
