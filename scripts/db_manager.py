import sys
import logging
from typing import Any, List, Dict
from scripts.db_client import get_db

logger = logging.getLogger("db-manager")
logging.basicConfig(level=logging.INFO)

class DBManager:
    """
    Authoritative schema manager for Abraxas ArangoDB.
    Ported from infra/mcp/db_manager.py
    """
    def __init__(self, database=None):
        self.db = database or get_db()

    def initialize_schema(self, skill_manifests: List[Dict] = None):
        logger.info("Initializing AbraxasDB Schema...")
        try:
            # 1. Core Document Collections (LOWERCASE)
            core_collections = [
                "tasks", "knowledge_fragments", "epistemic_ledger", 
                "fragments", "claims", "events", "sources", 
                "incidents", "reviews", "benchmark_results", "files"
            ]
            for col in core_collections:
                if not self.db.has_collection(col):
                    self.db.ensure_collection(col, edge=False)
                    logger.info(f"Created collection: {col}")

            # 2. Sovereign Edges (ALL_CAPS)
            sovereign_edges = [
                "DERIVED_FROM", "NEXT_STEP", "SUPERSEDES", 
                "SESS_TO_HYPO", "HYPO_TO_CONCEPT", "CONCEPT_TO_PLAN",
                "DEPENDS_ON", "STORED_IN", "PROVENANCE_OF", "TASK_EDGES"
            ]
            for edge in sovereign_edges:
                if not self.db.has_collection(edge):
                    self.db.ensure_collection(edge, edge=True)
                    logger.info(f"Created edge: {edge}")

            if skill_manifests:
                for manifest in skill_manifests:
                    for col in manifest.get("collections", []):
                        name = col if isinstance(col, str) else col.get("name")
                        is_edge = False if isinstance(col, str) else col.get("edge", False)
                        if not self.db.has_collection(name):
                            self.db.ensure_collection(name, edge=is_edge)
                            logger.info(f"Created skill collection: {name}")

            return True
        except Exception as e:
            logger.error(f"Schema initialization failed: {e}")
            return False

    def hard_reset(self):
        """Drops all non-system collections to allow for clean migration."""
        logger.info("Executing Hard Reset of all user collections...")
        collections = self.db.db.collections()
        for col in collections:
            name = col['name']
            if not col.get('system', True):
                logger.info(f"Dropping {name}...")
                self.db.db.delete_collection(name)

if __name__ == "__main__":
    manager = DBManager()
    # In production, you'd call this sequentially: hard_reset() -> initialize_schema()
    manager.initialize_schema()
