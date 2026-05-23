#!/usr/bin/env python3
"""
QAegisPralaya Backend - FastAPI application with PQC signing endpoints.
"""
import logging
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import time

from .pqc_signer import (
    IncidentReport,
    SignedReport,
    PQCSigner,
    ResponderKeyRegistry
)
from .qml_engine import CascadeAnalyzer
from .data_pipeline import get_live_features
from .scenario_runner import ScenarioRunner

from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="QAegisPralaya API",
    description="Emergency Operations Center - Post-Quantum Cryptographic API",
    version="1.0.0"
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize PQC components
pqc_signer = PQCSigner()
key_registry = ResponderKeyRegistry()

# Initialize QML cascade analyzer
cascade_analyzer = CascadeAnalyzer()

# Initialize scenario runner
scenario_runner = ScenarioRunner(pqc_signer, key_registry)

logger.info("QAegisPralaya backend initialized")


# Pydantic models for API validation
class IncidentReportRequest(BaseModel):
    """Request model for creating incident reports."""
    reporter_id: str = Field(..., description="ID of the reporting responder")
    location: Dict[str, Any] = Field(..., description="Location with lat, lon, district")
    incident_type: str = Field(..., description="Type of incident")
    severity: int = Field(..., ge=1, le=5, description="Severity level 1-5")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Additional data")


class SignReportRequest(BaseModel):
    """Request model for signing incident reports."""
    report: IncidentReportRequest
    signer_id: str = Field(..., description="ID of the responder signing the report")


class VerifyReportRequest(BaseModel):
    """Request model for verifying signed reports."""
    signed_report: Dict[str, Any] = Field(..., description="The signed report to verify")
    public_key_hex: str = Field(..., description="Public key for verification")


class VerificationResult(BaseModel):
    """Response model for signature verification."""
    valid: bool
    algorithm: str
    signer_id: str
    verification_time_ms: float


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "operational",
        "service": "QAegisPralaya Backend",
        "algorithms": ["Dilithium3", "HMAC-SHA256"],
        "active_responders": len(key_registry.list_active_responders())
    }


@app.get("/api/responders")
async def list_responders():
    """List active responders and their public keys."""
    responders = key_registry.list_active_responders()
    return {
        "responders": responders,
        "count": len(responders)
    }


