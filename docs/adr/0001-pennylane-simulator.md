# ADR-0001: PennyLane default.qubit Simulator

**Status:** Accepted
**Date:** 2026-05-23

## Context
Hackathon build time is 4 hours. No real quantum hardware access.
IBM Quantum / AWS Braket require API keys and have queue latency.

## Decision
Use `pennylane.device("default.qubit", wires=5)` for all VQC inference.
Pre-train weights and cache to `backend/models/vqc_weights.json`.

## Consequences
- Inference latency: 2–10s per call on CPU (acceptable; use caching)
- No quantum speedup claim is possible or needed
- Architecture is plug-in compatible with real hardware in future
- Judges told: "quantum-ready pipeline, simulator today"

## Rejected alternatives
- qiskit-aer: heavier install, no advantage over PennyLane for this use case
- Real IBM Quantum: queue latency incompatible with live demo
