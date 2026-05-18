import logging
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_env: str = "development"
    log_level: str = "INFO"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3.5:4b"
    ollama_timeout: int = 60

    # Ollama LLM 사용 여부 — False로 설정하면 즉시 폴백 사용 (빠름)
    use_ollama: bool = False

    # 뉴스 API — 네이버 뉴스 (한국어 뉴스 최적)
    naver_client_id: str = ""
    naver_client_secret: str = ""

    # 뉴스 API — NewsAPI.org (영문/글로벌)
    newsapi_key: str = ""

    # ChromaDB (라이브러리 저장소)
    chroma_host: str = "localhost"
    chroma_port: int = 8001

    # 팩트체크 설정
    factcheck_enabled: bool = True          # 팩트체크 활성화 여부
    factcheck_min_score: int = 30           # 이 점수 미만이면 필터링 (0~100)
    factcheck_use_llm: bool = True          # LLM 콘텐츠 분석 사용 여부

    # CORS — 문자열로 받아서 파싱
    cors_origins: str = "http://localhost:3000,http://localhost:4000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# 루트 로거 설정
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
