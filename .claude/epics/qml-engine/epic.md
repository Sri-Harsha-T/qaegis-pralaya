---
epic: qml-engine
phase: 1-B
agent: B
parallel: true
status: todo
---

# Epic: QML Engine

## Tasks
| ID | Title | Parallel | Est | Depends |
|----|-------|:--------:|-----|---------|
| 005 | PennyLane VQC circuit + AngleEmbedding | ❌ | 25m | — |
| 006 | Training loop + Adam optimiser + accuracy eval | ❌ | 20m | 005 |
| 007 | Weight serialisation (JSON) | ✅ | 10m | 006 |
| 008 | CascadeAnalyzer: graph + BFS propagation | ✅ | 20m | 005 |
| 009 | FastAPI /predict endpoint wrapper | ✅ | 10m | 007,008 |

## Spec
See `docs/phases/phase-1-qml/spec.md`
