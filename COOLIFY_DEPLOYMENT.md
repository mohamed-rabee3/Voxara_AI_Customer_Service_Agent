# Coolify Deployment Guide - Voara Voice Agent Backend

This guide covers deploying the Voara Voice Agent backend to Coolify.

---

## 📋 Prerequisites

Before starting, ensure you have:

1. **Coolify Instance** - Self-hosted or Coolify Cloud
2. **GitHub/GitLab Access** - Repository access configured in Coolify
3. **External Services Ready**:
   - LiveKit Cloud account with API credentials
   - Google AI API key (Gemini)
   - Qdrant Cloud cluster with API key

---

## 🚀 Deployment Options

You have **2 services** to deploy:

| Service | Description | Port | Dockerfile |
|---------|-------------|------|------------|
| **Backend API** | FastAPI REST API | 8000 | `backend/Dockerfile` |
| **Voice Agent** | LiveKit voice agent | - | `backend/Dockerfile.agent` |

---

## 📝 Step-by-Step Deployment

### Step 1: Connect Your Repository

1. Log into your Coolify dashboard
2. Navigate to **Projects** → Create new project (e.g., "Voara Voice Agent")
3. Click **+ Add Resource** → **Public Repository** or **Private Repository (with GitHub App)**
4. Enter your repository URL

### Step 2: Deploy Backend API Service

1. In your project, click **+ New Resource**
2. Select **Docker** → **Dockerfile**
3. Configure the resource:

   | Field | Value |
   |-------|-------|
   | **Name** | `voara-backend-api` |
   | **Repository** | Select your connected repo |
   | **Branch** | `main` (or your default branch) |
   | **Build Pack** | Dockerfile |
   | **Base Directory** | `/backend` |
   | **Dockerfile** | `Dockerfile` |
   | **Exposed Port** | `8000` |

4. Click **Save**

### Step 3: Configure Environment Variables

Go to **Environment Variables** tab and add:

```env
# LiveKit Configuration
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-livekit-api-key
LIVEKIT_API_SECRET=your-livekit-api-secret

# Google AI (Gemini)
GOOGLE_API_KEY=your-google-api-key

# Qdrant Vector Database
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key
```

> [!IMPORTANT]
> Mark sensitive values as **Secret** in Coolify to prevent them from showing in logs.

### Step 4: Configure Domain & SSL

1. Go to **Settings** → **Network**
2. Add your domain (e.g., `api.yourdomain.com`)
3. Coolify will auto-generate SSL certificates via Let's Encrypt

### Step 5: Deploy

1. Click **Deploy** button
2. Monitor the build logs for any issues
3. Once deployed, verify at: `https://api.yourdomain.com/docs`

---

## 🤖 Deploy Voice Agent (Optional)

If you want to run the LiveKit voice agent on Coolify:

1. **+ New Resource** → **Docker** → **Dockerfile**
2. Configure:

   | Field | Value |
   |-------|-------|
   | **Name** | `voara-voice-agent` |
   | **Base Directory** | `/backend` |
   | **Dockerfile** | `Dockerfile.agent` |
   | **Exposed Port** | Leave empty (no HTTP server) |

3. Add the **same environment variables** as the API
4. Deploy

> [!NOTE]
> The voice agent connects to LiveKit Cloud via WebSocket. It doesn't expose an HTTP port.

---

## 🔧 Advanced Configuration

### Health Checks

The API includes a health endpoint. Configure in Coolify:

| Setting | Value |
|---------|-------|
| Health Check Path | `/api/health` |
| Health Check Port | `8000` |
| Health Check Interval | `30s` |

### Resource Limits (Recommended)

| Resource | API Service | Voice Agent |
|----------|-------------|-------------|
| CPU | 0.5 - 1 core | 0.5 - 1 core |
| Memory | 512MB - 1GB | 512MB - 1GB |

### Auto-Scaling (Pro/Enterprise)

Enable horizontal scaling for the API if needed:
- Min replicas: 1
- Max replicas: 3
- Scale trigger: CPU > 70%

---

## 📌 CORS Configuration

The API is pre-configured to accept requests from:
- `http://localhost:3000` (local dev)
- `https://*.vercel.app` (Vercel deployments)

**To add your custom frontend domain**, edit `backend/api/main.py`:

```python
allow_origins=[
    "http://localhost:3000",
    "https://voxara-ai-customer-service-agent.vercel.app",
    "https://your-frontend-domain.com",  # Add your domain
],
```

---

## 🏥 Troubleshooting

### Build Fails: Poetry Installation

If you see Poetry installation errors:
1. Check Coolify has internet access
2. Verify the Dockerfile uses the correct Python version

### Container Won't Start

Check the logs for:
- Missing environment variables
- Qdrant connection failures
- Invalid API keys

### API Returns 500 Errors

1. Verify all environment variables are set correctly
2. Check Qdrant collection exists (run ingestion first)
3. Review container logs in Coolify dashboard

---

## 📊 Monitoring

After deployment, monitor via:

1. **Coolify Dashboard** - Container logs and metrics
2. **API Health Endpoint** - `GET /api/health`
3. **API Docs** - `GET /docs` or `/redoc`

---

## 🔄 CI/CD (Auto-Deploy)

Enable automatic deployments:

1. Go to **Settings** → **Git**
2. Enable **Auto Deploy on Push**
3. Set branch to `main`

Now every push to `main` will trigger a new deployment.

---

## ✅ Verification Checklist

After deployment, verify:

- [ ] API responds at `https://your-domain.com/`
- [ ] Swagger docs load at `https://your-domain.com/docs`
- [ ] Health check passes at `https://your-domain.com/api/health`
- [ ] RAG stats available at `https://your-domain.com/api/rag/stats`
- [ ] CORS works from your frontend domain
