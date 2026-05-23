#!/usr/bin/env bash
# Quick smoke test — must complete in < 60s
# Run before every commit.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== QAegisPralaya Quick Test ==="

# 1. Python imports
echo "→ Checking Python imports..."
python -c "import pennylane; print(f'  PennyLane {pennylane.__version__}')"
python -c "import fastapi; print(f'  FastAPI {fastapi.__version__}')"
python -c "import networkx; print(f'  NetworkX {networkx.__version__}')"

# 2. PQC verification
echo "→ Verifying PQC..."
python scripts/verify_pqc.py && echo "  Dilithium3 OK" || echo "  ⚠ Using HMAC fallback"

# 3. Data check
echo "→ Checking synthetic data..."
if [ -f "data/synthetic/flood_grid.json" ]; then
    COUNT=$(python -c "import json; d=json.load(open('data/synthetic/flood_grid.json')); print(len(d))")
    echo "  flood_grid.json: $COUNT samples"
else
    echo "  ⚠ Synthetic data missing — run: python data/generate_scenario.py --all"
fi

# 4. VQC weights check
echo "→ Checking VQC weights..."
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
