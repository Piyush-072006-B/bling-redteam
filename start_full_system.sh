#!/bin/bash
echo "Starting BLING Sandbox (Full System)..."

echo "Starting backend containers..."
docker compose up -d

echo "Checking dashboard dependencies..."
cd dashboard
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

echo "Starting frontend dev server..."
echo "The dashboard will be available at http://localhost:3000"
npm run dev