@app.post("/api/pqc/sign")
async def sign_report(request: SignReportRequest) -> Dict[str, Any]:
    """Sign an incident report with PQC signature.

    This endpoint:
    1. Creates an IncidentReport from the request data
    2. Looks up the signer's private key from the registry
    3. Signs the report using PQCSigner
    4. Returns the SignedReport
    """
    try:
        start_time = time.perf_counter()

        # Get signer's private key from registry
        private_key_hex = key_registry.get_private_key(request.signer_id)
        if not private_key_hex:
            raise HTTPException(
                status_code=401,
                detail=f"Unknown signer_id: {request.signer_id} or responder inactive"
            )

        # Create IncidentReport
        try:
            incident_report = IncidentReport.create(
                reporter_id=request.report.reporter_id,
                location=request.report.location,
                incident_type=request.report.incident_type,
                severity=request.report.severity,
                payload=request.report.payload
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid report data: {str(e)}")

        # Sign the report
        signed_report = pqc_signer.sign_report(incident_report, private_key_hex)
        # Update signer_id in the signed report
        signed_report.signer_id = request.signer_id

        sign_time = (time.perf_counter() - start_time) * 1000

        logger.info(f"Report {incident_report.report_id} signed by {request.signer_id} in {sign_time:.2f}ms")

        # Return as dictionary for JSON serialization
        result = {
            "signed_report": {
                "report_id": signed_report.report_id,
                "reporter_id": signed_report.reporter_id,
                "timestamp": signed_report.timestamp,
                "location": signed_report.location,
                "incident_type": signed_report.incident_type,
                "severity": signed_report.severity,
                "payload": signed_report.payload,
                "signature_hex": signed_report.signature_hex,
                "algorithm": signed_report.algorithm,
                "signer_id": signed_report.signer_id
            },
            "sign_time_ms": sign_time,
            "status": "signed"
        }

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Signing failed: {str(e)}")


@app.post("/api/pqc/verify")
async def verify_report(request: VerifyReportRequest) -> VerificationResult:
    """Verify a signed incident report.

    This endpoint:
    1. Deserializes the SignedReport from request
    2. Verifies the signature using the provided public key
    3. Returns verification result with timing
    """
    try:
        start_time = time.perf_counter()

        # Create SignedReport from request data
        try:
            signed_report = SignedReport(**request.signed_report)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid signed report format: {str(e)}")

        # Verify the signature
        is_valid = pqc_signer.verify_report(signed_report, request.public_key_hex)

        verify_time = (time.perf_counter() - start_time) * 1000

        logger.info(f"Report {signed_report.report_id} verification: {'✅' if is_valid else '❌'} ({verify_time:.2f}ms)")

        return VerificationResult(
            valid=is_valid,
            algorithm=signed_report.algorithm,
            signer_id=signed_report.signer_id,
            verification_time_ms=verify_time
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@app.post("/api/pqc/sign-verify")
async def sign_and_verify(request: SignReportRequest) -> Dict[str, Any]:
    """Sign and immediately verify a report (for testing/demo).

    This is a convenience endpoint that performs both operations
    and measures the complete round-trip time.
    """
    try:
        start_time = time.perf_counter()

        # Get keys for the signer
        private_key_hex = key_registry.get_private_key(request.signer_id)
        public_key_hex = key_registry.get_public_key(request.signer_id)

        if not private_key_hex or not public_key_hex:
            raise HTTPException(
                status_code=401,
                detail=f"Unknown signer_id: {request.signer_id} or responder inactive"
            )

        # Create and sign report
        incident_report = IncidentReport.create(
            reporter_id=request.report.reporter_id,
            location=request.report.location,
            incident_type=request.report.incident_type,
            severity=request.report.severity,
            payload=request.report.payload
        )

        signed_report = pqc_signer.sign_report(incident_report, private_key_hex)
        signed_report.signer_id = request.signer_id

        # Verify the signature
        is_valid = pqc_signer.verify_report(signed_report, public_key_hex)

        total_time = (time.perf_counter() - start_time) * 1000

        logger.info(f"Sign+verify round-trip for {incident_report.report_id}: {total_time:.2f}ms")

        return {
            "report_id": signed_report.report_id,
            "valid": is_valid,
            "algorithm": signed_report.algorithm,
            "signer_id": signed_report.signer_id,
            "round_trip_time_ms": total_time,
            "performance_target_met": total_time < 500.0,
            "status": "verified" if is_valid else "invalid"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sign-verify failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sign-verify failed: {str(e)}")


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "path": str(request.url.path)
        }
    )


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check with component status"""
    try:
        # Check QML weights
        weights_file = Path(__file__).parent / "models/vqc_weights.json"
        qml_status = "loaded" if weights_file.exists() else "missing"

        # Check PQC availability
        pqc_status = "available" if hasattr(pqc_signer, 'use_dilithium') and pqc_signer.use_dilithium else "fallback"

        return {
            "status": "ok",
            "qml": qml_status,
            "pqc": pqc_status,
            "responders": len(key_registry.list_responders()),
            "active_scenarios": len(scenario_runner.get_active_scenarios())
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/scenario/{scenario_type}")
async def start_scenario(scenario_type: str) -> Dict[str, Any]:
    """Start a background cascade scenario simulation"""
    try:
        if scenario_type not in ["flood_grid", "heat_hospital", "cyclone_comms"]:
            raise HTTPException(status_code=400, detail=f"Invalid scenario: {scenario_type}")

        result = await scenario_runner.start_scenario(scenario_type)
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start scenario {scenario_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Scenario start failed: {str(e)}")

@app.delete("/scenario/{scenario_type}")
async def stop_scenario(scenario_type: str) -> Dict[str, Any]:
    """Stop a running scenario"""
    try:
        stopped = await scenario_runner.stop_scenario(scenario_type)
        if stopped:
            return {"status": "stopped", "scenario": scenario_type}
        else:
            raise HTTPException(status_code=404, detail=f"Scenario {scenario_type} not running")
    except Exception as e:
        logger.error(f"Failed to stop scenario {scenario_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scenarios")
async def list_active_scenarios() -> Dict[str, Any]:
    """List all active scenarios"""
    return {"active_scenarios": scenario_runner.get_active_scenarios()}

@app.websocket("/ws/incidents")
async def incidents_websocket(websocket: WebSocket):
    """WebSocket stream of signed incident reports during active scenarios"""
    await websocket.accept()
    logger.info("New incidents WebSocket connection")

    queue = scenario_runner.subscribe_incidents()

    try:
        while True:
            # Get message from queue (wait for new incidents)
            try:
                message = await asyncio.wait_for(queue.get(), timeout=1.0)
                await websocket.send_text(json.dumps(message))
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                await websocket.send_text(json.dumps({"type": "heartbeat", "timestamp": time.time()}))

    except WebSocketDisconnect:
        logger.info("Incidents WebSocket disconnected")
    except Exception as e:
        logger.error(f"Incidents WebSocket error: {e}")
        await websocket.close()

@app.websocket("/ws/alerts")
async def alerts_websocket(websocket: WebSocket):
    """WebSocket stream of cascade analysis alerts during active scenarios"""
    await websocket.accept()
    logger.info("New alerts WebSocket connection")

    queue = scenario_runner.subscribe_alerts()

    try:
        while True:
            # Get message from queue (wait for new alerts)
            try:
                message = await asyncio.wait_for(queue.get(), timeout=1.0)
                await websocket.send_text(json.dumps(message))
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_text(json.dumps({"type": "heartbeat", "timestamp": time.time()}))

    except WebSocketDisconnect:
        logger.info("Alerts WebSocket disconnected")
    except Exception as e:
        logger.error(f"Alerts WebSocket error: {e}")
        await websocket.close()

# Pydantic model for cascade prediction
class PredictRequest(BaseModel):
    """Request model for cascade prediction."""
    city: str = Field(default="Bengaluru", description="City name for live data")
    features: Dict[str, float] = Field(default=None, description="Override features (optional)")

@app.post("/api/predict")
async def predict_cascade_risk(request: PredictRequest) -> Dict[str, Any]:
    """
    Predict cascade risk using live data and QML analysis.
    Returns comprehensive risk analysis with domain breakdown.
    """
    try:
        start_time = time.perf_counter()

        # Get live features or use provided ones
        if request.features:
            feature_dict = request.features
        else:
            feature_dict = get_live_features(request.city)

        # Run cascade analysis
        analysis = cascade_analyzer.analyze(feature_dict)

        prediction_time = (time.perf_counter() - start_time) * 1000

        logger.info(f"Cascade prediction for {request.city}: {prediction_time:.2f}ms")

        # Check performance requirement (<15s)
        if prediction_time > 15000:
            logger.warning(f"Prediction time {prediction_time:.2f}ms > 15s target")

        return {
            "city": request.city,
            "analysis": {
                "cascade_type": analysis.cascade_type,
                "overall_risk": analysis.overall_risk,
                "domain_risks": analysis.domain_risks,
                "propagation_chain": analysis.propagation_chain,
                "timeline_minutes": analysis.timeline_minutes,
                "confidence": analysis.confidence
            },
            "features_used": feature_dict,
            "prediction_time_ms": prediction_time,
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )