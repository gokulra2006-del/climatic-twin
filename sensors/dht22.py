import os
import random
import time

class DHT22:
    def __init__(self, mode="SIMULATION"):
        # MODE 1: SIMULATION | MODE 2: REAL_HARDWARE
        self.mode = os.getenv("SENSOR_MODE", mode).upper()
        print(f"Initializing DHT22 in {self.mode} mode.")

    def read_temperature(self) -> float:
        """Returns the temperature in Celsius."""
        if self.mode == "SIMULATION":
            # Simulate realistic Chennai temperature (e.g., 28 to 38 C)
            return round(random.uniform(28.0, 38.0), 2)
        else:
            # REAL HARDWARE logic goes here later (e.g. using Adafruit_DHT)
            raise NotImplementedError("Real hardware DHT22 logic not implemented yet.")

    def read_humidity(self) -> float:
        """Returns the relative humidity percentage."""
        if self.mode == "SIMULATION":
            # Simulate realistic humidity (e.g., 60% to 90%)
            return round(random.uniform(60.0, 90.0), 2)
        else:
            # REAL HARDWARE logic goes here later
            raise NotImplementedError("Real hardware DHT22 logic not implemented yet.")

if __name__ == "__main__":
    sensor = DHT22("SIMULATION")
    print(f"Temperature: {sensor.read_temperature()} °C")
    print(f"Humidity: {sensor.read_humidity()} %")
