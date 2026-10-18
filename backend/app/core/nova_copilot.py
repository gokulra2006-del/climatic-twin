"""Evidence-grounded NOVA copilot with an optional OpenRouter provider.

The key is read only on the backend.  When no provider key is configured the
same endpoint remains useful through a deterministic, traceable fallback.
"""

import json
import os
from typing import Any, Dict

import httpx


class NovaCopilot:
    endpoint = "https://openrouter.ai/api/v1/chat/completions"

    def provider_status(self) -> Dict[str, Any]:
        configured = bool(os.getenv("OPENROUTER_API_KEY", "").strip())
        return {
            "configured": configured,
            "provider": "OpenRouter" if configured else "Evidence-grounded local fallback",
            "model": os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini") if configured else None,
            "key_location": "Backend environment only; never expose an API key in the browser.",
            "boundary": "NOVA summarises supplied telemetry and model outputs. It must not issue public warnings, infer unseen field conditions, or replace an authorised human decision.",
        }

    def _fallback(self, question: str, briefing: Dict[str, Any]) -> str:
        """Useful no-key response grounded entirely in the supplied briefing."""
        brief = briefing.get("decision_brief", {})
        threat = briefing.get("priority_threat", {})
        confidence = briefing.get("confidence", {})
        asset = briefing.get("highest_priority_asset", {})
        q = question.lower()
        if any(word in q for word in ["action", "do now", "next step", "recommend"]):
            return f"Recommended next step: {brief.get('action', briefing.get('recommended_action', 'Review the latest inputs.'))} Owner: {brief.get('owner', 'Duty analyst')}. Review in {brief.get('review_in_minutes', 60)} minutes."
        if any(word in q for word in ["why", "driver", "priority"]):
            return "Current priority is " + str(threat.get("type", "UNKNOWN")).replace("_", " ") + ". " + " ".join(briefing.get("why_now", [])[:2])
        if any(word in q for word in ["reliable", "confidence", "trust", "data"]):
            return f"Confidence is {confidence.get('level', 'UNKNOWN')}. {confidence.get('explanation', '')} Verify the next telemetry cycle before escalation."
        if any(word in q for word in ["asset", "location", "where"]):
            return f"The current screening-priority asset is {asset.get('Asset Name', 'not available')}. This priority is model-derived and needs field verification."
        return f"Current assessed risk is {threat.get('level', 'UNKNOWN')} for {str(threat.get('type', 'UNKNOWN')).replace('_', ' ')}. {brief.get('evidence_boundary', '')}"

    async def answer(self, question: str, briefing: Dict[str, Any]) -> Dict[str, Any]:
        status = self.provider_status()
        citations = [
            "Current telemetry quality summary",
            "Prototype risk-model output",
            "Asset screening result",
        ]
        if not status["configured"]:
            return {
                "answer": self._fallback(question, briefing),
                "mode": "LOCAL_EVIDENCE_FALLBACK",
                "citations": citations,
                "safety_notice": status["boundary"],
            }

        system = (
            "You are NOVA, a cautious climate-risk decision-support copilot. "
            "Use only the supplied briefing. Do not invent measurements, sources, impacts, "
            "or operational authority. State uncertainty and recommend human verification. "
            "Never present a draft as a public warning or emergency command. Keep the response under 180 words."
        )
        payload = {
            "model": status["model"],
            "temperature": 0.2,
            "max_tokens": 260,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": f"Briefing JSON:\n{json.dumps(briefing, default=str)}\n\nQuestion: {question}"},
            ],
        }
        try:
            headers = {"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}", "Content-Type": "application/json"}
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(self.endpoint, headers=headers, json=payload)
                response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()
            return {"answer": content, "mode": "OPENROUTER_LLM", "citations": citations, "safety_notice": status["boundary"]}
        except Exception:
            return {
                "answer": self._fallback(question, briefing),
                "mode": "LOCAL_EVIDENCE_FALLBACK_AFTER_PROVIDER_ERROR",
                "citations": citations,
                "safety_notice": "The external AI provider was unavailable. " + status["boundary"],
            }


nova_copilot = NovaCopilot()
