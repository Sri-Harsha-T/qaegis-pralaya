---
epic: data-pipeline
phase: 1-A
agent: A
parallel: true
status: todo
---

# Epic: Data Pipeline

## Tasks
| ID | Title | Parallel | Est | Depends |
|----|-------|:--------:|-----|---------|
| 001 | Synthetic cascade scenario generator | ✅ | 20m | — |
| 002 | OpenWeatherMap API client + normaliser | ✅ | 15m | — |
| 003 | USGS seismic GeoJSON client | ✅ | 10m | — |
| 004 | Cascade label generator (graph simulation) | ❌ | 15m | 001 |

## Spec
See `docs/phases/phase-1-data/spec.md`
