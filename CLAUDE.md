# CLAUDE.md
<!-- Claude Code reads this file at the start of every session. Keep it tight. -->

## What this repo is

QAegisPralaya is a government-facing EOC (Emergency Operations Center) command
platform for multi-domain crisis response. It combines:

- **Hybrid VQC (QML)** — PennyLane 5-qubit Variational Quantum Circuit predicts
  cascading inter-departmental failure chains (climate→grid→water→medical→telecom)
- **PQC Security** — Dilithium3 (NIST ML-DSA / FIPS 204) signs all field incident
  reports; EOC acts as certificate authority
- **React Dashboard** — real-time EOC commander view via WebSocket

**GitHub:** `https://github.com/Sri-Harsha-T/qaegis-pralaya`
**Hackathon:** QuantumX 2026, Problem #16, May 23 Bengaluru

---

## How to navigate — read in this order each session

1. **This file** — commands, conventions, active stage
2. `memory-bank/activeContext.md` — current phase, active task, next action
3. `CHANGELOG.md` → "Failed Approaches" — do NOT retry listed approaches
4. On demand: `docs/adr/README.md`, `docs/phases/<phase>/spec.md`

---

## Quick-start commands

```bash
# Install all deps
pip install pennylane fastapi uvicorn websockets httpx networkx \
            scikit-learn numpy pandas python-dotenv liboqs-python
cd frontend && npm install && cd ..

# Generate synthetic training data
python data/generate_scenario.py --all

# Train VQC (writes backend/models/vqc_weights.json)
python scripts/train_vqc.py

# Verify PQC layer works on this machine (critical — run before anything else)
python scripts/verify_pqc.py

# Start backend
uvicorn backend.main:app --reload --port 8000

# Start frontend (separate terminal)
cd frontend && npm run dev

# Run full smoke test suite (<60s)
bash scripts/quick-test.sh

# Run a demo scenario
bash scripts/run_demo.sh flood_grid
```

---

## Active phase

**Phase 1 (parallel):** Data Pipeline + QML Engine + PQC Layer
→ See `memory-bank/activeContext.md` for exact current task.

CCPM epics live in `.claude/epics/`. PRD at `.claude/prds/qaegispralaya.md`.

---

## CCPM slash commands

```
/pm:prd-new           Create a new PRD for a phase
/pm:prd-parse         Parse PRD → epic + task structure
/pm:epic-decompose    Break epic into tasks with parallel/depends metadata
/pm:issue-start <id>  Mark task in-progress, begin implementation
/pm:next              Get next unblocked task across all epics
/pm:standup           Status across all open tasks
```

---

## Parallel agent execution protocol

Claude Code supports running multiple sub-agents on independent tasks.
Use this pattern to maximise throughput within a single session:

```
# Phase 1: launch 3 agents simultaneously on independent tasks
Task A (independent): data/generate_scenario.py + data_pipeline.py
Task B (independent): backend/qml_engine.py + VQC training
Task C (independent): backend/pqc_signer.py + key registry

# Phase 3: launch 2 agents simultaneously
Task D (independent): frontend/ React dashboard
Task E (independent): demo/ scenarios + README.md
```

Each agent reads only its own epic spec (`docs/phases/<phase>/spec.md`)
and writes only its own files. No agent reads another agent's output
until the integration phase.

---

## Token management — session discipline

- Read `memory-bank/activeContext.md` FIRST — skip re-reading completed phases
- Use `/compact` at ~60% context fill with directive: "focus: [current task]"
- Use `/clear` between unrelated phases — write state to `activeContext.md` first
- Never re-read entire codebase — read only the file you are about to edit
- ADRs exist so decisions are not re-litigated — check `docs/adr/README.md` before proposing changes
- Failed approaches are in `CHANGELOG.md` — do not retry them

---

## Python conventions

- Python 3.11+; type hints on all public functions
- `pathlib.Path` over `os.path`; `dataclasses` over plain dicts for schemas
- Return `dict` from API handlers, not custom objects (FastAPI serialises)
- All file paths relative to project root — use `Path(__file__).parent`
- No bare `except:` — always `except SpecificError as e:`
- Logging via `logging.getLogger(__name__)` — never `print()` in production code
- Tests: `pytest` with `tests/unit/test_<module>.py` naming

---

## Quantum conventions

- VQC device: `pennylane.device("default.qubit", wires=5)` — simulator only
- Never claim "quantum speedup" — say "quantum-ready architecture"
- PCA reduces 10 features → 5 angles before embedding
- Weights serialised to `backend/models/vqc_weights.json` after training
- PQC algorithm: `"Dilithium3"` via `liboqs.Signature` — test this first
- If liboqs unavailable: HMAC-SHA256 fallback with WARNING log — never silent fail

---

## Definition of Done (every task)

- [ ] Acceptance criteria from epic spec all pass
- [ ] `bash scripts/quick-test.sh` green (smoke tests)
- [ ] No bare `except:`, no `print()` in production code
- [ ] `memory-bank/activeContext.md` "Next Action" updated
- [ ] `CHANGELOG.md` updated (entry or "Failed Approaches" if relevant)

---

## Decided ADRs — do not re-open without a new ADR

See `docs/adr/README.md` for full index.
Key decisions locked:
- ADR-0001: PennyLane `default.qubit` simulator for hackathon (not real hardware)
- ADR-0002: Dilithium3 (ML-DSA) as the PQC algorithm — not Kyber (signing, not KEM)
- ADR-0003: Synthetic data via graph simulation + copula sampling (not real SCADA)
- ADR-0004: FastAPI + WebSocket for backend (not Django, not gRPC)
- ADR-0005: React + Vite + Tailwind for dashboard (not Next.js)
- ADR-0006: EOC as certificate authority for key distribution (not hierarchical PKI)
