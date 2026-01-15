# Voara AI Voice Agent

A real-time voice-enabled AI customer service agent built with LiveKit, Gemini Live API, and RAG.

![Architecture](docs/architecture.png)

## Features

- 🎤 **Real-time Voice Interaction** - Natural voice conversations powered by Gemini Live API
- 🧠 **RAG-Enhanced Responses** - Context-aware answers from your knowledge base
- 🌐 **Bilingual Support** - English and Arabic language support
- 🎨 **Modern UI** - Beautiful animated interface with dark/light mode
- ⚡ **Low Latency** - Sub-second response times

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Next.js       │     │   LiveKit       │     │   Python        │
│   Frontend      │◄───►│   Cloud         │◄───►│   Backend       │
│   (Vercel)      │     │   (WebRTC)      │     │   (FastAPI)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                              ┌──────────────────────────┼──────────────────────────┐
                              │                          │                          │
                              ▼                          ▼                          ▼
                    ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
                    │   Gemini Live   │     │   Qdrant        │     │   Google        │
                    │   API           │     │   Cloud         │     │   Embeddings    │
                    │   (Voice AI)    │     │   (Vector DB)   │     │   (RAG)         │
                    └─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Tech Stack

### Backend
- **FastAPI** - REST API framework
- **LiveKit Agents** - Real-time voice agent framework
- **Gemini Live API** - Speech-to-speech AI model
- **Qdrant** - Vector database for RAG
- **Google text-embedding-004** - Multilingual embeddings

### Frontend
- **Next.js 15** - React framework
- **shadcn/ui** - UI component library
- **Framer Motion** - Animations
- **LiveKit React SDK** - Real-time audio components

## Prerequisites

- Python 3.11+
- Node.js 18+
- Poetry (Python package manager)
- API keys for:
  - [LiveKit Cloud](https://cloud.livekit.io) (free tier)
  - [Google AI Studio](https://aistudio.google.com/apikey) (free tier)
  - [Qdrant Cloud](https://cloud.qdrant.io) (free tier)

## Quick Start

### 1. Clone and Setup Environment

```bash
git clone https://github.com/yourusername/voxara_AI_Customer_Service_Agent.git
cd voxara_AI_Customer_Service_Agent

# Copy environment template
cp .env.example .env
# Edit .env with your API keys
```

### 2. Backend Setup

```bash
cd backend

# Install dependencies
poetry install

# Ingest knowledge base
poetry run python scripts/ingest_knowledge.py

# Start FastAPI server (in one terminal)
poetry run uvicorn api.main:app --reload --port 8000

# Start LiveKit agent (in another terminal)
poetry run python -m agent.main dev
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Open the App

Navigate to http://localhost:3000 and click "Start Conversation" to begin!

## Project Structure

```
├── backend/
│   ├── api/              # FastAPI REST API
│   ├── agent/            # LiveKit Voice Agent
│   ├── rag/              # RAG pipeline
│   └── scripts/          # Utility scripts
├── frontend/
│   ├── app/              # Next.js app router
│   ├── components/       # React components
│   └── lib/              # Utilities
└── rag_data/             # Knowledge base documents
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `LIVEKIT_URL` | LiveKit Cloud WebSocket URL |
| `LIVEKIT_API_KEY` | LiveKit API key |
| `LIVEKIT_API_SECRET` | LiveKit API secret |
| `GOOGLE_API_KEY` | Google AI Studio API key |
| `QDRANT_URL` | Qdrant Cloud cluster URL |
| `QDRANT_API_KEY` | Qdrant API key |

## Testing

### Backend Tests
```bash
cd backend
poetry run pytest tests/ -v
```

### Manual Testing
1. Ask: "What does Voara AI do?"
2. Expected: Agent responds with company information from knowledge base

## Deployment

### Frontend (Vercel)
```bash
cd frontend
vercel deploy
```

### Backend (Render/Railway)
Use the provided Dockerfile or connect your repository directly.

## License

MIT

## Acknowledgments

- [LiveKit](https://livekit.io) - Real-time communication platform
- [Google Gemini](https://ai.google.dev) - AI models
- [Qdrant](https://qdrant.tech) - Vector search engine
