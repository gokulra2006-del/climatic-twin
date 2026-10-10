from .config import FUSION_WEIGHTS, THRESHOLDS

class SensorFusionEngine:
    def __init__(self):
        self.weights = FUSION_WEIGHTS
        self.thresholds = THRESHOLDS

    def evaluate(self, audio_data, vision_data, imu_impact: bool, smoke_level: float, temp: float) -> dict:
        """
        Takes data from all 5 sensors and calculates weighted confidence for different events.
        """
        results = []
        
        # 1. Check Accident
        results.append(self._evaluate_accident(audio_data, vision_data, imu_impact))
        
        # 2. Check Fire
        results.append(self._evaluate_fire(vision_data, smoke_level, temp))
        
        # 3. Check Emergency Vehicle
        results.append(self._evaluate_emergency(audio_data, vision_data))
        
        # 4. Check Road Obstacle
        results.append(self._evaluate_obstacle(vision_data))
        
        # Find the highest confidence event
        best_event = max(results, key=lambda x: x["confidence"])
        
        # If the highest confidence doesn't meet the minimum trigger threshold, return NORMAL
        if best_event["confidence"] < self.thresholds["fusion_confidence_trigger"]:
            return {
                "event_type": "NORMAL",
                "confidence": 100.0,
                "severity": "LOW",
                "evidence": ["All sensor readings within normal parameters."],
                "recommended_response": "Continue standard monitoring."
            }
            
        return best_event

    def _evaluate_accident(self, audio, vision, imu_impact) -> dict:
        confidence = 0.0
        evidence = []
        w = self.weights["ACCIDENT"]
        
        if imu_impact:
            confidence += w["impact_detected"] * 100
            evidence.append("MPU6050 detected physical impact (>2.5G)")
            
        if audio and audio.get("detected_event") == "CRASH":
            # Scale audio weight by the AI's internal confidence
            ai_conf = audio.get("confidence", 100) / 100.0
            confidence += (w["audio_crash"] * ai_conf) * 100
            evidence.append(f"Audio AI detected CRASH ({ai_conf*100:.1f}%)")
            
        if vision and vision.get("detected_event") == "ACCIDENT":
            ai_conf = vision.get("confidence", 100) / 100.0
            confidence += (w["vision_accident"] * ai_conf) * 100
            evidence.append(f"Vision AI detected ACCIDENT ({ai_conf*100:.1f}%)")
            
        return {
            "event_type": "ACCIDENT",
            "confidence": round(confidence, 2),
            "severity": "CRITICAL" if confidence > 70 else "MODERATE",
            "evidence": evidence,
            "recommended_response": "Dispatch ambulance and clear lane." if confidence > 70 else "Monitor for further evidence."
        }

    def _evaluate_fire(self, vision, smoke_level, temp) -> dict:
        confidence = 0.0
        evidence = []
        w = self.weights["FIRE"]
        
        if smoke_level > self.thresholds["mq2_smoke_danger"]:
            confidence += w["mq2_smoke_high"] * 100
            evidence.append(f"MQ-2 detected high gas/smoke level ({smoke_level})")
            
        if vision and vision.get("detected_event") in ["FIRE", "SMOKE"]:
            ai_conf = vision.get("confidence", 100) / 100.0
            confidence += (w["vision_fire_smoke"] * ai_conf) * 100
            evidence.append(f"Vision AI detected {vision['detected_event']} ({ai_conf*100:.1f}%)")
            
        if temp > self.thresholds["dht22_temp_danger"]:
            confidence += w["dht22_temp_high"] * 100
            evidence.append(f"DHT22 detected elevated temperature ({temp} C)")
            
        return {
            "event_type": "FIRE",
            "confidence": round(confidence, 2),
            "severity": "CRITICAL" if confidence > 75 else "MODERATE",
            "evidence": evidence,
            "recommended_response": "Dispatch fire department immediately." if confidence > 75 else "Investigate localized smoke source."
        }

    def _evaluate_emergency(self, audio, vision) -> dict:
        confidence = 0.0
        evidence = []
        w = self.weights["EMERGENCY_VEHICLE"]
        
        if audio and audio.get("detected_event") == "SIREN":
            ai_conf = audio.get("confidence", 100) / 100.0
            confidence += (w["audio_siren"] * ai_conf) * 100
            evidence.append(f"Audio AI detected SIREN ({ai_conf*100:.1f}%)")
            
        if vision and vision.get("detected_event") == "VEHICLE_DETECTED":
            ai_conf = vision.get("confidence", 100) / 100.0
            confidence += (w["vision_vehicle"] * ai_conf) * 100
            evidence.append(f"Vision AI detected VEHICLE ({ai_conf*100:.1f}%)")
            
        return {
            "event_type": "EMERGENCY_VEHICLE",
            "confidence": round(confidence, 2),
            "severity": "HIGH",
            "evidence": evidence,
            "recommended_response": "Trigger traffic light preemption (green wave)."
        }

    def _evaluate_obstacle(self, vision) -> dict:
        confidence = 0.0
        evidence = []
        w = self.weights["ROAD_OBSTACLE"]
        
        if vision and vision.get("detected_event") == "ROAD_OBSTACLE":
            ai_conf = vision.get("confidence", 100) / 100.0
            confidence += (w["vision_obstacle"] * ai_conf) * 100
            evidence.append(f"Vision AI detected ROAD OBSTACLE ({ai_conf*100:.1f}%)")
            
        return {
            "event_type": "ROAD_OBSTACLE",
            "confidence": round(confidence, 2),
            "severity": "MODERATE",
            "evidence": evidence,
            "recommended_response": "Alert approaching vehicles via V2X / digital signage."
        }
