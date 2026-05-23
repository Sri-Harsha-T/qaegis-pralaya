"""
Cascade dependency graph — edge weights LOCKED by ADR-0007.
Do NOT change weights without a new ADR.
"""
import networkx as nx

# Domain order matches VQC qubit assignment
DOMAINS = ["climate", "power_grid", "water", "medical", "telecom", "transport"]

QUBIT_DOMAIN_MAP = {
    0: "climate",
    1: "power_grid",
    2: "water",
    3: "medical",
    4: "telecom",
}


def build_cascade_graph() -> nx.DiGraph:
    G = nx.DiGraph()
    G.add_nodes_from(DOMAINS)

    # (source, target, propagation_probability, lag_minutes)
    edges = [
        ("climate",    "power_grid", 0.75, 30),
        ("climate",    "water",      0.50, 60),
        ("climate",    "transport",  0.60, 15),
        ("power_grid", "medical",    0.90,  5),
        ("power_grid", "water",      0.80, 20),
        ("power_grid", "telecom",    0.70, 10),
        ("water",      "medical",    0.65, 120),
        ("telecom",    "medical",    0.40, 45),
        ("transport",  "medical",    0.55, 30),
    ]
    for src, dst, weight, lag in edges:
        G.add_edge(src, dst, weight=weight, lag_minutes=lag)

    return G
