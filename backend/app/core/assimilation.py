import math
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
import threading
import numpy as np

logger = logging.getLogger(__name__)

# Standard bounds for physical validation
PHYSICAL_BOUNDS = {
    "POONDI": (0.0, 3500.0),
    "CHOLAVARAM": (0.0, 1200.0),
    "REDHILLS": (0.0, 3500.0),
    "CHEMBARAMBAKKAM": (0.0, 4000.0),
    "rainfall_daily": (0.0, 600.0),
    "rainfall_3d_sum": (0.0, 1500.0),
    "rainfall_5d_sum": (0.0, 2000.0),
    "rainfall_7d_sum": (0.0, 2500.0),
    "temp_mean": (5.0, 55.0),
    "temp_max": (5.0, 60.0),
    "temp_min": (0.0, 45.0),
    "dew_point_mean": (-10.0, 40.0),
    "wind_speed_mean": (0.0, 80.0),
    "water_level": (0.0, 5000.0),
}

# Approximate normal state standard deviations for outlier / 3-sigma detection
EXPECTED_SCALE = {
    "POONDI": 400.0,
    "CHOLAVARAM": 150.0,
    "REDHILLS": 350.0,
    "CHEMBARAMBAKKAM": 450.0,
    "rainfall_daily": 80.0,
    "rainfall_3d_sum": 150.0,
    "rainfall_5d_sum": 200.0,
    "rainfall_7d_sum": 250.0,
    "temp_mean": 5.0,
    "temp_max": 6.0,
    "temp_min": 5.0,
    "dew_point_mean": 4.0,
    "wind_speed_mean": 3.0,
    "water_level": 400.0,
}

# Quality-dependent base assimilation weights (alpha)
BASE_QUALITY_WEIGHTS = {
    "EXCELLENT": 0.85,
    "GOOD": 0.75,
    "ACCEPTABLE": 0.60,
    "DEFAULT": 0.60,
    "LOW_CONFIDENCE": 0.25,
    "WARNING": 0.20,
    "UNRELIABLE": 0.05,
    "REJECTED": 0.0,
    "OUTLIER": 0.0,
    "STALE": 0.0,
    "DUPLICATE": 0.0,
}

