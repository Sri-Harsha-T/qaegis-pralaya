#!/usr/bin/env python3
"""
Synthetic cascade scenario generator for QAegisPralaya.
Implements ADR-0003: Graph simulation + Gaussian copula sampling.
"""

import json
import logging
import numpy as np
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
from scipy.stats import norm
import networkx as nx
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

@dataclass
class CascadeSample:
    """Single synthetic cascade scenario sample"""
    temperature_c: float
    wind_kmh: float
    precipitation_mm: float
    grid_load_pct: float
    grid_outage_nodes: int
    water_pressure_bar: float
    water_treatment_pct: float
    hospital_bed_pct: float
    ambulance_available: int
    telecom_uptime_pct: float
    cascade_type: str
    cascade_risk: float
    propagation_chain: List[str]

class CascadeGenerator:
    """Monte Carlo cascade scenario generator using Gaussian copula"""

    def __init__(self, correlation_file: Path):
        """Initialize with feature correlations from JSON file"""
        with open(correlation_file) as f:
            config = json.load(f)

        self.correlation_matrix = np.array(config["correlation_matrix"])
        self.feature_names = config["feature_names"]
        # Use cascade domains from ADR-0007
        self.domains = ["climate", "power_grid", "water", "medical", "telecom", "transport"]

        # Cholesky decomposition for correlated sampling
        self.cholesky = np.linalg.cholesky(self.correlation_matrix)

        # Cascade graph for propagation simulation
        self.cascade_graph = self._build_cascade_graph()

    def _build_cascade_graph(self) -> nx.DiGraph:
        """Build cascade propagation graph per ADR-0007"""
        G = nx.DiGraph()

        # Add nodes
        for domain in self.domains:
            G.add_node(domain)

        # Add edges with weights (probability, lag_minutes) per ADR-0007
        edges = [
            ("climate", "power_grid", {"prob": 0.75, "lag_minutes": 30}),
            ("climate", "water", {"prob": 0.50, "lag_minutes": 60}),
            ("climate", "transport", {"prob": 0.60, "lag_minutes": 15}),
            ("power_grid", "medical", {"prob": 0.90, "lag_minutes": 5}),
            ("power_grid", "water", {"prob": 0.80, "lag_minutes": 20}),
            ("power_grid", "telecom", {"prob": 0.70, "lag_minutes": 10}),
            ("water", "medical", {"prob": 0.65, "lag_minutes": 120}),
            ("telecom", "medical", {"prob": 0.40, "lag_minutes": 45}),
            ("transport", "medical", {"prob": 0.55, "lag_minutes": 30}),
        ]

        G.add_edges_from([(u, v, data) for u, v, data in edges])
        return G

    def _sample_correlated_features(self, n_samples: int) -> np.ndarray:
        """Sample correlated features using Gaussian copula"""
        # Generate independent standard normal samples (10 features)
        independent = np.random.standard_normal((n_samples, len(self.feature_names)))

        # Apply correlation via Cholesky decomposition
        correlated = independent @ self.cholesky.T

        # Transform to uniform [0,1] via CDF
        uniform = norm.cdf(correlated)

        return uniform

    def _simulate_cascade_propagation(self, initial_domain: str, base_risk: float) -> Tuple[float, List[str]]:
        """BFS cascade propagation simulation per ADR-0007"""
        propagated = {domain: 0.0 for domain in self.domains}
        propagated[initial_domain] = base_risk

        propagation_chain = [initial_domain]
        queue = [(initial_domain, base_risk)]

        while queue:
            current_domain, current_risk = queue.pop(0)

            # Propagate to neighbors
            for neighbor in self.cascade_graph.neighbors(current_domain):
                edge_data = self.cascade_graph[current_domain][neighbor]
                prop_prob = edge_data["prob"]

                # Calculate propagated risk with probability
                new_risk = current_risk * prop_prob * np.random.uniform(0.5, 1.0)

                # Update if higher risk (cascade can amplify)
                if new_risk > propagated[neighbor]:
                    propagated[neighbor] = min(1.0, new_risk)  # Cap at 1.0

                    if neighbor not in propagation_chain and new_risk > 0.1:
                        propagation_chain.append(neighbor)
                        queue.append((neighbor, new_risk))

        # Overall risk is max across all domains
        overall_risk = max(propagated.values())
        return overall_risk, propagation_chain

    def generate_scenario(self, scenario_type: str, n_samples: int = 200) -> List[Dict[str, Any]]:
        """Generate synthetic samples for a specific scenario type"""
        log.info(f"Generating {n_samples} samples for {scenario_type} scenario")

        # Get correlated base features [0,1]
        uniform_features = self._sample_correlated_features(n_samples)

        samples = []
        for i in range(n_samples):
            # Map uniform features to realistic ranges based on scenario
            features = self._map_to_realistic_ranges(uniform_features[i], scenario_type)

            # Determine initial failure domain
            initial_domain = self._get_initial_domain(scenario_type)
            base_risk = self._calculate_base_risk(features, scenario_type)

            # Simulate cascade propagation
            cascade_risk, chain = self._simulate_cascade_propagation(initial_domain, base_risk)

            # Create sample
            sample = CascadeSample(
                temperature_c=features[0],
                wind_kmh=features[1],
                precipitation_mm=features[2],
                grid_load_pct=features[3],
                grid_outage_nodes=int(features[4]),
                water_pressure_bar=features[5],
                water_treatment_pct=features[6],
                hospital_bed_pct=features[7],
                ambulance_available=int(features[8]),
                telecom_uptime_pct=features[9],
                cascade_type=scenario_type,
                cascade_risk=cascade_risk,
                propagation_chain=chain
            )

            samples.append(asdict(sample))

        log.info(f"✅ Generated {len(samples)} {scenario_type} samples")
        return samples

    def _map_to_realistic_ranges(self, uniform: np.ndarray, scenario_type: str) -> List[float]:
        """Map [0,1] uniform features to realistic ranges per scenario"""
        if scenario_type == "flood_grid":
            return [
                uniform[0] * 20 + 25,      # temp: 25-45°C
                uniform[1] * 40 + 10,      # wind: 10-50 kmh
                uniform[2] * 200 + 50,     # precip: 50-250mm (heavy rain)
                uniform[3] * 30 + 70,      # grid_load: 70-100% (stressed)
                uniform[4] * 15 + 5,       # outages: 5-20 nodes
                uniform[5] * 2 + 1,        # pressure: 1-3 bar
                uniform[6] * 40 + 60,      # treatment: 60-100%
                uniform[7] * 30 + 70,      # hospital: 70-100%
                uniform[8] * 8 + 2,        # ambulance: 2-10
                uniform[9] * 20 + 80,      # telecom: 80-100%
            ]
        elif scenario_type == "heat_hospital":
            return [
                uniform[0] * 15 + 40,      # temp: 40-55°C (extreme heat)
                uniform[1] * 25 + 5,       # wind: 5-30 kmh
                uniform[2] * 10 + 0,       # precip: 0-10mm (drought)
                uniform[3] * 20 + 80,      # grid_load: 80-100% (AC demand)
                uniform[4] * 8 + 2,        # outages: 2-10 nodes
                uniform[5] * 1.5 + 0.5,    # pressure: 0.5-2 bar
                uniform[6] * 30 + 50,      # treatment: 50-80%
                uniform[7] * 20 + 80,      # hospital: 80-100% (heat stress)
                uniform[8] * 5 + 3,        # ambulance: 3-8
                uniform[9] * 15 + 85,      # telecom: 85-100%
            ]
        elif scenario_type == "cyclone_comms":
            return [
                uniform[0] * 10 + 20,      # temp: 20-30°C
                uniform[1] * 80 + 40,      # wind: 40-120 kmh (cyclonic)
                uniform[2] * 150 + 100,    # precip: 100-250mm
                uniform[3] * 40 + 60,      # grid_load: 60-100%
                uniform[4] * 25 + 10,      # outages: 10-35 nodes
                uniform[5] * 2.5 + 0.5,    # pressure: 0.5-3 bar
                uniform[6] * 50 + 50,      # treatment: 50-100%
                uniform[7] * 40 + 60,      # hospital: 60-100%
                uniform[8] * 6 + 4,        # ambulance: 4-10
                uniform[9] * 60 + 40,      # telecom: 40-100% (wind damage)
            ]
        else:
            raise ValueError(f"Unknown scenario: {scenario_type}")

    def _get_initial_domain(self, scenario_type: str) -> str:
        """Get the primary failure domain for scenario type"""
        mapping = {
            "flood_grid": "climate",
            "heat_hospital": "climate",
            "cyclone_comms": "telecom"
        }
        return mapping[scenario_type]

    def _calculate_base_risk(self, features: List[float], scenario_type: str) -> float:
        """Calculate initial risk based on scenario-specific thresholds"""
        temp, wind, precip = features[0], features[1], features[2]

        if scenario_type == "flood_grid":
            risk = min(1.0, (precip - 50) / 150 + (temp - 25) / 20)
        elif scenario_type == "heat_hospital":
            risk = min(1.0, (temp - 35) / 20 + (100 - features[6]) / 50)  # temp + treatment strain
        elif scenario_type == "cyclone_comms":
            risk = min(1.0, (wind - 40) / 80 + (100 - features[9]) / 60)  # wind + telecom damage
        else:
            risk = 0.5

        return max(0.1, risk)  # Minimum 10% base risk

