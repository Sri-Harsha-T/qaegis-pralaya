---
epic: demo
phase: 3-B
agent: E
parallel: true
status: todo
depends: [backend]
---

# Epic: Demo Scenarios + Docs

## Tasks
| ID | Title | Parallel | Est | Depends |
|----|-------|:--------:|-----|---------|
| 026 | Scenario JSONs (3 files × 30 events) | ✅ | 15m | — |
| 027 | run_demo.sh + fallback_playback.py | ✅ | 10m | 026 |
| 028 | README.md (full docs) | ✅ | 15m | — |

## Spec
See `docs/phases/phase-3-demo/spec.md`
