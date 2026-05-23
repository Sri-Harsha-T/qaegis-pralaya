#!/usr/bin/env python3
"""
PQC Signer - Post-Quantum Cryptographic signing for incident reports.
Uses Dilithium3 when available, falls back to HMAC-SHA256 with WARNING.
"""
import json
import logging
import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from uuid import uuid4

# Setup logging
logger = logging.getLogger(__name__)

# Force HMAC-SHA256 fallback mode (skip liboqs entirely for demo)
HAS_LIBOQS = False
logger.warning("⚠️  liboqs-python disabled for demo. Using HMAC-SHA256 fallback.")

# Original liboqs detection code (disabled for demo):
# try:
#     import oqs
#     if "Dilithium3" in oqs.get_enabled_sig_mechanisms():
#         HAS_LIBOQS = True
#         logger.info("✅ Dilithium3 available via liboqs-python")
#     else:
#         logger.warning("⚠️  Dilithium3 not available in liboqs mechanisms")
# except ImportError:
#     logger.warning("⚠️  liboqs-python not available. Using HMAC-SHA256 fallback.")


@dataclass
class IncidentReport:
    """Core incident report structure for PQC signing."""
    report_id: str
    reporter_id: str
    timestamp: str  # ISO 8601
    location: Dict[str, Any]  # {lat: float, lon: float, district: str}
    incident_type: str
    severity: int  # 1-5
    payload: Dict[str, Any]  # Free-form additional data

    @classmethod
    def create(cls, reporter_id: str, location: Dict[str, Any],
               incident_type: str, severity: int, payload: Optional[Dict[str, Any]] = None) -> "IncidentReport":
        """Create new incident report with auto-generated ID and timestamp."""
        if not (1 <= severity <= 5):
            raise ValueError(f"Severity must be 1-5, got {severity}")

        # Validate location
        if not isinstance(location, dict) or "lat" not in location or "lon" not in location:
            raise ValueError("Location must contain 'lat' and 'lon' fields")

        lat, lon = location["lat"], location["lon"]
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise ValueError(f"Invalid coordinates: lat={lat}, lon={lon}")

        return cls(
            report_id=str(uuid4()),
            reporter_id=reporter_id,
            timestamp=datetime.utcnow().isoformat() + "Z",
            location=location,
            incident_type=incident_type,
            severity=severity,
            payload=payload or {}
        )

    def to_json(self) -> str:
        """Serialize to JSON string for signing."""
        return json.dumps(asdict(self), sort_keys=True)

    @classmethod
    def from_json(cls, json_str: str) -> "IncidentReport":
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls(**data)


