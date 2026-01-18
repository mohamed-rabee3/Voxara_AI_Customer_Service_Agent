# 🚀 Voxara Deployment Guide - Ubuntu Server

Deploy Voxara Voice Agent backends on your Ubuntu home server with Nginx Proxy Manager and Cloudflare Tunnel.

---

## 📋 Prerequisites

- Ubuntu Server (18.04+) on Core2Duo E8400
- At least 4GB RAM (6GB+ recommended)
- Docker & Docker Compose installed
- Nginx Proxy Manager running
- Cloudflare account with a domain

---

## 🔧 Step 1: Install Docker

SSH into your Ubuntu server and run:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sudo sh

# Add your user to docker group (log out and back in after)
sudo usermod -aG docker $USER

# Install Docker Compose plugin
sudo apt install docker-compose-plugin -y

# Verify installation
docker --version
docker compose version
```

---

## 📁 Step 2: Clone the Project

```bash
# Create directory for your projects
mkdir -p ~/projects && cd ~/projects

# Clone the repository
git clone https://github.com/your-username/voxara_AI_Customer_Service_Agent.git
cd voxara_AI_Customer_Service_Agent
```

---

## ⚙️ Step 3: Configure Environment

```bash
# Copy the production environment template
cp .env.production.example .env

# Edit with your actual values
nano .env
```

Fill in your credentials:

```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-key
LIVEKIT_API_SECRET=your-secret
GOOGLE_API_KEY=your-gemini-key
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-qdrant-key
```

---

## 🏗️ Step 4: Build & Start Containers

```bash
# Build the images (this will take ~10-15 minutes on Core2Duo)
docker compose -f docker-compose.production.yml build

# Start the services
docker compose -f docker-compose.production.yml up -d

# Check status
docker compose -f docker-compose.production.yml ps

# View logs
docker compose -f docker-compose.production.yml logs -f
```

Expected output:
```
NAME                    STATUS              PORTS
voxara-backend-api      Up (healthy)        0.0.0.0:8000->8000/tcp
voxara-voice-agent      Up                  
```

---

## 🌐 Step 5: Configure Nginx Proxy Manager

1. **Access NPM Dashboard**: `http://your-server-ip:81`

2. **Add Proxy Host for Backend API**:

   | Field | Value |
   |-------|-------|
   | Domain Names | `api.yourdomain.com` |
   | Scheme | `http` |
   | Forward Hostname/IP | `your-server-local-ip` (e.g., `192.168.1.100`) |
   | Forward Port | `8000` |
   | Block Common Exploits | ✅ |
   | Websockets Support | ✅ |

3. **SSL Tab**:
   - Select "Request a new SSL Certificate"
   - Check "Force SSL"
   - Check "HTTP/2 Support"

---

## ☁️ Step 6: Configure Cloudflare Tunnel

### Option A: Using Cloudflare Dashboard (Recommended)

1. Go to [Cloudflare Zero Trust](https://one.dash.cloudflare.com/)
2. Navigate to **Access** → **Tunnels**
3. Create a new tunnel named `voxara-home-server`
4. Install the connector on your server:

```bash
# Install cloudflared
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# Authenticate (follow the URL in terminal)
cloudflared tunnel login

# Connect your tunnel (use the token from Cloudflare dashboard)
sudo cloudflared service install <YOUR_TUNNEL_TOKEN>
```

5. Add a **Public Hostname**:
   
   | Field | Value |
   |-------|-------|
   | Subdomain | `api` |
   | Domain | `yourdomain.com` |
   | Type | `HTTP` |
   | URL | `localhost:81` (points to NPM) |

### Option B: Tunnel Config File

Create `/etc/cloudflared/config.yml`:

```yaml
tunnel: YOUR_TUNNEL_ID
credentials-file: /root/.cloudflared/YOUR_TUNNEL_ID.json

ingress:
  - hostname: api.yourdomain.com
    service: http://localhost:81
  - service: http_status:404
```

Start the tunnel:
```bash
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
```

---

## ✅ Step 7: Verify Deployment

### Test locally on server:
```bash
curl http://localhost:8000/api/health
# Expected: {"status":"healthy"}
```

### Test via public URL:
```
https://api.yourdomain.com/docs
```

### Check voice agent:
```bash
docker compose -f docker-compose.production.yml logs -f voice-agent
```

You should see:
```
INFO: Connecting to LiveKit at wss://your-project.livekit.cloud
INFO: Agent connected successfully
```

---

## 🛠️ Management Commands

```bash
# Stop all services
docker compose -f docker-compose.production.yml down

# Restart services
docker compose -f docker-compose.production.yml restart

# Rebuild after code changes
docker compose -f docker-compose.production.yml build --no-cache
docker compose -f docker-compose.production.yml up -d

# View real-time logs
docker compose -f docker-compose.production.yml logs -f

# Check resource usage
docker stats
```

---

## 🔍 Troubleshooting

### Container won't start
```bash
# Check logs for errors
docker compose -f docker-compose.production.yml logs backend-api
```

### Out of memory on Core2Duo
Edit `docker-compose.production.yml` and reduce memory limits:
```yaml
limits:
  memory: 512M  # Reduce from 768M
```

### Build fails (NumPy issues)
The Dockerfile includes fixes for Core2Duo (no AVX). If still failing:
```bash
# Check if build has OpenBLAS
docker compose -f docker-compose.production.yml build --no-cache 2>&1 | grep -i blas
```

### API returns 502 via NPM
1. Check container is healthy: `docker ps`
2. Verify IP in NPM matches your server's IP
3. Test locally first: `curl http://localhost:8000/api/health`

---

## 📊 Resource Monitoring

For a Core2Duo E8400, expect:
- **CPU**: 50-80% during voice processing
- **Memory**: ~1.5GB for both containers
- **Disk**: ~2GB for Docker images

Monitor with:
```bash
htop                    # System resources
docker stats            # Container resources
```

---

## 🔄 Auto-Start on Boot

The containers are configured with `restart: unless-stopped`, so they will automatically start when Docker starts. Ensure Docker starts on boot:

```bash
sudo systemctl enable docker
```
