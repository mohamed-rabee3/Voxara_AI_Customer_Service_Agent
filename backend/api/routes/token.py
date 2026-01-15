"""
Token Generation Route

Generates LiveKit access tokens for frontend clients.
"""

import os
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from livekit import api

logger = logging.getLogger(__name__)

router = APIRouter()


class TokenRequest(BaseModel):
    """Request model for token generation."""
    
    room_name: str = Field(
        ...,
        description="Name of the LiveKit room to join",
        min_length=1,
        max_length=128,
        examples=["voara-session-123"]
    )
    participant_name: str = Field(
        ...,
        description="Display name for the participant",
        min_length=1,
        max_length=64,
        examples=["User"]
    )
    participant_identity: Optional[str] = Field(
        default=None,
        description="Unique identity for the participant (defaults to participant_name)",
        max_length=128
    )


class TokenResponse(BaseModel):
    """Response model for token generation."""
    
    token: str = Field(..., description="JWT access token for LiveKit")
    room_name: str = Field(..., description="Name of the room")
    participant_identity: str = Field(..., description="Participant identity")
    livekit_url: str = Field(..., description="LiveKit WebSocket URL")


@router.post("/token", response_model=TokenResponse)
async def generate_token(request: TokenRequest) -> TokenResponse:
    """
    Generate a LiveKit access token for joining a room.
    
    The token grants permission to:
    - Join the specified room
    - Publish and subscribe to audio/video
    - Access room metadata
    
    Args:
        request: Token request with room and participant info
        
    Returns:
        TokenResponse with JWT token and connection details
    """
    # Get credentials from environment
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    livekit_url = os.getenv("LIVEKIT_URL")
    
    if not api_key or not api_secret:
        logger.error("LiveKit credentials not configured")
        raise HTTPException(
            status_code=500,
            detail="LiveKit credentials not configured"
        )
    
    if not livekit_url:
        logger.error("LiveKit URL not configured")
        raise HTTPException(
            status_code=500,
            detail="LiveKit URL not configured"
        )
    
    # Use participant_name as identity if not specified
    identity = request.participant_identity or request.participant_name
    
    try:
        # Generate token using livekit-api
        token = (
            api.AccessToken(api_key, api_secret)
            .with_identity(identity)
            .with_name(request.participant_name)
            .with_grants(api.VideoGrants(
                room_join=True,
                room=request.room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            ))
            .to_jwt()
        )
        
        logger.info(f"Generated token for '{identity}' to join room '{request.room_name}'")
        
        return TokenResponse(
            token=token,
            room_name=request.room_name,
            participant_identity=identity,
            livekit_url=livekit_url
        )
        
    except Exception as e:
        logger.error(f"Failed to generate token: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate token: {str(e)}"
        )
