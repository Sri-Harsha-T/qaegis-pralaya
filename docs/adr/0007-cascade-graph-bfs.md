# ADR-0007: NetworkX BFS Cascade Propagation

**Status:** Accepted

## Decision
NetworkX DiGraph encodes domain dependencies with edge weights (propagation
probability) and lag_minutes. VQC scores per-domain base risk. BFS propagation
combines both into final cascade chain and timeline.

## Graph edges (locked)
climate → power_grid (0.75, 30m)
climate → water (0.50, 60m)
climate → transport (0.60, 15m)
power_grid → medical (0.90, 5m)
power_grid → water (0.80, 20m)
power_grid → telecom (0.70, 10m)
water → medical (0.65, 120m)
telecom → medical (0.40, 45m)
transport → medical (0.55, 30m)

Do not change edge weights without a new ADR — they are calibrated against
synthetic scenario labels.
