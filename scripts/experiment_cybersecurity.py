import os
import time
import json
import hmac
import hashlib
import numpy as np
import pandas as pd
from uuid import uuid4
import warnings
warnings.filterwarnings('ignore')

from backend.app.core.reproducibility import set_global_seed, get_logger

logger = get_logger("Cybersecurity_Harness")

# --- 1. SIMULATED BROKER & DEFENCE PIPELINE ---
SECRET_KEY = b"simulated_local_key_only_123"
NONCE_CACHE = set()

def generate_hmac(payload_dict):
    msg = f"{payload_dict['sensor_id']}_{payload_dict['value']}_{payload_dict['timestamp']}_{payload_dict['nonce']}".encode()
    return hmac.new(SECRET_KEY, msg, hashlib.sha256).hexdigest()

class LocalMessageBus:
    """Simulates a local MQTT broker to prevent external network calls."""
    def __init__(self):
        self.acls = {"S1": "telemetry/rain", "S2": "telemetry/water_level"}
        
    def publish(self, topic, message, client_id, auth_token):
        if auth_token != "valid_token":
            return "REJECTED_AUTH"
        if self.acls.get(client_id) != topic:
            return "REJECTED_ACL"
        return "ACCEPTED"

class DefenseProcessor:
    def __init__(self):
        self.plausibility_bounds = {"telemetry/rain": (0.0, 500.0)}
        
    def process_message(self, topic, raw_payload, current_time):
        start = time.time()
        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError:
            return "QUARANTINE_CORRUPTED", (time.time() - start) * 1000
            
        # 1. HMAC check
        provided_hmac = payload.get("hmac", "")
        expected_hmac = generate_hmac(payload)
        if not hmac.compare_digest(provided_hmac, expected_hmac):
            return "QUARANTINE_HMAC_FAIL", (time.time() - start) * 1000
            
        # 2. Replay Check (Freshness + Nonce)
        if current_time - payload.get("timestamp", 0) > 60:
            return "QUARANTINE_STALE_TIMESTAMP", (time.time() - start) * 1000
        if payload.get("nonce") in NONCE_CACHE:
            return "QUARANTINE_REPLAYED_NONCE", (time.time() - start) * 1000
        NONCE_CACHE.add(payload.get("nonce"))
        
        # 3. Plausibility Check
        val = float(payload.get("value", -1))
        bounds = self.plausibility_bounds.get(topic, (0.0, 1000.0))
        if not (bounds[0] <= val <= bounds[1]):
            return "QUARANTINE_IMPLAUSIBLE", (time.time() - start) * 1000
            
        return "VALID", (time.time() - start) * 1000

# --- 2. ATTACK SIMULATIONS ---
def create_valid_message():
    ts = int(time.time())
    nonce = str(uuid4())
    msg = {"sensor_id": "S1", "value": np.random.uniform(10, 50), "timestamp": ts, "nonce": nonce}
    msg["hmac"] = generate_hmac(msg)
    return msg

def simulate_harness():
    broker = LocalMessageBus()
    processor = DefenseProcessor()
    
    results = []
    
    # 1. Clean Messages (Measure False Quarantine)
    clean_count = 1000
    false_quarantines = 0
    total_latency = 0.0
    for _ in range(clean_count):
        msg = create_valid_message()
        status = broker.publish("telemetry/rain", json.dumps(msg), "S1", "valid_token")
        if status == "ACCEPTED":
            state, lat = processor.process_message("telemetry/rain", json.dumps(msg), int(time.time()))
            total_latency += lat
            if state != "VALID":
                false_quarantines += 1
                
    results.append({"Scenario": "Clean Traffic", "Detection_Rate": "N/A", "False_Quarantine_Rate": false_quarantines/clean_count, "Bypass_Triggered_Hazard": "N/A", "Added_Latency_ms": total_latency/clean_count})
    
    # 2. Attacks
    attacks = [
        {"name": "Spoofed Value", "auth": "valid_token", "topic": "telemetry/rain", "mutator": lambda m: {**m, "value": 999.0}}, # HMAC will fail
        {"name": "Replay Attack", "auth": "valid_token", "topic": "telemetry/rain", "mutator": lambda m: m}, # Sends exact same message twice
        {"name": "Corrupted JSON", "auth": "valid_token", "topic": "telemetry/rain", "mutator": lambda m: "{bad_json: True"},
        {"name": "Invalid Auth", "auth": "bad_token", "topic": "telemetry/rain", "mutator": lambda m: m},
        {"name": "Topic Misuse", "auth": "valid_token", "topic": "telemetry/water_level", "mutator": lambda m: m}, # S1 is not authorized for water_level
        {"name": "Stolen Key / Implausible Value", "auth": "valid_token", "topic": "telemetry/rain", "mutator": "stealth_implausible"} 
    ]
    
    for att in attacks:
        detected_count = 0
        bypassed_causing_hazard = 0
        n_trials = 200
        
        for _ in range(n_trials):
            base_msg = create_valid_message()
            
            if att["mutator"] == "stealth_implausible":
                # Attacker stole key, creates perfectly signed message but physically impossible value to trigger flood warning
                base_msg["value"] = 10000.0
                base_msg["hmac"] = generate_hmac(base_msg)
                payload_str = json.dumps(base_msg)
            elif att["name"] == "Corrupted JSON":
                payload_str = att["mutator"](base_msg)
            elif att["name"] == "Replay Attack":
                # First pass it goes through
                _ = processor.process_message(att["topic"], json.dumps(base_msg), int(time.time()))
                payload_str = json.dumps(base_msg)
            else:
                mutated = att["mutator"](base_msg)
                payload_str = json.dumps(mutated)
                
            broker_status = broker.publish(att["topic"], payload_str, "S1", att["auth"])
            
            if broker_status != "ACCEPTED":
                detected_count += 1
            else:
                proc_status, _ = processor.process_message(att["topic"], payload_str, int(time.time()))
                if proc_status != "VALID":
                    detected_count += 1
                else:
                    # Bypassed! Check if it causes hazard (Value > 150.0)
                    if att["name"] != "Corrupted JSON":
                        val = json.loads(payload_str).get("value", 0)
                        if val > 150.0:
                            bypassed_causing_hazard += 1
                            
        results.append({
            "Scenario": att["name"],
            "Detection_Rate": detected_count / n_trials,
            "False_Quarantine_Rate": "N/A",
            "Bypass_Triggered_Hazard": (bypassed_causing_hazard > 0),
            "Added_Latency_ms": "N/A"
        })
        
    return pd.DataFrame(results)

def main():
    logger.info("Starting Local Non-Destructive Security Test Harness...")
    set_global_seed(42)
    
    df = simulate_harness()
    
    out_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\results"
    df.to_csv(os.path.join(out_dir, "cybersecurity_metrics.csv"), index=False)
    
    logger.info("\n=== CYBERSECURITY ROBUSTNESS ===")
    logger.info("\n" + df.to_string(index=False))

if __name__ == "__main__":
    main()
