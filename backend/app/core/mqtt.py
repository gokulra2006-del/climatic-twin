import json
import logging
from typing import Dict, Any

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False

logger = logging.getLogger(__name__)

# In-memory store for assimilated state
assimilated_state: Dict[str, float] = {}

# Simple Kalman-filter inspired weighting (prototype assimilation)
ALPHA = 0.6  # 60% trust in new sensor reading, 40% in previous state

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to MQTT broker")
        client.subscribe("climatetwin/sensors/+/reading")
    else:
        logger.warning(f"Failed to connect to MQTT broker, return code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        topic_parts = msg.topic.split('/')
        if len(topic_parts) >= 3:
            station_id = topic_parts[2]
            
        # Example payload: {"temperature_c": 35.5, "rainfall_mm": 12.0}
        for key, value in payload.items():
            if isinstance(value, (int, float)):
                state_key = f"{station_id}_{key}"
                if state_key in assimilated_state:
                    # Prototype weighted state assimilation
                    assimilated_state[state_key] = (ALPHA * float(value)) + ((1.0 - ALPHA) * assimilated_state[state_key])
                else:
                    assimilated_state[state_key] = float(value)
                    
        logger.debug(f"Assimilated state updated: {assimilated_state}")
    except json.JSONDecodeError:
        logger.error(f"Failed to decode MQTT message from topic {msg.topic}")
    except Exception as e:
        logger.error(f"MQTT message processing error: {e}")

def start_mqtt_client(broker_url: str = "localhost", port: int = 1883):
    if not MQTT_AVAILABLE:
        logger.warning("paho-mqtt not installed, skipping MQTT initialization")
        return None
        
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(broker_url, port, 60)
        client.loop_start()
        logger.info(f"MQTT client started, connecting to {broker_url}:{port}")
        return client
    except Exception as e:
        logger.warning(f"Could not connect to MQTT broker at {broker_url}:{port}: {e}")
        return None
