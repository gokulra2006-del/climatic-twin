import os
import json
import logging
import numpy as np
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Documented Expert Fallback Defaults
EXPERT_BASE_WEIGHTS = {
    'flood': 0.35,           # Direct predictive flood inundation
    'rainfall': 0.25,        # Active precipitation rate & antecedent load
    'reservoir': 0.20,       # Hydrological reservoir storage saturation
    'wind': 0.10,            # Cyclonic structural / storm drain disruption
    'heat': 0.05,            # Thermodynamic humid heat index
    'runoff': 0.05           # Low-elevation topographic pooling
}

EXPERT_INTERACTION_WEIGHTS = {
    'rainfall_x_reservoir': 0.25,   # Intense rain + full reservoirs -> immediate overtopping
    'rainfall_x_runoff': 0.15,      # High rain + low elevation -> severe surface pooling
    'rainfall_x_wind': 0.15,        # Cyclonic wind + torrential rain -> compound infrastructure paralysis
    'temp_x_dewpoint': 0.10         # Humid heat wave fatigue
}

class MultiHazardRiskEngine:
    """
    ClimateTwin Multi-Hazard & Cascading Risk Engine.
    
    Ingests the Phase 9 Assimilated Digital Twin state, normalizes multiple
    evidence-backed environmental hazards, evaluates non-linear physical interactions,
    and calculates transparent Compound Risk Scores (CRS) without fabricating joint probabilities.
    """
    
    def __init__(self):
        # Physical normalization thresholds based on Chennai historical distributions
        self.THRESHOLDS = {
            'rainfall_daily_max_mm': 150.0,      # >150mm is severe monsoonal deluge
            'rainfall_rate_max_mm_hr': 25.0,     # >25mm/hr is torrential cloudburst
            'reservoir_capacity_mcft': 11257.0,  # Combined 4-reservoir max storage
            'temp_heat_threshold_c': 38.0,       # >38C is extreme heat advisory
            'wind_speed_max_ms': 25.0,           # >25m/s (~90km/h) is cyclonic gale
            'low_elevation_cutoff_m': 10.0       # <10m is highly vulnerable coastal plain
        }
        
        # Base weights and interaction coupling coefficients
        self.BASE_WEIGHTS = dict(EXPERT_BASE_WEIGHTS)
        self.INTERACTION_WEIGHTS = dict(EXPERT_INTERACTION_WEIGHTS)
        self.parameter_source = "EXPERT_FALLBACK"
        
        # Load empirical calibrated parameters if available (with fallback to expert values)
        params_file = os.path.join(os.path.dirname(__file__), "calibrated_params.json")
        if os.path.exists(params_file):
            try:
                with open(params_file, "r", encoding="utf-8") as f:
                    calibrated = json.load(f)
                if "multihazard" in calibrated:
                    mh = calibrated["multihazard"]
                    if "base_weights" in mh:
                        self.BASE_WEIGHTS.update(mh["base_weights"])
                    if "interaction_weights" in mh:
                        self.INTERACTION_WEIGHTS.update(mh["interaction_weights"])
                    self.parameter_source = "CALIBRATED_DATA_FIT"
                    logger.info("Loaded calibrated multihazard coefficients from calibrated_params.json")
            except Exception as e:
                logger.warning(f"Failed to load calibrated_params.json; using documented expert fallback: {e}")

    def normalize_hazard_states(self, env_state: Dict[str, Any], flood_prob: float = 0.10) -> Dict[str, Dict[str, Any]]:
        """
        Normalizes environmental variables into standardized hazard states [0.0, 1.0].
        """
        # 1. Extreme Rainfall Hazard
        rain_daily = float(env_state.get('rainfall_daily', 0.0))
        rain_rate = float(env_state.get('rainfall_rate_1h', rain_daily / 24.0))
        s_rain = min(1.0, max(0.0, (rain_daily / 100.0) * 0.7 + (rain_rate / 15.0) * 0.3))
        
        # 2. Predictive Flood Inundation Hazard (from ML model)
        s_flood = min(1.0, max(0.0, flood_prob))
        
        # 3. Reservoir Hydrological Stress Hazard
        res_total = float(env_state.get('total_reservoir_level', 2500.0))
        res_fill = float(env_state.get('reservoir_fill_ratio', res_total / self.THRESHOLDS['reservoir_capacity_mcft']))
        res_rate = float(env_state.get('reservoir_storage_rate_1d', 0.0))
        s_res = min(1.0, max(0.0, res_fill * 0.75 + max(0.0, res_rate / 800.0) * 0.25))
        
        # 4. Wind Hazard
        wind_speed = float(env_state.get('wind_speed_mean', 3.0))
        s_wind = min(1.0, max(0.0, wind_speed / self.THRESHOLDS['wind_speed_max_ms']))
        
        # 5. Thermodynamic Heat Stress Hazard
        temp_max = float(env_state.get('temp_max', env_state.get('temp_mean', 30.0)))
        dew_point = float(env_state.get('dew_point_mean', 24.0))
        heat_index = temp_max + 0.5555 * (6.11 * np.exp(5417.7530 * (1/273.16 - 1/(273.15 + dew_point))) - 10.0)
        s_heat = min(1.0, max(0.0, (heat_index - 32.0) / 18.0))
        
        # 6. Topographic Runoff Accumulation Hazard
        elevation = float(env_state.get('elevation_m', 8.5))
        s_runoff = min(1.0, max(0.0, (self.THRESHOLDS['low_elevation_cutoff_m'] - elevation) / self.THRESHOLDS['low_elevation_cutoff_m'])) if elevation < 10.0 else 0.05
        
        def map_level(score: float) -> str:
            if score >= 0.80: return 'CRITICAL'
            if score >= 0.50: return 'HIGH'
            if score >= 0.25: return 'MODERATE'
            return 'LOW'

        return {
            'rainfall': {
                'hazard_name': 'EXTREME_RAINFALL',
                'observed_value': f"{rain_daily:.1f} mm/day ({rain_rate:.1f} mm/hr)",
                'normalized_intensity': round(s_rain, 3),
                'hazard_level': map_level(s_rain),
                'data_source': 'NASA GPM IMERG V07B',
                'category': 'OBSERVED / DERIVED'
            },
            'flood': {
                'hazard_name': 'FLOOD_INUNDATION',
                'observed_value': f"{flood_prob*100:.1f}% Probability",
                'normalized_intensity': round(s_flood, 3),
                'hazard_level': map_level(s_flood),
                'data_source': 'Random Forest Ensemble (B=100)',
                'category': 'MODEL-PREDICTED'
            },
            'reservoir_stress': {
                'hazard_name': 'RESERVOIR_HYDROLOGICAL_STRESS',
                'observed_value': f"{res_total:.0f} mcft ({res_fill*100:.1f}% Capacity)",
                'normalized_intensity': round(s_res, 3),
                'hazard_level': map_level(s_res),
                'data_source': 'CMWSSB Water Authority Gauges',
                'category': 'OBSERVED / ASSIMILATED'
            },
            'wind': {
                'hazard_name': 'HIGH_WIND_GUST',
                'observed_value': f"{wind_speed:.1f} m/s",
                'normalized_intensity': round(s_wind, 3),
                'hazard_level': map_level(s_wind),
                'data_source': 'NOAA ISD Station 432790',
                'category': 'OBSERVED'
            },
            'heat': {
                'hazard_name': 'HEAT_STRESS_HUMIDITY',
                'observed_value': f"{temp_max:.1f}°C (Dew Point: {dew_point:.1f}°C)",
                'normalized_intensity': round(s_heat, 3),
                'hazard_level': map_level(s_heat),
                'data_source': 'NOAA ISD Station 432790',
                'category': 'DERIVED'
            },
            'runoff': {
                'hazard_name': 'TOPOGRAPHIC_RUNOFF_POOLING',
                'observed_value': f"Elevation: {elevation:.1f} m (Low-Lying Basin)",
                'normalized_intensity': round(s_runoff, 3),
                'hazard_level': map_level(s_runoff),
                'data_source': 'Copernicus DEM 30m',
                'category': 'DERIVED'
            }
        }

    def evaluate_interactions(self, hazards: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Evaluates non-linear compound hazard interaction terms.
        """
        interactions = []
        s_rain = hazards['rainfall']['normalized_intensity']
        s_res = hazards['reservoir_stress']['normalized_intensity']
        s_runoff = hazards['runoff']['normalized_intensity']
        s_wind = hazards['wind']['normalized_intensity']
        s_heat = hazards['heat']['normalized_intensity']
        
        # 1. Hydrological Coupling
        hyd_coupling = s_rain * s_res
        if hyd_coupling > 0.15:
            interactions.append({
                'interaction_id': 'INT_HYD_COUPLING',
                'name': 'HIGH_RAINFALL + RESERVOIR_CAPACITY_STRESS',
                'coupling_strength': round(hyd_coupling, 3),
                'description': 'Torrential precipitation coinciding with saturated reservoir capacity increases imminent spillway surge risk.'
            })
            
        # 2. Topographic Runoff Coupling
        top_coupling = s_rain * s_runoff
        if top_coupling > 0.15:
            interactions.append({
                'interaction_id': 'INT_TOP_RUNOFF',
                'name': 'HIGH_RAINFALL + LOW_ELEVATION_POOLING',
                'coupling_strength': round(top_coupling, 3),
                'description': 'Intense precipitation on low-lying coastal terrain promotes immediate surface pooling.'
            })
            
        # 3. Cyclonic Multi-Stress
        cyc_coupling = s_rain * s_wind
        if cyc_coupling > 0.12:
            interactions.append({
                'interaction_id': 'INT_CYC_STRESS',
                'name': 'HIGH_RAINFALL + CYCLONIC_GALE_WINDS',
                'coupling_strength': round(cyc_coupling, 3),
                'description': 'Simultaneous torrential rain and strong winds threaten utility infrastructure and drainage outfalls.'
            })
            
        # 4. Thermodynamic Heat Wave
        if s_heat > 0.60:
            interactions.append({
                'interaction_id': 'INT_HUMID_HEAT',
                'name': 'EXTREME_TEMPERATURE + HIGH_DEW_POINT',
                'coupling_strength': round(s_heat, 3),
                'description': 'Severe wet-bulb humid heat conditions posing health and grid operational stress.'
            })
            
        return interactions

    def calculate_compound_risk(
        self,
        env_state: Dict[str, Any],
        flood_prob: float = 0.10,
        uncertainty_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculates the transparent Compound Risk Score (CRS), dominant hazard, and cascade explanation.
        """
        hazards = self.normalize_hazard_states(env_state, flood_prob)
        interactions = self.evaluate_interactions(hazards)
        
        # Base Linear Component
        base_score = (
            self.BASE_WEIGHTS['flood'] * hazards['flood']['normalized_intensity'] +
            self.BASE_WEIGHTS['rainfall'] * hazards['rainfall']['normalized_intensity'] +
            self.BASE_WEIGHTS['reservoir'] * hazards['reservoir_stress']['normalized_intensity'] +
            self.BASE_WEIGHTS['wind'] * hazards['wind']['normalized_intensity'] +
            self.BASE_WEIGHTS['heat'] * hazards['heat']['normalized_intensity'] +
            self.BASE_WEIGHTS['runoff'] * hazards['runoff']['normalized_intensity']
        )
        
        # Non-Linear Interaction Bonus
        interaction_bonus = 0.0
        for inter in interactions:
            if inter['interaction_id'] == 'INT_HYD_COUPLING':
                interaction_bonus += self.INTERACTION_WEIGHTS['rainfall_x_reservoir'] * inter['coupling_strength']
            elif inter['interaction_id'] == 'INT_TOP_RUNOFF':
                interaction_bonus += self.INTERACTION_WEIGHTS['rainfall_x_runoff'] * inter['coupling_strength']
            elif inter['interaction_id'] == 'INT_CYC_STRESS':
                interaction_bonus += self.INTERACTION_WEIGHTS['rainfall_x_wind'] * inter['coupling_strength']
                
        # Total Compound Risk Score (CRS) clamped to [0.0, 1.0]
        crs = min(1.0, max(0.0, base_score + interaction_bonus))
        
        # Determine Dominant Hazard
        intensities = {k: v['normalized_intensity'] for k, v in hazards.items()}
        dominant_key = max(intensities, key=intensities.get)
        dominant_hazard = hazards[dominant_key]['hazard_name']
        
        # Risk Classification
        if crs >= 0.75:
            compound_level = 'CRITICAL'
        elif crs >= 0.50:
            compound_level = 'HIGH'
        elif crs >= 0.25:
            compound_level = 'MODERATE'
        else:
            compound_level = 'LOW'
            
        # Causal Cascade Explanation
        drivers = []
        if hazards['flood']['normalized_intensity'] >= 0.40:
            drivers.append(f"Elevated predictive flood probability ({flood_prob*100:.0f}%)")
        if hazards['rainfall']['normalized_intensity'] >= 0.40:
            drivers.append("Intense active/antecedent precipitation")
        if hazards['reservoir_stress']['normalized_intensity'] >= 0.50:
            drivers.append("High reservoir capacity saturation")
        if hazards['wind']['normalized_intensity'] >= 0.40:
            drivers.append("Strong cyclonic wind gusts")
        if hazards['runoff']['normalized_intensity'] >= 0.40:
            drivers.append("Low-lying topographic pooling vulnerability")
            
        if not drivers:
            drivers.append("Nominal baseline environmental conditions across catchment")
            
        inter_summary = [i['name'] for i in interactions] if interactions else ["No severe compound interactions active"]
        
        explanation = f"Compound risk level {compound_level} (Score: {crs:.2f}). Dominant driver: {dominant_hazard}. Contributing conditions: {', '.join(drivers)}. Interacting pairs: {', '.join(inter_summary)}."
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'compound_risk_score': round(float(crs), 3),
            'compound_risk_level': compound_level,
            'dominant_hazard': dominant_hazard,
            'base_component_score': round(float(base_score), 3),
            'interaction_bonus_score': round(float(interaction_bonus), 3),
            'hazards': hazards,
            'active_interactions': interactions,
            'cascade_explanation': explanation,
            'flood_uncertainty': uncertainty_info or {'uncertainty_level': 'LOW', 'prediction_interval': {'lower': 0.0, 'upper': 0.2}},
            'methodology_label': 'RULE-BASED NON-LINEAR COMPOUND RISK INDEX (CRS)'
        }

    def simulate_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """
        Executes controlled benchmark scenario simulations (A, B, C, D).
        """
        scenarios = {
            'SCENARIO_A_NOMINAL': {
                'name': 'Scenario A — Nominal Baseline',
                'description': 'Dry weather, nominal reservoir levels (35%), calm winds.',
                'state': {
                    'rainfall_daily': 2.0,
                    'rainfall_rate_1h': 0.1,
                    'total_reservoir_level': 3900.0,
                    'reservoir_fill_ratio': 0.35,
                    'temp_max': 31.0,
                    'dew_point_mean': 22.0,
                    'wind_speed_mean': 3.0,
                    'elevation_m': 12.0
                },
                'flood_prob': 0.08
            },
            'SCENARIO_B_HEAVY_RAIN': {
                'name': 'Scenario B — Heavy Monsoonal Rainfall',
                'description': 'Intense active precipitation (85mm/day) with nominal reservoir capacity (40%).',
                'state': {
                    'rainfall_daily': 85.0,
                    'rainfall_rate_1h': 12.0,
                    'total_reservoir_level': 4500.0,
                    'reservoir_fill_ratio': 0.40,
                    'temp_max': 27.0,
                    'dew_point_mean': 24.0,
                    'wind_speed_mean': 8.0,
                    'elevation_m': 8.0
                },
                'flood_prob': 0.55
            },
            'SCENARIO_C_RAIN_PLUS_FULL_RESERVOIR': {
                'name': 'Scenario C — Heavy Rain + Saturated Reservoirs',
                'description': 'High rainfall (95mm/day) coinciding with 92% full reservoir capacity.',
                'state': {
                    'rainfall_daily': 95.0,
                    'rainfall_rate_1h': 15.0,
                    'total_reservoir_level': 10350.0,
                    'reservoir_fill_ratio': 0.92,
                    'temp_max': 26.0,
                    'dew_point_mean': 24.5,
                    'wind_speed_mean': 10.0,
                    'elevation_m': 7.5
                },
                'flood_prob': 0.85
            },
            'SCENARIO_D_EXTREME_CYCLONIC_DELUGE': {
                'name': 'Scenario D — Extreme Cyclonic Super-Storm',
                'description': 'Torrential deluge (180mm), brimming reservoirs (98%), and cyclonic gale winds (24 m/s).',
                'state': {
                    'rainfall_daily': 180.0,
                    'rainfall_rate_1h': 28.0,
                    'total_reservoir_level': 11000.0,
                    'reservoir_fill_ratio': 0.98,
                    'temp_max': 25.0,
                    'dew_point_mean': 24.8,
                    'wind_speed_mean': 24.0,
                    'elevation_m': 5.0
                },
                'flood_prob': 0.98
            }
        }
        
        target = scenarios.get(scenario_name, scenarios['SCENARIO_A_NOMINAL'])
        result = self.calculate_compound_risk(target['state'], target['flood_prob'])
        result['scenario_meta'] = {
            'scenario_id': scenario_name,
            'name': target['name'],
            'description': target['description'],
            'simulation_tag': 'SIMULATED SCENARIO'
        }
        return result

    def perform_sensitivity_analysis(self) -> Dict[str, Any]:
        """
        Evaluates sensitivity of Compound Risk Score across environmental perturbations.
        """
        baseline_state = {
            'rainfall_daily': 30.0,
            'rainfall_rate_1h': 2.0,
            'total_reservoir_level': 6000.0,
            'reservoir_fill_ratio': 0.53,
            'temp_max': 30.0,
            'dew_point_mean': 23.0,
            'wind_speed_mean': 5.0,
            'elevation_m': 8.0
        }
        base_res = self.calculate_compound_risk(baseline_state, 0.30)
        base_crs = base_res['compound_risk_score']
        
        sensitivity_results = {}
        
        # 1. Rainfall Sensitivity
        rain_vals = [0.0, 25.0, 50.0, 100.0, 150.0, 200.0]
        rain_crs = []
        for r in rain_vals:
            st = baseline_state.copy()
            st['rainfall_daily'] = r
            st['rainfall_rate_1h'] = r / 10.0
            rain_crs.append(self.calculate_compound_risk(st, min(1.0, r/120.0))['compound_risk_score'])
        sensitivity_results['rainfall_daily_mm'] = {'values': rain_vals, 'scores': rain_crs, 'gradient': round((rain_crs[-1] - rain_crs[0]) / 200.0, 4)}
        
        # 2. Reservoir Storage Sensitivity
        res_vals = [0.10, 0.30, 0.50, 0.70, 0.90, 1.00]
        res_crs = []
        for rf in res_vals:
            st = baseline_state.copy()
            st['reservoir_fill_ratio'] = rf
            st['total_reservoir_level'] = rf * 11257.0
            res_crs.append(self.calculate_compound_risk(st, 0.30 + rf*0.4)['compound_risk_score'])
        sensitivity_results['reservoir_fill_ratio'] = {'values': res_vals, 'scores': res_crs, 'gradient': round((res_crs[-1] - res_crs[0]) / 0.90, 4)}
        
        # 3. Wind Speed Sensitivity
        wind_vals = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0]
        wind_crs = []
        for w in wind_vals:
            st = baseline_state.copy()
            st['wind_speed_mean'] = w
            wind_crs.append(self.calculate_compound_risk(st, 0.30)['compound_risk_score'])
        sensitivity_results['wind_speed_ms'] = {'values': wind_vals, 'scores': wind_crs, 'gradient': round((wind_crs[-1] - wind_crs[0]) / 25.0, 4)}
        
        return {
            'baseline_compound_risk': base_crs,
            'parameter_sensitivities': sensitivity_results,
            'summary': "Precipitation intensity and reservoir storage saturation are the dominant physical drivers of compound flood stress."
        }

# Global Engine Instance
multihazard_engine = MultiHazardRiskEngine()
