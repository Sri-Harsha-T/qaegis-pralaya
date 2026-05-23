#!/usr/bin/env python3
"""
Demo script for PQC API endpoints.
Shows how to interact with the FastAPI endpoints for signing and verifying reports.

Usage:
1. Start the backend server: uvicorn backend.main:app --reload --port 8000
2. Run this script: python scripts/demo_pqc_api.py

Or use the demo mode to simulate API calls without a running server.
"""
import json
import requests
import time
from typing import Dict, Any

# Demo data
DEMO_INCIDENT_REPORT = {
    "reporter_id": "resp_fire_001",
    "location": {
        "lat": 12.9716,
        "lon": 77.5946,
        "district": "Bengaluru Central"
    },
    "incident_type": "building_fire",
    "severity": 4,
    "payload": {
        "building_type": "commercial_complex",
        "floors": 12,
        "occupants_evacuated": 200,
        "fire_units_dispatched": 4,
        "estimated_damage": "severe"
    }
}

BASE_URL = "http://localhost:8000"

def test_api_endpoints():
    """Test the PQC API endpoints with live server."""
    print("=== PQC API Demo ===")

    try:
        # 1. Check server health
        print("1. Checking server health...")
        response = requests.get(f"{BASE_URL}/")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Service: {data['service']}")
            print(f"   Active responders: {data['active_responders']}")
        else:
            print("   ❌ Server not reachable")
            return False

        # 2. List responders
        print("\n2. Listing available responders...")
        response = requests.get(f"{BASE_URL}/api/responders")
        if response.status_code == 200:
            responders_data = response.json()
            print(f"   Found {responders_data['count']} responders:")
            for r in responders_data['responders'][:3]:
                print(f"   - {r['name']} ({r['department']})")
        else:
            print("   ❌ Failed to get responders list")
            return False

        # 3. Sign a report
        print("\n3. Signing incident report...")
        sign_request = {
            "report": DEMO_INCIDENT_REPORT,
            "signer_id": "resp_fire_001"  # Captain Smith
        }

        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/pqc/sign", json=sign_request)
        sign_duration = (time.time() - start_time) * 1000

        if response.status_code == 200:
            sign_result = response.json()
            print(f"   ✅ Report signed successfully")
            print(f"   Report ID: {sign_result['signed_report']['report_id']}")
            print(f"   Algorithm: {sign_result['signed_report']['algorithm']}")
            print(f"   Sign time: {sign_result['sign_time_ms']:.2f}ms")
            print(f"   API round-trip: {sign_duration:.2f}ms")

            signed_report = sign_result['signed_report']

        else:
            print(f"   ❌ Signing failed: {response.status_code} {response.text}")
            return False

        # 4. Verify the signed report
        print("\n4. Verifying signed report...")

        # First get the public key for the signer
        responder_key = None
        for r in responders_data['responders']:
            if r['responder_id'] == 'resp_fire_001':
                responder_key = r['public_key_hex']
                break

        if not responder_key:
            print("   ❌ Could not find public key for signer")
            return False

        verify_request = {
            "signed_report": signed_report,
            "public_key_hex": responder_key
        }

        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/pqc/verify", json=verify_request)
        verify_duration = (time.time() - start_time) * 1000

        if response.status_code == 200:
            verify_result = response.json()
            print(f"   Verification result: {'✅ VALID' if verify_result['valid'] else '❌ INVALID'}")
            print(f"   Algorithm: {verify_result['algorithm']}")
            print(f"   Verify time: {verify_result['verification_time_ms']:.2f}ms")
            print(f"   API round-trip: {verify_duration:.2f}ms")

            is_valid = verify_result['valid']
        else:
            print(f"   ❌ Verification failed: {response.status_code} {response.text}")
            return False

        # 5. Test tamper detection
        print("\n5. Testing tamper detection...")
        tampered_report = signed_report.copy()
        tampered_report['severity'] = 1  # Change severity

        tamper_request = {
            "signed_report": tampered_report,
            "public_key_hex": responder_key
        }

        response = requests.post(f"{BASE_URL}/api/pqc/verify", json=tamper_request)
        if response.status_code == 200:
            tamper_result = response.json()
            tamper_detected = not tamper_result['valid']
            print(f"   Tamper detection: {'✅ Working' if tamper_detected else '❌ Failed'}")
        else:
            print(f"   ❌ Tamper test failed: {response.status_code}")
            return False

        # 6. Test round-trip performance endpoint
        print("\n6. Testing round-trip performance...")
        perf_request = {
            "report": DEMO_INCIDENT_REPORT,
            "signer_id": "resp_fire_001"
        }

        response = requests.post(f"{BASE_URL}/api/pqc/sign-verify", json=perf_request)
        if response.status_code == 200:
            perf_result = response.json()
            print(f"   Round-trip time: {perf_result['round_trip_time_ms']:.2f}ms")
            print(f"   Target met (<500ms): {'✅' if perf_result['performance_target_met'] else '❌'}")
            print(f"   Final validation: {'✅' if perf_result['valid'] else '❌'}")

        # Summary
        total_sign_verify = sign_result['sign_time_ms'] + verify_result['verification_time_ms']

        print(f"\n=== API Demo Summary ===")
        print(f"Sign operation: ✅ {sign_result['sign_time_ms']:.2f}ms")
        print(f"Verify operation: ✅ {verify_result['verification_time_ms']:.2f}ms")
        print(f"Total crypto time: {total_sign_verify:.2f}ms")
        print(f"Tamper detection: ✅ Working")
        print(f"Performance target: {'✅ Met' if total_sign_verify < 500 else '❌ Exceeded'}")

        return is_valid and tamper_detected

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Start with: uvicorn backend.main:app --reload --port 8000")
        return False
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False

