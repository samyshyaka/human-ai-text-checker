from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_llama_client, get_rag_service
from app.models.schemas import AnalyzeRequest
from app.rag.vectorstore import RAGService
from app.services.humanize import run_humanize
from app.services.llama_client import LlamaAPIClient

router = APIRouter(tags=["humanize"])


@router.post("/improve")
async def improve_text(
    request: AnalyzeRequest,
    llama_client: Optional[LlamaAPIClient] = Depends(get_llama_client),
    rag_service: RAGService = Depends(get_rag_service),
) -> Dict:
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    return await run_humanize(request.text, llama_client, rag_service)
