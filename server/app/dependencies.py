from functools import lru_cache
from typing import Optional

from app.rag.vectorstore import RAGService
from app.services.llama_client import LlamaAPIClient


@lru_cache
def get_rag_service() -> RAGService:
    return RAGService()


@lru_cache
def get_llama_client() -> Optional[LlamaAPIClient]:
    try:
        return LlamaAPIClient()
    except ValueError as exc:
        print(f"Warning: {exc}")
        return None
