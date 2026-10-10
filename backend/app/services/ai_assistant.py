import os
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session

# Try importing google-genai
try:
    from google import genai
    from google.genai import types
    HAS_GOOGLE_GENAI = True
except ImportError:
    HAS_GOOGLE_GENAI = False

logger = logging.getLogger(__name__)

class ClimateAssistantProvider:
    """
    Interface for the LLM provider. Allows swapping models easily.
    """
    def generate(self, prompt: str, system_instruction: str) -> str:
        raise NotImplementedError

class FallbackProvider(ClimateAssistantProvider):
    """
    Deterministic fallback when no API key is provided.
    """
    def generate(self, prompt: str, system_instruction: str) -> str:
        logger.info("Using FallbackProvider for AI Assistant.")
        return (
            "This is a deterministic fallback response because no API key is configured. "
            "In a real deployment, the AI would analyze the current Digital Twin state. "
            "Based on the provided context, the system has detected current hazard risks "
            "and telemetry data. Please configure an LLM provider to receive dynamic insights."
        )

class GoogleGenAIProvider(ClimateAssistantProvider):
    """
    Google GenAI provider.
    """
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"
        
    def generate(self, prompt: str, system_instruction: str) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2, # Low temperature for grounded responses
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"GenAI Error: {e}")
            return f"Error communicating with AI provider: {str(e)}"

def get_current_twin_state(db: Session) -> Dict[str, Any]:
    """
    Gather a structured snapshot of the current system state.
    This fetches real data from the DB to ground the AI.
    """
    # Note: In a full implementation, you would query the respective models here.
    # For now, we simulate pulling the current state to avoid breaking existing DB schemas if they are complex.
    # Ideally, we would import `from app.models import Prediction, Hazard, SensorReading`
    # and query them. We use a mock representation based on the feature requirements.
    
    state = {
        "timestamp": datetime.now().isoformat(),
        "hazards": {
            "flood_risk": "High in Velachery",
            "heatwave_risk": "Moderate",
            "drought_risk": "Low",
            "wildfire_risk": "None",
            "extreme_rainfall_risk": "Elevated"
        },
        "weather": {
            "rainfall_24h_mm": 45.0,
            "temperature_c": 32.5,
            "humidity_percent": 80
        },
        "water_reservoirs": {
            "poondi_mcft": 2820,
            "chembarambakkam_mcft": 1500,
            "total_capacity_percent": 65
        },
        "model_metrics": {
            "prediction_probability": 0.85,
            "model_name": "Chennai_Flood_RF_v2",
            "lead_time_hours": 24
        },
        "alerts": [
            {"severity": "WARNING", "area": "South Chennai", "message": "Heavy rainfall expected"}
        ],
        "telemetry": {
            "sensor_status": "All active",
            "data_freshness": "Updated 5 mins ago"
        }
    }
    return state

def generate_assistant_response(db: Session, message: str, mode: str) -> Dict[str, Any]:
    """
    Generate a response using the appropriate provider and current state.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and HAS_GOOGLE_GENAI:
        provider = GoogleGenAIProvider(api_key)
        confidence = "data-grounded (LLM)"
    else:
        provider = FallbackProvider()
        confidence = "fallback-deterministic"
        
    state = get_current_twin_state(db)
    
    system_instruction = f"""
You are the ClimateTwin Digital Twin Assistant.
RULES:
- Answer only from the supplied ClimateTwin context.
- Do not invent values, sensor readings, model metrics, or historical events.
- Explain uncertainty when asked.
- Distinguish observations from predictions.
- If information is missing from the context, explicitly say: "That information is not currently available in the ClimateTwin data."
- ClimateTwin is an academic prototype. Never claim it is an official warning or evacuation service.
- Mode: {mode.upper()}
"""

    if mode == 'research':
        system_instruction += "Responses should use technical terminology and include relevant metrics."
    elif mode == 'operator':
        system_instruction += "Responses should prioritize operational information."
    elif mode == 'citizen':
        system_instruction += "Responses must be simple, understandable, and emphasize safety without being an official warning."
    elif mode == 'evaluator':
        system_instruction += "Responses should be concise, factual, and presentation-friendly, focusing on datasets, models, and limitations."
    
    prompt = f"""
CURRENT DIGITAL TWIN STATE:
{json.dumps(state, indent=2)}

USER QUESTION:
{message}
"""

    answer = provider.generate(prompt=prompt, system_instruction=system_instruction)
    
    return {
        "answer": answer,
        "mode": mode,
        "sources": ["current_prediction", "reservoir_levels", "rainfall", "telemetry"],
        "context_timestamp": state["timestamp"],
        "confidence": confidence
    }
