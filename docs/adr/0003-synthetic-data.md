# ADR-0003: Synthetic Data via Graph Simulation + Copula Sampling

**Status:** Accepted
**Date:** 2026-05-23

## Context
Real SCADA/NDRF operational data is not publicly available in 4 hours.
OpenWeatherMap provides real climate features but no cascade labels.

## Decision
Generate 600+ labelled cascade scenarios using three methods:
1. Monte Carlo graph traversal on dependency graph (cascade labels)
2. Gaussian copula sampling (preserves inter-feature correlation)
3. Template + Gaussian noise (200 samples per scenario type)

Disclose to judges: infrastructure data is synthetic; climate is real API.

## Consequences
- VQC will overfit to synthetic distribution — expected and disclosed
- Labels are physically plausible (graph-derived probabilities)
- Production system would use NDRF/state SCADA databases

## Rejected alternatives
- Kaggle flood datasets: not structured as multi-domain cascade features
- Purely random noise: no physical plausibility, judge credibility risk
