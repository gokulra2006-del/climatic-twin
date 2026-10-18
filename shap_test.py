import os
import pickle
import numpy as np

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

_MODEL_CACHE = None
def get_explainable_model():
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE
    
    path = os.path.join(os.path.dirname(__file__), '..', 'models', 'best_live_model.pkl')
    try:
        with open(path, 'rb') as f:
            data = pickle.load(f)
        _MODEL_CACHE = data
        return data
    except Exception:
        return None

def compute_feature_attributions(features_dict):
    data = get_explainable_model()
    if not data or 'model' not in data or not SHAP_AVAILABLE:
        # Fallback to simple logic
        return []
    
    feature_names = data['features']
    model = data['model']
    
    # Extract base estimator from CalibratedClassifierCV
    try:
        base_rf = model.calibrated_classifiers_[0].estimator
    except:
        try:
            base_rf = model.estimator
        except:
            return []
    
    X_arr = np.array([[features_dict.get(f, 0.0) for f in feature_names]])
    try:
        explainer = shap.TreeExplainer(base_rf)
        shap_values = explainer.shap_values(X_arr)
        # Random Forest returns list of shape [1, num_features] per class
        # Class 1 is flood
        if isinstance(shap_values, list):
            sv = shap_values[1][0]
        else:
            sv = shap_values[0]
            
        importances = []
        for i, f in enumerate(feature_names):
            importances.append({
                'feature': f,
                'importance': sv[i],
                'value': features_dict.get(f, 0.0)
            })
        
        # Sort by absolute magnitude of SHAP value
        importances.sort(key=lambda x: abs(x['importance']), reverse=True)
        return importances
    except Exception as e:
        print(f"SHAP Error: {e}")
        return []
