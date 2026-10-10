import sys
import os

# Ensure the parent directory is in the path to import actuators
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from actuators import TrafficLight, BarrierServo, Buzzer, Display

class AutonomousResponseEngine:
    def __init__(self, mode="SIMULATION"):
        print("Initializing Autonomous Response Engine...")
        self.traffic_light = TrafficLight(mode=mode)
        self.barrier = BarrierServo(mode=mode)
        self.buzzer = Buzzer(mode=mode)
        self.display = Display(mode=mode)
        print("All actuators initialized successfully.\n")

    def handle_event(self, event_type: str):
        """
        Executes hardware response rules based on the event type provided by the Sensor Fusion Engine.
        """
        print(f"--- EXECUTING AUTONOMOUS RESPONSE FOR: {event_type} ---")
        
        if event_type == "ACCIDENT":
            self.traffic_light.set_color("RED")
            self.barrier.set_state("CLOSED")
            self.buzzer.set_state("ON")
            self.display.show_message("ACCIDENT ALERT - ROAD CLOSED")
            
        elif event_type == "FIRE":
            self.traffic_light.set_color("RED")
            # Barrier state is maintained or left to default logic depending on specific fire protocol
            # We explicitly trigger the others as requested:
            self.buzzer.set_state("ON")
            self.display.show_message("FIRE ALERT - EVACUATE")
            
        elif event_type == "EMERGENCY_VEHICLE":
            self.traffic_light.set_color("GREEN")
            self.display.show_message("GREEN CORRIDOR - YIELD TO EMERGENCY VEHICLE")
            
        elif event_type == "ROAD_OBSTACLE":
            self.traffic_light.set_color("YELLOW")
            self.display.show_message("OBSTACLE WARNING - REDUCE SPEED")
            
        elif event_type == "NORMAL":
            self.traffic_light.set_color("GREEN")
            self.barrier.set_state("OPEN")
            self.buzzer.set_state("OFF")
            self.display.show_message("SYSTEM NORMAL - DRIVE SAFELY")
            
        else:
            print(f"Unknown event type: {event_type}. Defaulting to safe state.")
            self.traffic_light.set_color("YELLOW")
            
        print("-" * 55 + "\n")

if __name__ == "__main__":
    # Test all modes sequentially
    engine = AutonomousResponseEngine(mode="SIMULATION")
    
    events_to_test = [
        "NORMAL",
        "ROAD_OBSTACLE",
        "EMERGENCY_VEHICLE",
        "ACCIDENT",
        "FIRE",
        "NORMAL"
    ]
    
    for event in events_to_test:
        engine.handle_event(event)
