#!/bin/bash
# ============================================
# Voxara Voice Agent - Quick Deploy Script
# Run this on your Ubuntu server
# ============================================

set -e

echo "🚀 Voxara Voice Agent - Deployment Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Error: .env file not found!${NC}"
    echo "Please create .env from .env.production.example:"
    echo "  cp .env.production.example .env"
    echo "  nano .env"
    exit 1
fi

echo -e "${YELLOW}📦 Checking Docker installation...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not installed! Installing...${NC}"
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker $USER
    echo -e "${GREEN}✅ Docker installed. Please log out and back in, then run this script again.${NC}"
    exit 0
fi

echo -e "${GREEN}✅ Docker is installed${NC}"

echo -e "${YELLOW}🏗️ Building Docker images (this may take 10-15 minutes)...${NC}"
docker compose -f docker-compose.production.yml build

echo -e "${YELLOW}🚀 Starting services...${NC}"
docker compose -f docker-compose.production.yml up -d

echo -e "${YELLOW}⏳ Waiting for API to be healthy...${NC}"
sleep 10

# Check health
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health | grep -q "healthy"; then
        echo -e "${GREEN}✅ API is healthy!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ API health check failed after 5 minutes${NC}"
        echo "Check logs with: docker compose -f docker-compose.production.yml logs"
        exit 1
    fi
    echo "Waiting for API... ($i/30)"
    sleep 10
done

echo ""
echo -e "${GREEN}=========================================="
echo "🎉 Deployment Complete!"
echo "==========================================${NC}"
echo ""
echo "📊 Container Status:"
docker compose -f docker-compose.production.yml ps
echo ""
echo "🔗 Next Steps:"
echo "  1. Configure Nginx Proxy Manager to point to localhost:8000"
echo "  2. Set up Cloudflare Tunnel to point to your NPM instance"
echo "  3. Test: https://api.yourdomain.com/docs"
echo ""
echo "📝 Useful Commands:"
echo "  View logs:    docker compose -f docker-compose.production.yml logs -f"
echo "  Stop:         docker compose -f docker-compose.production.yml down"
echo "  Restart:      docker compose -f docker-compose.production.yml restart"
