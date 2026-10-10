import logging

logger = logging.getLogger(__name__)

class CriticalAsset:
    def __init__(self, asset_id, name, vulnerability, service_criticality, cost_miss, cost_fa, cost_delay):
        self.asset_id = asset_id
        self.name = name
        self.vulnerability = vulnerability
        self.service_criticality = service_criticality
        self.cost_miss = cost_miss
        self.cost_fa = cost_fa
        self.cost_delay = cost_delay # Cost incurred if action is delayed

ASSET_CATALOGUE = {
    "HOSPITAL_ACCESS": CriticalAsset(
        "HOSPITAL_ACCESS", "Hospital Access Route", 
        vulnerability=0.9, service_criticality=1.0, 
        cost_miss=50000, cost_fa=2000, cost_delay=10000
    ),
    "PUMP_STATION": CriticalAsset(
        "PUMP_STATION", "Primary Pump Station", 
        vulnerability=0.7, service_criticality=0.8, 
        cost_miss=20000, cost_fa=1000, cost_delay=5000
    ),
    "RESIDENTIAL_ROAD": CriticalAsset(
        "RESIDENTIAL_ROAD", "Residential Sector Road", 
        vulnerability=0.4, service_criticality=0.3, 
        cost_miss=5000, cost_fa=500, cost_delay=1000
    )
}

class ImpactBasedWarningEngine:
    """
    Scientific Purpose: Replaces abstract Green/Orange/Red alerts with concrete 
    impact-based warning classes. Calculates Equity-Weighted Priority Scores
    based on compound socio-economic factors.
    """
    
    @staticmethod
    def calculate_priority_score(prob: float, impact_magnitude: float, asset: CriticalAsset):
        """
        Calculates Equity-Weighted Priority Score:
        Risk = Probability * Impact Magnitude
        Priority = Risk * Vulnerability * Service Criticality
        """
        risk = prob * impact_magnitude
        equity_priority = risk * asset.vulnerability * asset.service_criticality
        return equity_priority, risk

    @staticmethod
    def generate_warning(prob: float, impact_magnitude: float, uncertainty_width: float, 
                         lead_time_hrs: float, asset_id: str):
        asset = ASSET_CATALOGUE[asset_id]
        priority, risk = ImpactBasedWarningEngine.calculate_priority_score(prob, impact_magnitude, asset)
        
        # Impact-Based Warning Class Logic
        if priority >= 0.7:
            if asset_id == "HOSPITAL_ACCESS":
                warning_class = "CRITICAL: HOSPITAL_ACCESS_LOST (Immediate Reroute Required)"
            elif asset_id == "PUMP_STATION":
                warning_class = "CRITICAL: PUMP_STATION_OVER_CAPACITY (Grid Failure Imminent)"
            else:
                warning_class = "CRITICAL: ROAD_IMPASSABLE"
        elif priority >= 0.4:
            warning_class = f"SEVERE: {asset_id}_COMPROMISED (Action within {max(1, int(lead_time_hrs))}h)"
        elif priority >= 0.15:
            warning_class = f"MODERATE: {asset_id}_AT_RISK (Deploy spotters)"
        else:
            warning_class = "MINOR: NORMAL_OPERATIONS"

        # Dynamically evaluate if delayed action cost pushes us to act early despite uncertainty
        delayed_penalty = asset.cost_delay * (1.0 / max(1.0, lead_time_hrs)) * uncertainty_width
        optimal_act_threshold = asset.cost_fa / (asset.cost_fa + asset.cost_miss + delayed_penalty)
        
        return {
            "Asset": asset.name,
            "Warning_Class": warning_class,
            "Equity_Priority_Score": priority,
            "Raw_Risk": risk,
            "Optimal_Decision_Threshold": optimal_act_threshold,
            "Action_Required": prob >= optimal_act_threshold
        }
