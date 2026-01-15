"""
Qdrant Vector Database Service Module

Provides async operations for vector storage and retrieval using Qdrant Cloud.
"""

import logging
from typing import Optional
from contextlib import asynccontextmanager

from qdrant_client import AsyncQdrantClient, QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    ScoredPoint,
)

from .config import get_rag_settings

logger = logging.getLogger(__name__)


class QdrantService:
    """
    Async Qdrant vector database service.
    
    Handles connection, collection management, and vector operations.
    """
    
    def __init__(self):
        """Initialize the Qdrant service."""
        self.settings = get_rag_settings()
        self._client: Optional[AsyncQdrantClient] = None
        self._sync_client: Optional[QdrantClient] = None
    
    @property
    def collection_name(self) -> str:
        """Get the collection name."""
        return self.settings.qdrant_collection_name
    
    async def get_client(self) -> AsyncQdrantClient:
        """
        Get or create the async Qdrant client.
        
        Returns:
            AsyncQdrantClient instance
        """
        if self._client is None:
            self._client = AsyncQdrantClient(
                url=self.settings.qdrant_url,
                api_key=self.settings.qdrant_api_key,
                timeout=30
            )
        return self._client
    
    def get_sync_client(self) -> QdrantClient:
        """
        Get or create the sync Qdrant client.
        Used for operations that don't support async.
        
        Returns:
            QdrantClient instance
        """
        if self._sync_client is None:
            self._sync_client = QdrantClient(
                url=self.settings.qdrant_url,
                api_key=self.settings.qdrant_api_key,
                timeout=30
            )
        return self._sync_client
    
    async def close(self) -> None:
        """Close the client connections."""
        if self._client is not None:
            await self._client.close()
            self._client = None
        if self._sync_client is not None:
            self._sync_client.close()
            self._sync_client = None
    
    async def collection_exists(self) -> bool:
        """
        Check if the collection exists.
        
        Returns:
            True if collection exists
        """
        client = await self.get_client()
        try:
            collections = await client.get_collections()
            return any(c.name == self.collection_name for c in collections.collections)
        except Exception as e:
            logger.error(f"Error checking collection existence: {e}")
            return False
    
    async def create_collection(self, recreate: bool = False) -> bool:
        """
        Create the vector collection.
        
        Args:
            recreate: If True, delete existing collection first
            
        Returns:
            True if collection was created successfully
        """
        client = await self.get_client()
        
        try:
            if recreate:
                await self.delete_collection()
            
            exists = await self.collection_exists()
            if exists:
                logger.info(f"Collection '{self.collection_name}' already exists")
                return True
            
            await client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.settings.embedding_dimension,
                    distance=Distance.COSINE
                )
            )
            
            logger.info(f"Created collection '{self.collection_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            raise
    
    async def delete_collection(self) -> bool:
        """
        Delete the collection if it exists.
        
        Returns:
            True if deleted or didn't exist
        """
        client = await self.get_client()
        
        try:
            exists = await self.collection_exists()
            if exists:
                await client.delete_collection(self.collection_name)
                logger.info(f"Deleted collection '{self.collection_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            return False
    
    async def upsert_vectors(
        self,
        ids: list[str],
        vectors: list[list[float]],
        payloads: Optional[list[dict]] = None
    ) -> bool:
        """
        Insert or update vectors in the collection.
        
        Args:
            ids: List of unique point IDs
            vectors: List of embedding vectors
            payloads: Optional list of metadata payloads
            
        Returns:
            True if successful
        """
        client = await self.get_client()
        
        if payloads is None:
            payloads = [{}] * len(ids)
        
        # Create points
        points = [
            PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )
            for point_id, vector, payload in zip(ids, vectors, payloads)
        ]
        
        try:
            await client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=True
            )
            
            logger.debug(f"Upserted {len(points)} vectors")
            return True
            
        except Exception as e:
            logger.error(f"Error upserting vectors: {e}")
            raise
    
    async def search(
        self,
        query_vector: list[float],
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[dict] = None
    ) -> list[ScoredPoint]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: The query embedding vector
            top_k: Number of results to return
            score_threshold: Minimum similarity score
            filter_conditions: Optional filter conditions
            
        Returns:
            List of ScoredPoint results
        """
        client = await self.get_client()
        
        if top_k is None:
            top_k = self.settings.top_k
        if score_threshold is None:
            score_threshold = self.settings.score_threshold
        
        try:
            results = await client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=top_k,
                with_payload=True,
                score_threshold=score_threshold
            )
            
            return results.points
            
        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            raise
    
    async def get_collection_info(self) -> Optional[dict]:
        """
        Get collection information.
        
        Returns:
            Collection info dict or None if not exists
        """
        client = await self.get_client()
        
        try:
            info = await client.get_collection(self.collection_name)
            return {
                'name': self.collection_name,
                'vectors_count': info.vectors_count,
                'points_count': info.points_count,
                'status': info.status
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return None
    
    async def count_points(self) -> int:
        """
        Get the number of points in the collection.
        
        Returns:
            Number of points
        """
        info = await self.get_collection_info()
        return info.get('points_count', 0) if info else 0


# Singleton instance
_qdrant_service: Optional[QdrantService] = None


def get_qdrant_service() -> QdrantService:
    """Get the singleton Qdrant service instance."""
    global _qdrant_service
    if _qdrant_service is None:
        _qdrant_service = QdrantService()
    return _qdrant_service


@asynccontextmanager
async def qdrant_lifespan():
    """
    Context manager for Qdrant service lifecycle.
    Use in FastAPI lifespan events.
    """
    service = get_qdrant_service()
    try:
        yield service
    finally:
        await service.close()
