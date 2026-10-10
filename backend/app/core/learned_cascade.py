import numpy as np
import networkx as nx
import pandas as pd
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class BayesianCascadeEngine:
    """
    Scientific Purpose: Dynamic, time-dependent causal cascade modeling.
    Upgrades fixed beta_ij to Bayesian-updated probabilities (Beta-Binomial conjugate).
    Incorporates survival analysis (Exponential delays), node capacity constraints, 
    and stochastic recovery. Evaluates via Monte Carlo (MC) simulation.
    """
    def __init__(self, edges_def: List[dict], nodes_def: List[dict], expert_confidence: float = 10.0):
        self.G = nx.DiGraph()
        
        # Initialize nodes (Capacity & Recovery dynamics)
        for nd in nodes_def:
            self.G.add_node(
                nd['id'],
                capacity=nd.get('capacity', 100.0),
                base_load=nd.get('base_load', 50.0),
                recovery_rate=nd.get('recovery_rate', 0.1) # 1/MTTR
            )
            
        # Initialize edges (Bayesian propagation & load transfer)
        for ed in edges_def:
            u, v, p_expert = ed['source'], ed['target'], ed['prior_p']
            alpha_0 = p_expert * expert_confidence
            beta_0 = (1 - p_expert) * expert_confidence
            self.G.add_edge(
                u, v,
                prior_alpha=alpha_0,
                prior_beta=beta_0,
                post_alpha=alpha_0,
                post_beta=beta_0,
                delay_rate=ed.get('delay_rate', 0.5), # Survival lambda
                load_impact=ed.get('load_impact', 20.0) # Load shifted to target if source fails
            )

    def learn_from_history(self, parent_fails: Dict[str, int], prop_fails: Dict[Tuple[str,str], int]):
        """Bayesian Update using Historical Hazard-Failure Records."""
        for u, v in self.G.edges():
            if u in parent_fails:
                n = parent_fails[u]
                k = prop_fails.get((u, v), 0)
                # Conjugate update
                self.G[u][v]['post_alpha'] += k
                self.G[u][v]['post_beta'] += (n - k)

    def get_edge_prob(self, u, v, use_expert=False):
        """Expected value of the Beta distribution."""
        if use_expert:
            a, b = self.G[u][v]['prior_alpha'], self.G[u][v]['prior_beta']
        else:
            a, b = self.G[u][v]['post_alpha'], self.G[u][v]['post_beta']
        return a / (a + b)

    def simulate_mc(self, initial_failures: List[str], steps=50, n_mc=1000, use_expert=False, independent=False):
        """
        Monte Carlo simulation of the cascade over time.
        Returns the expected failure probability of each node at the final step.
        """
        nodes = list(self.G.nodes())
        n_nodes = len(nodes)
        node_idx = {n: i for i, n in enumerate(nodes)}
        
        # State tensors: (n_mc, n_nodes)
        state = np.ones((n_mc, n_nodes)) # 1=Healthy, 0=Failed
        for f_node in initial_failures:
            state[:, node_idx[f_node]] = 0.0
            
        # Tracking cumulative metrics
        failure_counts = np.zeros(n_nodes)
        
        for step in range(steps):
            new_state = state.copy()
            
            # 1. Recovery Process (Stochastic)
            for i, n in enumerate(nodes):
                failed_mask = (state[:, i] == 0)
                recovery_prob = self.G.nodes[n]['recovery_rate']
                recovers = np.random.rand(n_mc) < recovery_prob
                new_state[failed_mask & recovers, i] = 1.0
                
            # 2. Failure Propagation (Interacting models only)
            if not independent:
                for u, v in self.G.edges():
                    u_i, v_i = node_idx[u], node_idx[v]
                    
                    # Parent is failed, Child is healthy
                    risk_mask = (state[:, u_i] == 0) & (state[:, v_i] == 1)
                    
                    # Edge probability
                    p_prop = self.get_edge_prob(u, v, use_expert)
                    # Survival delay (probability of failing in this timestep)
                    p_delay = 1.0 - np.exp(-self.G[u][v]['delay_rate'])
                    p_total = p_prop * p_delay
                    
                    fails = np.random.rand(n_mc) < p_total
                    new_state[risk_mask & fails, v_i] = 0.0
                    
            # 3. Capacity Constraints
            if not independent:
                current_loads = np.zeros((n_mc, n_nodes))
                for i, n in enumerate(nodes):
                    current_loads[:, i] = self.G.nodes[n]['base_load']
                    
                # Add shifted load from failed parents
                for u, v in self.G.edges():
                    u_i, v_i = node_idx[u], node_idx[v]
                    failed_u_mask = (new_state[:, u_i] == 0)
                    current_loads[failed_u_mask, v_i] += self.G[u][v]['load_impact']
                    
                # Fail if capacity exceeded
                for i, n in enumerate(nodes):
                    cap = self.G.nodes[n]['capacity']
                    overload = current_loads[:, i] > cap
                    new_state[overload, i] = 0.0
                    
            state = new_state
            
        return 1.0 - np.mean(state, axis=0) # Failure Probability

    def sensitivity_analysis(self, initial_failures, target_node, delta=0.1, steps=50, n_mc=1000):
        """Measures variance in target node failure prob given perturbations to learned beta_ij."""
        base_probs = self.simulate_mc(initial_failures, steps, n_mc)
        target_idx = list(self.G.nodes()).index(target_node)
        base_risk = base_probs[target_idx]
        
        sensitivities = []
        for u, v in self.G.edges():
            # Perturb +delta
            orig_alpha = self.G[u][v]['post_alpha']
            self.G[u][v]['post_alpha'] *= (1 + delta)
            up_risk = self.simulate_mc(initial_failures, steps, n_mc)[target_idx]
            
            # Perturb -delta
            self.G[u][v]['post_alpha'] = orig_alpha * (1 - delta)
            dn_risk = self.simulate_mc(initial_failures, steps, n_mc)[target_idx]
            
            # Restore
            self.G[u][v]['post_alpha'] = orig_alpha
            
            sensitivities.append({
                "Edge": f"{u}->{v}",
                "Base_Risk": base_risk,
                "+10%_Impact": up_risk - base_risk,
                "-10%_Impact": dn_risk - base_risk
            })
            
        return pd.DataFrame(sensitivities)
