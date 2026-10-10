import os
import pandas as pd
from backend.app.core.learned_cascade import BayesianCascadeEngine
from backend.app.core.reproducibility import set_global_seed, get_logger

logger = get_logger("Cascade_Experiments")

def generate_synthetic_history():
    """Generates synthetic historical records to simulate learning from data."""
    # Parent failure count
    parent_fails = {
        "Substation_North": 50,
        "PumpStation_A": 30,
        "Main_Drain_1": 40
    }
    # Propagation failure count (k times child failed after parent)
    prop_fails = {
        ("Substation_North", "PumpStation_A"): 45,  # 90% true prop (Expert guessed 50%)
        ("PumpStation_A", "Road_Sector_4"): 28,     # 93% true prop (Expert guessed 80%)
        ("Main_Drain_1", "Road_Sector_4"): 10       # 25% true prop (Expert guessed 60%)
    }
    return parent_fails, prop_fails

def main():
    logger.info("Starting Bayesian Cascade Engine Experiments...")
    set_global_seed(42)
    
    # 1. Define Network (Expert Priors)
    nodes_def = [
        {"id": "Substation_North", "capacity": 100, "base_load": 50, "recovery_rate": 0.2},
        {"id": "PumpStation_A", "capacity": 100, "base_load": 40, "recovery_rate": 0.3},
        {"id": "Main_Drain_1", "capacity": 100, "base_load": 80, "recovery_rate": 0.1},
        {"id": "Road_Sector_4", "capacity": 100, "base_load": 20, "recovery_rate": 0.5}
    ]
    
    edges_def = [
        {"source": "Substation_North", "target": "PumpStation_A", "prior_p": 0.5, "delay_rate": 1.0, "load_impact": 0.0},
        {"source": "PumpStation_A", "target": "Road_Sector_4", "prior_p": 0.8, "delay_rate": 0.5, "load_impact": 50.0},
        {"source": "Main_Drain_1", "target": "Road_Sector_4", "prior_p": 0.6, "delay_rate": 0.2, "load_impact": 40.0}
    ]
    
    engine = BayesianCascadeEngine(edges_def, nodes_def, expert_confidence=10.0)
    
    # 2. Learn from Data
    parent_fails, prop_fails = generate_synthetic_history()
    engine.learn_from_history(parent_fails, prop_fails)
    
    # Log learned coefficients
    coeff_data = []
    for u, v in engine.G.edges():
        coeff_data.append({
            "Edge": f"{u}->{v}",
            "Expert_Prior": f"{engine.get_edge_prob(u, v, use_expert=True):.2f}",
            "Learned_Posterior": f"{engine.get_edge_prob(u, v, use_expert=False):.2f}"
        })
    df_coeffs = pd.DataFrame(coeff_data)
    logger.info("\n=== COEFFICIENT UPDATES ===")
    logger.info("\n" + df_coeffs.to_string(index=False))

    # 3. Monte Carlo Ablation Experiments
    initial_failures = ["Substation_North"] # Substation fails at t=0
    steps = 20
    n_mc = 2000
    
    nodes = list(engine.G.nodes())
    
    res_indep = engine.simulate_mc(initial_failures, steps, n_mc, independent=True)
    res_expert = engine.simulate_mc(initial_failures, steps, n_mc, use_expert=True, independent=False)
    res_learned = engine.simulate_mc(initial_failures, steps, n_mc, use_expert=False, independent=False)
    
    results = []
    for i, n in enumerate(nodes):
        results.append({
            "Node": n,
            "Independent_Model": res_indep[i],
            "Expert_Cascade": res_expert[i],
            "Learned_Cascade": res_learned[i]
        })
        
    df_res = pd.DataFrame(results)
    logger.info("\n=== MONTE CARLO FAILURE PROBABILITIES (t=20) ===")
    logger.info("\n" + df_res.to_string(index=False))
    
    # 4. Sensitivity Analysis
    logger.info("\n=== SENSITIVITY ANALYSIS (Target: Road_Sector_4) ===")
    df_sens = engine.sensitivity_analysis(initial_failures, target_node="Road_Sector_4", delta=0.2, steps=20, n_mc=2000)
    logger.info("\n" + df_sens.to_string(index=False))
    
    # Save to docs
    out_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\docs"
    df_coeffs.to_csv(os.path.join(out_dir, "cascade_coefficients.csv"), index=False)
    df_res.to_csv(os.path.join(out_dir, "cascade_mc_results.csv"), index=False)
    df_sens.to_csv(os.path.join(out_dir, "cascade_sensitivity.csv"), index=False)
    
if __name__ == "__main__":
    main()
