"""Evidence-grounded NOVA copilot with multi-intent weather intelligence and optional OpenRouter provider.

Distinguishes current observations from future forecast probabilities and handles local micro-climate disagreements without hallucination.
"""

import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

# WMO Weather Code Descriptions
WMO_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    62: "Moderate rain",
    63: "Heavy rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def detect_weather_intent(question: str) -> str:
    """Classify user query into LOCATION_MISMATCH, FORECAST, CURRENT_OBSERVATION, or NON_WEATHER."""
    q = question.lower().strip()

    # 1. Local disagreement / mismatch
    mismatch_phrases = [
        "sunny here",
        "weather is different here",
        "different here",
        "not raining here",
        "no rain here",
        "clear here",
        "dry here",
        "sunny outside here",
        "it is sunny",
        "it's sunny",
        "it is clear",
        "it's clear",
        "not raining in my",
        "clear sky here",
        "weather different",
        "sunny right now here",
    ]
    if any(p in q for p in mismatch_phrases):
        return "LOCATION_MISMATCH"
    if ("sunny" in q or "clear" in q or "dry" in q or "no rain" in q or "not raining" in q) and any(
        w in q for w in ["here", "where i am", "but", "my location", "my area"]
    ):
        return "LOCATION_MISMATCH"

    # 2. Forecast queries
    forecast_phrases = [
        "chance of rain",
        "chance of rainfall",
        "will it rain",
        "is it going to rain",
        "going to rain",
        "rainfall in my area",
        "rain in my area",
        "in my area",
        "next 1 hour",
        "next 3 hour",
        "next 6 hour",
        "next 12 hour",
        "next 24 hour",
        "next 1h",
        "next 3h",
        "next 6h",
        "next 12h",
        "next 24h",
        "next 1 ",
        "next 3 ",
        "next 6 ",
        "next 12 ",
        "next 24 ",
        "next hour",
        "next few hours",
        "forecast",
        "will rain",
        "expecting rain",
        "upcoming rain",
        "probability of rain",
        "rain later",
        "rain tonight",
        "rain tomorrow",
        "rain today",
        "rainfall forecast",
        "expected rain",
        "chances of rain",
    ]
    if any(p in q for p in forecast_phrases):
        return "FORECAST"

    # 3. Current observation queries
    obs_phrases = [
        "weather now",
        "rainfall right now",
        "rain right now",
        "temperature now",
        "weather outside",
        "current weather",
        "current temperature",
        "current rain",
        "current precipitation",
        "is it raining now",
        "is it raining outside",
        "how is the weather",
        "what is the weather",
        "what is the temperature",
        "outside temperature",
        "weather today right now",
        "weather right now",
    ]
    if any(p in q for p in obs_phrases):
        return "CURRENT_OBSERVATION"

    # Generic weather terms if not matched as forecast/mismatch
    weather_words = ["weather", "temperature", "temp", "rain", "rainfall", "precipitation", "precip"]
    if any(w in q for w in weather_words):
        if any(fw in q for fw in ["later", "tomorrow", "tonight", "soon", "upcoming", "future", "expect"]):
            return "FORECAST"
        return "CURRENT_OBSERVATION"

    return "NON_WEATHER"


