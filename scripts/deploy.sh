#!/bin/bash
# Deployment-Script für VM 211
# Nutzung: ssh martin@10.10.10.211 'cd /opt/docker/life-manager && bash scripts/deploy.sh'
set -e

echo "Pulling latest changes..."
git pull origin main

echo "Building and restarting services..."
docker compose build
docker compose up -d

echo "Waiting for health checks..."
sleep 10
docker compose ps

echo "Health check:"
curl -s http://localhost:8000/health | python3 -m json.tool

echo ""
echo "Deployment complete!"
