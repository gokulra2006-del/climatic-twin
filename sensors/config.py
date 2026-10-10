import os

# FUSION ENGINE WEIGHTS
# Configurable weights representing how much confidence each sensor provides.
# Total weights per event type should sum to 1.0 (or 100%)

FUSION_WEIGHTS = {
    "ACCIDENT": {
        "impact_detected": 0.5,      # Hard physical impact is strong evidence
        "audio_crash": 0.3,          # Crash sound is secondary evidence
        "vision_accident": 0.2       # Visual confirmation completes it
    },
    "FIRE": {
        "mq2_smoke_high": 0.45,      # Chemical detection is primary
        "vision_fire_smoke": 0.35,   # Visual confirmation is strong
        "dht22_temp_high": 0.20      # High heat supports the chemical/visual
    },
    "EMERGENCY_VEHICLE": {
        "audio_siren": 0.7,          # Sirens are the primary indicator
        "vision_vehicle": 0.3        # Visual confirmation of a vehicle
    },
    "ROAD_OBSTACLE": {
        "vision_obstacle": 1.0       # Obstacles are purely visual for now
    }
}

# THRESHOLDS
THRESHOLDS = {
    "mq2_smoke_danger": 0.6,
    "dht22_temp_danger": 40.0,
    "fusion_confidence_trigger": 50.0  # Minimum % required to declare an event
}
