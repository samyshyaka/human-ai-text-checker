from typing import Dict

from fastapi import APIRouter, Depends

from app.dependencies import get_rag_service
from app.rag.vectorstore import RAGService

router = APIRouter(tags=["rag"])


@router.get("/rag/test")
async def test_rag(rag_service: RAGService = Depends(get_rag_service)) -> Dict:
    test_queries = [
        "How can I detect AI-generated text?",
        "What are the characteristics of human writing?",
        "Tell me about grammar patterns in AI vs human text",
    ]

    results = {}
    for query in test_queries:
        context = rag_service.retrieve_relevant_context(query)
        results[query] = {
            "retrieved_context": context[:200] + "..." if len(context) > 200 else context,
            "context_length": len(context),
        }

    return {
        "status": "RAG test completed",
        "collection_count": rag_service.collection_count,
        "test_results": results,
    }
