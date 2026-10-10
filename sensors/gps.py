import os
import random

class GPS:
    def __init__(self, mode="SIMULATION"):
        self.mode = os.getenv("SENSOR_MODE", mode).upper()
        # Default Chennai coordinates
        self.base_lat = 13.0827
        self.base_lon = 80.2707
        print(f"Initializing GPS module in {self.mode} mode.")

    def read_gps(self) -> dict:
        """
        Returns latitude and longitude coordinates.
        """
        if self.mode == "SIMULATION":
            # Simulate slight GPS drift or movement around Chennai
            lat = self.base_lat + random.uniform(-0.01, 0.01)
            lon = self.base_lon + random.uniform(-0.01, 0.01)
            return {
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
                "satellites": random.randint(4, 12)
            }
        else:
            # REAL HARDWARE logic goes here later (e.g. reading from /dev/ttyS0 via serial)
            raise NotImplementedError("Real hardware GPS logic not implemented yet.")

if __name__ == "__main__":
    sensor = GPS("SIMULATION")
    coords = sensor.read_gps()
    print(f"GPS Coordinates: Lat {coords['latitude']}, Lon {coords['longitude']} (Sats: {coords['satellites']})")
