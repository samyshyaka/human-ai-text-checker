from typing import Dict, Optional

from fastapi import APIRouter, Depends

import config
from app.dependencies import get_llama_client
from app.services.llama_client import LlamaAPIClient

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(
    llama_client: Optional[LlamaAPIClient] = Depends(get_llama_client),
) -> Dict:
    api_status = "configured" if llama_client is not None else "not_configured"
    debug_info = {
        "status": "healthy",
        "llama_api": api_status,
        "message": "Human-AI Text Checker API is running",
        "app_name": "AI vs Human Text Checker",
    }

    if llama_client is not None:
        key = llama_client.api_key
        debug_info.update(
            {
                "api_url": llama_client.api_url,
                "api_key_preview": (
                    f"{key[:10]}...{key[-4:]}" if len(key) > 14 else "***"
                ),
                "model": config.LLAMA_MODEL,
            }
        )

    return debug_info


@router.get("/debug/test-simple")
async def test_simple(
    llama_client: Optional[LlamaAPIClient] = Depends(get_llama_client),
) -> Dict:
    if llama_client is None:
        return {"error": "No API client configured"}

    try:
        return await llama_client.test_simple_request()
    except Exception as exc:
        return {
            "error": str(exc),
            "api_url": llama_client.api_url,
            "model": llama_client.model,
        }