class DigitalTwinAssimilationEngine:
    def __init__(self):
        self._lock = threading.Lock()
        self._history: List[Dict[str, Any]] = []
        self._seen_observations: set = set()
        
        # Initial nominal baseline digital-twin state (dry weather / low risk condition)
        self._state: Dict[str, float] = {
            "rainfall_daily": 0.0,
            "rainfall_3d_sum": 0.0,
            "rainfall_5d_sum": 0.0,
            "rainfall_7d_sum": 0.0,
            "temp_mean": 29.5,
            "temp_max": 33.5,
            "temp_min": 25.5,
            "dew_point_mean": 22.0,
            "wind_speed_mean": 2.5,
            "POONDI": 2500.0,
            "CHOLAVARAM": 800.0,
            "REDHILLS": 2600.0,
            "CHEMBARAMBAKKAM": 2800.0,
            "total_reservoir_level": 8700.0
        }
        
        self._last_update: Dict[str, datetime] = {
            k: datetime.now(timezone.utc) for k in self._state
        }
        self._state_quality: Dict[str, str] = {
            k: "NOMINAL" for k in self._state
        }

    def reset_to_baseline(self):
        with self._lock:
            self._state = {
                "rainfall_daily": 0.0,
                "rainfall_3d_sum": 0.0,
                "rainfall_5d_sum": 0.0,
                "rainfall_7d_sum": 0.0,
                "temp_mean": 29.5,
                "temp_max": 33.5,
                "temp_min": 25.5,
                "dew_point_mean": 22.0,
                "wind_speed_mean": 2.5,
                "POONDI": 2500.0,
                "CHOLAVARAM": 800.0,
                "REDHILLS": 2600.0,
                "CHEMBARAMBAKKAM": 2800.0,
                "total_reservoir_level": 8700.0
            }
            self._history.clear()
            self._seen_observations.clear()
            self._last_update = {k: datetime.now(timezone.utc) for k in self._state}
            self._state_quality = {k: "NOMINAL" for k in self._state}

    def get_current_state(self) -> Dict[str, Any]:
        with self._lock:
            # Recompute total reservoir level
            self._state["total_reservoir_level"] = sum([
                self._state.get("POONDI", 0.0),
                self._state.get("CHOLAVARAM", 0.0),
                self._state.get("REDHILLS", 0.0),
                self._state.get("CHEMBARAMBAKKAM", 0.0)
            ])
            return {
                "state": dict(self._state),
                "last_update": {k: v.isoformat() for k, v in self._last_update.items()},
                "quality": dict(self._state_quality)
            }

    def validate_observation(
        self,
        asset_id: str,
        variable: str,
        value: Optional[float],
        obs_timestamp: Optional[datetime],
        quality_flag: str = "GOOD",
        sensor_id: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Validates incoming observation.
        Returns (validation_status, reason_message)
        """
        # 1. Missing Value Check
        if value is None or (isinstance(value, float) and (np.isnan(value) or np.isinf(value))):
            return "REJECTED", "Observation value is missing, NaN, or Inf"

        # 2. Timestamp Validation
        if obs_timestamp is None:
            return "REJECTED", "Missing timestamp"
            
        now_utc = datetime.now(timezone.utc)
        if obs_timestamp.tzinfo is None:
            obs_timestamp = obs_timestamp.replace(tzinfo=timezone.utc)
            
        # 3. Future Timestamp Check (> 5 min in future)
        if obs_timestamp > now_utc + timedelta(minutes=5):
            return "REJECTED", f"Observation has future timestamp: {obs_timestamp.isoformat()}"
            
        # 4. Staleness Check (> 24 hours old)
        age_seconds = (now_utc - obs_timestamp).total_seconds()
        if age_seconds > 86400.0:
            return "STALE", f"Observation is stale (age: {age_seconds/3600.0:.1f} hours > 24h limit)"

        # Determine target state key
        key = asset_id if asset_id in self._state else variable
        if key not in self._state:
            # Check for synonyms
            key_upper = asset_id.upper()
            if key_upper in self._state:
                key = key_upper
            elif variable in self._state:
                key = variable
            else:
                return "REJECTED", f"Unknown asset or state variable: asset='{asset_id}', var='{variable}'"

        # 5. Physical Bounds Check
        bounds = PHYSICAL_BOUNDS.get(key, PHYSICAL_BOUNDS.get(variable))
        if bounds:
            min_val, max_val = bounds
            if value < min_val or value > max_val:
                return "OUT_OF_BOUNDS", f"Value {value} out of physical bounds [{min_val}, {max_val}] for {key}"

        # 6. Duplicate Observation Check
        obs_signature = f"{sensor_id or asset_id}_{key}_{obs_timestamp.isoformat()}_{value:.4f}"
        if obs_signature in self._seen_observations:
            return "DUPLICATE", f"Duplicate observation already ingested: {obs_signature}"

        # 7. Extreme Outlier Check (Statistical 3.5-Sigma Innovation Test)
        prior_val = self._state.get(key, value)
        scale = EXPECTED_SCALE.get(key, EXPECTED_SCALE.get(variable, 100.0))
        innovation = abs(value - prior_val)
        
        # If the jump is larger than 3.5x expected standard deviation and quality is not forced
        if innovation > 3.5 * scale and quality_flag.upper() not in ["FORCE_ACCEPT", "GROUND_TRUTH"]:
            return "OUTLIER", f"Extreme innovation (|{value} - {prior_val}| = {innovation:.1f} > 3.5 * {scale:.1f})"

        return "ACCEPTED", "Observation passed all validation criteria"

    def compute_assimilation_weight(
        self,
        quality_flag: str,
        obs_timestamp: datetime,
        validation_status: str
    ) -> float:
        """
        Computes the adaptive nudging weight alpha in [0.0, 1.0].
        alpha = alpha_base(Q) * exp(-Delta_t / tau)
        """
        if validation_status != "ACCEPTED":
            return 0.0

        q_key = quality_flag.upper() if quality_flag else "DEFAULT"
        base_alpha = BASE_QUALITY_WEIGHTS.get(q_key, BASE_QUALITY_WEIGHTS["DEFAULT"])

        # Exponential decay for age (tau = 12 hours = 43200 seconds)
        now_utc = datetime.now(timezone.utc)
        if obs_timestamp.tzinfo is None:
            obs_timestamp = obs_timestamp.replace(tzinfo=timezone.utc)
            
        age_seconds = max(0.0, (now_utc - obs_timestamp).total_seconds())
        tau = 43200.0  # 12-hour half-life parameter
        decay_factor = math.exp(-age_seconds / tau)

        alpha = float(np.clip(base_alpha * decay_factor, 0.0, 1.0))
        return alpha

    def assimilate(
        self,
        asset_id: str,
        variable: str,
        value: float,
        obs_timestamp: Optional[datetime] = None,
        unit: Optional[str] = None,
        quality_flag: str = "GOOD",
        sensor_id: Optional[str] = None,
        source: str = "SIMULATION"
    ) -> Dict[str, Any]:
        """
        Executes full validation -> assimilation -> twin state update.
        """
        t_start = time.perf_counter()
        
        if obs_timestamp is None:
            obs_timestamp = datetime.now(timezone.utc)
        elif obs_timestamp.tzinfo is None:
            obs_timestamp = obs_timestamp.replace(tzinfo=timezone.utc)

        # 1. Validation Stage
        validation_status, reason = self.validate_observation(
            asset_id=asset_id,
            variable=variable,
            value=value,
            obs_timestamp=obs_timestamp,
            quality_flag=quality_flag,
            sensor_id=sensor_id
        )

        with self._lock:
            # Map to internal state key
            target_key = asset_id if asset_id in self._state else variable
            if target_key not in self._state:
                if asset_id.upper() in self._state:
                    target_key = asset_id.upper()
                elif variable in self._state:
                    target_key = variable
                else:
                    target_key = asset_id

            prior_state = float(self._state.get(target_key, value if value is not None else 0.0))

            # 2. Assimilation Weight Calculation
            alpha = self.compute_assimilation_weight(quality_flag, obs_timestamp, validation_status)

            # 3. State Update Formula: x_a = (1 - alpha) * x_b + alpha * y
            if validation_status == "ACCEPTED" and alpha > 0.0:
                updated_state = float((1.0 - alpha) * prior_state + alpha * float(value))
                self._state[target_key] = updated_state
                self._last_update[target_key] = datetime.now(timezone.utc)
                self._state_quality[target_key] = quality_flag
                
                # Dynamic update of antecedent and rate metrics for rainfall
                if target_key == "rainfall_daily":
                    r_val = float(updated_state)
                    self._state["rainfall_3d_sum"] = max(float(self._state.get("rainfall_3d_sum", 0.0)), r_val * 1.5)
                    self._state["rainfall_5d_sum"] = max(float(self._state.get("rainfall_5d_sum", 0.0)), r_val * 2.0)
                    self._state["rainfall_7d_sum"] = max(float(self._state.get("rainfall_7d_sum", 0.0)), r_val * 2.5)
                    self._state["rainfall_rate_1h"] = r_val / 24.0
                    self._state["rainfall_trend"] = max(0.0, r_val - prior_state)
                
                # Register seen signature for duplicate detection
                obs_signature = f"{sensor_id or asset_id}_{target_key}_{obs_timestamp.isoformat()}_{value:.4f}"
                self._seen_observations.add(obs_signature)
            else:
                updated_state = prior_state

            # Recompute total reservoir storage and rate of change
            prior_total = float(self._state.get("total_reservoir_level", 8700.0))
            new_total = sum([
                self._state.get("POONDI", 0.0),
                self._state.get("CHOLAVARAM", 0.0),
                self._state.get("REDHILLS", 0.0),
                self._state.get("CHEMBARAMBAKKAM", 0.0)
            ])
            self._state["total_reservoir_level"] = new_total
            self._state["reservoir_storage_rate_1d"] = new_total - prior_total

            t_end = time.perf_counter()
            assimilation_duration_ms = (t_end - t_start) * 1000.0

            # Record event in assimilation history
            event_id = len(self._history) + 1
            event_record = {
                "event_id": event_id,
                "asset_id": asset_id,
                "variable": variable,
                "target_key": target_key,
                "sensor_id": sensor_id,
                "source": source,
                "prior_state": prior_state,
                "observation_value": value,
                "unit": unit,
                "assimilation_weight": alpha,
                "updated_state": updated_state,
                "quality_flag": quality_flag,
                "validation_status": validation_status,
                "validation_message": reason,
                "obs_timestamp": obs_timestamp.isoformat(),
                "assimilated_at": datetime.now(timezone.utc).isoformat(),
                "assimilation_ms": max(0.01, assimilation_duration_ms)
            }
            self._history.append(event_record)
            if len(self._history) > 1000:
                self._history.pop(0)

            return event_record

    def get_feature_vector(self) -> List[float]:
        """
        Returns the exact 14-feature vector formatted for the Random Forest baseline model.
        """
        with self._lock:
            feature_order = [
                "rainfall_daily", "rainfall_3d_sum", "rainfall_5d_sum", "rainfall_7d_sum",
                "temp_mean", "temp_max", "temp_min", "dew_point_mean", "wind_speed_mean",
                "POONDI", "CHOLAVARAM", "REDHILLS", "CHEMBARAMBAKKAM", "total_reservoir_level"
            ]
            
            # Ensure total reservoir level is synchronized
            self._state["total_reservoir_level"] = sum([
                self._state.get("POONDI", 0.0),
                self._state.get("CHOLAVARAM", 0.0),
                self._state.get("REDHILLS", 0.0),
                self._state.get("CHEMBARAMBAKKAM", 0.0)
            ])
            
            return [float(self._state.get(f, 0.0)) for f in feature_order]

    def get_forecasting_feature_vector(self) -> List[float]:
        """
        Returns the 20 temporal features formatted for the Phase 10 short-horizon forecasting models (RF_15, RF_30, RF_60).
        """
        with self._lock:
            total_storage = sum([
                self._state.get("POONDI", 0.0),
                self._state.get("CHOLAVARAM", 0.0),
                self._state.get("REDHILLS", 0.0),
                self._state.get("CHEMBARAMBAKKAM", 0.0)
            ])
            self._state["total_reservoir_level"] = total_storage
            
            fill_ratio = min(1.0, max(0.0, total_storage / 11257.0))
            dew_dep = max(0.0, float(self._state.get("temp_mean", 29.5) - self._state.get("dew_point_mean", 22.0)))
            rate_1h = float(self._state.get("rainfall_rate_1h", self._state.get("rainfall_daily", 0.0) / 24.0))
            rain_trend = float(self._state.get("rainfall_trend", 0.0))
            wind_trend = float(self._state.get("wind_speed_trend", 0.0))
            storage_rate = float(self._state.get("reservoir_storage_rate_1d", 0.0))
            
            forecast_features = [
                float(self._state.get("rainfall_daily", 0.0)),
                float(self._state.get("rainfall_3d_sum", 0.0)),
                float(self._state.get("rainfall_5d_sum", 0.0)),
                float(self._state.get("rainfall_7d_sum", 0.0)),
                rate_1h,
                rain_trend,
                float(self._state.get("temp_mean", 29.5)),
                float(self._state.get("temp_max", 33.5)),
                float(self._state.get("temp_min", 25.5)),
                float(self._state.get("dew_point_mean", 22.0)),
                dew_dep,
                float(self._state.get("wind_speed_mean", 2.5)),
                wind_trend,
                float(self._state.get("POONDI", 2500.0)),
                float(self._state.get("CHOLAVARAM", 800.0)),
                float(self._state.get("REDHILLS", 2600.0)),
                float(self._state.get("CHEMBARAMBAKKAM", 2800.0)),
                total_storage,
                fill_ratio,
                storage_rate
            ]
            return forecast_features

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return list(reversed(self._history[-limit:]))

# Global singleton instance of the Data Assimilation Engine
twin_engine = DigitalTwinAssimilationEngine()
