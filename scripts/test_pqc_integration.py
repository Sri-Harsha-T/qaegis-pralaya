#!/usr/bin/env python3
"""
Integration test for PQC layer - verify all components work together.
This script tests the complete PQC signing flow without needing FastAPI server.
"""
import sys
import logging
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.pqc_signer import (
    IncidentReport,
    SignedReport,
    PQCSigner,
    ResponderKeyRegistry,
    performance_test
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_complete_flow():
    """Test complete PQC signing flow."""
    logger.info("=== PQC Integration Test ===")

    # 1. Initialize components
    logger.info("1. Initializing PQC components...")
    signer = PQCSigner()
    registry = ResponderKeyRegistry()

    # 2. List available responders
    responders = registry.list_active_responders()
    logger.info(f"2. Found {len(responders)} active responders:")
    for r in responders[:3]:  # Show first 3
        logger.info(f"   - {r['name']} ({r['department']}) ID: {r['responder_id']}")

    # 3. Create incident report
    logger.info("3. Creating incident report...")
    report = IncidentReport.create(
        reporter_id="resp_fire_001",  # Captain Smith
        location={
            "lat": 12.9716,
            "lon": 77.5946,
            "district": "Bengaluru Central"
        },
        incident_type="building_fire",
        severity=4,
        payload={
            "building_type": "commercial",
            "floors": 8,
            "occupants_evacuated": 150,
            "fire_dept_units": 3
        }
    )
    logger.info(f"   Report ID: {report.report_id}")
    logger.info(f"   Incident: {report.incident_type} (severity {report.severity})")

    # 4. Sign the report
    logger.info("4. Signing incident report...")
    signer_id = "resp_fire_001"
    private_key = registry.get_private_key(signer_id)
    public_key = registry.get_public_key(signer_id)

    if not private_key or not public_key:
        logger.error(f"Failed to get keys for {signer_id}")
        return False

    start_time = time.perf_counter()
    signed_report = signer.sign_report(report, private_key)
    signed_report.signer_id = signer_id
    sign_time = (time.perf_counter() - start_time) * 1000

    logger.info(f"   Algorithm: {signed_report.algorithm}")
    logger.info(f"   Sign time: {sign_time:.2f}ms")
    logger.info(f"   Signature: {signed_report.signature_hex[:32]}...")

    # 5. Verify the signature
    logger.info("5. Verifying signature...")
    start_time = time.perf_counter()
    is_valid = signer.verify_report(signed_report, public_key)
    verify_time = (time.perf_counter() - start_time) * 1000

    total_time = sign_time + verify_time

    logger.info(f"   Valid: {'✅' if is_valid else '❌'}")
    logger.info(f"   Verify time: {verify_time:.2f}ms")
    logger.info(f"   Total time: {total_time:.2f}ms")
    logger.info(f"   Performance target (<500ms): {'✅' if total_time < 500 else '❌'}")

    # 6. Test tamper detection
    logger.info("6. Testing tamper detection...")
    tampered_report = SignedReport.from_json(signed_report.to_json())
    tampered_report.severity = 1  # Change severity
    tampered_valid = signer.verify_report(tampered_report, public_key)

    logger.info(f"   Tampered report valid: {'❌ SECURITY FAILURE' if tampered_valid else '✅ Correctly rejected'}")

    # 7. Test JSON serialization
    logger.info("7. Testing JSON serialization...")
    json_str = signed_report.to_json()
    restored = SignedReport.from_json(json_str)

    serialization_ok = (
        restored.report_id == signed_report.report_id and
        restored.signature_hex == signed_report.signature_hex and
        restored.algorithm == signed_report.algorithm
    )

    logger.info(f"   JSON round-trip: {'✅' if serialization_ok else '❌'}")
    logger.info(f"   JSON size: {len(json_str)} bytes")

    # Summary
    all_tests_passed = (
        is_valid and
        not tampered_valid and
        serialization_ok and
        total_time < 500
    )

    logger.info("=== Test Summary ===")
    logger.info(f"All tests passed: {'✅' if all_tests_passed else '❌'}")
    logger.info(f"Ready for EOC dashboard integration: {'✅' if all_tests_passed else '❌'}")

    return all_tests_passed

def test_multiple_signers():
    """Test with multiple signers to verify key isolation."""
    logger.info("\n=== Multi-Signer Test ===")

    signer = PQCSigner()
    registry = ResponderKeyRegistry()

    # Get two different responders
    responders = registry.list_active_responders()
    if len(responders) < 2:
        logger.error("Need at least 2 responders for this test")
        return False

    signer1_id = responders[0]["responder_id"]
    signer2_id = responders[1]["responder_id"]

    logger.info(f"Testing with {signer1_id} and {signer2_id}")

    # Create identical reports
    report = IncidentReport.create(
        reporter_id="test_multi",
        location={"lat": 12.9716, "lon": 77.5946, "district": "Bengaluru"},
        incident_type="test",
        severity=2,
        payload={"test": "multi_signer"}
    )

    # Sign with signer 1
    private1 = registry.get_private_key(signer1_id)
    public1 = registry.get_public_key(signer1_id)
    signed1 = signer.sign_report(report, private1)
    signed1.signer_id = signer1_id

    # Sign with signer 2
    private2 = registry.get_private_key(signer2_id)
    public2 = registry.get_public_key(signer2_id)
    signed2 = signer.sign_report(report, private2)
    signed2.signer_id = signer2_id

    # Verify each signature with correct key
    valid1_correct = signer.verify_report(signed1, public1)
    valid2_correct = signer.verify_report(signed2, public2)

    # Try to verify with wrong keys (should fail)
    valid1_wrong = signer.verify_report(signed1, public2)
    valid2_wrong = signer.verify_report(signed2, public1)

    logger.info(f"Signer 1 with correct key: {'✅' if valid1_correct else '❌'}")
    logger.info(f"Signer 2 with correct key: {'✅' if valid2_correct else '❌'}")
    logger.info(f"Signer 1 with wrong key: {'✅ Correct rejection' if not valid1_wrong else '❌ Security failure'}")
    logger.info(f"Signer 2 with wrong key: {'✅ Correct rejection' if not valid2_wrong else '❌ Security failure'}")

    # Check signatures are different
    signatures_different = signed1.signature_hex != signed2.signature_hex
    logger.info(f"Signatures are different: {'✅' if signatures_different else '❌'}")

    multi_test_passed = (
        valid1_correct and valid2_correct and
        not valid1_wrong and not valid2_wrong and
        signatures_different
    )

    logger.info(f"Multi-signer test passed: {'✅' if multi_test_passed else '❌'}")
    return multi_test_passed

if __name__ == "__main__":
    print("QAegisPralaya PQC Integration Test")
    print("=" * 50)

    # Run tests
    test1_passed = test_complete_flow()
    test2_passed = test_multiple_signers()

    # Run performance test from pqc_signer module
    print("\n=== Performance Baseline ===")
    performance_test()

    # Final result
    all_passed = test1_passed and test2_passed
    print(f"\n{'='*50}")
    print(f"OVERALL RESULT: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    print(f"{'='*50}")

    sys.exit(0 if all_passed else 1)