"""
RAG Query Route

Provides endpoints for testing and debugging the RAG pipeline.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from rag import Retriever, get_rag_settings

logger = logging.getLogger(__name__)

router = APIRouter()


class RAGQueryRequest(BaseModel):
    """Request model for RAG query."""
    
    query: str = Field(
        ...,
        description="The search query",
        min_length=1,
        max_length=1000,
        examples=["What does Voara AI do?"]
    )
    top_k: Optional[int] = Field(
        default=None,
        description="Number of results to return (default from settings)",
        ge=1,
        le=10
    )


class RAGResult(BaseModel):
    """A single RAG retrieval result."""
    
    text: str = Field(..., description="The retrieved text chunk")
    score: float = Field(..., description="Similarity score")
    header: str = Field(default="", description="Section header if available")
    source: str = Field(default="", description="Source document")


class RAGQueryResponse(BaseModel):
    """Response model for RAG query."""
    
    query: str = Field(..., description="The original query")
    results: list[RAGResult] = Field(..., description="Retrieved results")
    context: str = Field(..., description="Formatted context for LLM")
    retrieval_time_ms: float = Field(..., description="Retrieval time in milliseconds")


@router.post("/rag/query", response_model=RAGQueryResponse)
async def query_rag(request: RAGQueryRequest) -> RAGQueryResponse:
    """
    Query the RAG pipeline and return retrieved chunks.
    
    Useful for testing and debugging RAG retrieval accuracy.
    
    Args:
        request: Query request with search text
        
    Returns:
        RAGQueryResponse with retrieved chunks and formatted context
    """
    import time
    
    settings = get_rag_settings()
    
    try:
        retriever = Retriever(
            top_k=request.top_k or settings.top_k
        )
        
        start_time = time.time()
        
        # Get results with sources
        context, sources = await retriever.retrieve_with_sources(
            query=request.query,
            top_k=request.top_k
        )
        
        # Get full results for detailed info
        results = await retriever.retrieve(
            query=request.query,
            top_k=request.top_k
        )
        
        retrieval_time = (time.time() - start_time) * 1000
        
        return RAGQueryResponse(
            query=request.query,
            results=[
                RAGResult(
                    text=r.text,
                    score=r.score,
                    header=r.metadata.get("header", ""),
                    source=r.metadata.get("source", "")
                )
                for r in results
            ],
            context=context,
            retrieval_time_ms=round(retrieval_time, 2)
        )
        
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"RAG query failed: {str(e)}"
        )


@router.get("/rag/stats")
async def get_rag_stats():
    """
    Get RAG pipeline statistics.
    
    Returns:
        Statistics about the knowledge base and configuration
    """
    from rag import get_qdrant_service
    
    settings = get_rag_settings()
    qdrant = get_qdrant_service()
    
    try:
        info = await qdrant.get_collection_info()
        
        return {
            "collection": {
                "name": settings.qdrant_collection_name,
                "exists": info is not None,
                "points_count": info.get("points_count", 0) if info else 0,
                "status": info.get("status", "unknown") if info else "not_found"
            },
            "config": {
                "embedding_model": settings.embedding_model,
                "embedding_dimension": settings.embedding_dimension,
                "chunk_size": settings.chunk_size,
                "chunk_overlap": settings.chunk_overlap,
                "top_k": settings.top_k,
                "score_threshold": settings.score_threshold
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get RAG stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get RAG stats: {str(e)}"
        )
