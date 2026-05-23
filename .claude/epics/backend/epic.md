---
epic: backend
phase: 2
agent: single
parallel: false
status: todo
depends: [data-pipeline, qml-engine, pqc-layer]
---

# Epic: FastAPI Backend

## Tasks
| ID | Title | Parallel | Est | Depends |
|----|-------|:--------:|-----|---------|
| 015 | FastAPI app + CORS + startup sequence | ❌ | 15m | Phase 1 done |
| 016 | WebSocket manager + /ws/incidents | ✅ | 15m | 015 |
| 017 | WebSocket /ws/alerts + cascade stream | ✅ | 15m | 015 |
| 018 | Scenario runner background task | ❌ | 20m | 016,017 |
| 019 | GET /responders + GET /health | ✅ | 10m | 015 |

## Spec
See `docs/phases/phase-2-backend/spec.md`
