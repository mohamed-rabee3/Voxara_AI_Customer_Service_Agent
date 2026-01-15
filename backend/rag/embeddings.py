"""
Embedding Service Module

Provides text embedding functionality using Google's text-embedding-004 model.
Supports both document and query embedding with appropriate task types.
"""

import asyncio
from functools import lru_cache
from typing import Optional

import google.generativeai as genai

from .config import get_rag_settings


# Module-level client initialization flag
_initialized = False


def _ensure_initialized() -> None:
    """Ensure the Google AI client is initialized."""
    global _initialized
    if not _initialized:
        settings = get_rag_settings()
        genai.configure(api_key=settings.google_api_key)
        _initialized = True


def embed_text_sync(
    text: str,
    task_type: str = "retrieval_document"
) -> list[float]:
    """
    Generate embedding for a single text synchronously.
    
    Args:
        text: The text to embed
        task_type: Either "retrieval_document" for documents or "retrieval_query" for queries
        
    Returns:
        List of floats representing the embedding vector (768 dimensions)
    """
    _ensure_initialized()
    settings = get_rag_settings()
    
    result = genai.embed_content(
        model=settings.embedding_model,
        content=text,
        task_type=task_type
    )
    
    return result["embedding"]


async def embed_text(
    text: str,
    task_type: str = "retrieval_document"
) -> list[float]:
    """
    Generate embedding for a single text asynchronously.
    
    Args:
        text: The text to embed
        task_type: Either "retrieval_document" for documents or "retrieval_query" for queries
        
    Returns:
        List of floats representing the embedding vector (768 dimensions)
    """
    # Run sync function in thread pool for async compatibility
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        embed_text_sync,
        text,
        task_type
    )


async def embed_query(query: str) -> list[float]:
    """
    Generate embedding for a search query.
    Uses RETRIEVAL_QUERY task type for optimized query embeddings.
    
    Args:
        query: The search query text
        
    Returns:
        List of floats representing the embedding vector (768 dimensions)
    """
    return await embed_text(query, task_type="retrieval_query")


async def embed_document(document: str) -> list[float]:
    """
    Generate embedding for a document chunk.
    Uses RETRIEVAL_DOCUMENT task type for optimized document embeddings.
    
    Args:
        document: The document text to embed
        
    Returns:
        List of floats representing the embedding vector (768 dimensions)
    """
    return await embed_text(document, task_type="retrieval_document")


async def embed_batch(
    texts: list[str],
    task_type: str = "retrieval_document",
    batch_size: int = 10
) -> list[list[float]]:
    """
    Generate embeddings for multiple texts with batching.
    
    Args:
        texts: List of texts to embed
        task_type: Task type for all texts
        batch_size: Number of texts to process concurrently
        
    Returns:
        List of embedding vectors
    """
    embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_tasks = [embed_text(text, task_type) for text in batch]
        batch_results = await asyncio.gather(*batch_tasks)
        embeddings.extend(batch_results)
    
    return embeddings


def get_embedding_dimension() -> int:
    """Get the embedding dimension for the configured model."""
    settings = get_rag_settings()
    return settings.embedding_dimension
