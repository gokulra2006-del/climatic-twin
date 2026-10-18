path = 'backend/app/core/decision_support.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

search = '''        decision_record = {
            "decision_level": decision_level,
            "decision_score": round(dss, 4),
            "decision_confidence": decision_confidence,'''

replace = '''        decision_record = {
            "decision_level": decision_level,
            "decision_score": round(dss, 4),
            "decision_confidence": decision_confidence,
            "expected_costs": expected_costs,
            "rationale": f"Selected {decision_level} by minimizing expected cost (P50={flood_probability:.2f}, Width={uncertainty_width:.2f}).",'''

code = code.replace(search, replace)
with open(path, 'w', encoding='utf-8') as f:
    f.write(code)
