import networkx as nx
from app.core.graph_provenance import GraphProvenance


def test_graph_provenance_does_not_assume_unlabelled_edges_are_synthetic():
    graph = nx.DiGraph()
    graph.add_edge("A", "B")
    graph.add_edge("B", "C", status="REAL")
    report = GraphProvenance(graph, "test", "unit-test").get_report()
    assert report["UNVERIFIED_Edges"] == 1
    assert report["REAL_Edges"] == 1
    assert report["verified_edge_fraction"] == 0.5
