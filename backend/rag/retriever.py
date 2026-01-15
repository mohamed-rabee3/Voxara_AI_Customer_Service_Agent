"""
RAG Retriever Module

High-level retrieval interface that combines embedding and vector search.
Provides formatted context for LLM consumption.
"""

import logging
import time
from dataclasses import dataclass
from typing import Optional

from .config import get_rag_settings
from .embeddings import embed_query
from .qdrant_service import get_qdrant_service, ScoredPoint

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Result from a retrieval operation."""
    
    text: str
    score: float
    metadata: dict
    
    @classmethod
    def from_scored_point(cls, point: ScoredPoint) -> "RetrievalResult":
        """Create from a Qdrant ScoredPoint."""
        payload = point.payload or {}
        return cls(
            text=payload.get("text", ""),
            score=point.score,
            metadata={
                k: v for k, v in payload.items() if k != "text"
            }
        )


class Retriever:
    """
    RAG Retriever combining embedding and vector search.
    
    Provides high-level retrieval methods with formatting for LLM context.
    """
    
    def __init__(
        self,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None
    ):
        """
        Initialize the retriever.
        
        Args:
            top_k: Number of chunks to retrieve (default from settings)
            score_threshold: Minimum similarity score (default from settings)
        """
        self.settings = get_rag_settings()
        self.top_k = top_k or self.settings.top_k
        self.score_threshold = score_threshold or self.settings.score_threshold
        self.qdrant = get_qdrant_service()
    
    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None
    ) -> list[RetrievalResult]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: The search query
            top_k: Override number of results
            score_threshold: Override minimum score
            
        Returns:
            List of RetrievalResult objects sorted by relevance
        """
        if not query.strip():
            logger.warning("Empty query provided to retriever")
            return []
        
        top_k = top_k or self.top_k
        score_threshold = score_threshold or self.score_threshold
        
        start_time = time.time()
        
        try:
            # Generate query embedding
            query_embedding = await embed_query(query)
            embed_time = time.time() - start_time
            
            # Search Qdrant
            search_start = time.time()
            results = await self.qdrant.search(
                query_vector=query_embedding,
                top_k=top_k,
                score_threshold=score_threshold
            )
            search_time = time.time() - search_start
            
            total_time = time.time() - start_time
            
            logger.info(
                f"Retrieval completed: {len(results)} results in {total_time:.3f}s "
                f"(embed: {embed_time:.3f}s, search: {search_time:.3f}s)"
            )
            
            return [RetrievalResult.from_scored_point(p) for p in results]
            
        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            raise
    
    async def retrieve_context(
        self,
        query: str,
        top_k: Optional[int] = None,
        include_metadata: bool = False
    ) -> str:
        """
        Retrieve and format context for LLM consumption.
        
        Args:
            query: The search query
            top_k: Number of chunks to retrieve
            include_metadata: Include source information in context
            
        Returns:
            Formatted context string ready for LLM prompt
        """
        results = await self.retrieve(query, top_k)
        
        if not results:
            return ""
        
        context_parts = []
        
        for i, result in enumerate(results, 1):
            if include_metadata:
                header = result.metadata.get("header", "")
                source = result.metadata.get("source", "unknown")
                if header:
                    context_parts.append(f"[{i}] {header}\n{result.text}")
                else:
                    context_parts.append(f"[{i}] {result.text}")
            else:
                context_parts.append(result.text)
        
        return "\n\n---\n\n".join(context_parts)
    
    async def retrieve_with_sources(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> tuple[str, list[dict]]:
        """
        Retrieve context with separate source information.
        
        Useful for displaying sources in UI alongside the context.
        
        Args:
            query: The search query
            top_k: Number of chunks to retrieve
            
        Returns:
            Tuple of (context_string, list of source dicts)
        """
        results = await self.retrieve(query, top_k)
        
        if not results:
            return "", []
        
        context_parts = []
        sources = []
        
        for i, result in enumerate(results, 1):
            context_parts.append(result.text)
            sources.append({
                "index": i,
                "text": result.text[:100] + "..." if len(result.text) > 100 else result.text,
                "score": round(result.score, 3),
                "header": result.metadata.get("header", ""),
                "source": result.metadata.get("source", "unknown")
            })
        
        context = "\n\n".join(context_parts)
        return context, sources


def create_system_prompt_with_context(
    base_prompt: str,
    context: str,
    query: Optional[str] = None
) -> str:
    """
    Create a system prompt with RAG context injected.
    
    Args:
        base_prompt: The base system prompt
        context: Retrieved context to inject
        query: Optional query for reference
        
    Returns:
        Complete system prompt with context
    """
    if not context:
        return base_prompt
    
    return f"""{base_prompt}

Use the following information from the knowledge base to answer the user's question accurately:

---
{context}
---

Important instructions:
- Base your answer primarily on the provided context above
- If the context doesn't contain enough information to answer fully, say so
- Be helpful and conversational while staying accurate
- If asked about something not in the context, acknowledge that and offer what help you can
"""


# Default Voara AI system prompt
VOARA_SYSTEM_PROMPT = """You are Voara AI, a friendly and professional voice-based customer service assistant.

Your role is to:
- Answer customer questions about Voara AI's products and services
- Provide helpful, accurate information
- Be conversational and natural in your responses
- Keep responses concise since you're speaking, not writing
- If you don't know something, honestly say so and offer to help in other ways

Remember: You're having a voice conversation, so speak naturally and avoid long monologues."""
