import random
import json

class SimulatedNodeLocalization:
    """
    FUTURE EXTENSION: Software simulation of distributed nodes (e.g., for TDOA or multi-sensor grids).
    Disclaimer: This is a software simulation to demonstrate modular logic. 
    It does NOT represent real-world acoustic/RF localization algorithms.
    """
    
    def __init__(self, node_names=["Node A", "Node B", "Node C"]):
        self.nodes = node_names
        print(f"Initialized Distributed Node Simulation with nodes: {self.nodes}")

    def simulate_node_reception(self) -> dict:
        """
        Simulates an event being picked up by multiple distinct nodes.
        Each node reports a different confidence/signal strength.
        """
        receptions = {}
        for node in self.nodes:
            # Simulate a signal reception confidence percentage (0 to 100)
            receptions[node] = round(random.uniform(40.0, 99.0), 1)
        
        return receptions

    def select_most_probable_zone(self, node_receptions: dict) -> str:
        """
        Identifies the node with the highest confidence/signal strength.
        The system selects this as the 'MOST PROBABLE ZONE'.
        """
        # Find the node with the max value
        best_node = max(node_receptions, key=node_receptions.get)
        best_score = node_receptions[best_node]
        
        return best_node

    def run_simulation(self):
        """
        Runs a complete end-to-end node simulation sequence.
        """
        print("\n--- INITIATING DISTRIBUTED NODE SIMULATION ---")
        
        # 1. Simulate an event occurring and hitting all nodes
        data = self.simulate_node_reception()
        
        print("Received Signal Confidences:")
        for node, score in data.items():
            print(f"{node} = {score}%")
            
        # 2. Select the most probable zone
        best_zone = self.select_most_probable_zone(data)
        
        print(f"\n>> MOST PROBABLE ZONE = {best_zone.upper()} <<")
        print("----------------------------------------------\n")
        
        return best_zone

if __name__ == "__main__":
    estimator = SimulatedNodeLocalization()
    estimator.run_simulation()
