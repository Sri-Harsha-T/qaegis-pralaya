---
epic: pqc-layer
phase: 1-C
agent: C
parallel: true
status: todo
---

# Epic: PQC Layer

## Tasks
| ID | Title | Parallel | Est | Depends |
|----|-------|:--------:|-----|---------|
| 010 | liboqs verify + Dilithium3 keygen | ❌ | 15m | — |
| 011 | IncidentReport + SignedReport dataclasses | ✅ | 10m | — |
| 012 | PQCSigner: sign / verify / serialize | ❌ | 20m | 010,011 |
| 013 | ResponderKeyRegistry + synthetic responders | ✅ | 10m | 012 |
| 014 | FastAPI /sign + /verify endpoints | ✅ | 10m | 012 |

## Spec
See `docs/phases/phase-1-pqc/spec.md`
