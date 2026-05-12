import uuid
import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

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
            "timestamp": datetime.utcnow().isoformat(),
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

