#!/usr/bin/env bash
# ==============================================================================
# GeoTani — Instant Public Demo Share Script
#
# Exposes your local GeoTani stack (Frontend + FastAPI + Martin Vector Tiles)
# to the internet using a secure HTTPS tunnel so anyone can test the live map.
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "================================================================="
echo "               🌾 GeoTani — Instant Demo Sharer                 "
echo "================================================================="

# 1. Ensure Docker Backend Services are running
echo "1. Checking GeoTani backend & database containers..."
if ! docker ps --format '{{.Names}}' | grep -q "geotani-db"; then
    echo "   Starting Docker services (db, api, tiles)..."
    docker compose up -d
else
    echo "   ✓ Docker backend services are running."
fi

# 2. Check if frontend dev server is running on port 5173
echo "2. Checking frontend dev server..."
if ! curl -s -m 2 http://localhost:5173 > /dev/null; then
    echo "   Starting frontend in the background..."
    (cd frontend && npm run dev) &
    FRONTEND_PID=$!
    sleep 3
    echo "   ✓ Frontend dev server started (PID: $FRONTEND_PID)."
else
    echo "   ✓ Frontend dev server is already running on http://localhost:5173."
fi

# 3. Tunneling Options
echo ""
echo "3. Choose a tunneling method to create your instant HTTPS demo URL:"
echo "   [1] Cloudflare Quick Tunnel (Free, no account needed, highly stable) [Recommended]"
echo "   [2] ngrok (Fast, requires free ngrok account)"
echo "   [3] SSH Pinggy (Instant, no install required via SSH)"
echo "   [4] Localtunnel (via npx)"
echo ""
read -p "Select option [1-4] (default: 1): " choice
choice=${choice:-1}

echo ""
case $choice in
    1)
        echo "Launching Cloudflare Tunnel on port 5173..."
        CLOUDFLARED_CMD="npx cloudflared"
        if command -v cloudflared &> /dev/null; then
            CLOUDFLARED_CMD="cloudflared"
        fi

        $CLOUDFLARED_CMD tunnel --url http://localhost:5173 2>&1 | while IFS= read -r line; do
            # Filter routine client tile cancellation messages (user zooming/panning map)
            if [[ "$line" =~ (context\ canceled|canceled\ by\ remote|Group\ ID\ 1000\ is\ not\ between|ICMP\ proxy) ]]; then
                continue
            fi

            # Highlight the public demo URL
            if [[ "$line" =~ https://[a-zA-Z0-9.-]+\.trycloudflare\.com ]]; then
                URL=$(echo "$line" | grep -o 'https://[^ ]*trycloudflare.com')
                echo ""
                echo -e "\033[1;32m=================================================================\033[0m"
                echo -e "\033[1;32m  🎉 YOUR LIVE DEMO URL IS READY:\033[0m"
                echo -e "\033[1;36m  👉 $URL\033[0m"
                echo -e "\033[1;32m=================================================================\033[0m"
                echo "  (Share this link with anyone to demo GeoTani on any device)"
                echo ""
            fi

            # Print standard setup logs
            echo "$line"
        done
        ;;
    2)
        echo "Launching ngrok on port 5173..."
        ngrok http 5173
        ;;
    3)
        echo "Launching Pinggy SSH tunnel on port 5173..."
        ssh -p 443 -R0:localhost:5173 a.pinggy.io
        ;;
    4)
        echo "Launching Localtunnel on port 5173..."
        npx localtunnel --port 5173
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac
