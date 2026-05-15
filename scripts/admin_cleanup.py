import os
import sys
from arango import ArangoClient

def admin_cleanup():
    host = os.getenv("ARANGO_URL", "http://localhost:8529")
    user = os.getenv("ARANGO_USER", "root")
    password = os.getenv("ARANGO_ROOT_PASSWORD", "")
    
    client = ArangoClient(hosts=host)
    sys_db = client.db('_system', username=user, password=password)
    
    # 1. Delete legacy 'abraxas' database
    if sys_db.has_database('abraxas'):
        print("Deleting legacy 'abraxas' database...")
        sys_db.delete_database('abraxas')
        print("Legacy database deleted.")
    else:
        print("Legacy 'abraxas' database not found. Skipping.")

    # 2. Ensure 'abraxas_db' is clean (drop all non-system collections)
    if sys_db.has_database('abraxas_db'):
        print("Cleaning 'abraxas_db' collections...")
        target_db = client.db('abraxas_db', username=user, password=password)
        collections = target_db.collections()
        for col in collections:
            name = col['name']
            if not col.get('system', True):
                print(f"Dropping: {name}")
                target_db.delete_collection(name)
        print("Clean slate prepared in abraxas_db.")
    else:
        print("'abraxas_db' not found. It will be created by the manager.")

if __name__ == "__main__":
    admin_cleanup()
