#!/usr/bin/env python3
"""
Train the VQC on synthetic data and save weights.
Run after generate_scenario.py --all.
"""
import sys, json, logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent

def main():
    # Verify data exists
    data_dir = ROOT / "data" / "synthetic"
    if not data_dir.exists():
        log.error("Synthetic data not found. Run: python data/generate_scenario.py --all")
        sys.exit(1)

    sys.path.insert(0, str(ROOT))
    from backend.qml_engine import CascadeRiskScorer
    import numpy as np

    # Load all synthetic data
    all_samples = []
    for f in data_dir.glob("*.json"):
        with open(f) as fp:
            all_samples.extend(json.load(fp))

    log.info(f"Loaded {len(all_samples)} training samples")

    feature_keys = [
        "temperature_c", "wind_kmh", "precipitation_mm",
        "grid_load_pct", "grid_outage_nodes", "water_pressure_bar",
        "water_treatment_pct", "hospital_bed_pct",
        "ambulance_available", "telecom_uptime_pct"
    ]
    domain_keys = ["climate", "power_grid", "water", "medical", "telecom"]

    X = np.array([[s[k] for k in feature_keys] for s in all_samples])
    y = np.array([[s.get(f"risk_{k}", s["cascade_risk"]) for k in domain_keys]
                  for s in all_samples])

    scorer = CascadeRiskScorer()
    scorer.fit(X, y)
    scorer.save_weights(ROOT / "backend" / "models" / "vqc_weights.json")
    log.info("✅ VQC weights saved to backend/models/vqc_weights.json")

if __name__ == "__main__":
    main()
