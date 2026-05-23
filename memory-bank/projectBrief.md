# Project Brief

## Problem
Indian municipal EOCs face inter-departmental coordination failure during
cascading crises (flooding → power → water → hospital). Departments (NDRF,
electricity board, civil water, hospitals) operate with siloed data and no
shared situational awareness. Field incident reports carry no integrity guarantee.

## Solution
QAegisPralaya: two quantum primitives in one platform.
1. Hybrid VQC (PennyLane) — models cross-departmental cascade risk in real time
2. Dilithium3 PQC (liboqs) — EOC-issued keypairs; every report signed + verified

## Primary User
EOC commander — single dashboard view, unified cascade alerts, authenticated reports.
Field responders submit reports; they do not use the dashboard.

## Quantum Framing (for judges)
"Quantum-ready architecture" — VQC on simulator today, IBM Quantum / AWS Braket
tomorrow. We show genuine scope of application, not exaggerated speedup claims.

## Hackathon Constraints
- Build time: 4 hours
- No real quantum hardware
- No real SCADA/NDRF data (synthetic generation required)
- All dependencies: free-tier APIs and pip-installable packages