@dataclass
class SignedReport:
    """Incident report with cryptographic signature."""
    # All IncidentReport fields
    report_id: str
    reporter_id: str
    timestamp: str
    location: Dict[str, Any]
    incident_type: str
    severity: int
    payload: Dict[str, Any]

    # Signature fields
    signature_hex: str
    algorithm: str  # "Dilithium3" or "HMAC-SHA256"
    signer_id: str

    @classmethod
    def from_incident_report(cls, report: IncidentReport, signature_hex: str,
                           algorithm: str, signer_id: str) -> "SignedReport":
        """Create SignedReport from IncidentReport + signature data."""
        return cls(
            report_id=report.report_id,
            reporter_id=report.reporter_id,
            timestamp=report.timestamp,
            location=report.location,
            incident_type=report.incident_type,
            severity=report.severity,
            payload=report.payload,
            signature_hex=signature_hex,
            algorithm=algorithm,
            signer_id=signer_id
        )

    def get_incident_report(self) -> IncidentReport:
        """Extract the IncidentReport portion (for verification)."""
        return IncidentReport(
            report_id=self.report_id,
            reporter_id=self.reporter_id,
            timestamp=self.timestamp,
            location=self.location,
            incident_type=self.incident_type,
            severity=self.severity,
            payload=self.payload
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(asdict(self), sort_keys=True)

    @classmethod
    def from_json(cls, json_str: str) -> "SignedReport":
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls(**data)


class PQCSigner:
    """Post-quantum cryptographic signer with HMAC fallback."""

    def __init__(self):
        """Initialize PQC signer with appropriate algorithm."""
        self.use_dilithium = HAS_LIBOQS
        if self.use_dilithium:
            logger.info("PQCSigner initialized with Dilithium3")
        else:
            logger.warning("PQCSigner using HMAC-SHA256 fallback (liboqs unavailable)")

    def generate_keypair(self) -> Tuple[str, str]:
        """Generate a new keypair.

        Returns:
            Tuple of (public_key_hex, private_key_hex)
        """
        if self.use_dilithium:
            return self._generate_dilithium_keypair()
        else:
            return self._generate_hmac_keypair()

    def _generate_dilithium_keypair(self) -> Tuple[str, str]:
        """Generate Dilithium3 keypair."""
        try:
            import oqs
            signer = oqs.Signature("Dilithium3")
            public_key = signer.generate_keypair()
            private_key = signer.export_secret_key()
            return public_key.hex(), private_key.hex()
        except ImportError:
            raise RuntimeError("liboqs not available - this method should not be called in fallback mode")

    def _generate_hmac_keypair(self) -> Tuple[str, str]:
        """Generate HMAC-SHA256 keypair (symmetric key used for both)."""
        key = secrets.token_bytes(32)  # 256-bit key
        key_hex = key.hex()
        # For HMAC, public and private key are the same (symmetric)
        return key_hex, key_hex

    def sign_report(self, report: IncidentReport, private_key_hex: str) -> SignedReport:
        """Sign an incident report.

        Args:
            report: The incident report to sign
            private_key_hex: Hex-encoded private key

        Returns:
            SignedReport with signature attached
        """
        message = report.to_json().encode('utf-8')

        if self.use_dilithium:
            signature_hex, algorithm = self._sign_dilithium(message, private_key_hex)
        else:
            signature_hex, algorithm = self._sign_hmac(message, private_key_hex)

        return SignedReport.from_incident_report(
            report=report,
            signature_hex=signature_hex,
            algorithm=algorithm,
            signer_id="system"  # TODO: Pass signer_id as parameter
        )

    def _sign_dilithium(self, message: bytes, private_key_hex: str) -> Tuple[str, str]:
        """Sign with Dilithium3."""
        try:
            import oqs
            signer = oqs.Signature("Dilithium3")
            private_key = bytes.fromhex(private_key_hex)

            # Import the private key
            signer.set_secret_key(private_key)

            signature = signer.sign(message)
            return signature.hex(), "Dilithium3"
        except ImportError:
            raise RuntimeError("liboqs not available - this method should not be called in fallback mode")

    def _sign_hmac(self, message: bytes, private_key_hex: str) -> Tuple[str, str]:
        """Sign with HMAC-SHA256."""
        key = bytes.fromhex(private_key_hex)
        signature = hmac.new(key, message, hashlib.sha256).digest()
        return signature.hex(), "HMAC-SHA256"

    def verify_report(self, signed_report: SignedReport, public_key_hex: str) -> bool:
        """Verify a signed incident report.

        Args:
            signed_report: The signed report to verify
            public_key_hex: Hex-encoded public key

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Extract the original report for verification
            original_report = signed_report.get_incident_report()
            message = original_report.to_json().encode('utf-8')
            signature = bytes.fromhex(signed_report.signature_hex)

            if signed_report.algorithm == "Dilithium3":
                return self._verify_dilithium(message, signature, public_key_hex)
            elif signed_report.algorithm == "HMAC-SHA256":
                return self._verify_hmac(message, signature, public_key_hex)
            else:
                logger.error(f"Unknown signature algorithm: {signed_report.algorithm}")
                return False

        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False

    def _verify_dilithium(self, message: bytes, signature: bytes, public_key_hex: str) -> bool:
        """Verify Dilithium3 signature."""
        try:
            import oqs
            verifier = oqs.Signature("Dilithium3")
            public_key = bytes.fromhex(public_key_hex)
            return verifier.verify(message, signature, public_key)
        except ImportError:
            raise RuntimeError("liboqs not available - this method should not be called in fallback mode")

    def _verify_hmac(self, message: bytes, signature: bytes, public_key_hex: str) -> bool:
        """Verify HMAC-SHA256 signature."""
        key = bytes.fromhex(public_key_hex)
        expected = hmac.new(key, message, hashlib.sha256).digest()
        return hmac.compare_digest(signature, expected)


@dataclass
class ResponderInfo:
    """Information about a field responder."""
    responder_id: str
    public_key_hex: str
    private_key_hex: str  # Stored for demo purposes only
    name: str
    department: str
    active: bool = True


class ResponderKeyRegistry:
    """Registry for managing responder public keys."""

    def __init__(self, filepath: Optional[Path] = None):
        """Initialize registry with optional file persistence."""
        self.filepath = filepath or Path("backend/models/responder_keys.json")
        self.responders: Dict[str, ResponderInfo] = {}
        self.signer = PQCSigner()

        # Create models directory if it doesn't exist
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

        # Load existing registry or create synthetic responders
        if self.filepath.exists():
            self.load_from_file()
        else:
            self._create_synthetic_responders()
            self.save_to_file()

    def _create_synthetic_responders(self) -> None:
        """Create 5 synthetic responders for demo purposes."""
        synthetic_responders = [
            ("resp_fire_001", "Captain Smith", "Fire Department"),
            ("resp_fire_002", "Lieutenant Jones", "Fire Department"),
            ("resp_police_001", "Officer Brown", "Police Department"),
            ("resp_police_002", "Sergeant Davis", "Police Department"),
            ("resp_medical_001", "Paramedic Wilson", "Medical Services")
        ]

        logger.info("Creating 5 synthetic responders for demo...")

        for responder_id, name, department in synthetic_responders:
            public_key_hex, private_key_hex = self.signer.generate_keypair()

            self.responders[responder_id] = ResponderInfo(
                responder_id=responder_id,
                public_key_hex=public_key_hex,
                private_key_hex=private_key_hex,  # Demo only - never do this in production
                name=name,
                department=department,
                active=True
            )

        logger.info(f"Created {len(self.responders)} synthetic responders")

    def add_responder(self, responder_id: str, public_key_hex: str,
                     name: str, department: str, private_key_hex: str = "") -> None:
        """Add a new responder to the registry."""
        self.responders[responder_id] = ResponderInfo(
            responder_id=responder_id,
            public_key_hex=public_key_hex,
            private_key_hex=private_key_hex,
            name=name,
            department=department,
            active=True
        )

    def get_public_key(self, responder_id: str) -> Optional[str]:
        """Get public key for a responder."""
        responder = self.responders.get(responder_id)
        if responder and responder.active:
            return responder.public_key_hex
        return None

    def get_private_key(self, responder_id: str) -> Optional[str]:
        """Get private key for a responder (demo only)."""
        responder = self.responders.get(responder_id)
        if responder and responder.active:
            return responder.private_key_hex
        return None

    def list_active_responders(self) -> List[Dict[str, Any]]:
        """List all active responders (without private keys)."""
        active = []
        for responder in self.responders.values():
            if responder.active:
                active.append({
                    "responder_id": responder.responder_id,
                    "name": responder.name,
                    "department": responder.department,
                    "public_key_hex": responder.public_key_hex
                })
        return active

    def deactivate_responder(self, responder_id: str) -> bool:
        """Deactivate a responder."""
        if responder_id in self.responders:
            self.responders[responder_id].active = False
            return True
        return False

    def save_to_file(self) -> None:
        """Save registry to JSON file."""
        data = {
            "responders": {
                rid: asdict(info) for rid, info in self.responders.items()
            },
            "algorithm": "Dilithium3" if HAS_LIBOQS else "HMAC-SHA256",
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }

        with open(self.filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Registry saved to {self.filepath}")

    def load_from_file(self) -> None:
        """Load registry from JSON file."""
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)

            self.responders = {}
            for rid, info in data.get("responders", {}).items():
                self.responders[rid] = ResponderInfo(**info)

            logger.info(f"Loaded {len(self.responders)} responders from {self.filepath}")

        except Exception as e:
            logger.error(f"Failed to load registry from {self.filepath}: {e}")
            self._create_synthetic_responders()


def performance_test() -> None:
    """Test PQC signing performance."""
    logger.info("Running PQC performance test...")

    signer = PQCSigner()
    public_key_hex, private_key_hex = signer.generate_keypair()

    # Create test report
    report = IncidentReport.create(
        reporter_id="test_responder",
        location={"lat": 12.9716, "lon": 77.5946, "district": "Bengaluru"},
        incident_type="flood",
        severity=3,
        payload={"test": True}
    )

    # Measure signing performance
    start_time = time.perf_counter()
    signed_report = signer.sign_report(report, private_key_hex)
    sign_time = (time.perf_counter() - start_time) * 1000

    # Measure verification performance
    start_time = time.perf_counter()
    is_valid = signer.verify_report(signed_report, public_key_hex)
    verify_time = (time.perf_counter() - start_time) * 1000

    total_time = sign_time + verify_time

    logger.info(f"Performance test results:")
    logger.info(f"  Algorithm: {signed_report.algorithm}")
    logger.info(f"  Sign:      {sign_time:.2f}ms")
    logger.info(f"  Verify:    {verify_time:.2f}ms")
    logger.info(f"  Total:     {total_time:.2f}ms")
    logger.info(f"  Valid:     {is_valid}")
    logger.info(f"  Target:    <500ms {'✅' if total_time < 500 else '❌'}")

    # Test tamper detection
    tampered_report = SignedReport.from_json(signed_report.to_json())
    tampered_report.severity = 5  # Modify the report
    tampered_valid = signer.verify_report(tampered_report, public_key_hex)

    logger.info(f"  Tamper detection: {'✅' if not tampered_valid else '❌'}")


if __name__ == "__main__":
    # Configure logging for standalone testing
    logging.basicConfig(level=logging.INFO)

    # Run performance test
    performance_test()

    # Test registry
    registry = ResponderKeyRegistry()
    responders = registry.list_active_responders()
    logger.info(f"Registry has {len(responders)} active responders")

    for responder in responders[:2]:  # Show first 2
        logger.info(f"  {responder['name']} ({responder['department']})")