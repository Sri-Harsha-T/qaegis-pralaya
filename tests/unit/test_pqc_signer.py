#!/usr/bin/env python3
"""
Unit tests for PQC Signer functionality.
Tests both Dilithium3 and HMAC-SHA256 paths.
"""
import json
import tempfile
import time
from pathlib import Path
import pytest

from backend.pqc_signer import (
    IncidentReport,
    SignedReport,
    PQCSigner,
    ResponderKeyRegistry,
    ResponderInfo
)


class TestIncidentReport:
    """Test IncidentReport dataclass and methods."""

    def test_create_valid_report(self):
        """Test creating valid incident report."""
        location = {"lat": 12.9716, "lon": 77.5946, "district": "Bengaluru"}
        report = IncidentReport.create(
            reporter_id="test_responder",
            location=location,
            incident_type="flood",
            severity=3,
            payload={"description": "Heavy flooding on MG Road"}
        )

        assert report.reporter_id == "test_responder"
        assert report.location == location
        assert report.incident_type == "flood"
        assert report.severity == 3
        assert "description" in report.payload
        assert report.report_id  # Should be auto-generated
        assert report.timestamp  # Should be auto-generated

    def test_severity_validation(self):
        """Test severity range validation."""
        location = {"lat": 12.9716, "lon": 77.5946, "district": "Bengaluru"}

        # Valid severities
        for severity in [1, 2, 3, 4, 5]:
            report = IncidentReport.create(
                reporter_id="test",
                location=location,
                incident_type="test",
                severity=severity
            )
            assert report.severity == severity

        # Invalid severities
        for severity in [0, 6, -1, 10]:
            with pytest.raises(ValueError, match="Severity must be 1-5"):
                IncidentReport.create(
                    reporter_id="test",
                    location=location,
                    incident_type="test",
                    severity=severity
                )

    def test_location_validation(self):
        """Test location coordinate validation."""
        # Valid coordinates
        valid_locations = [
            {"lat": 0, "lon": 0, "district": "Equator"},
            {"lat": 90, "lon": 180, "district": "North Pole"},
            {"lat": -90, "lon": -180, "district": "South Pole"},
            {"lat": 12.9716, "lon": 77.5946, "district": "Bengaluru"}
        ]

        for location in valid_locations:
            report = IncidentReport.create(
                reporter_id="test",
                location=location,
                incident_type="test",
                severity=1
            )
            assert report.location == location

        # Invalid coordinates
        invalid_locations = [
            {"lat": 91, "lon": 0},  # Lat too high
            {"lat": -91, "lon": 0},  # Lat too low
            {"lat": 0, "lon": 181},  # Lon too high
            {"lat": 0, "lon": -181},  # Lon too low
            {"district": "Missing coords"},  # Missing lat/lon
            {"lat": 12.97, "missing": "lon"}  # Missing lon
        ]

        for location in invalid_locations:
            with pytest.raises(ValueError):
                IncidentReport.create(
                    reporter_id="test",
                    location=location,
                    incident_type="test",
                    severity=1
                )

    def test_json_serialization(self):
        """Test JSON serialization and deserialization."""
        original = IncidentReport.create(
            reporter_id="test_responder",
            location={"lat": 12.9716, "lon": 77.5946, "district": "Bengaluru"},
            incident_type="fire",
            severity=4,
            payload={"building": "Tech Park", "floors": 5}
        )

        # Serialize to JSON
        json_str = original.to_json()
        assert isinstance(json_str, str)
        assert "report_id" in json_str

        # Deserialize from JSON
        restored = IncidentReport.from_json(json_str)
        assert restored.report_id == original.report_id
        assert restored.reporter_id == original.reporter_id
        assert restored.location == original.location
        assert restored.severity == original.severity
        assert restored.payload == original.payload


