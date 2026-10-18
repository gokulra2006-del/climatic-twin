import re

path = 'backend/app/core/alert_intelligence.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# Add import
code = code.replace('from app.core.sensor_health import sensor_health_engine',
                    'from app.core.sensor_health import sensor_health_engine\nfrom app.core.explainability import explainability_engine')

search = '''        # 6. Generate NOVA Explanation
        trend_msg = "rapidly increasing" if (score - prev_score) > 0.10 else ("increasing" if score > prev_score else "stable")
        nova_explanation = self._generate_nova_explanation(
            hazard_type, severity, prev_severity, score, 
            [], top_asset, confidence, sensor_msg, trend_msg
        )'''

replace = '''        # 6. Generate ML/UX Explanation (Feature Attributions)
        trend_msg = "rapidly increasing" if (score - prev_score) > 0.10 else ("increasing" if score > prev_score else "stable")
        
        # Call the new operator-facing explanation layer
        hazard_payload = {
            "contributing_features": current_state,
            "risk_level": severity
        }
        xai_result = explainability_engine.explain(hazard_type, hazard_payload)
        
        # We append the sensor msg to the new plain-English explanation
        nova_explanation = f"{xai_result['explanation']} {sensor_msg}"'''

code = code.replace(search, replace)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)
