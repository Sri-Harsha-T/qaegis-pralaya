# Phase 1-B — QML Engine Spec
**Wall time:** 60 min | **Agent:** B (parallel with A and C) | **Status:** TODO

## Files to create
- `backend/qml_engine.py`
- `backend/cascade_graph.py`
- `scripts/train_vqc.py`

## Acceptance criteria
- [ ] `python scripts/train_vqc.py` trains VQC on synthetic data and saves
      `backend/models/vqc_weights.json`
- [ ] Accuracy on held-out 20% test split: > 65%
- [ ] `CascadeRiskScorer.predict_domain_risks(feature_dict)` returns dict
      with keys: climate, power_grid, water, medical, telecom (all float 0-1)
- [ ] `CascadeAnalyzer.analyze(feature_dict)` returns:
      {cascade_type, overall_risk, domain_risks, propagation_chain,
       timeline_minutes, confidence}
- [ ] Single inference call completes in < 15 seconds on CPU

## VQC architecture (locked by ADR-0001)
- Device: `pennylane.device("default.qubit", wires=5)`
- Encoding: `qml.AngleEmbedding(features, wires=range(5), rotation="X")`
- Ansatz: `qml.StronglyEntanglingLayers(weights, wires=range(5))`, n_layers=2
- Measurement: `[qml.expval(qml.PauliZ(i)) for i in range(5)]`
- Map [-1,1] → [0,1]: `risk = (measurement + 1) / 2`

## Cascade graph (locked by ADR-0007)
See `docs/adr/0007-cascade-graph-bfs.md` for exact edge weights.
Do NOT change without new ADR.