def main():
    """CLI entry point for scenario generation"""
    parser = argparse.ArgumentParser(description="Generate synthetic cascade scenarios")
    parser.add_argument("--all", action="store_true", help="Generate all scenario types")
    parser.add_argument("--scenario", choices=["flood_grid", "heat_hospital", "cyclone_comms"],
                      help="Generate specific scenario type")
    parser.add_argument("--samples", type=int, default=200, help="Number of samples per scenario")

    args = parser.parse_args()

    # Paths
    project_root = Path(__file__).parent.parent
    correlation_file = project_root / "docs/phases/phase-1-data/feature_correlations.json"
    output_dir = project_root / "data/synthetic"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize generator
    generator = CascadeGenerator(correlation_file)

    # Generate scenarios
    scenarios = ["flood_grid", "heat_hospital", "cyclone_comms"] if args.all else [args.scenario]

    for scenario in scenarios:
        if scenario is None:
            continue

        samples = generator.generate_scenario(scenario, args.samples)

        # Save to JSON
        output_file = output_dir / f"{scenario}.json"
        with open(output_file, 'w') as f:
            json.dump(samples, f, indent=2)

        log.info(f"💾 Saved {len(samples)} samples to {output_file}")

    log.info("✅ Scenario generation complete")

if __name__ == "__main__":
    main()