class TestPQCSigner:
    """Test PQCSigner functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.signer = PQCSigner()
        self.test_report = IncidentReport.create(
            reporter_id="test_responder",
            location={"lat": 12.9716, "lon": 77.5946, "district": "Bengaluru"},
            incident_type="earthquake",
            severity=5,
            payload={"magnitude": 7.2, "depth": 15}
        )

    def test_keypair_generation(self):
        """Test key pair generation."""
        self.setUp()
        public_key_hex, private_key_hex = self.signer.generate_keypair()

        # Keys should be hex strings
        assert isinstance(public_key_hex, str)
        assert isinstance(private_key_hex, str)

        # Hex validation
        bytes.fromhex(public_key_hex)  # Should not raise
        bytes.fromhex(private_key_hex)  # Should not raise

        # Keys should not be empty
        assert len(public_key_hex) > 0
        assert len(private_key_hex) > 0

    def test_sign_and_verify_cycle(self):
        """Test complete sign and verify cycle."""
        self.setUp()
        public_key_hex, private_key_hex = self.signer.generate_keypair()

        # Sign the report
        signed_report = self.signer.sign_report(self.test_report, private_key_hex)

        # Verify signature structure
        assert isinstance(signed_report, SignedReport)
        assert signed_report.report_id == self.test_report.report_id
        assert signed_report.signature_hex
        assert signed_report.algorithm in ["Dilithium3", "HMAC-SHA256"]
        assert signed_report.signer_id == "system"  # Default value

        # Verify the signature
        is_valid = self.signer.verify_report(signed_report, public_key_hex)
        assert is_valid is True

    def test_tamper_detection(self):
        """Test that tampered reports are rejected."""
        self.setUp()
        public_key_hex, private_key_hex = self.signer.generate_keypair()

        # Sign original report
        signed_report = self.signer.sign_report(self.test_report, private_key_hex)

        # Verify original is valid
        assert self.signer.verify_report(signed_report, public_key_hex) is True

        # Tamper with the report content
        tampered_report = SignedReport.from_json(signed_report.to_json())
        tampered_report.severity = 1  # Change severity

        # Tampered report should fail verification
        is_valid = self.signer.verify_report(tampered_report, public_key_hex)
        assert is_valid is False

    def test_performance_requirements(self):
        """Test that sign+verify meets <500ms requirement."""
        self.setUp()
        public_key_hex, private_key_hex = self.signer.generate_keypair()

        # Measure sign + verify round trip
        start_time = time.perf_counter()

        signed_report = self.signer.sign_report(self.test_report, private_key_hex)
        is_valid = self.signer.verify_report(signed_report, public_key_hex)

        total_time = (time.perf_counter() - start_time) * 1000  # ms

        assert is_valid is True
        assert total_time < 500.0, f"Performance requirement failed: {total_time:.2f}ms > 500ms"

    def test_invalid_key_handling(self):
        """Test error handling for invalid keys."""
        self.setUp()
        public_key_hex, private_key_hex = self.signer.generate_keypair()

        # Test with invalid private key for signing
        with pytest.raises(Exception):
            self.signer.sign_report(self.test_report, "invalid_hex_key")

        # Sign a valid report
        signed_report = self.signer.sign_report(self.test_report, private_key_hex)

        # Test with invalid public key for verification
        is_valid = self.signer.verify_report(signed_report, "invalid_hex_key")
        assert is_valid is False  # Should fail gracefully, not crash


class TestResponderKeyRegistry:
    """Test ResponderKeyRegistry functionality."""

    def setUp(self):
        """Set up test fixtures with temporary registry."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.registry = ResponderKeyRegistry(filepath=Path(self.temp_file.name))

    def tearDown(self):
        """Clean up temporary files."""
        Path(self.temp_file.name).unlink(missing_ok=True)

    def test_synthetic_responder_creation(self):
        """Test that 5 synthetic responders are created."""
        self.setUp()

        responders = self.registry.list_active_responders()
        assert len(responders) == 5

        # Check responder structure
        for responder in responders:
            assert "responder_id" in responder
            assert "name" in responder
            assert "department" in responder
            assert "public_key_hex" in responder
            assert responder["public_key_hex"]  # Should not be empty

        # Check specific departments are represented
        departments = {r["department"] for r in responders}
        assert "Fire Department" in departments
        assert "Police Department" in departments
        assert "Medical Services" in departments

        self.tearDown()

    def test_responder_lookup(self):
        """Test responder key lookup functionality."""
        self.setUp()

        responders = self.registry.list_active_responders()
        test_responder = responders[0]

        # Test public key lookup
        public_key = self.registry.get_public_key(test_responder["responder_id"])
        assert public_key == test_responder["public_key_hex"]

        # Test private key lookup (demo only)
        private_key = self.registry.get_private_key(test_responder["responder_id"])
        assert private_key is not None
        assert isinstance(private_key, str)

        # Test lookup for non-existent responder
        assert self.registry.get_public_key("non_existent") is None
        assert self.registry.get_private_key("non_existent") is None

        self.tearDown()

    def test_responder_deactivation(self):
        """Test responder deactivation functionality."""
        self.setUp()

        responders = self.registry.list_active_responders()
        initial_count = len(responders)
        test_responder_id = responders[0]["responder_id"]

        # Deactivate a responder
        result = self.registry.deactivate_responder(test_responder_id)
        assert result is True

        # Check that active count decreased
        active_responders = self.registry.list_active_responders()
        assert len(active_responders) == initial_count - 1

        # Deactivated responder should not be in active list
        active_ids = {r["responder_id"] for r in active_responders}
        assert test_responder_id not in active_ids

        # Should not be able to get keys for inactive responder
        assert self.registry.get_public_key(test_responder_id) is None

        # Test deactivating non-existent responder
        result = self.registry.deactivate_responder("non_existent")
        assert result is False

        self.tearDown()

    def test_registry_persistence(self):
        """Test saving and loading registry to/from file."""
        self.setUp()

        # Get original responders
        original_responders = self.registry.list_active_responders()
        original_count = len(original_responders)

        # Save to file
        self.registry.save_to_file()

        # Create new registry from same file
        new_registry = ResponderKeyRegistry(filepath=Path(self.temp_file.name))
        loaded_responders = new_registry.list_active_responders()

        # Should have same responders
        assert len(loaded_responders) == original_count

        # Check that specific responder data matches
        original_ids = {r["responder_id"] for r in original_responders}
        loaded_ids = {r["responder_id"] for r in loaded_responders}
        assert original_ids == loaded_ids

        self.tearDown()

    def test_add_responder(self):
        """Test adding new responders to registry."""
        self.setUp()

        initial_count = len(self.registry.list_active_responders())

        # Add new responder
        signer = PQCSigner()
        public_key_hex, private_key_hex = signer.generate_keypair()

        self.registry.add_responder(
            responder_id="test_new_responder",
            public_key_hex=public_key_hex,
            private_key_hex=private_key_hex,
            name="Test Responder",
            department="Test Department"
        )

        # Check that responder was added
        responders = self.registry.list_active_responders()
        assert len(responders) == initial_count + 1

        # Check new responder details
        new_responder = None
        for r in responders:
            if r["responder_id"] == "test_new_responder":
                new_responder = r
                break

        assert new_responder is not None
        assert new_responder["name"] == "Test Responder"
        assert new_responder["department"] == "Test Department"
        assert new_responder["public_key_hex"] == public_key_hex

        # Should be able to lookup keys
        assert self.registry.get_public_key("test_new_responder") == public_key_hex
        assert self.registry.get_private_key("test_new_responder") == private_key_hex

        self.tearDown()


if __name__ == "__main__":
    # Run performance test directly
    import logging
    logging.basicConfig(level=logging.INFO)

    signer = PQCSigner()
    public_key_hex, private_key_hex = signer.generate_keypair()

    test_report = IncidentReport.create(
        reporter_id="test_responder",
        location={"lat": 12.9716, "lon": 77.5946, "district": "Bengaluru"},
        incident_type="test",
        severity=3
    )

    start_time = time.perf_counter()
    signed = signer.sign_report(test_report, private_key_hex)
    valid = signer.verify_report(signed, public_key_hex)
    total_time = (time.perf_counter() - start_time) * 1000

    print(f"Algorithm: {signed.algorithm}")
    print(f"Valid: {valid}")
    print(f"Time: {total_time:.2f}ms")
    print(f"Target met: {'✅' if total_time < 500 else '❌'}")