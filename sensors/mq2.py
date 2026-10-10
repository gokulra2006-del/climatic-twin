import os
import random

class MQ2:
    def __init__(self, mode="SIMULATION"):
        self.mode = os.getenv("SENSOR_MODE", mode).upper()
        print(f"Initializing MQ-2 Smoke Sensor in {self.mode} mode.")

    def read_smoke(self) -> float:
        """
        Returns an abstract smoke/gas level.
        Typically, an MQ-2 returns an analog value (0-1023 on Arduino, or normalized 0.0 - 1.0).
        Here we return a normalized value where >0.6 might indicate fire/smoke.
        """
        if self.mode == "SIMULATION":
            # Simulate a normal clean air baseline (0.05 to 0.15)
            # Occasional spikes can be tested by changing this range manually
            return round(random.uniform(0.05, 0.15), 3)
        else:
            # REAL HARDWARE logic goes here later (e.g. using an ADC like ADS1115 to read analog out)
            raise NotImplementedError("Real hardware MQ-2 logic not implemented yet.")

if __name__ == "__main__":
    sensor = MQ2("SIMULATION")
    smoke_level = sensor.read_smoke()
    print(f"Smoke Level: {smoke_level}")
    if smoke_level > 0.6:
        print("WARNING: Smoke detected!")