class NovaCopilot:
    endpoint = "https://openrouter.ai/api/v1/chat/completions"

    def provider_status(self) -> Dict[str, Any]:
        key_configured = bool(os.getenv("OPENROUTER_API_KEY", "").strip())
        configured = key_configured and os.getenv("NOVA_EXTERNAL_AI_ENABLED", "false").lower() in {"1", "true", "yes"}
        return {
            "configured": configured,
            "provider": "OpenRouter" if configured else "Evidence-grounded local fallback",
            "model": os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini") if configured else None,
            "key_location": "Backend environment only; never expose an API key in the browser.",
            "external_ai_opt_in": configured,
            "external_ai_ready": key_configured,
            "enablement_note": (
                "External AI is enabled by the backend operator."
                if configured
                else "Local evidence mode is active. To enable an external provider, set NOVA_EXTERNAL_AI_ENABLED=true on the backend after approving data sharing."
            ),
            "boundary": "NOVA summarises supplied telemetry and model outputs. It must not issue public warnings, infer unseen field conditions, or replace an authorised human decision.",
        }

    def _fetch_forecast_direct(self) -> Dict[str, Any]:
        """Fetch fresh hourly forecast directly from Open-Meteo if not in briefing."""
        try:
            import requests

            lat = 13.0827
            lon = 80.2707
            url = (
                f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation,weather_code"
                f"&hourly=precipitation_probability,precipitation,weather_code,temperature_2m&timezone=Asia%2FKolkata&forecast_days=2"
            )
            res = requests.get(url, timeout=8).json()
            current = res.get("current", {})
            hourly = res.get("hourly", {})
            observed_at = current.get("time", "")
            times = hourly.get("time", [])
            probs = hourly.get("precipitation_probability", [])
            precip = hourly.get("precipitation", [])
            codes = hourly.get("weather_code", [])

            curr_idx = -1
            for i, t in enumerate(times):
                if observed_at and t >= observed_at[:13]:
                    curr_idx = i
                    break

            if curr_idx != -1 and curr_idx + 1 < len(times):
                idx1 = curr_idx + 1

                def _safe_slice(arr, start, count):
                    return [x for x in arr[start : start + count] if x is not None]

                p1, p3, p6, p24 = [_safe_slice(probs, idx1, n) for n in (1, 3, 6, 24)]
                r1, r3, r6, r24 = [_safe_slice(precip, idx1, n) for n in (1, 3, 6, 24)]
                c1, c3, c6, c24 = [_safe_slice(codes, idx1, n) for n in (1, 3, 6, 24)]

                return {
                    "status": "AVAILABLE",
                    "mode": "LIVE_WEATHER_API",
                    "source": "Open-Meteo hourly forecast",
                    "forecast_generated_at": datetime.now(timezone.utc).isoformat(),
                    "forecast_start_time": times[idx1],
                    "windows": {
                        "1h": {
                            "period": "next 1 hour",
                            "precipitation_probability_pct": max(p1) if p1 else 0,
                            "expected_rainfall_mm": round(sum(r1), 2) if r1 else 0.0,
                            "weather_code": c1[0] if c1 else None,
                            "condition": WMO_WEATHER_CODES.get(c1[0], f"Code {c1[0]}") if c1 else "Unknown",
                        },
                        "3h": {
                            "period": "next 3 hours",
                            "precipitation_probability_pct": max(p3) if p3 else 0,
                            "expected_rainfall_mm": round(sum(r3), 2) if r3 else 0.0,
                            "weather_code": c3[0] if c3 else None,
                            "condition": WMO_WEATHER_CODES.get(c3[0], f"Code {c3[0]}") if c3 else "Unknown",
                        },
                        "6h": {
                            "period": "next 6 hours",
                            "precipitation_probability_pct": max(p6) if p6 else 0,
                            "expected_rainfall_mm": round(sum(r6), 2) if r6 else 0.0,
                            "weather_code": c6[0] if c6 else None,
                            "condition": WMO_WEATHER_CODES.get(c6[0], f"Code {c6[0]}") if c6 else "Unknown",
                        },
                        "24h": {
                            "period": "next 24 hours",
                            "precipitation_probability_pct": max(p24) if p24 else 0,
                            "expected_rainfall_mm": round(sum(r24), 2) if r24 else 0.0,
                        },
                    },
                    "city_scale_note": "City-scale weather forecast for central Chennai grid (lat 13.08, lon 80.27); micro-climatic distribution may vary by neighborhood or ward.",
                }
        except Exception as exc:
            logger.warning("Direct forecast fetch failed: %s", exc)

        return {"status": "UNAVAILABLE", "mode": "UNAVAILABLE"}

    def _build_current_observation(self, live_weather: Dict[str, Any], question: str) -> Dict[str, Any]:
        """Requirement 2: Return current Open-Meteo observation details."""
        mode = live_weather.get("mode")
        if mode == "UNAVAILABLE" or (live_weather.get("precipitation_mm") is None and live_weather.get("temperature_c") is None):
            return {
                "answer": "The live city weather provider is unavailable, so NOVA cannot verify current rain or temperature. Refresh the source before relying on a weather answer.",
                "intent": "CURRENT_OBSERVATION",
                "badge": "CURRENT OBSERVATION",
                "data_nature": "UNAVAILABLE",
                "source": "Open-Meteo current observation",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "citations": ["Open-Meteo current observation"],
                "safety_notice": "NOVA provides verified observation summaries only. It does not replace official meteorological bulletins.",
            }

        precip = live_weather.get("precipitation_mm")
        temp = live_weather.get("temperature_c")
        weather_code = live_weather.get("weather_code")
        condition_name = WMO_WEATHER_CODES.get(weather_code, f"Code {weather_code}") if weather_code is not None else None
        observed_at = live_weather.get("observed_at") or "recent observation hour"
        source = live_weather.get("source") or "Open-Meteo current observation"
        coverage_note = live_weather.get("coverage_note") or "City-scale provider observation near central Chennai; it may differ from conditions at your exact location."

        lines = ["Current Observed Weather (Chennai City Grid):"]
        if precip is not None:
            lines.append(f"• Precipitation: {float(precip):.1f} mm for its current observation hour")
        if temp is not None:
            lines.append(f"• Temperature: {float(temp):.1f}°C")
        if condition_name:
            lines.append(f"• Weather Condition: {condition_name} (WMO Code {weather_code})")
        lines.append(f"• Observed Timestamp: {observed_at}")
        lines.append(f"• Source: {source}")
        lines.append(f"• Coverage Note: {coverage_note}")

        return {
            "answer": "\n".join(lines),
            "intent": "CURRENT_OBSERVATION",
            "badge": "CURRENT OBSERVATION",
            "data_nature": "OBSERVED",
            "source": "Open-Meteo current observation",
            "timestamp": observed_at,
            "citations": ["Open-Meteo current observation"],
            "safety_notice": "NOVA reports physical provider observations. Observations near central Chennai may differ from individual ward micro-climates.",
        }

    def _build_forecast(self, forecast_weather: Dict[str, Any], live_weather: Dict[str, Any], question: str) -> Dict[str, Any]:
        """Requirement 3: Return hourly forecast with clear 1h, 3h, 6h, 24h windows."""
        if not forecast_weather or forecast_weather.get("status") != "AVAILABLE":
            forecast_weather = self._fetch_forecast_direct()

        if forecast_weather.get("status") != "AVAILABLE" or not forecast_weather.get("windows"):
            return {
                "answer": "The city weather forecast provider is currently unavailable, so NOVA cannot compute upcoming rainfall probabilities. Check back shortly or refresh telemetry before relying on forecast projections.",
                "intent": "FORECAST",
                "badge": "FORECAST",
                "data_nature": "UNAVAILABLE",
                "source": "Open-Meteo hourly forecast",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "citations": ["Open-Meteo hourly forecast"],
                "safety_notice": "Forecast projections do not constitute an official municipal disaster warning or evacuation directive.",
            }

        windows = forecast_weather.get("windows", {})
        w1 = windows.get("1h", {})
        w3 = windows.get("3h", {})
        w6 = windows.get("6h", {})
        w24 = windows.get("24h", {})

        prob_1h = w1.get("precipitation_probability_pct", 0)
        rain_1h = w1.get("expected_rainfall_mm", 0.0)
        cond_1h = w1.get("condition") or "Cloudy"

        prob_3h = w3.get("precipitation_probability_pct", 0)
        rain_3h = w3.get("expected_rainfall_mm", 0.0)
        cond_3h = w3.get("condition") or "Cloudy"

        prob_6h = w6.get("precipitation_probability_pct", 0)
        rain_6h = w6.get("expected_rainfall_mm", 0.0)

        prob_24h = w24.get("precipitation_probability_pct", 0)
        rain_24h = w24.get("expected_rainfall_mm", 0.0)

        outlook_text = (
            "High likelihood of precipitation"
            if prob_6h >= 70
            else "Moderate chance of scattered rainfall"
            if prob_6h >= 35
            else "Low probability of significant rainfall"
        )

        lines = [
            "Chennai City-Scale Rainfall & Weather Forecast (Open-Meteo Hourly Numerical Model):",
            f"• Next 1 Hour: {prob_1h}% rain probability | ~{rain_1h:.1f} mm expected | {cond_1h}",
            f"• Next 3 Hours: {prob_3h}% peak probability | ~{rain_3h:.1f} mm total accumulation | {cond_3h}",
            f"• Next 6 Hours: {prob_6h}% peak probability | ~{rain_6h:.1f} mm total accumulation",
            f"• Next 24 Hours: {prob_24h}% peak probability | ~{rain_24h:.1f} mm total accumulation",
            "",
            f"Forecast Outlook: {outlook_text} across the Greater Chennai basin over the next 1–6 hours.",
            "Coverage Note: This is a city-scale meteorological weather forecast (central Chennai grid), not an exact street-level prediction. Precipitation probability reflects hourly ensemble projections and does not equal current observed precipitation.",
            "Operational Notice: Meteorological forecast projections do not constitute an official municipal disaster warning or evacuation directive.",
        ]

        timestamp = forecast_weather.get("forecast_generated_at") or datetime.now(timezone.utc).isoformat()

        return {
            "answer": "\n".join(lines),
            "intent": "FORECAST",
            "badge": "FORECAST",
            "data_nature": "FORECAST",
            "source": "Open-Meteo hourly forecast",
            "timestamp": timestamp,
            "citations": ["Open-Meteo hourly forecast"],
            "safety_notice": "Forecast projections do not constitute an official municipal warning. Field conditions must be verified by authorised municipal responders.",
            "forecast_summary": {
                "next_1h": {"probability_pct": prob_1h, "rainfall_mm": rain_1h},
                "next_3h": {"probability_pct": prob_3h, "rainfall_mm": rain_3h},
                "next_6h": {"probability_pct": prob_6h, "rainfall_mm": rain_6h},
                "next_24h": {"probability_pct": prob_24h, "rainfall_mm": rain_24h},
            },
        }

    def _build_location_mismatch(self, live_weather: Dict[str, Any], question: str) -> Dict[str, Any]:
        """Requirement 4: Acknowledge micro-climate variation without claiming the user is wrong."""
        observed_temp = live_weather.get("temperature_c")
        observed_precip = live_weather.get("precipitation_mm")
        context_str = ""
        if observed_precip is not None and observed_temp is not None:
            context_str = f" The central station grid currently registers {observed_precip:.1f} mm and {observed_temp:.1f}°C."

        lines = [
            "Understood. Your local observation can indeed differ from the central Chennai provider grid.",
            "",
            f"Chennai spans over 426 km² across diverse coastal and inland micro-basins (such as coastal Adyar, South Velachery, or Northern Manali). Localized convective showers or dry sunny breaks frequently occur in one neighborhood while the central station grid (lat 13.08, lon 80.27) records different conditions.{context_str} NOVA does not treat this spatial disagreement as an error or an emergency trigger.",
            "",
            "If you specify your particular ward or neighborhood (such as Velachery Ward 177, Adyar Ward 170, or Vyasarpadi Ward 36), NOVA can check localized digital twin indicators and elevation-specific drainage conditions for your area.",
        ]

        return {
            "answer": "\n".join(lines),
            "intent": "LOCATION_MISMATCH",
            "badge": "LOCATION MISMATCH",
            "data_nature": "OBSERVED",
            "source": "Open-Meteo & Chennai micro-climate boundary",
            "timestamp": live_weather.get("observed_at") or datetime.now(timezone.utc).isoformat(),
            "citations": ["Open-Meteo current observation", "Chennai localized micro-climate boundary"],
            "safety_notice": "Micro-climatic variations are normal in urban basins. Local weather observations are acknowledged as valid neighborhood variations.",
        }

    def _fallback_structured(self, question: str, briefing: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministic, evidence-grounded fallback returning full metadata."""
        brief = briefing.get("decision_brief", {})
        threat = briefing.get("priority_threat", {})
        confidence = briefing.get("confidence", {})
        asset = briefing.get("highest_priority_asset", {})
        live_weather = briefing.get("live_weather", {})
        forecast_weather = briefing.get("forecast_weather", {})

        intent = detect_weather_intent(question)

        if intent == "LOCATION_MISMATCH":
            return self._build_location_mismatch(live_weather, question)

        if intent == "FORECAST":
            return self._build_forecast(forecast_weather, live_weather, question)

        if intent == "CURRENT_OBSERVATION":
            return self._build_current_observation(live_weather, question)

        q = question.lower()
        if any(word in q for word in ["action", "do now", "next step", "recommend"]):
            action_text = f"Recommended next step: {brief.get('action', briefing.get('recommended_action', 'Review the latest inputs.'))} Owner: {brief.get('owner', 'Duty analyst')}. Review in {brief.get('review_in_minutes', 60)} minutes."
            return {
                "answer": action_text,
                "intent": "DECISION_SUPPORT",
                "badge": "DECISION SUPPORT",
                "data_nature": "ANALYSIS",
                "source": "Digital Twin Decision Brief",
                "timestamp": briefing.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                "citations": ["Current telemetry quality summary", "Prototype risk-model output"],
                "safety_notice": brief.get("evidence_boundary", "Prototype decision support."),
            }

        if any(word in q for word in ["why", "driver", "priority"]):
            why_text = "Current priority is " + str(threat.get("type", "UNKNOWN")).replace("_", " ") + ". " + " ".join(briefing.get("why_now", [])[:2])
            return {
                "answer": why_text,
                "intent": "DECISION_SUPPORT",
                "badge": "DECISION SUPPORT",
                "data_nature": "ANALYSIS",
                "source": "Multi-Hazard Risk Engine",
                "timestamp": briefing.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                "citations": ["Current telemetry quality summary", "Prototype risk-model output"],
                "safety_notice": "Model-derived priority indicators require human confirmation before field actuation.",
            }

        if any(word in q for word in ["reliable", "confidence", "trust", "data"]):
            conf_text = f"Confidence is {confidence.get('level', 'UNKNOWN')}. {confidence.get('explanation', '')} Verify the next telemetry cycle before escalation."
            return {
                "answer": conf_text,
                "intent": "DECISION_SUPPORT",
                "badge": "DECISION SUPPORT",
                "data_nature": "ANALYSIS",
                "source": "Sensor Health & Quality Guardian",
                "timestamp": briefing.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                "citations": ["Current telemetry quality summary", "Sensor health audit"],
                "safety_notice": "Confidence metrics reflect data completeness and physical plausibility gates.",
            }

        if any(word in q for word in ["asset", "location", "where"]):
            asset_text = f"The current screening-priority asset is {asset.get('Asset Name', 'not available')}. This priority is model-derived and needs field verification."
            return {
                "answer": asset_text,
                "intent": "DECISION_SUPPORT",
                "badge": "DECISION SUPPORT",
                "data_nature": "ANALYSIS",
                "source": "Asset Criticality Screener",
                "timestamp": briefing.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                "citations": ["Asset screening result", "SRTM 30m DEM"],
                "safety_notice": "Asset screening priorities are advisory and require field reconnaissance.",
            }

        general_text = f"Current assessed risk is {threat.get('level', 'UNKNOWN')} for {str(threat.get('type', 'UNKNOWN')).replace('_', ' ')}. {brief.get('evidence_boundary', '')}"
        return {
            "answer": general_text,
            "intent": "DECISION_SUPPORT",
            "badge": "DECISION SUPPORT",
            "data_nature": "ANALYSIS",
            "source": "ClimateTwin Command Summary",
            "timestamp": briefing.get("timestamp") or datetime.now(timezone.utc).isoformat(),
            "citations": ["Current telemetry quality summary", "Prototype risk-model output", "Asset screening result"],
            "safety_notice": self.provider_status()["boundary"],
        }

    def _fallback(self, question: str, briefing: Dict[str, Any]) -> str:
        """Backwards-compatible string fallback."""
        res = self._fallback_structured(question, briefing)
        return res["answer"]

    async def answer(self, question: str, briefing: Dict[str, Any]) -> Dict[str, Any]:
        status = self.provider_status()
        fallback_res = self._fallback_structured(question, briefing)

        if not status["configured"]:
            return {
                "answer": fallback_res["answer"],
                "mode": "LOCAL_EVIDENCE_FALLBACK",
                "intent": fallback_res.get("intent", "DECISION_SUPPORT"),
                "badge": fallback_res.get("badge", "DECISION SUPPORT"),
                "data_nature": fallback_res.get("data_nature", "ANALYSIS"),
                "source": fallback_res.get("source", "ClimateTwin Telemetry"),
                "timestamp": fallback_res.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "citations": fallback_res.get("citations", ["Open-Meteo current observation"]),
                "safety_notice": fallback_res.get("safety_notice", status["boundary"]),
                "forecast_summary": fallback_res.get("forecast_summary"),
            }

        system = (
            "You are NOVA, a cautious climate-risk decision-support copilot. "
            "Use only the supplied briefing. Do not invent measurements, sources, impacts, "
            "or operational authority. State uncertainty and recommend human verification. "
            "Never present a draft as a public warning or emergency command. Keep the response under 180 words."
        )
        payload = {
            "model": status["model"],
            "temperature": 0.2,
            "max_tokens": 260,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": f"Briefing JSON:\n{json.dumps(briefing, default=str)}\n\nQuestion: {question}"},
            ],
        }
        try:
            headers = {"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}", "Content-Type": "application/json"}
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(self.endpoint, headers=headers, json=payload)
                response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()
            return {
                "answer": content,
                "mode": "OPENROUTER_LLM",
                "intent": fallback_res.get("intent", "DECISION_SUPPORT"),
                "badge": fallback_res.get("badge", "DECISION SUPPORT"),
                "data_nature": fallback_res.get("data_nature", "ANALYSIS"),
                "source": fallback_res.get("source", "OpenRouter LLM + Local Grounding"),
                "timestamp": fallback_res.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "citations": fallback_res.get("citations", ["Open-Meteo current observation"]),
                "safety_notice": status["boundary"],
                "forecast_summary": fallback_res.get("forecast_summary"),
            }
        except Exception:
            return {
                "answer": fallback_res["answer"],
                "mode": "LOCAL_EVIDENCE_FALLBACK_AFTER_PROVIDER_ERROR",
                "intent": fallback_res.get("intent", "DECISION_SUPPORT"),
                "badge": fallback_res.get("badge", "DECISION SUPPORT"),
                "data_nature": fallback_res.get("data_nature", "ANALYSIS"),
                "source": fallback_res.get("source", "Local Telemetry"),
                "timestamp": fallback_res.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "citations": fallback_res.get("citations", ["Open-Meteo current observation"]),
                "safety_notice": "The external AI provider was unavailable. " + status["boundary"],
                "forecast_summary": fallback_res.get("forecast_summary"),
            }


nova_copilot = NovaCopilot()
