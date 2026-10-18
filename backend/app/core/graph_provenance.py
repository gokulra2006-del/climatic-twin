
import networkx as nx


class GraphProvenance:
    def __init__(self, graph, name, source):
        self.name = name
        self.source = source
        self.nodes = len(graph.nodes)
        self.edges = len(graph.edges)
        self.isolated = len(list(nx.isolates(graph))) if not graph.is_directed() else 0
        self.status_counts = {"REAL": 0, "SYNTHETIC": 0, "PROXY": 0, "UNVERIFIED": 0}
        for u, v, data in graph.edges(data=True):
            s = str(data.get("status", "UNVERIFIED")).upper()
            self.status_counts[s] = self.status_counts.get(s, 0) + 1
            
    def get_report(self):
        verified_fraction = self.status_counts.get("REAL", 0) / self.edges if self.edges else 0.0
        return {
            "Graph": self.name,
            "Source": self.source,
            "Nodes": self.nodes,
            "Edges": self.edges,
            "Isolated_Nodes": self.isolated,
            "REAL_Edges": self.status_counts.get("REAL", 0),
            "PROXY_Edges": self.status_counts.get("PROXY", 0),
            "SYNTHETIC_Edges": self.status_counts.get("SYNTHETIC", 0),
            "UNVERIFIED_Edges": self.status_counts.get("UNVERIFIED", 0),
            "verified_edge_fraction": round(verified_fraction, 4),
            "interpretation": "Graph-based model claims require verified dependency data; proxy, synthetic, and unverified edges must remain labelled."
        }
    
