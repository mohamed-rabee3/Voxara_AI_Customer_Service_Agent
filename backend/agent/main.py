"""
LiveKit Voice Agent Entry Point

Main entry point for running the Voara Voice Agent with LiveKit.
Run with: python -m agent.main dev
"""

import logging
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, room_io
from livekit.plugins import google, silero

from .config import get_agent_settings, validate_agent_settings, VOARA_SYSTEM_INSTRUCTIONS
from .voice_agent import VoaraAgent, setup_session_events

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Validate settings on import
try:
    validate_agent_settings()
    logger.info("Agent settings validated successfully")
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    logger.error("Please set required environment variables in .env file")


# Create agent server
server = AgentServer()


@server.rtc_session()
async def voara_agent(ctx: agents.JobContext):
    """
    Main agent session handler.
    
    Called when a participant joins a room that requests an agent.
    Sets up the Gemini Live API model and starts the conversation.
    """
    settings = get_agent_settings()
    
    logger.info(f"Starting agent session for room: {ctx.room.name}")
    
    # Create the Voara agent with RAG support
    agent = VoaraAgent(
        base_instructions=VOARA_SYSTEM_INSTRUCTIONS,
        enable_rag=settings.enable_rag
    )
    
    # Retrieve initial context if RAG is enabled
    initial_context = ""
    if settings.enable_rag:
        try:
            # Pre-fetch general context about Voara
            initial_context = await agent.retrieve_context(
                "What is Voara AI and what services do you offer?"
            )
        except Exception as e:
            logger.warning(f"Failed to retrieve initial context: {e}")
    
    # Build instructions with context
    instructions = VOARA_SYSTEM_INSTRUCTIONS
    if initial_context:
        instructions = agent.get_instructions_with_context(initial_context)
    
    # Create AgentSession with Gemini Live API
    session = AgentSession(
        llm=google.realtime.RealtimeModel(
            model=settings.gemini_model,
            voice=settings.gemini_voice,
            temperature=settings.temperature,
            instructions=instructions,
        ),
        vad=silero.VAD.load(),  # Voice Activity Detection
    )
    
    # Set up event handlers
    await setup_session_events(session, agent, ctx.room)
    
    # Start the session
    await session.start(
        room=ctx.room,
        agent=agent,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                # Enable noise cancellation if available
                # noise_cancellation=noise_cancellation.BVC(),
            ),
        ),
    )
    
    logger.info("Agent session started, waiting for user interaction...")
    
    # Generate initial greeting
    await session.generate_reply(
        instructions="Greet the user warmly and introduce yourself as Voara AI. "
                    "Ask how you can help them today. Keep it brief and friendly."
    )
    
    # Wait for the session to end
    await session.wait_for_close()
    
    logger.info("Agent session ended")


def main():
    """
    Main entry point for the agent.
    
    Handles CLI arguments and starts the agent server.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Voara Voice Agent")
    parser.add_argument(
        "command",
        choices=["dev", "start", "download-files"],
        help="Command to run"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    if args.command == "download-files":
        logger.info("Downloading model files...")
        # Silero VAD and other models are downloaded automatically on first use
        silero.VAD.load()
        logger.info("Model files downloaded successfully")
        return
    
    # Start the agent server
    logger.info("Starting Voara Voice Agent...")
    logger.info(f"LiveKit URL: {os.getenv('LIVEKIT_URL', 'not set')}")
    
    # The server.run() handles both 'dev' and 'start' modes
    server.run()


if __name__ == "__main__":
    main()
