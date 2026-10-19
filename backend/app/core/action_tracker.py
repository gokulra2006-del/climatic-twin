"""
Municipal Emergency Action Effectiveness Tracker
ClimateTwin Chennai Digital Twin Project

Tracks whether recommended operational interventions (pump deployments, road diversions,
reservoir gate regulations, hospital power transfers, tanker dispatches) were:
- Suggested by NOVA Decision Intelligence
- Acknowledged by Agency Personnel (GCC, TANGEDCO, CMWSSB, Traffic Police)
- In Progress / Dispatched
- Completed
- Evaluated for Effectiveness with field telemetry & outcome evidence
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

# Seed actions representing typical Chennai monsoon and crisis interventions
INITIAL_SEED_ACTIONS: List[Dict[str, Any]] = [
    {
        "action_id": "ACT-CHN-2026-001",
        "action_type": "pump_deployment",
        "title_en": "Deploy 50 HP High-Capacity Dewatering Pump at Velachery Micro-Basin",
        "title_ta": "வேளச்சேரி தாழ்வான பகுதியில் 50 HP நீர் இறைக்கும் மோட்டார் பொருத்துதல்",
        "target_location": "Velachery 100-ft Road / AGS Colony Junction (Zone 14)",
        "zone": "Zone 14 - Perungudi",
        "latitude": 12.9796,
        "longitude": 80.2185,
        "department": "Greater Chennai Corporation (GCC)",
        "urgency": "HIGH",
        "suggested_by": "NOVA Decision Support System",
        "suggested_at": "2026-10-18T08:00:00Z",
        "status": "effective",
        "acknowledged_at": "2026-10-18T08:15:00Z",
        "acknowledged_by": "AE M. Murugan (GCC Zone 14 SWD)",
        "completed_at": "2026-10-18T09:45:00Z",
        "response_time_minutes": 105.0,
        "effectiveness_rating": "HIGHLY_EFFECTIVE",
        "outcome_evidence": "Pump operated continuously for 4 hours; stagnant surface flood depth reduced from 0.65m to 0.12m, restoring two-wheeler transit.",
        "verified_source_url": "https://chennaicorporation.gov.in/gcc/pump_deployment_log_2026.pdf",
        "notes": "Verified against GCC Storm Water Drainage motor deployment register."
    },
    {
        "action_id": "ACT-CHN-2026-002",
        "action_type": "road_closure_warning",
        "title_en": "Precautionary Subway Closure & Emergency Traffic Diversion",
        "title_ta": "கணேசபுரம் ரயில்வே சுரங்கப்பாதை முன்னெச்சரிக்கை மூடல் மற்றும் போக்குவரத்து மாற்றம்",
        "target_location": "Ganesapuram Subway, Vyasarpadi (Zone 4)",
        "zone": "Zone 4 - Tondiarpet",
        "latitude": 13.1118,
        "longitude": 80.2634,
        "department": "Greater Chennai Traffic Police / GCC",
        "urgency": "CRITICAL",
        "suggested_by": "NOVA Hydro-Meteorological Hazard Rule",
        "suggested_at": "2026-10-18T09:30:00Z",
        "status": "effective",
        "acknowledged_at": "2026-10-18T09:40:00Z",
        "acknowledged_by": "Inspector S. Parthasarathy (Traffic)",
        "completed_at": "2026-10-18T10:10:00Z",
        "response_time_minutes": 40.0,
        "effectiveness_rating": "HIGHLY_EFFECTIVE",
        "outcome_evidence": "Bollards and barricades deployed prior to subway accumulating 1.8m backwater; zero vehicle entrapments reported.",
        "verified_source_url": "https://traffic.chennaipolice.gov.in/sitrep/subway_clearance.pdf",
        "notes": "Coordinated with automated depth sensor alerting at Vyasarpadi rail underpass."
    },
    {
        "action_id": "ACT-CHN-2026-003",
        "action_type": "reservoir_monitoring",
        "title_en": "Regulated Controlled Discharge from Chembarambakkam Reservoir",
        "title_ta": "செம்பரம்பாக்கம் ஏரியிலிருந்து கட்டுப்படுத்தப்பட்ட உபரி நீர் வெளியேற்றம்",
        "target_location": "Chembarambakkam Surplus Sluice & Adyar River Headworks",
        "zone": "Zone 11 - Valasaravakkam Basin",
        "latitude": 13.0116,
        "longitude": 80.0606,
        "department": "Tamil Nadu Water Resources Department (WRD)",
        "urgency": "CRITICAL",
        "suggested_by": "NOVA Inflow Hydrological Model",
        "suggested_at": "2026-10-18T11:00:00Z",
        "status": "in_progress",
        "acknowledged_at": "2026-10-18T11:20:00Z",
        "acknowledged_by": "Executive Engineer K. Ramesh (WRD)",
        "completed_at": None,
        "response_time_minutes": None,
        "effectiveness_rating": "PENDING_ASSESSMENT",
        "outcome_evidence": "Controlled release capped at 3,500 cusecs; Adyar river downstream causeway gauges being monitored hourly.",
        "verified_source_url": "https://www.wrd.tn.gov.in/reservoir_bulletin.pdf",
        "notes": "Action ongoing to maintain safe freeboard ahead of predicted 6-hour rainfall band."
    },
    {
        "action_id": "ACT-CHN-2026-004",
        "action_type": "hospital_power_transfer",
        "title_en": "Verification of Hospital Emergency Diesel Generator Backup Fuel Levels",
        "title_ta": "அரசு மருத்துவமனைகளில் அவசர கால ஜெனரேட்டர் எரிபொருள் இருப்பு சரிபார்ப்பு",
        "target_location": "Rajiv Gandhi Government General Hospital & Kilpauk Medical College",
        "zone": "Zone 5 - Royapuram",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "department": "TANGEDCO & State Health Dept",
        "urgency": "HIGH",
        "suggested_by": "NOVA Healthcare Vulnerability Module",
        "suggested_at": "2026-10-18T12:00:00Z",
        "status": "completed",
        "acknowledged_at": "2026-10-18T12:25:00Z",
        "acknowledged_by": "Chief Electrical Engineer TANGEDCO Central",
        "completed_at": "2026-10-18T14:15:00Z",
        "response_time_minutes": 135.0,
        "effectiveness_rating": "HIGHLY_EFFECTIVE",
        "outcome_evidence": "Fuel reservoirs filled to 100% (72-hour operational runtime confirmed for ICUs and surgical wards).",
        "verified_source_url": "https://www.tangedco.gov.in/critical_facility_check.pdf",
        "notes": "Precautionary cascade protection following elevated substation flood alert."
    }
]

class ActionTracker:
    def __init__(self):
        self.actions: List[Dict[str, Any]] = list(INITIAL_SEED_ACTIONS)

    def list_actions(
        self,
        status: Optional[str] = None,
        department: Optional[str] = None,
        action_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        res = self.actions
        if status:
            res = [a for a in res if str(a.get("status", "")).lower() == status.lower()]
        if department:
            res = [a for a in res if department.lower() in str(a.get("department", "")).lower()]
        if action_type:
            res = [a for a in res if str(a.get("action_type", "")).lower() == action_type.lower()]
        return res

    def get_action(self, action_id: str) -> Optional[Dict[str, Any]]:
        for a in self.actions:
            if a["action_id"] == action_id:
                return a
        return None

    def create_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        action_id = f"ACT-CHN-{datetime.now(timezone.utc).year}-{len(self.actions) + 1:03d}"
        record = {
            **data,
            "action_id": action_id,
            "suggested_at": datetime.now(timezone.utc).isoformat(),
            "status": "suggested",
            "effectiveness_rating": "PENDING_ASSESSMENT"
        }
        self.actions.insert(0, record)
        return record

    def update_action(
        self,
        action_id: str,
        status: str,
        reviewer_name: str,
        effectiveness_rating: Optional[str] = None,
        outcome_evidence: Optional[str] = None,
        verified_source_url: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        action = self.get_action(action_id)
        if not action:
            raise ValueError(f"Action '{action_id}' not found")

        now_iso = datetime.now(timezone.utc).isoformat()
        action["status"] = status.lower()
        
        if status.lower() == "acknowledged" and not action.get("acknowledged_at"):
            action["acknowledged_at"] = now_iso
            action["acknowledged_by"] = reviewer_name

        if status.lower() in ("completed", "effective", "ineffective"):
            if not action.get("completed_at"):
                action["completed_at"] = now_iso
            if action.get("suggested_at") and action.get("completed_at"):
                try:
                    s_dt = datetime.fromisoformat(action["suggested_at"].replace("Z", "+00:00"))
                    c_dt = datetime.fromisoformat(action["completed_at"].replace("Z", "+00:00"))
                    action["response_time_minutes"] = round((c_dt - s_dt).total_seconds() / 60.0, 1)
                except Exception:
                    pass

        if effectiveness_rating:
            action["effectiveness_rating"] = effectiveness_rating
        if outcome_evidence:
            action["outcome_evidence"] = outcome_evidence
        if verified_source_url:
            action["verified_source_url"] = verified_source_url
        if notes:
            action["notes"] = notes

        return action

    def get_summary(self) -> Dict[str, Any]:
        total = len(self.actions)
        effective = sum(1 for a in self.actions if a.get("status") == "effective" or a.get("effectiveness_rating") == "HIGHLY_EFFECTIVE")
        completed = sum(1 for a in self.actions if a.get("status") in ("completed", "effective"))
        in_progress = sum(1 for a in self.actions if a.get("status") == "in_progress")
        suggested = sum(1 for a in self.actions if a.get("status") == "suggested")

        completed_times = [a["response_time_minutes"] for a in self.actions if a.get("response_time_minutes")]
        avg_response = round(sum(completed_times) / len(completed_times), 1) if completed_times else 0.0

        return {
            "total_actions": total,
            "completed_actions": completed,
            "effective_actions": effective,
            "in_progress_actions": in_progress,
            "suggested_pending_actions": suggested,
            "effectiveness_rate": round((effective / completed) * 100, 1) if completed > 0 else 0.0,
            "average_response_time_minutes": avg_response,
            "monitored_departments": ["Greater Chennai Corporation", "CMWSSB", "TANGEDCO", "Traffic Police"]
        }

action_tracker = ActionTracker()
