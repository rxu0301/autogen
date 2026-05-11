import logging
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_env: str = "development"
    log_level: str = "INFO"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    ollama_timeout: int = 120  # seconds

    # Pinecone
    pinecone_api_key: str = ""
    pinecone_index_name: str = "shortform-content"

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8001

    # CORS — comma-separated origins are parsed automatically by pydantic-settings
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:4000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Configure root logger once at import time so all modules share the same level.
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
