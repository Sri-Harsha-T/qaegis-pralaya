# Phase 2 — FastAPI Backend Spec
**Wall time:** 50 min | **Agent:** Single (sequential after Phase 1) | **Status:** TODO

## Files to create / modify
- `backend/main.py`
- `backend/scenario_runner.py`
- `backend/api/routes.py`

## Acceptance criteria
- [ ] `uvicorn backend.main:app --port 8000` starts without errors
- [ ] `GET /health` returns `{status: ok, qml: loaded, pqc: available|fallback}`
- [ ] `POST /predict` with 10-feature body returns cascade analysis dict
- [ ] `POST /sign` returns SignedReport JSON
- [ ] `POST /verify` returns `{verified: bool, report_id, signer_id, algorithm}`
- [ ] `POST /scenario/{flood_grid|heat_hospital|cyclone_comms}` starts background task
- [ ] `WS /ws/incidents` streams SignedReport events every 3s during active scenario
- [ ] `WS /ws/alerts` streams cascade update every 5s during active scenario
- [ ] `GET /responders` returns list of 5 synthetic responders

## Startup sequence
1. Load cascade graph (cascade_graph.py)
2. Load VQC weights (models/vqc_weights.json) — train if missing (log WARNING)
3. Verify PQC availability (pqc_signer.py) — fallback if unavailable
4. Pre-populate ResponderKeyRegistry with 5 synthetic responders
5. Start FastAPI app

## Token-efficient implementation note
Do not read all Phase 1 files before starting. Read only the function signatures
from qml_engine.py and pqc_signer.py (first 50 lines of each).
