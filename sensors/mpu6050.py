import os
import random
import math

class MPU6050:
    def __init__(self, mode="SIMULATION"):
        self.mode = os.getenv("SENSOR_MODE", mode).upper()
        self.impact_threshold = 2.5 # Acceleration in Gs that triggers an impact
        print(f"Initializing MPU6050 (IMU) in {self.mode} mode.")

    def read_imu(self) -> dict:
        """
        Returns raw accelerometer (g) and gyroscope (deg/s) data.
        """
        if self.mode == "SIMULATION":
            # Simulate sitting still at 1G (gravity on Z axis roughly)
            accel_x = random.uniform(-0.05, 0.05)
            accel_y = random.uniform(-0.05, 0.05)
            accel_z = random.uniform(0.95, 1.05)
            
            gyro_x = random.uniform(-1.0, 1.0)
            gyro_y = random.uniform(-1.0, 1.0)
            gyro_z = random.uniform(-1.0, 1.0)
            
            return {
                "accel": {"x": accel_x, "y": accel_y, "z": accel_z},
                "gyro": {"x": gyro_x, "y": gyro_y, "z": gyro_z}
            }
        else:
            # REAL HARDWARE logic goes here later (e.g. using smbus/i2c)
            raise NotImplementedError("Real hardware MPU6050 logic not implemented yet.")

    def calculate_magnitude(self, accel_data: dict) -> float:
        """
        Calculates the overall acceleration magnitude: sqrt(x^2 + y^2 + z^2).
        Resting state is ~1.0 G.
        """
        x, y, z = accel_data["x"], accel_data["y"], accel_data["z"]
        return math.sqrt(x**2 + y**2 + z**2)

    def detect_impact(self) -> bool:
        """
        Reads IMU, calculates magnitude, and checks if it exceeds the impact threshold.
        Useful for detecting accidents/crashes.
        """
        imu_data = self.read_imu()
        magnitude = self.calculate_magnitude(imu_data["accel"])
        return magnitude > self.impact_threshold

if __name__ == "__main__":
    sensor = MPU6050("SIMULATION")
    data = sensor.read_imu()
    mag = sensor.calculate_magnitude(data["accel"])
    impact = sensor.detect_impact()
    
    print(f"Raw Data: {data}")
    print(f"Acceleration Magnitude: {mag:.2f} G")
    print(f"Impact Detected: {impact}")
