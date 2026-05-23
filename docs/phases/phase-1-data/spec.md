# Phase 1-A — Data Pipeline Spec
**Wall time:** 60 min | **Agent:** A (parallel with B and C) | **Status:** TODO

## Files to create
- `data/generate_scenario.py`
- `backend/data_pipeline.py`

## Acceptance criteria
- [ ] `python data/generate_scenario.py --all` creates:
      `data/synthetic/flood_grid.json` (200 samples)
      `data/synthetic/heat_hospital.json` (200 samples)
      `data/synthetic/cyclone_comms.json` (200 samples)
- [ ] Each sample has exactly these keys:
      temperature_c, wind_kmh, precipitation_mm, grid_load_pct,
      grid_outage_nodes, water_pressure_bar, water_treatment_pct,
      hospital_bed_pct, ambulance_available, telecom_uptime_pct,
      cascade_type, cascade_risk (float 0-1), propagation_chain (list)
- [ ] `backend/data_pipeline.py` has `get_live_features(city="Bengaluru")` that:
      - Returns normalised feature dict from OpenWeatherMap API
      - Falls back to synthetic sample if API unavailable
      - Completes in < 3 seconds

## Implementation notes
- Use Graph-based Monte Carlo (see ADR-0003) for cascade_risk labels
- Gaussian copula via `scipy.stats.norm` + Cholesky decomposition for correlation
- Load correlation matrix from docs/phases/phase-1-data/feature_correlations.json
