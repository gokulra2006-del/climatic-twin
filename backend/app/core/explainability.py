import os
import pickle
import numpy as np
import datetime
import logging

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

logger = logging.getLogger(__name__)

class ExplainabilityEngine:
    def __init__(self):
        self._model_cache = None
        self._feature_names = []

    def _get_model(self):
        if self._model_cache is not None:
            return self._model_cache, self._feature_names
            
        path = os.path.join(os.path.dirname(__file__), '..', 'models', 'best_live_model.pkl')
        if not os.path.exists(path):
            return None, []
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
            self._model_cache = data.get('model')
            self._feature_names = data.get('features', [])
            return self._model_cache, self._feature_names
        except Exception as e:
            logger.error(f"Error loading model for XAI: {e}")
            return None, []

    def _compute_attributions(self, features: dict):
        model, f_names = self._get_model()
        if not model or not f_names:
            return []

        X_arr = np.array([[features.get(f, 0.0) for f in f_names]])
        
        # Try to extract base RF estimator
        try:
            base_estimator = model.calibrated_classifiers_[0].estimator
        except:
            try:
                base_estimator = model.estimator
            except:
                base_estimator = model

        importances = []
        if SHAP_AVAILABLE:
            try:
                explainer = shap.TreeExplainer(base_estimator)
                shap_values = explainer.shap_values(X_arr)
                if isinstance(shap_values, list):
                    sv = shap_values[1][0]
                else:
                    sv = shap_values[0]
                for i, f in enumerate(f_names):
                    importances.append({
                        'feature': f,
                        'importance': sv[i],
                        'value': features.get(f, 0.0)
                    })
            except Exception as e:
                logger.error(f"SHAP error: {e}")
                SHAP_AVAILABLE = False
                
        if not importances:
            # Fallback to permutation importance
            try:
                base_prob = model.predict_proba(X_arr)[0][1]
                for i, f in enumerate(f_names):
                    X_perm = X_arr.copy()
                    X_perm[0][i] = 0.0  # Zero out feature
                    perm_prob = model.predict_proba(X_perm)[0][1]
                    importances.append({
                        'feature': f,
                        'importance': base_prob - perm_prob,
                        'value': features.get(f, 0.0)
                    })
            except Exception as e:
                logger.error(f"Permutation error: {e}")
                return []
                
        # Sort by absolute magnitude
        importances.sort(key=lambda x: abs(x['importance']), reverse=True)
        return importances

    def _generate_plain_english(self, hazard_type, risk_level, attributions):
        # TEMPLATE-based generator
        if not attributions:
            return f"{risk_level} {hazard_type.lower()} alert based on current environmental readings."
            
        # Top 3 drivers (positive importance)
        drivers = [a for a in attributions if a['importance'] > 0][:3]
        
        if not drivers:
            return f"{risk_level} {hazard_type.lower()} alert triggered by compound conditions."
            
        parts = []
        for d in drivers:
            name = d['feature'].replace('_', ' ').title()
            val = round(d['value'], 2)
            # Add basic units
            unit = ""
            if 'rain' in name.lower(): unit = " mm"
            elif 'temp' in name.lower(): unit = " °C"
            elif 'ratio' in name.lower(): unit = " %"
            elif 'level' in name.lower(): unit = "%"
            parts.append(f"{name} {val}{unit}")
            
        driver_str = ", ".join(parts)
        return f"{risk_level} {hazard_type.lower()} alert: {driver_str}."

    def explain(self, hazard_type: str, hazard_payload: dict, previous_payload: dict = None):
        features = hazard_payload.get('contributing_features', {})
        risk_level = hazard_payload.get('risk_level', hazard_payload.get('early_warning_status', 'UNKNOWN'))
        
        attributions = self._compute_attributions(features)
        
        drivers = [f"↑ {a['feature']} ({a['value']:.2f})" for a in attributions if a['importance'] > 0][:3]
        protectors = [f"↓ {a['feature']} ({a['value']:.2f})" for a in attributions if a['importance'] < 0][:3]
        
        explanation_text = self._generate_plain_english(hazard_type, risk_level, attributions)
        
        return {
            "hazard_type": hazard_type,
            "risk_level": risk_level,
            "dominant_drivers": drivers,
            "protective_factors": protectors,
            "explanation": explanation_text,
            "attributions": attributions, # Provide raw attributions for UI
            "provenance": {
                "model": "SHAP/Permutation Explainable AI Engine v2.0"
            }
        }

explainability_engine = ExplainabilityEngine()
