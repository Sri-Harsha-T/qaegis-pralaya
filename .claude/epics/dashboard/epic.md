---
epic: dashboard
phase: 3-A
agent: D
parallel: true
status: todo
depends: [backend]
---

# Epic: React Dashboard

## Tasks
| ID | Title | Parallel | Est | Depends |
|----|-------|:--------:|-----|---------|
| 020 | Vite scaffold + Tailwind + dark theme | ❌ | 10m | — |
| 021 | IncidentMap (Leaflet) | ✅ | 20m | 020 |
| 022 | CascadePanel (risk gauge + domain flow) | ✅ | 20m | 020 |
| 023 | PQCStatusPanel (report feed + sign form) | ✅ | 20m | 020 |
| 024 | AlertTimeline sidebar | ✅ | 15m | 020 |
| 025 | WebSocket hook + ScenarioControls | ❌ | 15m | 021-024 |

## Spec
See `docs/phases/phase-3-dashboard/spec.md`
