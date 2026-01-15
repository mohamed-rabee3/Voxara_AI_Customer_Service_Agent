"""
RAG Pipeline Configuration Module

Loads environment variables and defines constants for the RAG pipeline.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class RAGSettings(BaseSettings):
    """RAG pipeline configuration settings."""
    
    # Qdrant Configuration
    qdrant_url: str = Field(default="", description="Qdrant Cloud URL")
    qdrant_api_key: str = Field(default="", description="Qdrant API key")
    qdrant_collection_name: str = Field(default="voara_kb", description="Qdrant collection name")
    
    # Google AI Configuration
    google_api_key: str = Field(default="", description="Google AI API key")
    embedding_model: str = Field(default="models/text-embedding-004", description="Embedding model name")
    embedding_dimension: int = Field(default=768, description="Embedding vector dimension")
    
    # Chunking Configuration
    chunk_size: int = Field(default=500, description="Maximum chunk size in characters")
    chunk_overlap: int = Field(default=50, description="Overlap between chunks in characters")
    
    # Retrieval Configuration
    top_k: int = Field(default=3, description="Number of chunks to retrieve")
    score_threshold: float = Field(default=0.3, description="Minimum similarity score threshold")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_rag_settings() -> RAGSettings:
    """Get cached RAG settings instance."""
    return RAGSettings()


def validate_settings() -> bool:
    """
    Validate that all required settings are configured.
    
    Returns:
        True if all required settings are present, raises ValueError otherwise.
    """
    settings = get_rag_settings()
    
    errors = []
    
    if not settings.qdrant_url:
        errors.append("QDRANT_URL is not set")
    if not settings.qdrant_api_key:
        errors.append("QDRANT_API_KEY is not set")
    if not settings.google_api_key:
        errors.append("GOOGLE_API_KEY is not set")
    
    if errors:
        raise ValueError(f"Missing required configuration: {', '.join(errors)}")
    
    return True
