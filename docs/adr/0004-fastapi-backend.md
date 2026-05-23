# ADR-0004: FastAPI + WebSocket Backend

**Status:** Accepted
**Date:** 2026-05-23

## Decision
FastAPI + Uvicorn with WebSocket support for live dashboard streaming.

## Consequences
- OpenAPI docs auto-generated at /docs — useful for demo
- WebSocket: asyncio background task replays scenario JSON every 3-5s
- CORS: allow all origins for hackathon (tighten in production)
