"""
Voara Voice Agent - RAG Module

Retrieval-Augmented Generation pipeline for knowledge-grounded responses.
"""

from .config import get_rag_settings, validate_settings, RAGSettings
from .embeddings import embed_text, embed_query, embed_document, embed_batch
from .chunker import MarkdownChunker, Chunk, chunk_markdown_file
from .qdrant_service import QdrantService, get_qdrant_service, qdrant_lifespan
from .retriever import (
    Retriever,
    RetrievalResult,
    create_system_prompt_with_context,
    VOARA_SYSTEM_PROMPT
)

__all__ = [
    # Config
    "get_rag_settings",
    "validate_settings",
    "RAGSettings",
    # Embeddings
    "embed_text",
    "embed_query",
    "embed_document",
    "embed_batch",
    # Chunking
    "MarkdownChunker",
    "Chunk",
    "chunk_markdown_file",
    # Qdrant
    "QdrantService",
    "get_qdrant_service",
    "qdrant_lifespan",
    # Retriever
    "Retriever",
    "RetrievalResult",
    "create_system_prompt_with_context",
    "VOARA_SYSTEM_PROMPT",
]
