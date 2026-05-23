# ADR-0006: EOC as Certificate Authority

**Status:** Accepted

## Decision
EOC generates Dilithium3 keypairs for each responder at mission briefing.
Private key sent to responder device. Public key stored in ResponderKeyRegistry
(in-memory dict, keyed by responder_id).

## Consequences
- Simple, implementable in 4 hours
- No external PKI infrastructure required
- Production extension: hierarchical PKI with ML-DSA certificates
- Demo: 5 synthetic responders pre-populated at startup
