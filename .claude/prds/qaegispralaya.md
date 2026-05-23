---
prd: qaegispralaya
version: 1.0
created: 2026-05-23
status: approved
---

# PRD: QAegisPralaya

## Problem
Indian municipal EOCs face critical inter-departmental coordination failure during
cascading crises. Departments (electricity board, civil water, NDRF, hospitals) operate
with siloed data. No system predicts cross-departmental cascades before they complete.
Field incident reports reaching EOC carry no integrity guarantee.

## Solution
Pillar 1 — Hybrid VQC (QML): 5-qubit PennyLane VQC predicts cascading failure risk
across departments using 10 real-time sensor features.
Pillar 2 — PQC (Dilithium3): EOC generates keypairs at mission briefing; all field
reports signed and verified before reaching commander.

## Primary User
EOC commander — single dashboard, unified view.

## Success Criteria
1. VQC > 65% accuracy on held-out synthetic test data
2. PQC sign+verify < 500ms per report
3. All 3 demo scenarios run unattended end-to-end
4. Dashboard auto-updates without manual refresh

## Constraints
- 4-hour build time
- No real quantum hardware
- No real SCADA/NDRF data (synthetic)
- Free-tier APIs only

## Out of Scope
- Real IoT sensor integration
- Multi-tenant auth / RBAC
- Native mobile app for responders
- Production deployment
