# Active Context
<!-- Update "Next Action" before ending every session -->

## Current Phase
Phase 0 — Scaffold complete. Phase 1 starting.

## Active Tasks
- [ ] Task 001: Synthetic scenario generator (Agent A)
- [ ] Task 005: VQC architecture + training (Agent B)
- [ ] Task 010: Dilithium3 key gen + signing (Agent C)

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
Run `python scripts/verify_pqc.py` immediately — this is the highest-risk
dependency. If it fails, switch to HMAC fallback and log to CHANGELOG.md.

## Completed
- [x] Phase 0: Repo scaffold, CLAUDE.md, memory-bank, ADRs, phase specs
