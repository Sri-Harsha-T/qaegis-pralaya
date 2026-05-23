# Phase 3-A — React Dashboard Spec
**Wall time:** 60 min | **Agent:** D (parallel with E) | **Status:** TODO

## Location
`frontend/` (Vite + React project)

## Acceptance criteria
- [ ] `cd frontend && npm run dev` starts without errors on localhost:5173
- [ ] Dashboard loads with dark theme (#060B18 background)
- [ ] IncidentMap panel: Leaflet.js map centered on Bengaluru (12.97, 77.59)
      with 5 responder markers and incident event popups
- [ ] CascadePanel: risk gauge (RadialBarChart), cascade type badge, domain
      propagation flow (5 nodes: Climate→Grid→Water→Medical→Telecom)
- [ ] PQCStatusPanel: last 10 signed reports with ✓/✗ badge, sign form
- [ ] AlertTimeline: auto-scrolling sidebar with color-coded severity events
- [ ] ScenarioControls: 3 buttons trigger POST /scenario/{name}
- [ ] WebSocket hook connects to /ws/incidents and /ws/alerts; auto-reconnects
- [ ] All panels update without page refresh during active scenario

## Component map
App.jsx → 3-column layout
IncidentMap.jsx → Leaflet.js
CascadePanel.jsx → Recharts RadialBarChart + domain flow
PQCStatusPanel.jsx → report list + sign form
AlertTimeline.jsx → auto-scroll list
ScenarioControls.jsx → 3 trigger buttons
hooks/useBackendWS.js → WebSocket + reconnect logic
