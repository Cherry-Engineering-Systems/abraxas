import uuid
import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("harmonia-orchestrator")

@dataclass
class ContextEnvelope:
    """
    The fundamental state object that travels between skills during composition.
    """
    id: str = field(default_factory=lambda: f"env-{uuid.uuid4().hex[:8]}")
    origin_skill: Optional[str] = None
    origin_command: Optional[str] = None
    epistemic_mode: str = "sol"  # sol | nox | mixed
    primary_output: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    handoff_history: List[Dict[str, Any]] = field(default_factory=list)

    def update_output(self, skill: str, content: Any):
        self.primary_output = content
        self.handoff_history.append({
            "skill": skill,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "output_preview": str(content)[:100] + "..." if content else "None"
        })

class HarmoniaOrchestrator:
    """
    Sovereign Skill Composition Engine.
    Executes chains of MCP tools via state handoff.
    """
    def __init__(self, mcp_client: Any):
        self.mcp = mcp_client
        self.active_compositions: Dict[str, List[str]] = {}

    def compose(self, name: str, sequence: List[str]):
        """Defines a named sequential workflow."""
        self.active_compositions[name] = sequence
        logger.info(f"Composition {name} defined: {' -> '.join(sequence)}")
        return f"[COMPOSITION CREATED] Name: {name}, Sequence: {' -> '.join(sequence)}"

    async def execute_sequence(self, name: str, initial_input: Any) -> ContextEnvelope:
        """Executes the named sequence with state propagation."""
        if name not in self.active_compositions:
            raise ValueError(f"Composition {name} not defined.")

        sequence = self.active_compositions[name]
        envelope = ContextEnvelope()
        envelope.primary_output = initial_input

        logger.info(f"Executing composition {name}...")

        for skill_name in sequence:
            logger.info(f"Invoking {skill_name}...")
            
            # In a real MCP environment, we would lookup the tool mapped to this skill
            # For now, we simulate the call using the mcp_client
            try:
                # Protocol: we call the tool associated with the skill
                # This assumes the mcp_client has a way to route skill_name to a specific tool
                result = await self.mcp.call_tool(skill_name, {"input": envelope.primary_output})
                
                envelope.update_output(skill_name, result)
                envelope.origin_skill = skill_name
                
            except Exception as e:
                logger.error(f"Error in step {skill_name}: {e}")
                envelope.metadata["error"] = str(e)
                envelope.metadata["failed_at"] = skill_name
                break

        return envelope

    def audit_dag(self, composition_id: str) -> Dict[str, Any]:
        """
        Metanoia: Analyzes a cognitive composition DAG for bottlenecks,
        redundancy, and inefficiency.
        """
        if composition_id not in self.active_compositions:
            return {"error": f"Composition {composition_id} not found."}

        sequence = self.active_compositions[composition_id]
        bottlenecks = []
        redundant = []

        if len(sequence) > 4:
            bottlenecks.append({
                "step": sequence[2],
                "reason": "Deeply nested sequential chain — consider parallel branches."
            })

        seen = set()
        for step in sequence:
            if step in seen:
                redundant.append({"step": step, "reason": "Duplicate invocation in sequence."})
            seen.add(step)

        report = {
            "composition_id": composition_id,
            "step_count": len(sequence),
            "bottlenecks": bottlenecks,
            "redundancy": redundant,
            "efficiency_score": max(0, 1.0 - (len(redundant) * 0.2) - (len(bottlenecks) * 0.15)),
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        }
        logger.info(f"Metanoia DAG audit for '{composition_id}': efficiency={report['efficiency_score']:.2f}")
        return report

    def propose_refinement(self, composition_id: str) -> Dict[str, Any]:
        """
        Metanoia: Proposes DAG restructuring with quantified efficiency delta.
        """
        audit = self.audit_dag(composition_id)
        if "error" in audit:
            return audit

        current_efficiency = audit["efficiency_score"]
        proposals = []

        if audit["bottlenecks"]:
            proposals.append({
                "action": "parallelize",
                "target": audit["bottlenecks"][0]["step"],
                "description": "Convert deep sequential chain into parallel branch where steps are independent.",
                "expected_efficiency_gain": 0.15
            })

        if audit["redundancy"]:
            proposals.append({
                "action": "deduplicate",
                "target": audit["redundancy"][0]["step"],
                "description": "Remove redundant invocation — results are already available in the envelope.",
                "expected_efficiency_gain": 0.20
            })

        projected_efficiency = min(1.0, current_efficiency + sum(p["expected_efficiency_gain"] for p in proposals))

        refinement = {
            "composition_id": composition_id,
            "current_efficiency": current_efficiency,
            "proposed_efficiency": projected_efficiency,
            "efficiency_delta": projected_efficiency - current_efficiency,
            "proposals": proposals,
            "status": "APPROVED" if projected_efficiency > current_efficiency else "NO_CHANGE",
            "proposed_at": datetime.now(timezone.utc).isoformat()
        }
        logger.info(f"Metanoia DAG refinement for '{composition_id}': delta={refinement['efficiency_delta']:.2f}")
        return refinement

