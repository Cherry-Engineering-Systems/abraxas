from mcp.server.fastmcp import FastMCP
from infra.mcp.context import AbraxasContext
from skills.krisis.python.logic import KrisisAuditLogic

def register_tools(mcp: FastMCP, context: AbraxasContext):
    """Registers Krisis audit tools to the Abraxas MCP server."""
    logic = KrisisAuditLogic()

    @mcp.tool()
    def krisis_boundary_audit(discovery_text: str) -> str:
        """
        Performs a non-verdict ethical boundary audit of a discovery. 
        Identifies ethical tensions without recommending action.
        """
        result = logic.audit_discovery(discovery_text)
        
        # Format as a professional report
        output = f"[KRISIS — BOUNDARY AUDIT]\n\nDiscovery: {result['discovery']}\n\n"
        if not result['tensions_found']:
            output += "No immediate ethical tensions detected across the 4 frameworks."
        else:
            output += "--- ETHICAL TENSIONS ---\n"
            for t in result['analysis']:
                output += f"- {t['framework']}: {t['observation']}\n"
        
        output += f"\nVerdict: {result['verdict']}\n{result['closing']}"
        return output
