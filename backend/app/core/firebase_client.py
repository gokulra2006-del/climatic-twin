import logging
import requests
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_firebase_telemetry() -> Optional[Dict[str, Any]]:
    """
    Fetches live telemetry data from Firebase Realtime Database if configured.
    Returns None if Firebase is not configured or data is unavailable.
    """
    if not settings.FIREBASE_DB_URL:
        return None
        
    try:
        # Assuming the Raspberry Pi writes to a 'telemetry' node
        url = f"{settings.FIREBASE_DB_URL.rstrip('/')}/telemetry.json"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                return data
        return None
    except Exception as e:
        logger.error(f"Error fetching from Firebase: {e}")
        return None

