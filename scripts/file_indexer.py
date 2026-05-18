import os
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, Any
from pathlib import Path
from scripts.db_client import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("file-indexer")

class AbraxasFileIndexer:
    """
    Indexes .abraxas and project files into the ArangoDB 'files' collection.
    """
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.collection = "files"
        db.ensure_collection(self.collection, edge=False)

    def _compute_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        h = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    h.update(chunk)
            return h.hexdigest()
        except Exception as e:
            logger.error(f"Failed to hash {file_path}: {e}")
            return "error"

    def index_directory(self, directory_path: str):
        """Crawl directory and sync metadata to ArangoDB."""
        logger.info(f"Indexing directory: {directory_path}")
        path = Path(directory_path).expanduser()
        
        if not path.exists():
            logger.warning(f"Directory {directory_path} not found. Skipping.")
            return

        for file in path.rglob("*"):
            if file.is_file():
                self._sync_file(file)

    def _sync_file(self, file_path: Path):
        """Update or insert file metadata in the 'files' collection."""
        rel_path = str(file_path.relative_to(self.root_dir)) if self.root_dir else str(file_path)
        
        # Use path as the primary key for simplicity in this bridge
        safe_key = hashlib.md5(rel_path.encode()).hexdigest()
        
        stat = file_path.stat()
        current_hash = self._compute_hash(file_path)
        
        # Check if update is needed (based on mtime or hash)
        doc = {
            "_key": safe_key,
            "path": rel_path,
            "name": file_path.name,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            "hash": current_hash,
            "extension": file_path.suffix
        }
        
        # We use a simplified update: just insert/overwrite
        # In a real production system, we'd check the hash first to avoid unnecessary writes
        db.update(f"files/{safe_key}", "files", doc) if hasattr(db, 'update') else db.insert("files", doc)

if __name__ == "__main__":
    # Example usage within project
    indexer = AbraxasFileIndexer(root_dir=os.getcwd())
    # Index .abraxas directory if it exists (home dir)
    abraxas_home = os.path.expanduser("~/.abraxas")
    indexer.index_directory(abraxas_home)
    # Also index the project root for core files
    indexer.index_directory(os.getcwd())
