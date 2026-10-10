import json
import os
import networkx as nx
from typing import Dict, List, Any

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "cascade_config.json")

class CausalCascadeEngine:
    def __init__(self, config_path: str = CONFIG_PATH):
        self.config_path = config_path
        self.graph = nx.DiGraph()
        self.metadata = {}
        self._load_config()

    def _load_config(self):
        """Loads provisional causal coupling values (beta_ij)."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Provisional causal config not found at {self.config_path}")
            
        with open(self.config_path, "r") as f:
            data = json.load(f)
            
        self.metadata = data.get("__metadata__", {})
        
        # Add nodes
        for node in data.get("base_nodes", []):
            self.graph.add_node(node)
            
        # Add edges with beta values
        for edge in data.get("edges", []):
            self.graph.add_edge(edge["source"], edge["target"], beta=edge["beta"])
            
        if not nx.is_directed_acyclic_graph(self.graph):
            raise ValueError("Causal cascade graph must be a Directed Acyclic Graph (DAG).")

    def forward_cascade(self, intrinsic_probs: Dict[str, float]) -> Dict[str, float]:
        """
        Computes the final failure probability for every node in the graph.
        Formula: P(fail_j) = 1 - (1 - P_intrinsic(j)) * Product_{i in parents(j)} (1 - beta_{ij} * P(fail_i))
        """
        final_probs = {}
        
        # Process in topological order so parents are always computed before children
        topological_order = list(nx.topological_sort(self.graph))
        
        for node in topological_order:
            p_intrinsic = intrinsic_probs.get(node, 0.0)
            
            # Gather parent propagation
            parent_survival_factor = 1.0
            for parent in self.graph.predecessors(node):
                beta = self.graph[parent][node]['beta']
                p_parent_fail = final_probs.get(parent, 0.0)
                # Survival from this specific parent's cascade
                parent_survival_factor *= (1.0 - (beta * p_parent_fail))
                
            # Node fails if it fails intrinsically OR if it fails due to a parent
            # P(Survive) = P(Survive_Intrinsic) * P(Survive_All_Cascades)
            p_survive = (1.0 - p_intrinsic) * parent_survival_factor
            final_probs[node] = 1.0 - p_survive
            
        return final_probs

    def simulate_intervention(
        self, 
        intrinsic_probs: Dict[str, float], 
        interventions: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Applies a do-operation (intervention).
        interventions: Dict mapping node name to forced probability (e.g., 'Pump_X': 0.0 means perfect resilience intervention).
        """
        # Baseline run
        baseline_probs = self.forward_cascade(intrinsic_probs)
        baseline_total_risk = sum(baseline_probs.values())
        
        # Intervention run (do-calculus)
        # We override the intrinsic probability with the forced intervention value.
        # Furthermore, if we force a node's probability, we effectively sever its dependence on its parents for that specific node's state?
        # A true do(X=x) severs incoming edges to X.
        
        intervened_probs = {}
        topological_order = list(nx.topological_sort(self.graph))
        
        for node in topological_order:
            if node in interventions:
                # do-operation: force the probability, ignore parents
                intervened_probs[node] = interventions[node]
            else:
                p_intrinsic = intrinsic_probs.get(node, 0.0)
                parent_survival_factor = 1.0
                for parent in self.graph.predecessors(node):
                    beta = self.graph[parent][node]['beta']
                    p_parent_fail = intervened_probs.get(parent, 0.0)
                    parent_survival_factor *= (1.0 - (beta * p_parent_fail))
                
                p_survive = (1.0 - p_intrinsic) * parent_survival_factor
                intervened_probs[node] = 1.0 - p_survive

        intervened_total_risk = sum(intervened_probs.values())
        
        # Calculate delta (which downstream failures are avoided)
        delta = {}
        for node in baseline_probs:
            delta[node] = intervened_probs[node] - baseline_probs[node]
            
        return {
            "metadata": self.metadata,
            "baseline_probs": baseline_probs,
            "intervened_probs": intervened_probs,
            "delta": delta,
            "net_risk_delta": intervened_total_risk - baseline_total_risk
        }

causal_engine = CausalCascadeEngine()
