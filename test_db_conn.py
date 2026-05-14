import os
from arango import ArangoClient

def test_connection():
    url = "http://localhost:8529"
    user = "root"
    
    try:
        with open('/root/.openclaw/workspace/projects/abraxas/.env.sovereign', 'r') as f:
            for line in f:
                if line.startswith('ARANGO_ROOT_PASSWORD='):
                    password = line.split('=')[1].strip()
    except:
        password = "5orange5"

    print(f"Testing connection to {url} as {user}...")
    try:
        # Correct pattern for python-arango:
        client = ArangoClient(hosts=url)
        # Connect to the system database first to verify credentials
        sys_db = client.db("_system", username=user, password=password)
        # Try to perform a simple operation: list collections
        collections = sys_db.collections()
        print(f"Connection Successful! Access to _system db granted.")
        print(f"Collections found: {collections}")
        return True
    except Exception as e:
        print(f"Connection Failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
