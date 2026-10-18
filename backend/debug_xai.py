from app.core.explainability import explainability_engine
features = {'rainfall_daily': 250.0, 'total_reservoir_level': 95.0, 'temp_mean': 28.0}
importances = explainability_engine._compute_attributions(features)
print('Importances length:', len(importances))
