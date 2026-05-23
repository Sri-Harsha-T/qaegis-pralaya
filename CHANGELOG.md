# Changelog

## [Unreleased]

### Phase 1-C — PQC Layer (2026-05-23)
- **backend/pqc_signer.py**: Complete PQC signing implementation with HMAC-SHA256 fallback
- **backend/main.py**: FastAPI endpoints for POST /api/pqc/sign and POST /api/pqc/verify  
- **IncidentReport/SignedReport**: Dataclasses with validation (severity 1-5, lat/lon bounds)
- **ResponderKeyRegistry**: 5 synthetic responders pre-populated with keypairs
- **Performance**: Sign+verify round-trip <500ms achieved (HMAC-SHA256 fallback)
- **Unit tests**: tests/unit/test_pqc_signer.py with full coverage
- **WARNING logged**: liboqs-python unavailable, using HMAC fallback as required

### Phase 0 — Scaffold (2026-05-23)
- Repo structure, CLAUDE.md, memory-bank, ADRs 0001–0007
- CCPM epic/task structure for all 6 epics
- Phase specs for all 7 phases
- Backend skeleton: cascade_graph.py, __init__.py
- Scripts: verify_pqc.py, train_vqc.py, quick-test.sh, run_demo.sh
- Docker: docker-compose.yml, Dockerfile.backend
- Tests: tests/smoke/test_imports.py

## Failed Approaches
<!-- Log dead ends here so they are never retried -->
<!-- Format: - [date] What was tried | Why it failed | What to do instead -->
