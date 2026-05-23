#!/usr/bin/env python3
"""
QML Engine for QAegisPralaya cascade risk prediction.
Implements VQC per ADR-0001 and cascade analysis per ADR-0007.
"""

import json
import logging
import time
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

import pennylane as qml
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import networkx as nx

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

@dataclass
class CascadeAnalysis:
    """Complete cascade risk analysis result"""
    cascade_type: str
    overall_risk: float
    domain_risks: Dict[str, float]
    propagation_chain: List[str]
    timeline_minutes: List[int]
    confidence: float

class CascadeRiskScorer:
    """VQC-based cascade risk scorer per ADR-0001"""

    def __init__(self, n_qubits: int = 5, n_layers: int = 2):
        """Initialize VQC with fixed architecture per ADR-0001"""
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.n_features = 10  # Input features
        self.n_pca_dims = 5   # PCA reduction target

        # Create PennyLane device - simulator only per ADR-0001
        self.device = qml.device("default.qubit", wires=n_qubits)

        # Initialize components
        self.pca = PCA(n_components=self.n_pca_dims)
        self.scaler = StandardScaler()
        self.weights = None
        self.is_trained = False

        # Weight file path
        self.project_root = Path(__file__).parent.parent
        self.weights_file = self.project_root / "backend/models/vqc_weights.json"

        # Create VQC circuit
        self._create_vqc_circuit()

    def _create_vqc_circuit(self):
        """Create VQC circuit per ADR-0001 specification"""
        @qml.qnode(self.device)
        def vqc_circuit(features, weights):
            """
            VQC circuit: AngleEmbedding + StronglyEntanglingLayers
            Per ADR-0001: exact architecture locked
            """
            # Angle embedding with clipped angles
            angles = np.clip(features, 0, np.pi)
            qml.AngleEmbedding(angles, wires=range(self.n_qubits), rotation="X")

            # Strongly entangling layers (2 layers per spec)
            qml.StronglyEntanglingLayers(weights, wires=range(self.n_qubits))

            # Measurement: Pauli-Z expectation values
            return [qml.expval(qml.PauliZ(i)) for i in range(self.n_qubits)]

        self.circuit = vqc_circuit

    def preprocess_features(self, features: np.ndarray) -> np.ndarray:
        """PCA preprocessing: 10 features → 5 angles"""
        if not self.is_trained:
            raise ValueError("Model must be trained before preprocessing")

        # Normalize features
        features_scaled = self.scaler.transform(features.reshape(1, -1))

        # Apply PCA: 10 → 5 dimensions
        features_pca = self.pca.transform(features_scaled)

        # Clip angles to [0, π] per ADR requirements
        angles = np.clip(features_pca[0], 0, np.pi)

        return angles

    def predict_domain_risks(self, feature_dict: Dict[str, Any]) -> Dict[str, float]:
        """
        Predict risk for each domain using VQC.
        Returns dict with keys: climate, power_grid, water, medical, telecom
        """
        if not self.is_trained:
            self._load_weights()

        # Convert feature dict to array
        features = self._dict_to_feature_array(feature_dict)

        # Preprocess: 10 → 5 PCA components
        angles = self.preprocess_features(features)

        # Run VQC inference
        start_time = time.time()
        measurements = self.circuit(angles, self.weights)
        inference_time = time.time() - start_time

        if inference_time > 15.0:
            log.warning(f"Inference time {inference_time:.2f}s > 15s target")

        # Map measurements [-1,1] → [0,1] risks
        domain_risks = {}
        domains = ["climate", "power_grid", "water", "medical", "telecom"]

        for i, domain in enumerate(domains):
            risk = (measurements[i] + 1) / 2  # Map [-1,1] → [0,1]
            domain_risks[domain] = float(risk)

        log.debug(f"Domain risks predicted in {inference_time:.3f}s")
        return domain_risks

    def train(self, training_data: List[Dict[str, Any]],
              validation_split: float = 0.2,
              epochs: int = 100,
              learning_rate: float = 0.01) -> Dict[str, float]:
        """
        Train VQC on synthetic cascade data.
        Returns training metrics including accuracy.
        """
        log.info(f"Training VQC on {len(training_data)} samples")

        # Prepare data
        X, y = self._prepare_training_data(training_data)

        # Train/test split (no stratify for continuous targets)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=validation_split, random_state=42
        )

        # Fit PCA and scaler on training data
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_train_pca = self.pca.fit_transform(X_train_scaled)

        # Initialize weights
        self.weights = np.random.uniform(
            0, 2*np.pi,
            (self.n_layers, self.n_qubits, 3)
        )

        # Adam optimizer setup
        opt = qml.AdamOptimizer(stepsize=learning_rate)

        # Training loop
        best_accuracy = 0.0
        patience = 10
        no_improve_count = 0

        for epoch in range(epochs):
            # Batch training (simplified - full batch for demo)
            def cost_fn(weights):
                predictions = []
                targets = []

                for i, (features, target) in enumerate(zip(X_train_pca, y_train)):
                    angles = np.clip(features, 0, np.pi)
                    measurements = self.circuit(angles, weights)

                    # Convert measurements to risk prediction
                    pred_risk = np.mean([(m + 1) / 2 for m in measurements])
                    predictions.append(pred_risk)
                    targets.append(target)

                # MSE loss
                loss = np.mean([(p - t)**2 for p, t in zip(predictions, targets)])
                return loss

            # Optimization step
            self.weights = opt.step(cost_fn, self.weights)

            # Validation every 10 epochs
            if epoch % 10 == 0:
                train_loss = cost_fn(self.weights)
                test_accuracy = self._evaluate_accuracy(X_test, y_test)

                log.info(f"Epoch {epoch}: train_loss={train_loss:.4f}, test_acc={test_accuracy:.3f}")

                # Early stopping
                if test_accuracy > best_accuracy:
                    best_accuracy = test_accuracy
                    no_improve_count = 0
                else:
                    no_improve_count += 1

                if no_improve_count >= patience:
                    log.info(f"Early stopping at epoch {epoch}")
                    break

        self.is_trained = True

        # Final evaluation
        final_accuracy = self._evaluate_accuracy(X_test, y_test)
        train_accuracy = self._evaluate_accuracy(X_train, y_train)

        metrics = {
            "train_accuracy": train_accuracy,
            "test_accuracy": final_accuracy,
            "epochs_trained": epoch + 1,
            "best_accuracy": best_accuracy
        }

        log.info(f"✅ Training complete: {final_accuracy:.3f} accuracy")

        if final_accuracy < 0.65:
            log.warning(f"Accuracy {final_accuracy:.3f} < 0.65 target")

        return metrics

    def save_weights(self, metadata: Dict[str, Any] = None):
        """Save VQC weights to JSON file"""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")

        self.weights_file.parent.mkdir(parents=True, exist_ok=True)

        weight_data = {
            "weights": self.weights.tolist(),
            "n_qubits": self.n_qubits,
            "n_layers": self.n_layers,
            "n_pca_dims": self.n_pca_dims,
            "pca_components": self.pca.components_.tolist(),
            "pca_mean": self.pca.mean_.tolist(),
            "scaler_mean": self.scaler.mean_.tolist(),
            "scaler_scale": self.scaler.scale_.tolist(),
            "metadata": metadata or {},
            "saved_at": time.time()
        }

        with open(self.weights_file, 'w') as f:
            json.dump(weight_data, f, indent=2)

        log.info(f"💾 Weights saved to {self.weights_file}")

    def _load_weights(self):
        """Load VQC weights from JSON file"""
        if not self.weights_file.exists():
            raise FileNotFoundError(f"Weight file not found: {self.weights_file}")

        with open(self.weights_file) as f:
            data = json.load(f)

        self.weights = np.array(data["weights"])

        # Restore PCA and scaler
        self.pca.components_ = np.array(data["pca_components"])
        self.pca.mean_ = np.array(data["pca_mean"])
        self.pca.n_features_in_ = len(data["pca_mean"])

        self.scaler.mean_ = np.array(data["scaler_mean"])
        self.scaler.scale_ = np.array(data["scaler_scale"])
        self.scaler.n_features_in_ = len(data["scaler_mean"])

        self.is_trained = True
        log.info("✅ Weights loaded successfully")

    def _dict_to_feature_array(self, feature_dict: Dict[str, Any]) -> np.ndarray:
        """Convert feature dictionary to numpy array"""
        feature_order = [
            "temperature_c", "wind_kmh", "precipitation_mm", "grid_load_pct",
            "grid_outage_nodes", "water_pressure_bar", "water_treatment_pct",
            "hospital_bed_pct", "ambulance_available", "telecom_uptime_pct"
        ]

        features = np.array([feature_dict[key] for key in feature_order])
        return features

    def _prepare_training_data(self, training_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare X, y arrays from training data"""
        X = []
        y = []

        for sample in training_data:
            features = self._dict_to_feature_array(sample)
            target = sample["cascade_risk"]

            X.append(features)
            y.append(target)

        return np.array(X), np.array(y)

    def _evaluate_accuracy(self, X: np.ndarray, y: np.ndarray) -> float:
        """Evaluate model accuracy on test set"""
        if len(X) == 0:
            return 0.0

        X_scaled = self.scaler.transform(X)
        X_pca = self.pca.transform(X_scaled)

        correct = 0
        total = len(X)

        for features, target in zip(X_pca, y):
            angles = np.clip(features, 0, np.pi)
            measurements = self.circuit(angles, self.weights)

            # Convert to prediction
            pred_risk = np.mean([(m + 1) / 2 for m in measurements])

            # Binary classification: >0.5 = high risk
            pred_class = 1 if pred_risk > 0.5 else 0
            true_class = 1 if target > 0.5 else 0

            if pred_class == true_class:
                correct += 1

        return correct / total

class CascadeAnalyzer:
    """Cascade propagation analyzer per ADR-0007"""

    def __init__(self):
        """Initialize cascade graph per ADR-0007 locked specification"""
        self.cascade_graph = self._build_cascade_graph()
        self.risk_scorer = CascadeRiskScorer()

    def _build_cascade_graph(self) -> nx.DiGraph:
        """Build cascade graph with exact ADR-0007 edge weights (locked)"""
        G = nx.DiGraph()

        # Add domain nodes
        domains = ["climate", "power_grid", "water", "medical", "telecom"]
        G.add_nodes_from(domains)

        # Add edges with exact weights from ADR-0007 (DO NOT CHANGE)
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

        # Add transport node (referenced in edges)
        if "transport" not in G.nodes:
            G.add_node("transport")

        return G

    def analyze(self, feature_dict: Dict[str, Any]) -> CascadeAnalysis:
        """
        Complete cascade analysis combining VQC + graph propagation.
        Returns comprehensive risk assessment.
        """
        start_time = time.time()

        # Step 1: Get base domain risks from VQC
        domain_risks = self.risk_scorer.predict_domain_risks(feature_dict)

        # Step 2: Determine primary failure domain
        primary_domain = max(domain_risks.items(), key=lambda x: x[1])[0]
        primary_risk = domain_risks[primary_domain]

        # Step 3: BFS cascade propagation per ADR-0007
        propagated_risks, propagation_chain, timeline = self._simulate_cascade_bfs(
            primary_domain, primary_risk, domain_risks
        )

        # Step 4: Overall risk assessment
        overall_risk = max(propagated_risks.values())

        # Step 5: Determine cascade type heuristically
        cascade_type = self._classify_cascade_type(feature_dict, primary_domain)

        # Step 6: Calculate confidence
        confidence = self._calculate_confidence(propagated_risks, primary_risk)

        analysis_time = time.time() - start_time

        if analysis_time > 15.0:
            log.warning(f"Analysis time {analysis_time:.2f}s > 15s target")

        result = CascadeAnalysis(
            cascade_type=cascade_type,
            overall_risk=overall_risk,
            domain_risks=propagated_risks,
            propagation_chain=propagation_chain,
            timeline_minutes=timeline,
            confidence=confidence
        )

        log.debug(f"Cascade analysis completed in {analysis_time:.3f}s")
        return result

    def _simulate_cascade_bfs(self, initial_domain: str, initial_risk: float,
                            base_risks: Dict[str, float]) -> Tuple[Dict[str, float], List[str], List[int]]:
        """BFS cascade propagation per ADR-0007"""
        propagated = base_risks.copy()
        propagated[initial_domain] = max(initial_risk, base_risks[initial_domain])

        propagation_chain = [initial_domain]
        timeline = [0]  # Initial domain at t=0
        queue = [(initial_domain, initial_risk, 0)]  # (domain, risk, time)

        visited = set([initial_domain])

        while queue:
            current_domain, current_risk, current_time = queue.pop(0)

            # Check neighbors in cascade graph
            if current_domain in self.cascade_graph:
                for neighbor in self.cascade_graph.neighbors(current_domain):
                    if neighbor in propagated:  # Only consider core domains
                        edge_data = self.cascade_graph[current_domain][neighbor]
                        prop_prob = edge_data["prob"]
                        lag_minutes = edge_data["lag_minutes"]

                        # Calculate propagated risk
                        propagated_risk = current_risk * prop_prob

                        # Update if higher than existing (cascades can amplify)
                        if propagated_risk > propagated[neighbor]:
                            propagated[neighbor] = min(1.0, propagated_risk)  # Cap at 1.0

                            # Add to chain if significant and not visited
                            if neighbor not in visited and propagated_risk > 0.2:
                                propagation_chain.append(neighbor)
                                timeline.append(current_time + lag_minutes)
                                queue.append((neighbor, propagated_risk, current_time + lag_minutes))
                                visited.add(neighbor)

        return propagated, propagation_chain, timeline

    def _classify_cascade_type(self, features: Dict[str, Any], primary_domain: str) -> str:
        """Heuristic cascade type classification"""
        temp = features.get("temperature_c", 25)
        wind = features.get("wind_kmh", 10)
        precip = features.get("precipitation_mm", 0)

        if precip > 100 or primary_domain == "water":
            return "flood_grid"
        elif temp > 40 or primary_domain == "medical":
            return "heat_hospital"
        elif wind > 60 or primary_domain == "telecom":
            return "cyclone_comms"
        else:
            return "mixed_cascade"

    def _calculate_confidence(self, risks: Dict[str, float], primary_risk: float) -> float:
        """Calculate confidence score based on risk distribution"""
        # Higher confidence when:
        # 1. Primary risk is clear (not borderline)
        # 2. Risk distribution is consistent
        # 3. Cascade propagation is logical

        risk_values = list(risks.values())
        risk_std = np.std(risk_values)
        risk_mean = np.mean(risk_values)

        # Primary risk clarity (avoid 0.5 borderline)
        primary_clarity = abs(primary_risk - 0.5) * 2

        # Risk consistency (lower std = higher confidence)
        consistency_score = max(0, 1 - risk_std)

        # Overall confidence
        confidence = (primary_clarity + consistency_score) / 2

        return min(1.0, confidence)