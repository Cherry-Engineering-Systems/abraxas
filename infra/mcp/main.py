from fastapi import FastAPI, Response
import uvicorn
from mcp.server.fastmcp import FastMCP
from infra.mcp.context import get_context
from infra.mcp.registry import MCPRegistry
from infra.mcp.db_manager import DBManager

# Initialize the Unified Abraxas OS MCP Server
mcp = FastMCP("abraxas-os")
context = get_context()
registry = MCPRegistry(mcp, context)
db_manager = DBManager(context)

# Initialize FastAPI for REST health and monitoring
app = FastAPI(title="Abraxas Sovereign Monitor")

@app.get("/health")
async def health_check():
    """
    Unified health check that probes both the MCP registry and the Sovereign Database.
    """
    # 1. DB Connectivity
    db_ok = db_manager.connect()
    
    # 2. Skill Registry Status
    skills_loaded = len(registry.get_registered_modules()) > 0
    
    # 3. Basic Filesystem Check
    root_ok = True
    try:
        import os
        root_ok = os.path.exists(context.root_dir)
    except Exception:
        root_ok = False

    if db_ok and skills_loaded and root_ok:
        return {
            "status": "Sovereign Mode",
            "db": "connected",
            "skills_count": len(registry.get_registered_modules()),
            "filesystem": "verified"
        }
    
    return Response(
        content='{"status": "Simulation Mode", "db": "disconnected", "skills": "incomplete"}',
        status_code=503,
        media_type="application/json"
    )

# --- MCP Tools ---
# We keep the system_mode_health_check as an MCP tool for the agent's own self-awareness
@mcp.tool()
def system_mode_health_check() -> str:
    """
    Determines if the server should be in Sovereign Mode or Simulation Mode.
    """
    # Re-use the same logic as the REST endpoint
    db_ok = db_manager.connect()
    skills_loaded = len(registry.get_registered_modules()) > 0
    root_ok = True
    try:
        import os
        root_ok = os.path.exists(context.root_dir)
    except:
        root_ok = False

    if db_ok and skills_loaded and root_ok:
        return "Sovereign Mode"
    return "Simulation Mode"

def main():
    """Main entry point for the unified MCP server."""
    print("Starting Abraxas Unified MCP Server...")
    
    # Initialize Database
    if db_manager.connect():
        print("Database connection established. Running schema checks...")
        db_manager.initialize_schema([]) 
    else:
        print("Warning: Database connection failed. Server will start in Simulation Mode.")

    # Load all skill-based tools
    registry.load_skills()
    
    print(f"Successfully loaded {len(registry.get_registered_modules())} skill modules.")
    
    try:
        print("Launching FastAPI health monitor on port 9900...")
        uvicorn.run(app, host="0.0.0.0", port=9900, log_level="info")
    except Exception as e:
        print(f"CRITICAL: Server failed to start: {e}")


if __name__ == "__main__":
    main()



if __name__ == "__main__":
    main()

