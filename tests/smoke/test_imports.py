"""Smoke tests — verify all modules are importable."""
import importlib, pytest

MODULES = [
    "pennylane",
    "fastapi",
    "networkx",
    "sklearn",
    "numpy",
    "pandas",
]

@pytest.mark.parametrize("module", MODULES)
def test_import(module):
    importlib.import_module(module)

def test_cascade_graph_importable():
    from backend.cascade_graph import build_cascade_graph
    G = build_cascade_graph()
    assert G.number_of_nodes() == 6
    assert G.number_of_edges() == 9

def test_cascade_graph_edge_weights():
    from backend.cascade_graph import build_cascade_graph
    G = build_cascade_graph()
    assert G["power_grid"]["medical"]["weight"] == 0.90  # highest priority edge
    assert G["power_grid"]["medical"]["lag_minutes"] == 5
