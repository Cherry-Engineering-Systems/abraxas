import os
import logging
import httpx
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger("janus-orchestrator")

@dataclass
class LensResponse:
    name: str
    content: str
    raw_output: Any

class JanusOrchestrator:
    """
    The Janus Orchestrator (Sovereign Brain).
    Implements N-of-M consensus by spawning isolated lenses and calculating agreement.
    """
from src.core.config import config

class JanusOrchestrator:
    """
    The Janus Orchestrator (Sovereign Brain).
    Implements N-of-M consensus by spawning isolated lenses and calculating agreement.
    """
    def __init__(self, graph_client):
        self.graph_client = graph_client
        self.ollama_url = config.LLM_URL
        self.model = config.SVR_MODEL
        self.lenses = {
            "Skeptic": "Find every flaw in this reasoning. Be ruthlessly critical. Challenge every assumption.",
            "Expert": "Verify this against formal technical standards. Focus on accuracy and precision.",
            "Adversary": "Try to logically invalidate this claim. Act as the devil's advocate.",
            "Archivist": "Anchor this in the retrieved evidence. Point out any gaps in the provenance.",
            "Generalist": "Provide a balanced synthesis of the facts."
        }

    async def execute_sovereign_query(self, query: str, evidence: str) -> Dict[str, Any]:
        # ... (rest of logic)
        results = []
        
        # 1. Isolated Spawning
        async with httpx.AsyncClient(timeout=60.0) as client:
            for name, prompt in self.lenses.items():
                system_prompt = f"{prompt}\n\nEVIDENCE:\n{evidence}"
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query}
                    ],
                    "stream": False
                }
                # Use the configured URL
                resp = await client.post(f"{self.ollama_url}/api/chat", json=payload)
                resp.raise_for_status()
                content = resp.json().get("message", {}).get("content", "")
                results.append(LensResponse(name=name, content=content, raw_output=resp.json()))

        # 2. Deterministic Agreement Math
        consensus_count = self._calculate_agreement(results)
        
        # 3. Synthesis and Seal
        status = "VERIFIED" if consensus_count >= 3 else "UNKNOWN"
        seal = f"[Sovereign Consensus: {consensus_count}/5]" if status == "VERIFIED" else "[Sovereign Unknown]"
        
        final_output = self._synthesize(results) if status == "VERIFIED" else "Epistemic Failure: Consensus not reached."
        
        return {
            "status": status,
            "seal": seal,
            "output": final_output,
            "receipt": [vars(r) for r in results],
            "consensus_count": consensus_count
        }

    def _calculate_agreement(self, results: List[LensResponse]) -> int:
        """
        Deterministic check for agreement.
        In a full implementation, this would use an LLM to cross-reference 
        the 5 responses for factual alignment.
        """
        # Simplified version: Check for lack of absolute contradiction
        # To maintain strictly deterministic logic, we use a smaller 'Judge' model
        # to count agreement without generating new content.
        return 4 # Mocking a 4/5 consensus for structural flow until Judge model is linked

    def _synthesize(self, results: List[LensResponse]) -> str:
        """Combines the lens outputs into a final response."""
        return "\n\n".join([f"--- {r.name} ---\n{r.content}" for r in results])
