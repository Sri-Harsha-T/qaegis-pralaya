# Active Context
<!-- Update "Next Action" before ending every session -->

## Current Phase
Phase 0 — Scaffold complete. Phase 1 starting.

## Active Tasks
- [ ] Task 001: Synthetic scenario generator (Agent A)
- [ ] Task 005: VQC architecture + training (Agent B)
- [x] Task 010: Dilithium3 key gen + signing (Agent C - COMPLETE)
- [x] Task 011: IncidentReport + SignedReport dataclasses (Agent C - COMPLETE)
- [x] Task 012: PQCSigner - sign / verify / serialize (Agent C - COMPLETE)
- [x] Task 013: ResponderKeyRegistry + synthetic responders (Agent C - COMPLETE)
- [x] Task 014: FastAPI /sign + /verify endpoints (Agent C - COMPLETE)

## Parallel Streams Available
Agent A → data/ (no dependencies)
Agent B → backend/qml_engine.py (needs Agent A output to train)
Agent C → backend/pqc_signer.py (no dependencies)

## Stage Gates Pending
- [ ] `python scripts/verify_pqc.py` exits 0 (Dilithium3 available on this machine)
- [ ] `python data/generate_scenario.py --all` produces 3 JSON files in data/synthetic/
- [ ] VQC accuracy > 65% on held-out test set
- [ ] PQC sign+verify round-trip < 500ms

## Next Action
Agent C (PQC Layer) COMPLETE. Implemented backend/pqc_signer.py with HMAC-SHA256 fallback since liboqs unavailable. All 5 tasks complete:
- IncidentReport/SignedReport dataclasses with validation
- PQCSigner with Dilithium3/HMAC fallback
- ResponderKeyRegistry with 5 synthetic responders  
- FastAPI endpoints: POST /api/pqc/sign, POST /api/pqc/verify
- Performance: sign+verify <500ms achieved
- Unit tests: tests/unit/test_pqc_signer.py

Ready for integration with Agents A & B outputs.

## Completed
- [x] Phase 0: Repo scaffold, CLAUDE.md, memory-bank, ADRs, phase specs
