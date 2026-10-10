import unittest
import sys
import os

# Ensure the parent directory is in the path to import sensors
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sensors.fusion_engine import SensorFusionEngine

class TestSensorFusionEngine(unittest.TestCase):
    def setUp(self):
        self.engine = SensorFusionEngine()

    def test_true_accident(self):
        # Scenario: Hard physical impact + Crash Sound + Vision sees accident
        audio = {"detected_event": "CRASH", "confidence": 90.0}
        vision = {"detected_event": "ACCIDENT", "confidence": 85.0}
        imu_impact = True
        smoke = 0.1
        temp = 32.0
        
        result = self.engine.evaluate(audio, vision, imu_impact, smoke, temp)
        
        self.assertEqual(result["event_type"], "ACCIDENT")
        # Impact (50) + Audio (0.3*90 = 27) + Vision (0.2*85 = 17) = 94.0 confidence
        self.assertTrue(result["confidence"] >= 90.0)
        self.assertEqual(result["severity"], "CRITICAL")
        print("\n--- TRUE ACCIDENT ---")
        print("Evidence:", result["evidence"])

    def test_false_accident(self):
        # Scenario: Audio heard a crash, but no impact on IMU and no vision confirmation
        audio = {"detected_event": "CRASH", "confidence": 80.0}
        vision = {"detected_event": "CLEAR", "confidence": 99.0}
        imu_impact = False
        smoke = 0.1
        temp = 32.0
        
        result = self.engine.evaluate(audio, vision, imu_impact, smoke, temp)
        
        # Audio weight is 0.3 * 80 = 24.0 confidence. 
        # Threshold is 50.0, so this should return NORMAL (False alarm)
        self.assertEqual(result["event_type"], "NORMAL")
        print("\n--- FALSE ACCIDENT (False Alarm Rejected) ---")
        print("Evidence:", result["evidence"])

    def test_true_fire(self):
        # Scenario: MQ2 senses smoke + Vision sees fire + high temp
        audio = {"detected_event": "NORMAL_TRAFFIC", "confidence": 95.0}
        vision = {"detected_event": "FIRE", "confidence": 90.0}
        imu_impact = False
        smoke = 0.8  # Above 0.6 threshold
        temp = 45.0  # Above 40.0 threshold
        
        result = self.engine.evaluate(audio, vision, imu_impact, smoke, temp)
        
        self.assertEqual(result["event_type"], "FIRE")
        self.assertEqual(result["severity"], "CRITICAL")
        print("\n--- TRUE FIRE ---")
        print("Evidence:", result["evidence"])

    def test_false_fire(self):
        # Scenario: MQ2 senses some smoke (maybe exhaust/vape) but temp is normal and vision is clear
        audio = {"detected_event": "NORMAL_TRAFFIC", "confidence": 95.0}
        vision = {"detected_event": "CLEAR", "confidence": 95.0}
        imu_impact = False
        smoke = 0.65 # Barely above threshold
        temp = 30.0  # Normal temp
        
        result = self.engine.evaluate(audio, vision, imu_impact, smoke, temp)
        
        # MQ2 weight (45) is below the 50 trigger threshold by itself.
        self.assertEqual(result["event_type"], "NORMAL")
        print("\n--- FALSE FIRE (Rejected) ---")
        print("Evidence:", result["evidence"])

    def test_emergency_vehicle(self):
        # Scenario: Siren heard + Vehicle detected visually
        audio = {"detected_event": "SIREN", "confidence": 95.0}
        vision = {"detected_event": "VEHICLE_DETECTED", "confidence": 88.0}
        imu_impact = False
        smoke = 0.1
        temp = 30.0
        
        result = self.engine.evaluate(audio, vision, imu_impact, smoke, temp)
        
        self.assertEqual(result["event_type"], "EMERGENCY_VEHICLE")
        self.assertEqual(result["severity"], "HIGH")
        print("\n--- EMERGENCY VEHICLE ---")
        print("Evidence:", result["evidence"])

    def test_normal_traffic(self):
        # Scenario: Nothing unusual
        audio = {"detected_event": "NORMAL_TRAFFIC", "confidence": 99.0}
        vision = {"detected_event": "CLEAR", "confidence": 99.0}
        imu_impact = False
        smoke = 0.05
        temp = 31.0
        
        result = self.engine.evaluate(audio, vision, imu_impact, smoke, temp)
        
        self.assertEqual(result["event_type"], "NORMAL")
        print("\n--- NORMAL TRAFFIC ---")
        print("Evidence:", result["evidence"])

if __name__ == '__main__':
    unittest.main(verbosity=2)
