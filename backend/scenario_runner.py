#!/usr/bin/env python3
"""
Scenario Runner - Background task management for cascade scenario simulation.
"""
import asyncio
import json
import logging
import random
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from .pqc_signer import IncidentReport, PQCSigner, ResponderKeyRegistry
from .qml_engine import CascadeAnalyzer

logger = logging.getLogger(__name__)

class ScenarioRunner:
    """Manages running cascade scenarios with real-time incident generation"""

    def __init__(self, pqc_signer: PQCSigner, key_registry: ResponderKeyRegistry):
        self.pqc_signer = pqc_signer
        self.key_registry = key_registry
        self.cascade_analyzer = CascadeAnalyzer()

        self.active_scenarios: Dict[str, Dict] = {}
        self.incident_subscribers: List[asyncio.Queue] = []
        self.alert_subscribers: List[asyncio.Queue] = []

        # Load scenario templates
        self.scenario_templates = self._load_scenario_templates()

    def _load_scenario_templates(self) -> Dict[str, List[Dict]]:
        """Load synthetic scenario data for simulation"""
        templates = {}
        data_dir = Path(__file__).parent.parent / "data/synthetic"

        for scenario_file in ["flood_grid.json", "heat_hospital.json", "cyclone_comms.json"]:
            scenario_name = scenario_file.replace(".json", "")
            file_path = data_dir / scenario_file

            if file_path.exists():
                with open(file_path) as f:
                    templates[scenario_name] = json.load(f)
                logger.info(f"Loaded {len(templates[scenario_name])} samples for {scenario_name}")
            else:
                logger.warning(f"Scenario template missing: {scenario_file}")
                templates[scenario_name] = []

        return templates

    async def start_scenario(self, scenario_type: str) -> Dict[str, Any]:
        """Start a background scenario simulation"""
        if scenario_type not in self.scenario_templates:
            raise ValueError(f"Unknown scenario: {scenario_type}")

        if scenario_type in self.active_scenarios:
            logger.warning(f"Scenario {scenario_type} already running")
            return self.active_scenarios[scenario_type]

        scenario_id = f"{scenario_type}_{int(time.time())}"

        scenario_info = {
            "scenario_id": scenario_id,
            "scenario_type": scenario_type,
            "start_time": time.time(),
            "incidents_sent": 0,
            "alerts_sent": 0,
            "status": "running"
        }

        self.active_scenarios[scenario_type] = scenario_info

        # Start background task
        asyncio.create_task(self._run_scenario_background(scenario_type))

        logger.info(f"Started scenario: {scenario_type}")
        return scenario_info

    async def stop_scenario(self, scenario_type: str) -> bool:
        """Stop a running scenario"""
        if scenario_type in self.active_scenarios:
            self.active_scenarios[scenario_type]["status"] = "stopped"
            del self.active_scenarios[scenario_type]
            logger.info(f"Stopped scenario: {scenario_type}")
            return True
        return False

    async def _run_scenario_background(self, scenario_type: str):
        """Background task that generates incidents and alerts"""
        try:
            samples = self.scenario_templates[scenario_type]
            if not samples:
                logger.error(f"No samples available for {scenario_type}")
                return

            responder_ids = self.key_registry.list_responders()
            if not responder_ids:
                logger.error("No responders available for signing")
                return

            incident_count = 0

            while scenario_type in self.active_scenarios:
                # Generate incident every 3s
                await asyncio.sleep(3)

                if scenario_type not in self.active_scenarios:
                    break

                # Pick random sample and responder
                sample = random.choice(samples)
                responder_id = random.choice(responder_ids)

                # Create incident
                incident = await self._create_incident_from_sample(sample, responder_id, incident_count)
                if incident:
                    await self._broadcast_incident(incident)
                    incident_count += 1

                # Generate alert every 5s (aligned with incident timing)
                if incident_count % 2 == 1:  # Every other incident (roughly 6s)
                    alert = await self._create_cascade_alert(sample)
                    if alert:
                        await self._broadcast_alert(alert)

                # Update scenario stats
                if scenario_type in self.active_scenarios:
                    self.active_scenarios[scenario_type]["incidents_sent"] = incident_count

        except Exception as e:
            logger.error(f"Scenario {scenario_type} failed: {e}")
        finally:
            # Cleanup
            if scenario_type in self.active_scenarios:
                self.active_scenarios[scenario_type]["status"] = "completed"

    async def _create_incident_from_sample(self, sample: Dict, responder_id: str, incident_num: int) -> Optional[Dict]:
        """Create and sign an incident report from scenario sample"""
        try:
            # Map sample to incident
            incident_types = {
                "flood_grid": "Flooding",
                "heat_hospital": "Heat Emergency",
                "cyclone_comms": "Communications Outage"
            }

            incident_type = incident_types.get(sample["cascade_type"], "General Emergency")

            # Create report
            incident_report = IncidentReport.create(
                reporter_id=responder_id,
                location={
                    "lat": 12.9716 + random.uniform(-0.1, 0.1),  # Bengaluru +/- noise
                    "lon": 77.5946 + random.uniform(-0.1, 0.1),
                    "district": f"Zone-{random.choice(['North', 'South', 'East', 'West'])}"
                },
                incident_type=incident_type,
                severity=min(5, max(1, int(sample["cascade_risk"] * 5) + 1)),
                payload={
                    "temperature_c": sample["temperature_c"],
                    "wind_kmh": sample["wind_kmh"],
                    "precipitation_mm": sample["precipitation_mm"],
                    "cascade_risk": sample["cascade_risk"],
                    "incident_sequence": incident_num
                }
            )

            # Sign the report
            private_key = self.key_registry.get_private_key(responder_id)
            if not private_key:
                logger.error(f"No private key for responder {responder_id}")
                return None

            signed_report = self.pqc_signer.sign_report(incident_report, private_key)
            signed_report.signer_id = responder_id

            return asdict(signed_report)

        except Exception as e:
            logger.error(f"Failed to create incident: {e}")
            return None

    async def _create_cascade_alert(self, sample: Dict) -> Optional[Dict]:
        """Create cascade analysis alert from sample"""
        try:
            # Run cascade analysis
            feature_dict = {
                "temperature_c": sample["temperature_c"],
                "wind_kmh": sample["wind_kmh"],
                "precipitation_mm": sample["precipitation_mm"],
                "grid_load_pct": sample["grid_load_pct"],
                "grid_outage_nodes": sample["grid_outage_nodes"],
                "water_pressure_bar": sample["water_pressure_bar"],
                "water_treatment_pct": sample["water_treatment_pct"],
                "hospital_bed_pct": sample["hospital_bed_pct"],
                "ambulance_available": sample["ambulance_available"],
                "telecom_uptime_pct": sample["telecom_uptime_pct"]
            }

            analysis = self.cascade_analyzer.analyze(feature_dict)

            alert = {
                "alert_type": "cascade_update",
                "timestamp": datetime.utcnow().isoformat(),
                "analysis": asdict(analysis),
                "source_sample": sample["cascade_type"]
            }

            return alert

        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            return None

    async def _broadcast_incident(self, incident: Dict):
        """Broadcast incident to WebSocket subscribers"""
        if self.incident_subscribers:
            message = {"type": "incident", "data": incident}

            # Send to all subscribers (remove failed ones)
            active_subs = []
            for queue in self.incident_subscribers:
                try:
                    queue.put_nowait(message)
                    active_subs.append(queue)
                except asyncio.QueueFull:
                    logger.warning("Incident subscriber queue full, dropping")

            self.incident_subscribers = active_subs

    async def _broadcast_alert(self, alert: Dict):
        """Broadcast cascade alert to WebSocket subscribers"""
        if self.alert_subscribers:
            message = {"type": "alert", "data": alert}

            # Send to all subscribers (remove failed ones)
            active_subs = []
            for queue in self.alert_subscribers:
                try:
                    queue.put_nowait(message)
                    active_subs.append(queue)
                except asyncio.QueueFull:
                    logger.warning("Alert subscriber queue full, dropping")

            self.alert_subscribers = active_subs

    def subscribe_incidents(self) -> asyncio.Queue:
        """Subscribe to incident stream"""
        queue = asyncio.Queue(maxsize=50)
        self.incident_subscribers.append(queue)
        return queue

    def subscribe_alerts(self) -> asyncio.Queue:
        """Subscribe to alert stream"""
        queue = asyncio.Queue(maxsize=50)
        self.alert_subscribers.append(queue)
        return queue

    def get_active_scenarios(self) -> Dict[str, Dict]:
        """Get status of all active scenarios"""
        return self.active_scenarios.copy()