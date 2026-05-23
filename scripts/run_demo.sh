#!/usr/bin/env bash
# Run a demo scenario against the live backend
# Usage: bash scripts/run_demo.sh [flood_grid|heat_hospital|cyclone_comms]
set -euo pipefail
SCENARIO="${1:-flood_grid}"
PORT="${2:-8000}"

echo "🌊 Starting scenario: $SCENARIO"

# Check backend is running
if ! curl -sf "http://localhost:$PORT/health" > /dev/null 2>&1; then
    echo "❌ Backend not running. Start with: uvicorn backend.main:app --port $PORT"
    exit 1
fi

# Trigger scenario
curl -sf -X POST "http://localhost:$PORT/scenario/$SCENARIO" \
  -H "Content-Type: application/json" | python -m json.tool

echo ""
echo "📡 Tailing alert stream for 60 seconds..."
echo "   (Press Ctrl+C to stop)"

# WebSocket tail via Python
python - << PYEOF
import asyncio, websockets, json, sys

async def tail():
    uri = "ws://localhost:$PORT/ws/alerts"
    try:
        async with websockets.connect(uri) as ws:
            count = 0
            while count < 20:
                msg = await asyncio.wait_for(ws.recv(), timeout=10)
                data = json.loads(msg)
                risk = data.get('overall_risk', 0)
                chain = ' → '.join(data.get('propagation_chain', []))
                print(f"  ⚠ Risk: {risk:.0%} | {data.get('cascade_type','—')} | {chain}")
                count += 1
    except Exception as e:
        print(f"  Stream ended: {e}")

asyncio.run(tail())
PYEOF

echo "✅ Demo scenario complete"
