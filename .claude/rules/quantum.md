# Quantum Rules (enforced)

## QML
- VQC device: ONLY `pennylane.device("default.qubit", wires=5)` — see ADR-0001
- Never call real hardware APIs (IBM Quantum, AWS Braket) — latency incompatible
- PCA BEFORE embedding: 10 features → 5 angles via sklearn PCA
- Angle clipping: `np.clip(angles, 0, np.pi)` before AngleEmbedding
- Weight file: always `backend/models/vqc_weights.json` — never other paths
- Do NOT claim quantum speedup — say "quantum-ready architecture"

## PQC
- Algorithm: ONLY `"Dilithium3"` — see ADR-0002. Never Kyber (wrong primitive)
- Always run `verify_pqc.py` before implementing PQC features
- HMAC-SHA256 fallback REQUIRED if liboqs unavailable — never silent fail
- Private keys: never log, never serialise to disk, never include in responses

## Cascade Graph
- Edge weights are LOCKED (see ADR-0007) — do not change without new ADR
- BFS propagation only — do not switch to Dijkstra or other algorithm
- `propagated[node] = min(1.0, ...)` — risk is always capped at 1.0
