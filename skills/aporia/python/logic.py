import re
from typing import List, Dict, Any

class AporiaLogic:
    """
    Aporia: The Void Mapper.
    Specializes in identifying 'unknown-unknowns' and logical gaps in reasoning chains.
    """
    def __init__(self):
        # Common indicators of logical leaps or unfounded conclusions
        self.gap_indicators = [
            r"therefore it must be",
            r"it follows that",
            r"clearly,",
            r"obviously,",
            r"without doubt",
            r"it is evident that"
        ]

    def analyze_gap(self, reasoning_chain: str, known_premises: List[str]) -> Dict[str, Any]:
        """
        Analyzes a reasoning chain against a set of known premises to find epistemic gaps.
        """
        gaps = []
        
        # 1. Check for explicit gap indicators
        for pattern in self.gap_indicators:
            if re.search(pattern, reasoning_chain, re.IGNORECASE):
                gaps.append({
                    "type": "LOGICAL_LEAP",
                    "indicator": pattern,
                    "description": "Conclusion drawn with a high-certainty indicator but potentially missing grounding."
                })

        # 2. Cross-reference claims with known premises
        # Simple heuristic: find key nouns/concepts in conclusions that aren't in premises
        conclusions = self._extract_conclusions(reasoning_chain)
        for conclusion in conclusions:
            if not any(self._has_semantic_overlap(conclusion, premise) for premise in known_premises):
                gaps.append({
                    "type": "UNGROUNDED_CLAIM",
                    "claim": conclusion,
                    "description": "Conclusion does not appear to be grounded in the provided known premises."
                })

        return {
            "has_gaps": len(gaps) > 0,
            "gap_count": len(gaps),
            "gaps": gaps,
            "status": "VOID_MAPPED" if gaps else "SOLID"
        }

    def _extract_conclusions(self, text: str) -> List[str]:
        # Simple extraction based on common conclusion markers
        markers = ["conclusion:", "therefore,", "thus,", "in summary:"]
        sentences = text.split('.')
        conclusions = []
        for s in sentences:
            if any(marker in s.lower() for marker in markers):
                conclusions.append(s.strip())
        return conclusions if conclusions else [text.split('.')[-1].strip()]

    def _has_semantic_overlap(self, claim: str, premise: str) -> bool:
        # Basic keyword overlap as a proxy for semantic connection
        claim_words = set(re.findall(r'\w+', claim.lower()))
        premise_words = set(re.findall(r'\w+', premise.lower()))
        # Ignore common stop words
        stop_words = {'the', 'is', 'and', 'a', 'of', 'in', 'to', 'it', 'that', 'this'}
        significant_claim = claim_words - stop_words
        overlap = significant_claim.intersection(premise_words)
        return len(overlap) >= 2 # Require at least 2 overlapping significant words

