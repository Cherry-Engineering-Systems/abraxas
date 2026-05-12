from mcp.server.fastmcp import FastMCP
from infra.mcp.context import AbraxasContext
from skills.auto_agon.python.logic import AutoAgonLogic

def register_tools(mcp: FastMCP, context: AbraxasContext):
    """Registers Auto-Agon tools to the Abraxas MCP server."""
    logic = AutoAgonLogic(mcp)

    @mcp.tool()
    async def auto_stress_test(claim: str) -> str:
        """
        Automatically triggers an adversarial Red Team debate against a claim.
        Returns the convergence rate and promotion status.
        """
        result = await logic.trigger_stress_test(claim)
        
        output = (
            f"[AUTO-AGON — STRESS TEST]\n"
            f"Claim: {result['claim']}\n"
            f"Convergence Rate: {result['convergence_rate']:.2%}\n"
            f"Status: {result['status']}\n"
            f"Action: {result['action']}\n\n"
            f"Report Summary:\n{result['report']}"
        )
        return output

    @mcp.tool()
    async def promote_truth(claim: str, proof_trace: str) -> str:
        """
        Promotes a belief to [VERIFIED TRUTH] after it survives the Auto-Agon trial.
        """
        success = logic.promote_truth(claim, proof_trace)
        return "✓ Truth promoted to Sovereign Ledger." if success else "✗ Promotion failed."