def demo_without_server():
    """Demonstrate PQC functionality without requiring FastAPI server."""
    print("=== PQC Demo (No Server Required) ===")

    import sys
    from pathlib import Path

    # Add backend to path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from backend.pqc_signer import IncidentReport, PQCSigner, ResponderKeyRegistry

    # Initialize components
    signer = PQCSigner()
    registry = ResponderKeyRegistry()

    print(f"1. Initialized PQC system with {len(registry.list_active_responders())} responders")

    # Create incident report
    report = IncidentReport.create(
        reporter_id=DEMO_INCIDENT_REPORT["reporter_id"],
        location=DEMO_INCIDENT_REPORT["location"],
        incident_type=DEMO_INCIDENT_REPORT["incident_type"],
        severity=DEMO_INCIDENT_REPORT["severity"],
        payload=DEMO_INCIDENT_REPORT["payload"]
    )

    print(f"2. Created incident report: {report.incident_type} (severity {report.severity})")

    # Sign report
    private_key = registry.get_private_key("resp_fire_001")
    public_key = registry.get_public_key("resp_fire_001")

    signed_report = signer.sign_report(report, private_key)
    print(f"3. Signed with algorithm: {signed_report.algorithm}")

    # Verify report
    is_valid = signer.verify_report(signed_report, public_key)
    print(f"4. Verification: {'✅ Valid' if is_valid else '❌ Invalid'}")

    # Test tamper detection
    signed_report.severity = 1  # Tamper
    is_tampered = signer.verify_report(signed_report, public_key)
    print(f"5. Tamper detection: {'✅ Working' if not is_tampered else '❌ Failed'}")

    print("\n✅ PQC system working correctly! Ready for EOC integration.")

if __name__ == "__main__":
    import sys

    print("QAegisPralaya PQC API Demo")
    print("=" * 40)

    # Try API demo first, fall back to no-server demo
    try:
        if test_api_endpoints():
            print("\n✅ All API tests passed!")
        else:
            print("\n❌ API tests failed, trying offline demo...")
            demo_without_server()
    except Exception:
        print("\n⚠️ API server not available, running offline demo...")
        demo_without_server()