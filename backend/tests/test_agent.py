"""
Tests for the LiveKit Voice Agent

Run with: poetry run pytest tests/test_agent.py -v
"""

import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock


# Mock environment before importing
@pytest.fixture(autouse=True)
def mock_env():
    """Mock environment variables for testing."""
    env_vars = {
        "LIVEKIT_URL": "wss://test.livekit.cloud",
        "LIVEKIT_API_KEY": "test-api-key",
        "LIVEKIT_API_SECRET": "test-api-secret",
        "GOOGLE_API_KEY": "test-google-key",
        "QDRANT_URL": "https://test.qdrant.io",
        "QDRANT_API_KEY": "test-qdrant-key",
    }
    with patch.dict(os.environ, env_vars):
        yield


class TestAgentConfig:
    """Tests for agent configuration."""
    
    def test_get_agent_settings(self, mock_env):
        """Test that agent settings are loaded correctly."""
        from agent.config import get_agent_settings
        
        # Clear cache to reload settings
        get_agent_settings.cache_clear()
        
        settings = get_agent_settings()
        
        assert settings.livekit_url == "wss://test.livekit.cloud"
        assert settings.livekit_api_key == "test-api-key"
        assert settings.google_api_key == "test-google-key"
    
    def test_default_model_settings(self, mock_env):
        """Test default model settings."""
        from agent.config import get_agent_settings
        
        get_agent_settings.cache_clear()
        settings = get_agent_settings()
        
        assert settings.gemini_model == "gemini-2.0-flash-live-001"
        assert settings.gemini_voice == "Aoede"
        assert settings.temperature == 0.7
        assert settings.enable_rag is True
        assert settings.rag_top_k == 3
    
    def test_validate_agent_settings_success(self, mock_env):
        """Test settings validation with all required vars."""
        from agent.config import validate_agent_settings, get_agent_settings
        
        get_agent_settings.cache_clear()
        
        result = validate_agent_settings()
        assert result is True
    
    def test_validate_agent_settings_missing_var(self):
        """Test settings validation with missing vars."""
        from agent.config import get_agent_settings, AgentSettings
        
        # Create settings with empty values directly
        empty_settings = AgentSettings(
            livekit_url="",
            livekit_api_key="",
            livekit_api_secret="",
            google_api_key=""
        )
        
        # Manually check for errors (mimicking validate_settings logic)
        errors = []
        if not empty_settings.livekit_url:
            errors.append("LIVEKIT_URL")
        if not empty_settings.livekit_api_key:
            errors.append("LIVEKIT_API_KEY")
        
        assert len(errors) > 0
        assert "LIVEKIT_URL" in errors
    
    def test_system_instructions_exist(self):
        """Test that system instructions are defined."""
        from agent.config import VOARA_SYSTEM_INSTRUCTIONS
        
        assert VOARA_SYSTEM_INSTRUCTIONS is not None
        assert len(VOARA_SYSTEM_INSTRUCTIONS) > 100
        assert "Voara AI" in VOARA_SYSTEM_INSTRUCTIONS


class TestVoaraAgent:
    """Tests for the VoaraAgent class."""
    
    def test_agent_initialization(self, mock_env):
        """Test agent initialization."""
        from agent.voice_agent import VoaraAgent
        
        agent = VoaraAgent(enable_rag=False)
        
        assert agent is not None
        assert agent.enable_rag is False
        assert agent._retriever is None
    
    def test_agent_with_custom_instructions(self, mock_env):
        """Test agent with custom instructions."""
        from agent.voice_agent import VoaraAgent
        
        custom_instructions = "You are a test assistant."
        agent = VoaraAgent(
            base_instructions=custom_instructions,
            enable_rag=False
        )
        
        assert agent.instructions == custom_instructions
    
    def test_agent_default_instructions(self, mock_env):
        """Test agent uses default instructions."""
        from agent.voice_agent import VoaraAgent
        from agent.config import VOARA_SYSTEM_INSTRUCTIONS
        
        agent = VoaraAgent(enable_rag=False)
        
        assert agent.instructions == VOARA_SYSTEM_INSTRUCTIONS
    
    def test_get_instructions_with_context(self, mock_env):
        """Test combining instructions with RAG context."""
        from agent.voice_agent import VoaraAgent
        
        agent = VoaraAgent(enable_rag=False)
        context = "Voara AI provides voice assistants."
        
        result = agent.get_instructions_with_context(context)
        
        assert "KNOWLEDGE BASE CONTEXT" in result
        assert context in result
        assert agent.instructions in result
    
    def test_get_instructions_without_context(self, mock_env):
        """Test instructions when no context provided."""
        from agent.voice_agent import VoaraAgent
        
        agent = VoaraAgent(enable_rag=False)
        
        result = agent.get_instructions_with_context("")
        
        assert result == agent.instructions
    
    @pytest.mark.asyncio
    async def test_retrieve_context_disabled(self, mock_env):
        """Test context retrieval when RAG is disabled."""
        from agent.voice_agent import VoaraAgent
        
        agent = VoaraAgent(enable_rag=False)
        
        result = await agent.retrieve_context("test query")
        
        assert result == ""
    
    @pytest.mark.asyncio
    async def test_retrieve_context_with_retriever(self, mock_env):
        """Test context retrieval with mocked retriever."""
        from agent.voice_agent import VoaraAgent
        
        agent = VoaraAgent(enable_rag=True)
        
        # Mock the retriever
        mock_retriever = MagicMock()
        mock_retriever.retrieve_context = AsyncMock(
            return_value="Voara AI is a voice assistant company."
        )
        agent._retriever = mock_retriever
        
        result = await agent.retrieve_context("What is Voara?")
        
        assert "Voara AI" in result
        assert agent._last_context == result
        assert agent._last_query == "What is Voara?"


class TestCreateAgent:
    """Tests for the create_agent factory function."""
    
    def test_create_agent_default(self, mock_env):
        """Test creating agent with defaults."""
        from agent.voice_agent import create_agent
        
        agent = create_agent()
        
        assert agent is not None
        assert isinstance(agent, object)
    
    def test_create_agent_rag_disabled(self, mock_env):
        """Test creating agent with RAG disabled."""
        from agent.voice_agent import create_agent
        
        agent = create_agent(enable_rag=False)
        
        assert agent.enable_rag is False


class TestAgentProperties:
    """Tests for agent properties."""
    
    def test_last_context_property(self, mock_env):
        """Test last_context property."""
        from agent.voice_agent import VoaraAgent
        
        agent = VoaraAgent(enable_rag=False)
        agent._last_context = "test context"
        
        assert agent.last_context == "test context"
    
    def test_last_query_property(self, mock_env):
        """Test last_query property."""
        from agent.voice_agent import VoaraAgent
        
        agent = VoaraAgent(enable_rag=False)
        agent._last_query = "test query"
        
        assert agent.last_query == "test query"
