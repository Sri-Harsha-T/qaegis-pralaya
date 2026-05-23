# ADR-0005: React + Vite + Tailwind Dashboard

**Status:** Accepted

## Decision
Vite + React + Tailwind CSS + Leaflet.js (map) + Recharts (charts).
Single-page EOC command center; no Next.js (overkill for 4-hour build).

## Consequences
- Vite dev server: localhost:5173
- No SSR, no routing — pure SPA
- WebSocket hook reconnects automatically on disconnect
