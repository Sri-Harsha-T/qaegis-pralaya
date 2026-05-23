# Phase 1-C — PQC Layer Spec
**Wall time:** 40 min | **Agent:** C (parallel with A and B) | **Status:** TODO

## Files to create
- `backend/pqc_signer.py`

## Acceptance criteria
- [ ] `python scripts/verify_pqc.py` exits 0 (run this FIRST)
- [ ] `PQCSigner.generate_keypair()` returns (public_key_hex, private_key_hex)
- [ ] `PQCSigner.sign_report(report, private_key_hex)` returns SignedReport
- [ ] `PQCSigner.verify_report(signed_report, public_key_hex)` returns True
- [ ] Tampered report returns False (test this explicitly)
- [ ] Sign + verify round-trip < 500ms
- [ ] `ResponderKeyRegistry` pre-populated with 5 synthetic responders
- [ ] HMAC-SHA256 fallback if liboqs unavailable (WARNING logged, not silent)

## Algorithm (locked by ADR-0002)
`oqs.Signature("Dilithium3")` — do not change to Kyber or other algorithm.

## IncidentReport schema
report_id (UUID), reporter_id (str), timestamp (ISO 8601), location
(dict: lat, lon, district), incident_type (str), severity (int 1-5),
payload (dict, free-form)

## SignedReport schema
All IncidentReport fields + signature_hex (str), algorithm (str), signer_id (str)
