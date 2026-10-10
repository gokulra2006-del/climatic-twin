import os

class TrafficLight:
    def __init__(self, mode="SIMULATION"):
        self.mode = os.getenv("ACTUATOR_MODE", mode).upper()
        self.current_color = "GREEN"

    def set_color(self, color: str):
        color = color.upper()
        if color not in ["RED", "YELLOW", "GREEN"]:
            raise ValueError(f"Invalid traffic light color: {color}")
            
        self.current_color = color
        
        if self.mode == "SIMULATION":
            print(f"[SIMULATION] Traffic Light changed to: {self.current_color}")
        else:
            # REAL HARDWARE logic (e.g. GPIO.output(RED_PIN, GPIO.HIGH))
            raise NotImplementedError("Real hardware Traffic Light logic not implemented.")

class BarrierServo:
    def __init__(self, mode="SIMULATION"):
        self.mode = os.getenv("ACTUATOR_MODE", mode).upper()
        self.current_state = "OPEN"

    def set_state(self, state: str):
        state = state.upper()
        if state not in ["OPEN", "CLOSED"]:
            raise ValueError(f"Invalid barrier state: {state}")
            
        self.current_state = state
        
        if self.mode == "SIMULATION":
            print(f"[SIMULATION] Barrier Servo is now: {self.current_state}")
        else:
            # REAL HARDWARE logic (e.g. pwm.ChangeDutyCycle(7.5))
            raise NotImplementedError("Real hardware Barrier Servo logic not implemented.")

class Buzzer:
    def __init__(self, mode="SIMULATION"):
        self.mode = os.getenv("ACTUATOR_MODE", mode).upper()
        self.current_state = "OFF"

    def set_state(self, state: str):
        state = state.upper()
        if state not in ["ON", "OFF"]:
            raise ValueError(f"Invalid buzzer state: {state}")
            
        self.current_state = state
        
        if self.mode == "SIMULATION":
            print(f"[SIMULATION] Buzzer turned: {self.current_state}")
        else:
            # REAL HARDWARE logic (e.g. GPIO.output(BUZZER_PIN, GPIO.HIGH))
            raise NotImplementedError("Real hardware Buzzer logic not implemented.")

class Display:
    def __init__(self, mode="SIMULATION"):
        self.mode = os.getenv("ACTUATOR_MODE", mode).upper()
        self.current_message = ""

    def show_message(self, message: str):
        self.current_message = message
        
        if self.mode == "SIMULATION":
            print(f"[SIMULATION] Display Screen: \"{self.current_message}\"")
        else:
            # REAL HARDWARE logic (e.g. I2C LCD lcd.message(message))
            raise NotImplementedError("Real hardware Display logic not implemented.")
