import os
from typing import Any, Dict, List, Optional
from arango import ArangoClient

class AbraxasDB:
    def __init__(self, host: Optional[str] = None, db_name: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None):
        # Prioritize environment variables and enforce their presence
        self.host = host or os.getenv("ARANGO_URL")
        self.db_name = db_name or os.getenv("ARANGO_DB")
        self.username = username or os.getenv("ARANGO_USER")
        self.password = password or os.getenv("ARANGO_ROOT_PASSWORD")
        
        missing = []
        if not self.host: missing.append("ARANGO_URL")
        if not self.db_name: missing.append("ARANGO_DB")
        if not self.username: missing.append("ARANGO_USER")
        if not self.password: missing.append("ARANGO_ROOT_PASSWORD")
        
        if missing:
            raise EnvironmentError(f"Missing required ArangoDB environment variables: {', '.join(missing)}")
        
        self.client = ArangoClient(hosts=self.host)
        
        # Ensure database exists
        try:
            sys_db = self.client.db('_system', username=self.username, password=self.password)
            if not sys_db.has_database(self.db_name):
                sys_db.create_database(self.db_name)
        except Exception as e:
            raise RuntimeError(f"Critical failure during DB initialization: {e}")
            
        self.db = self.client.db(self.db_name, username=self.username, password=self.password)

    def has_collection(self, name: str) -> bool:
        return self.db.has_collection(name)

    def ensure_collection(self, name: str, edge: bool = False):
        if not self.has_collection(name):
            self.db.create_collection(name, edge=edge)

    def insert(self, collection: str, document: Dict[str, Any]) -> str:
        col = self.db.collection(collection)
        res = col.insert(document)
        return res['_id']

    def query(self, aql: str, bind_vars: Dict[str, Any] = None) -> List[Any]:
        cursor = self.db.aql.execute(aql, bind_vars=bind_vars)
        return list(cursor)

    def update(self, doc_id: str, collection: str, update_data: Dict[str, Any]):
        col = self.db.collection(collection)
        key = doc_id.split('/')[-1] if '/' in doc_id else doc_id
        col.update({'_key': key}, update_data)

    def delete(self, doc_id: str, collection: str):
        col = self.db.collection(collection)
        key = doc_id.split('/')[-1] if '/' in doc_id else doc_id
        col.delete(key)

    def aql_cursor(self, aql: str, bind_vars: Dict[str, Any] = None):
        return self.db.aql.execute(aql, bind_vars=bind_vars)

# Singleton for shared use across scripts
db = AbraxasDB()
