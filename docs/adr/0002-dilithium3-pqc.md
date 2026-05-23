# ADR-0002: Dilithium3 (ML-DSA) as PQC Algorithm

**Status:** Accepted
**Date:** 2026-05-23

## Context
NIST finalized ML-DSA (Dilithium) as FIPS 204 in August 2024.
We need digital signatures (not key encapsulation) for incident report authentication.

## Decision
Use `liboqs-python` with algorithm `"Dilithium3"` for all signing/verification.
EOC generates keypairs; private key to responder device; public key in EOC registry.

## Consequences
- NIST-standard: auditable, no custom crypto
- liboqs requires C compiler — run `scripts/verify_pqc.py` before anything else
- HMAC-SHA256 fallback implemented for platform compatibility
- Sign+verify < 500ms per report (measured on x86 Linux)

## Rejected alternatives
- Kyber (ML-KEM): key encapsulation, not signatures — wrong primitive
- Custom lattice scheme: not auditable, judge credibility risk
- RSA/ECDSA: vulnerable to Shor's Algorithm — defeats the quantum narrative
