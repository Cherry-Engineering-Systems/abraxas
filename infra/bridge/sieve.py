import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sovereign-sieve")

@dataclass
class Signal:
    source: str
    content: str
    timestamp: str
    metadata: Dict[str, Any]

class SovereignSieve:
    """
    The Sieve: High-Valence Curation.
    Implement the 'Gremlin Signature' to separate high-valence anomalies from noise.
    """
    def __init__(self, novelty_threshold: float = 0.7, urgency_threshold: float = 0.6):
        self.novelty_threshold = novelty_threshold
        self.urgency_threshold = urgency_threshold
        
    def calculate_valence(self, signal: Signal) -> float:
        """
        Calculate valence score based on Epistemic Novelty and Temporal Urgency.
        Sovereign Formula: Valence = (Novelty * 0.6) + (Urgency * 0.4)
        """
        novelty = self._assess_novelty(signal.content)
        urgency = self._assess_urgency(signal.content, signal.metadata)
        
        valence = (novelty * 0.6) + (urgency * 0.4)
        logger.info(f"Sieve Analysis [{signal.source}]: Novelty={novelty}, Urgency={urgency}, Final Valence={valence}")
        return valence

    def is_high_valence(self, signal: Signal) -> bool:
        """Determines if a signal should pass through to the Sovereign Brain."""
        return self.calculate_valence(signal) >= self.novelty_threshold

    def _assess_novelty(self, content: str) -> float:
        """
        Heuristic for epistemic novelty. 
        """
        novelty_markers = ["anomaly", "paradigm shift", "contradicts", "first-ever", "unexpectedly", "breaking"]
        score = 0.3 # Baseline
        for marker in novelty_markers:
            if marker in content.lower():
                score += 0.2
        return min(score, 1.0)


    def _assess_urgency(self, content: str, metadata: Dict[str, Any]) -> float:
        """Assesses temporal urgency based on content and metadata."""
        urgency_markers = ["immediate", "critical", "urgent", "breaking", "now"]
        score = 0.2 # Baseline
        for marker in urgency_markers:
            if marker in content.lower():
                score += 0.2
        
        # Urgency boost from metadata (e.g., high-frequency updates)
        if metadata.get("priority") == "high":
            score += 0.3
            
        return min(score, 1.0)

    def strip_noise(self, content: str) -> str:
        """
        Noise Reduction: Strips boilerplate and irrelevant formatting.
        """
        # Simplified noise removal
        lines = content.split('\n')
        filtered = [line for line in lines if not line.strip().startswith(('http', '---', '***'))]
        return '\n'.join(filtered).strip()
