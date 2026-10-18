import time
from sensors.fusion_engine import SensorFusionEngine
from response.response_engine import AutonomousResponseEngine
from localization.gps_location import EventLocator
from database.database import initialize_database, insert_event

# Import the actual sensor modules!
from sensors.microphone import Microphone
from sensors.camera import Camera
from sensors.mpu6050 import MPU6050
from sensors.mq2 import MQ2
from sensors.dht22 import DHT22

def main():
    print("=== INITIALIZING CLIMATETWIN EDGE AI ===")
    
    # 1. Initialize the SQLite Database
    initialize_database()
    
    # 2. Initialize the AI & Hardware Sensors (Seamlessly handles missing models)
    print("\n--- Booting Hardware & AI Sensors ---")
    mic = Microphone()
    cam = Camera()
    imu = MPU6050()
    smoke_sensor = MQ2()
    dht = DHT22()
    
    # 3. Initialize the Engines
    fusion_engine = SensorFusionEngine()
    response_engine = AutonomousResponseEngine(mode="SIMULATION")
    locator = EventLocator(mode="SIMULATION")
    
    print("\n[SUCCESS] System Online. Monitoring live environment...\n")
    
    try:
        while True:
            # --- STEP A: REAL/SIMULATED SENSOR READINGS ---
            # This now actually calls the modules. If the AI model is trained, 
            # it will run real inference! Otherwise it simulates it cleanly.
            audio_data = mic.analyze_audio() 
            vision_data = cam.analyze_frame()
            imu_impact = imu.detect_impact()
            smoke_level = smoke_sensor.read_smoke()
            temperature = dht.read_temperature()
            
            # --- STEP B: FUSION ENGINE ---
            event = fusion_engine.evaluate(audio_data, vision_data, imu_impact, smoke_level, temperature)
            
            # --- STEP C: IF EMERGENCY DETECTED ---
            if event["event_type"] != "NORMAL":
                print(f"[ALERT] EMERGENCY DETECTED: {event['event_type']} ({event['confidence']}%)")
                print(f"Evidence: {event['evidence']}")
                
                # 1. Get GPS Location
                event = locator.attach_location(event)
                
                # 2. Trigger Actuators (Traffic lights, barrier, buzzer)
                response_engine.handle_event(event["event_type"])
                
                # 3. Save to SQLite Database
                db_payload = {
                    "event_type": event["event_type"],
                    "confidence": event["confidence"],
                    "severity": event["severity"],
                    "audio_class": audio_data["detected_event"],
                    "audio_confidence": audio_data["confidence"],
                    "vision_class": vision_data["detected_event"],
                    "vision_confidence": vision_data["confidence"],
                    "impact_detected": imu_impact,
                    "temperature": temperature,
                    "smoke_level": smoke_level,
                    "latitude": event["latitude"],
                    "longitude": event["longitude"],
                    "traffic_status": response_engine.traffic_light.current_color,
                    "barrier_status": response_engine.barrier.current_state,
                    "buzzer_status": response_engine.buzzer.current_state,
                }
                
                event_id = insert_event(db_payload)
                print(f"[SUCCESS] Event securely logged to SQLite (Event ID: {event_id})")
                print("=========================================================\n")
                
                # Sleep briefly to prevent spamming the database during a continuous event
                time.sleep(5) 
            else:
                # Normal conditions, check again rapidly
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\nShutting down ClimateTwin Edge System.")

if __name__ == "__main__":
    main()
