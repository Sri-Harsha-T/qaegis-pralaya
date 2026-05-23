# System Patterns

## Cascade Analysis: Three-Layer Architecture
1. NetworkX dependency graph (static structure, domain knowledge)
2. PennyLane VQC (dynamic risk scores from live sensor features)
3. BFS propagator (combines graph + VQC into cascade chain)

## Data Flow
OpenWeatherMap/USGS → data_pipeline.py → feature_dict (10 keys)
→ CascadeRiskScorer.predict_domain_risks() → domain_risks dict
→ CascadeAnalyzer._propagate() → propagated risks
→ CascadeAnalyzer._extract_chain() → ordered chain list
→ FastAPI /predict response → WebSocket broadcast → React dashboard

## PQC Flow
Responder registers → EOC generates Dilithium3 keypair
→ private key returned to responder device
→ public key stored in ResponderKeyRegistry (in-memory dict)
→ responder signs IncidentReport → SignedReport JSON
→ EOC verifies: public key lookup → oqs.Signature.verify()
→ verified: True/False → dashboard PQC status panel

## API Contract
POST /predict  → {cascade_type, overall_risk, domain_risks, chain, timeline, confidence}
POST /sign     → SignedReport (IncidentReport + signature_hex + algorithm + signer_id)
POST /verify   → {verified: bool, report_id, signer_id, algorithm}
POST /scenario/{name} → {started: bool, scenario: str, duration_s: int}
GET  /responders → [{id, name, role, location, last_ping_verified}]
WS   /ws/incidents → stream of SignedReport events
WS   /ws/alerts    → stream of cascade prediction updates

## Token-Efficient Reading Pattern
Session start: read CLAUDE.md + memory-bank/activeContext.md only.
Before editing file X: read X only (not the whole module).
Before creating file X: read the phase spec only.
ADR lookup: read docs/adr/README.md index, then specific ADR file if needed.
