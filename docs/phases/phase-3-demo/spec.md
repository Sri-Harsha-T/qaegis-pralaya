# Phase 3-B — Demo Scenarios + Docs Spec
**Wall time:** 30 min | **Agent:** E (parallel with D) | **Status:** TODO

## Files to create
- `demo/scenario_flood_grid.json`
- `demo/scenario_heat_hospital.json`
- `demo/scenario_cyclone_comms.json`
- `demo/fallback_playback.py`
- `scripts/run_demo.sh`
- `README.md`

## Acceptance criteria
- [ ] Each scenario JSON: 30-event timeline array, each event has:
      {t_seconds, event_type, domain, severity, cascade_risk, description}
- [ ] `bash scripts/run_demo.sh flood_grid` triggers scenario and tails alerts 60s
- [ ] `python demo/fallback_playback.py` serves scenario on localhost:8001
      (static demo mode — works without backend)
- [ ] README.md contains: overview, architecture diagram (ASCII), setup (3 steps),
      demo walkthrough, data sources table, SDG alignment, honest quantum framing

## Scenario timelines (locked)
flood_grid:     0m rain, 30m grid, 35m hospital, 45m ambulances, 60m all-clear
heat_hospital:  0m heat, 20m water, 45m hospital surge, 60m mutual aid, 80m resolved
cyclone_comms:  0m landfall, 15m telecom, 30m coord breakdown, 45m PQC relay, 60m restored
