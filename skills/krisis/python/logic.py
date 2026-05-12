from typing import List, Dict, Any

class KrisisAuditLogic:
    """
    Implements the non-verdict ethical boundary audit for autonomous discoveries.
    """
    def __init__(self):
        self.frameworks = ["Consequentialist", "Deontological", "Virtue Ethics", "Care Ethics"]

    def audit_discovery(self, discovery_text: Any) -> Dict[str, Any]:
        """
        Analyzes a discovery for ethical tensions without issuing a verdict.
        """
        # Ensure input is a string (handle dicts from Aporia)
        if isinstance(discovery_text, dict):
            # Extract the most relevant text from Aporia's output
            discovery_text = str(discovery_text.get("gaps", "Discovery gap identified"))
        elif not isinstance(discovery_text, str):
            discovery_text = str(discovery_text)
        tensions = []
        tension_keywords = {
            "Consequentialist": ["outcome", "stakeholder", "utility", "cost", "benefit"],
            "Deontological": ["duty", "right", "rule", "forbidden", "obligation"],
            "Virtue Ethics": ["character", "virtue", "integrity", "wisdom", "prudence"],
            "Care Ethics": ["relationship", "vulnerability", "need", "nurture", "empathy"]
        }

        for framework, keywords in tension_keywords.items():
            found = [k for k in keywords if k in discovery_text.lower()]
            if found:
                tensions.append({
                    "framework": framework,
                    "points_of_tension": found,
                    "observation": f"Discovery triggers {framework} considerations via: {', '.join(found)}."
                })

        return {
            "discovery": discovery_text,
            "tensions_found": len(tensions) > 0,
            "analysis": tensions,
            "verdict": "NONE (C-PROHIBITION)",
            "closing": "This deliberation has surfaced the ethical landscape. The decision remains yours."
        }
