#!/bin/bash
echo "Rebuilding and Starting BLING Sandbox..."
docker compose down
docker compose up -d --build
echo ""
echo "Rebuild complete. Backend services are starting."
