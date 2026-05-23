#!/usr/bin/env python3
"""
Fallback demo playback server for QAegisPralaya.
Serves scenario data on localhost:8001 when backend is unavailable.
"""

import json
import asyncio
import time
from pathlib import Path
from typing import Dict, Any, List
import logging
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import socket

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class FallbackDemoServer:
    """Serves static scenario data for demo purposes"""

    def __init__(self, port: int = 8001):
        self.port = port
        self.scenarios = self._load_scenarios()
        self.current_scenario = None
        self.start_time = None
        self.running = False

    def _load_scenarios(self) -> Dict[str, List[Dict]]:
        """Load all scenario JSON files"""
        scenarios = {}
        demo_dir = Path(__file__).parent

        for scenario_file in ["scenario_flood_grid.json", "scenario_heat_hospital.json", "scenario_cyclone_comms.json"]:
            scenario_name = scenario_file.replace("scenario_", "").replace(".json", "")
            file_path = demo_dir / scenario_file

            if file_path.exists():
                with open(file_path) as f:
                    scenarios[scenario_name] = json.load(f)
                log.info(f"Loaded {len(scenarios[scenario_name])} events for {scenario_name}")
            else:
                log.warning(f"Scenario file missing: {scenario_file}")
                scenarios[scenario_name] = []

        return scenarios

    def get_current_events(self, scenario: str) -> List[Dict]:
        """Get events that should be active now"""
        if scenario not in self.scenarios:
            return []

        if self.start_time is None:
            self.start_time = time.time()

        elapsed = time.time() - self.start_time
        events = self.scenarios[scenario]

        # Return events that should have occurred by now
        current_events = [e for e in events if e["t_seconds"] <= elapsed]
        return current_events[-5:]  # Last 5 events

    def get_health(self) -> Dict[str, Any]:
        """Health check endpoint"""
        return {
            "status": "fallback_demo",
            "scenarios_loaded": list(self.scenarios.keys()),
            "current_scenario": self.current_scenario,
            "port": self.port,
            "uptime_seconds": time.time() - (self.start_time or time.time())
        }

    def start_scenario(self, scenario: str) -> Dict[str, Any]:
        """Start demo scenario"""
        if scenario not in self.scenarios:
            return {"error": f"Unknown scenario: {scenario}"}

        self.current_scenario = scenario
        self.start_time = time.time()
        self.running = True

        return {
            "scenario_id": f"{scenario}_demo",
            "scenario_type": scenario,
            "start_time": self.start_time,
            "status": "running",
            "total_events": len(self.scenarios[scenario])
        }

    def stop_scenario(self, scenario: str) -> Dict[str, Any]:
        """Stop demo scenario"""
        self.running = False
        self.current_scenario = None
        self.start_time = None

        return {"status": "stopped", "scenario": scenario}

class DemoHTTPHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler for demo API"""

    def __init__(self, *args, demo_server=None, **kwargs):
        self.demo_server = demo_server
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/health":
            self._send_json(self.demo_server.get_health())
        elif self.path.startswith("/events/"):
            scenario = self.path.split("/")[-1]
            events = self.demo_server.get_current_events(scenario)
            self._send_json({"events": events, "scenario": scenario})
        elif self.path == "/":
            self._send_demo_page()
        else:
            self.send_error(404, "Not found")

    def do_POST(self):
        """Handle POST requests"""
        if self.path.startswith("/scenario/"):
            scenario = self.path.split("/")[-1]
            result = self.demo_server.start_scenario(scenario)
            self._send_json(result)
        else:
            self.send_error(404, "Not found")

    def do_DELETE(self):
        """Handle DELETE requests"""
        if self.path.startswith("/scenario/"):
            scenario = self.path.split("/")[-1]
            result = self.demo_server.stop_scenario(scenario)
            self._send_json(result)
        else:
            self.send_error(404, "Not found")

    def _send_json(self, data: Dict[str, Any]):
        """Send JSON response"""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def _send_demo_page(self):
        """Send simple demo page"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>QAegisPralaya Fallback Demo</title>
    <style>
        body {{ background: #060B18; color: #E5E5E5; font-family: monospace; padding: 20px; }}
        button {{ background: #1E293B; border: 1px solid #334155; color: #E5E5E5; padding: 8px 16px; margin: 4px; cursor: pointer; }}
        button:hover {{ background: #334155; }}
        pre {{ background: #0A1020; padding: 16px; border-radius: 4px; overflow: auto; }}
    </style>
</head>
<body>
    <h1>🌊 QAegisPralaya Fallback Demo</h1>
    <p>Backend not available - serving static scenario data on port {self.demo_server.port}</p>

    <h2>Demo Scenarios</h2>
    <button onclick="startScenario('flood_grid')">🌊 Flood + Grid</button>
    <button onclick="startScenario('heat_hospital')">🌡️ Heat + Hospital</button>
    <button onclick="startScenario('cyclone_comms')">🌀 Cyclone + Comms</button>
    <button onclick="checkHealth()">❤️ Health Check</button>

    <h2>Output</h2>
    <pre id="output">Ready for demo...</pre>

    <script>
        async function startScenario(scenario) {{
            const response = await fetch(`/scenario/${{scenario}}`, {{method: 'POST'}});
            const data = await response.json();
            document.getElementById('output').textContent = JSON.stringify(data, null, 2);

            // Poll events
            pollEvents(scenario);
        }}

        async function checkHealth() {{
            const response = await fetch('/health');
            const data = await response.json();
            document.getElementById('output').textContent = JSON.stringify(data, null, 2);
        }}

        async function pollEvents(scenario) {{
            for(let i = 0; i < 10; i++) {{
                await new Promise(resolve => setTimeout(resolve, 3000));
                const response = await fetch(`/events/${{scenario}}`);
                const data = await response.json();
                document.getElementById('output').textContent = JSON.stringify(data, null, 2);
            }}
        }}
    </script>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, format, *args):
        """Override to use our logger"""
        log.info(f"{self.address_string()} - {format % args}")

def main():
    """Run fallback demo server"""
    port = 8001

    # Check if port is available
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
    except OSError:
        log.error(f"Port {port} already in use. Choose different port or stop conflicting service.")
        return

    demo_server = FallbackDemoServer(port)

    # Create handler with demo_server reference
    handler = lambda *args, **kwargs: DemoHTTPHandler(*args, demo_server=demo_server, **kwargs)

    httpd = HTTPServer(('localhost', port), handler)

    log.info(f"🚀 QAegisPralaya Fallback Demo starting on http://localhost:{port}")
    log.info("📊 Available endpoints:")
    log.info("   GET  /health - Server status")
    log.info("   POST /scenario/{name} - Start scenario")
    log.info("   GET  /events/{name} - Get current events")
    log.info("   GET  / - Demo web interface")
    log.info("")
    log.info("💡 This is a fallback demo for when the main backend is unavailable")
    log.info("🔗 Open http://localhost:8001 in your browser")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        log.info("🛑 Demo server stopped")
        httpd.shutdown()

if __name__ == "__main__":
    main()