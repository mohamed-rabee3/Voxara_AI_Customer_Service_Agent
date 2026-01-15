"""
Agent Configuration Module

Loads and validates configuration for the LiveKit Voice Agent.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class AgentSettings(BaseSettings):
    """Voice agent configuration settings."""
    
    # LiveKit Configuration
    livekit_url: str = Field(default="", description="LiveKit Cloud WebSocket URL")
    livekit_api_key: str = Field(default="", description="LiveKit API key")
    livekit_api_secret: str = Field(default="", description="LiveKit API secret")
    
    # Google AI Configuration
    google_api_key: str = Field(default="", description="Google AI API key")
    
    # Agent Configuration
    gemini_model: str = Field(
        default="gemini-2.0-flash-live-001",
        description="Gemini model for voice agent"
    )
    gemini_voice: str = Field(
        default="Aoede",
        description="Voice for Gemini TTS (Aoede, Puck, Charon, Kore, Fenrir)"
    )
    temperature: float = Field(
        default=0.7,
        description="LLM temperature for response generation",
        ge=0.0,
        le=2.0
    )
    
    # RAG Configuration
    enable_rag: bool = Field(
        default=True,
        description="Enable RAG context retrieval"
    )
    rag_top_k: int = Field(
        default=3,
        description="Number of RAG chunks to retrieve"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_agent_settings() -> AgentSettings:
    """Get cached agent settings instance."""
    return AgentSettings()


def validate_agent_settings() -> bool:
    """
    Validate that all required settings are configured.
    
    Returns:
        True if all required settings are present, raises ValueError otherwise.
    """
    settings = get_agent_settings()
    
    errors = []
    
    if not settings.livekit_url:
        errors.append("LIVEKIT_URL is not set")
    if not settings.livekit_api_key:
        errors.append("LIVEKIT_API_KEY is not set")
    if not settings.livekit_api_secret:
        errors.append("LIVEKIT_API_SECRET is not set")
    if not settings.google_api_key:
        errors.append("GOOGLE_API_KEY is not set")
    
    if errors:
        raise ValueError(f"Missing required configuration: {', '.join(errors)}")
    
    return True


# System prompt for Voara AI
VOARA_SYSTEM_INSTRUCTIONS = """You are Voara AI, a friendly and professional voice-based customer service assistant.

Your role is to:
- Answer customer questions about Voara AI's products and services accurately
- Use the context provided from the knowledge base to answer questions
- Be conversational, warm, and natural in your responses
- Keep your responses concise and clear since you're speaking, not writing
- If you don't know something, honestly say so and offer to help in other ways
- Support both English and Arabic - respond in the same language the user speaks

Important guidelines:
- Base your answers primarily on the provided knowledge base context
- If the context doesn't contain enough information, acknowledge that limitation
- Never make up information that isn't in the knowledge base
- Be helpful and maintain a professional yet friendly tone
- Avoid long monologues - keep responses to 2-3 sentences when possible

Remember: You're having a voice conversation, so speak naturally!"""
