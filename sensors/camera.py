import os
import random

class Camera:
    def __init__(self, mode="SIMULATION"):
        self.mode = os.getenv("SENSOR_MODE", mode).upper()
        print(f"Initializing Camera in {self.mode} mode.")

    def capture_frame(self) -> str:
        """
        Captures a single image frame and returns the filepath.
        """
        if self.mode == "SIMULATION":
            # Simulate a camera capture delay
            print("Simulating camera frame capture...")
            return "simulated_frame.jpg"
        else:
            # REAL HARDWARE logic goes here (e.g. using cv2.VideoCapture(0) or PiCamera)
            raise NotImplementedError("Real hardware Camera logic not implemented yet.")
            
    def analyze_frame(self) -> dict:
        """
        Captures a frame and automatically calls the Vision AI module.
        """
        filepath = self.capture_frame()
        
        if self.mode == "SIMULATION":
            # Simulate calling the YOLO11 Vision AI module
            # Randomly return one of the detection targets
            events = ["CLEAR", "VEHICLE_DETECTED", "ACCIDENT", "ROAD_OBSTACLE", "FIRE", "SMOKE"]
            # Weight 'CLEAR' heavily for realistic simulation
            simulated_event = random.choices(events, weights=[0.75, 0.1, 0.05, 0.05, 0.025, 0.025])[0]
            confidence = round(random.uniform(50.0, 99.9), 2)
            
            return {
                "file": filepath,
                "detected_event": simulated_event,
                "confidence": confidence,
                "model": "YOLO11",
                "bounding_boxes": [] if simulated_event == "CLEAR" else [{"x": 100, "y": 100, "w": 50, "h": 50}]
            }
        else:
            # REAL HARDWARE: Capture frame, run through ultralytics YOLO11 model.
            try:
                from ultralytics import YOLO
                # Load YOLO11 nano model for Edge AI performance
                model = YOLO("yolo11n.pt")
                results = model(filepath)
                # Parse results
                boxes = results[0].boxes
                
                # In a real scenario, map YOLO COCO classes to our events
                return {
                    "file": filepath,
                    "detected_event": "VEHICLE_DETECTED" if len(boxes) > 0 else "CLEAR",
                    "confidence": round(float(boxes[0].conf[0]) * 100, 2) if len(boxes) > 0 else 0.0,
                    "model": "YOLO11",
                    "bounding_boxes": [{"x": int(b.xywh[0][0]), "y": int(b.xywh[0][1]), "w": int(b.xywh[0][2]), "h": int(b.xywh[0][3])} for b in boxes]
                }
            except ImportError:
                print("[ERROR] ultralytics package not installed. Run: pip install ultralytics")
                return {"error": "Missing YOLO11 dependencies"}

if __name__ == "__main__":
    sensor = Camera("SIMULATION")
    result = sensor.analyze_frame()
    print(f"Vision AI Result: {result}")
