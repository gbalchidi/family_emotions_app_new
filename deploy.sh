#!/bin/bash
# Manual deployment script for Family Emotions Bot

echo "🚀 Starting fresh deployment..."

# Stop and remove old containers
echo "Stopping old containers..."
docker ps | grep -E "bot|family" | awk '{print $1}' | xargs -r docker stop
docker ps -a | grep -E "bot|family" | awk '{print $1}' | xargs -r docker rm

# Remove old images
echo "Removing old images..."
docker images | grep -E "family|bot" | awk '{print $3}' | xargs -r docker rmi -f

# Clear builder cache
echo "Clearing Docker build cache..."
docker builder prune -af

# Build fresh image
echo "Building fresh image without cache..."
docker build \
  --no-cache \
  --pull \
  --build-arg BUILDKIT_INLINE_CACHE=0 \
  -t family-emotions-bot:latest \
  .

# Run with docker-compose
echo "Starting services..."
docker-compose -f docker-compose.v3.yml up -d

# Check logs
echo "Waiting for bot to start..."
sleep 10
docker-compose -f docker-compose.v3.yml logs bot --tail 20

echo "✅ Deployment complete!"