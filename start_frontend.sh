#!/bin/bash
echo "Starting BLING Dashboard Frontend..."
cd dashboard
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi
npm run dev
