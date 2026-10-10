import os
import subprocess
import time
from backend.app.core.reproducibility import get_logger

logger = get_logger("Master_Pipeline")

def run_script(script_name):
    logger.info(f"========== RUNNING {script_name} ==========")
    start_time = time.time()
    
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    
    # Run the script using the current python executable
    try:
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
            check=True
        )
        duration = time.time() - start_time
        logger.info(f"SUCCESS: {script_name} completed in {duration:.2f} seconds.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"FAILED: {script_name} failed with exit code {e.returncode}.")
        logger.error(f"Error Output:\n{e.stderr}")
        return False

def main():
    logger.info("Initializing Master Research Pipeline execution...")
    
    # Ordered list of all features we've built
    scripts = [
        "experiment_event_evaluation.py",
        "experiment_drift_adaptation.py",
        "experiment_sensor_networks.py",
        "experiment_downscaling.py",
        "experiment_decision_value.py",
        "experiment_explainability.py",
        "experiment_cybersecurity.py",
        "experiment_gis_topology.py"
    ]
    
    success_count = 0
    for script in scripts:
        if run_script(script):
            success_count += 1
            
    logger.info("===========================================")
    logger.info(f"Master Pipeline Complete. {success_count}/{len(scripts)} experiments succeeded.")
    
    if success_count == len(scripts):
        logger.info("STATUS: ALL FEATURES WORKING. The platform is functionally complete.")
    else:
        logger.warning("STATUS: DEGRADED. Some experiments failed.")

if __name__ == "__main__":
    main()
