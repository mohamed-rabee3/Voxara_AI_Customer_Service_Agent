"""
Voara Voice Agent Logic

Implements the voice agent using LiveKit Agents with Gemini Live API and RAG.
"""

import logging
from typing import Optional

from livekit import rtc
from livekit.agents import Agent, AgentSession, UserInputTranscribedEvent

from .config import get_agent_settings, VOARA_SYSTEM_INSTRUCTIONS

logger = logging.getLogger(__name__)


class VoaraAgent(Agent):
    """
    Voara AI Voice Agent.
    
    A RAG-enhanced voice agent that uses Gemini Live API for
    natural voice conversations grounded in company knowledge.
    """
    
    def __init__(
        self,
        base_instructions: Optional[str] = None,
        enable_rag: bool = True
    ):
        """
        Initialize the Voara Agent.
        
        Args:
            base_instructions: Custom base instructions (defaults to Voara system prompt)
            enable_rag: Whether to enable RAG context retrieval
        """
        self.enable_rag = enable_rag
        self._retriever = None
        self._last_context = ""
        self._last_query = ""
        
        # Use custom instructions or default Voara prompt
        instructions = base_instructions or VOARA_SYSTEM_INSTRUCTIONS
        
        super().__init__(instructions=instructions)
        
        logger.info(f"VoaraAgent initialized (RAG enabled: {enable_rag})")
    
    async def _get_retriever(self):
        """Lazy-load the RAG retriever."""
        if self._retriever is None and self.enable_rag:
            try:
                from rag import Retriever
                self._retriever = Retriever()
                logger.info("RAG retriever initialized")
            except Exception as e:
                logger.error(f"Failed to initialize RAG retriever: {e}")
                self.enable_rag = False
        return self._retriever
    
    async def retrieve_context(self, query: str) -> str:
        """
        Retrieve context from the knowledge base.
        
        Args:
            query: The user's query
            
        Returns:
            Formatted context string for LLM consumption
        """
        if not self.enable_rag:
            return ""
        
        try:
            retriever = await self._get_retriever()
            if retriever is None:
                return ""
            
            context = await retriever.retrieve_context(
                query=query,
                include_metadata=False
            )
            
            if context:
                self._last_context = context
                self._last_query = query
                logger.info(f"Retrieved {len(context)} chars of context for: {query[:50]}...")
            
            return context
            
        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}")
            return ""
    
    def get_instructions_with_context(self, context: str) -> str:
        """
        Combine base instructions with RAG context.
        
        Args:
            context: Retrieved knowledge base context
            
        Returns:
            Full instructions with context
        """
        if not context:
            return self.instructions
        
        return f"""{self.instructions}

---
KNOWLEDGE BASE CONTEXT:
Use the following information to answer the user's question:

{context}

---
Remember to base your answer on this context. If the context doesn't contain the answer, acknowledge that and offer what help you can."""
    
    @property
    def last_context(self) -> str:
        """Get the last retrieved context (for UI display)."""
        return self._last_context
    
    @property
    def last_query(self) -> str:
        """Get the last query (for debugging)."""
        return self._last_query


async def setup_session_events(
    session: AgentSession,
    agent: VoaraAgent,
    room: rtc.Room
):
    """
    Set up event handlers for the agent session.
    
    Handles transcription events and RAG context injection.
    
    Args:
        session: The AgentSession instance
        agent: The VoaraAgent instance
        room: The LiveKit room
    """
    
    @session.on("user_input_transcribed")
    async def on_user_input_transcribed(event: UserInputTranscribedEvent):
        """Handle user speech transcription."""
        if not event.is_final:
            return
        
        transcript = event.transcript.strip()
        if not transcript:
            return
        
        logger.info(f"User said: {transcript}")
        
        # Retrieve RAG context for the user's query
        if agent.enable_rag and transcript:
            context = await agent.retrieve_context(transcript)
            
            if context:
                # Update room metadata with context (for UI display)
                try:
                    metadata = {
                        "rag_context": context[:500],  # Truncate for metadata
                        "rag_query": transcript
                    }
                    # Note: Room metadata updates would go here
                    # await room.local_participant.update_metadata(json.dumps(metadata))
                    logger.info("RAG context retrieved and ready")
                except Exception as e:
                    logger.warning(f"Failed to update metadata: {e}")
    
    logger.info("Session event handlers configured")


def create_agent(enable_rag: bool = True) -> VoaraAgent:
    """
    Factory function to create a VoaraAgent instance.
    
    Args:
        enable_rag: Whether to enable RAG context retrieval
        
    Returns:
        Configured VoaraAgent instance
    """
    settings = get_agent_settings()
    
    return VoaraAgent(
        base_instructions=VOARA_SYSTEM_INSTRUCTIONS,
        enable_rag=enable_rag and settings.enable_rag
    )
