import json

config = {
  "chennai": {
    "features": ["rain", "temp", "humidity", "wind"],
    "reservoirs": ["poondi", "cholavaram", "redhills", "chembarambakkam"],
    "critical_thresholds": {"rain_mm": 150}
  },
  "mumbai": {
    "features": ["rain", "temp", "humidity", "wind"],
    "reservoirs": ["vihar", "tulsi", "tansa", "bhatsa"],
    "critical_thresholds": {"rain_mm": 200}
  }
}

with open(r'C:\Users\gokul\Desktop\PROJECTS\climatetwin\backend\app\core\city_configs.json', 'w') as f:
    json.dump(config, f)
