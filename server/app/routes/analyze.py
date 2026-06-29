from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_llama_client, get_rag_service
from app.models.schemas import AnalyzeRequest
from app.rag.vectorstore import RAGService
from app.services.analysis import run_langchain_analysis, run_llama_analysis
from app.services.llama_client import LlamaAPIClient

router = APIRouter(tags=["analysis"])


@router.post("/analyze")
async def analyze_text(
    request: AnalyzeRequest,
    llama_client: Optional[LlamaAPIClient] = Depends(get_llama_client),
    rag_service: RAGService = Depends(get_rag_service),
) -> Dict:
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    return await run_llama_analysis(request.text, llama_client, rag_service)


@router.post("/analyze/langchain")
async def analyze_text_langchain(
    request: AnalyzeRequest,
    rag_service: RAGService = Depends(get_rag_service),
) -> Dict:
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    return run_langchain_analysis(request.text, rag_service)
