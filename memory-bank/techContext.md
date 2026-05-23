# Technical Context

## Stack
| Layer | Technology | Notes |
|-------|-----------|-------|
| QML | PennyLane 0.36+ | default.qubit simulator, 5 qubits |
| PQC | liboqs-python | Dilithium3 (ML-DSA / NIST FIPS 204) |
| Graph | NetworkX | Cascade dependency graph, BFS propagation |
| Data | NumPy, scikit-learn | PCA, MinMaxScaler, synthetic generation |
| Backend | FastAPI + Uvicorn | REST + WebSocket |
| Frontend | React + Vite + Tailwind + Leaflet.js | EOC dashboard |
| Real APIs | OpenWeatherMap, Open-Meteo, USGS GeoJSON | Climate features only |

## Critical Build Risk
liboqs-python requires a C compiler and may fail on some platforms.
Always run `python scripts/verify_pqc.py` FIRST before any other work.
HMAC-SHA256 fallback is implemented for demo continuity.

## Port Map
- Backend: localhost:8000
- Frontend: localhost:5173
- Fallback demo server: localhost:8001

## Key File Paths
- VQC weights: backend/models/vqc_weights.json
- Synthetic data: data/synthetic/{flood_grid,heat_hospital,cyclone_comms}.json
- Cascade graph: backend/cascade_graph.py
- Key registry: backend/pqc_signer.py (in-memory ResponderKeyRegistry)
- Demo scenarios: demo/scenario_{flood_grid,heat_hospital,cyclone_comms}.json
