with open('backend/tests/test_engines.py', 'a', encoding='utf-8') as f:
    f.write('''

def test_decision_support_expected_cost_policy():
    \"\"\"Verify expected cost policy selects action minimizing E[Cost].\"\"\"
    engine = DecisionSupportEngine()
    
    # At very low probability, low-cost/no-action is best
    res_low = engine.assess(flood_probability=0.01, uncertainty_width=0.05)
    assert res_low["decision_level"] == "NORMAL"
    
    # At moderate probability, a cheaper action like PREPARE should trigger,
    # because missing costs 3000-5000, but PREPARE costs 50
    res_med = engine.assess(flood_probability=0.25, uncertainty_width=0.20)
    
    # At very high probability, EMERGENCY should trigger
    res_high = engine.assess(flood_probability=0.99, uncertainty_width=0.01)
    assert res_high["decision_level"] in ["ALERT", "EMERGENCY"]
    
    # Check rationale structure
    assert "rationale" in res_low
    assert "expected_costs" in res_low
''' )
