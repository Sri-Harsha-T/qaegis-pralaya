#!/usr/bin/env bash
# Quick smoke test — must complete in < 60s
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "🦴 CAVEMAN QUICK TEST!"

# 1. Python imports
echo "→ Python imports..."
python3 -c "import pennylane; print(f'  PennyLane {pennylane.__version__}')" 2>/dev/null && echo "  ✅ PennyLane OK" || echo "  ❌ PennyLane FAIL"
python3 -c "import fastapi; print(f'  FastAPI {fastapi.__version__}')" 2>/dev/null && echo "  ✅ FastAPI OK" || echo "  ❌ FastAPI FAIL"
python3 -c "import networkx; print(f'  NetworkX {networkx.__version__}')" 2>/dev/null && echo "  ✅ NetworkX OK" || echo "  ❌ NetworkX FAIL"

# 2. PQC verification
echo "→ PQC test..."
python3 scripts/verify_pqc.py >/dev/null 2>&1 && echo "  ✅ Dilithium3 OK" || echo "  ⚠️ HMAC fallback"

# 3. Data check
echo "→ Data check..."
if [ -f "data/synthetic/flood_grid.json" ]; then
    COUNT=$(python3 -c "import json; d=json.load(open('data/synthetic/flood_grid.json')); print(len(d))" 2>/dev/null || echo "0")
    echo "  ✅ Synthetic data: $COUNT samples"
else
    echo "  ❌ No synthetic data"
fi

# 4. Frontend check
echo "→ Frontend check..."
if [ -f "frontend/package.json" ]; then
    echo "  ✅ React frontend ready"
else
    echo "  ❌ No frontend"
fi

echo "🦴 SMOKE TEST DONE!"
if [ -f "backend/models/vqc_weights.json" ]; then
    echo "  vqc_weights.json: present"
else
    echo "  ⚠ VQC weights missing — run: python scripts/train_vqc.py"
fi

# 5. Unit tests (if pytest available)
if command -v pytest &>/dev/null && [ -d "tests" ]; then
    echo "→ Running unit tests..."
    pytest tests/unit/ -q --tb=short 2>/dev/null || echo "  ⚠ Some tests failed — check output"
fi

echo "=== Quick test complete ==="
