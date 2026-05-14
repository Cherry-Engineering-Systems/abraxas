import os
from arango import ArangoClient

def test_connection():
    url = "http://localhost:8529"
    user = "root"
    password = "5orange5"

    print(f"Testing connection to {url} as {user} with password '5orange5'...")
    try:
        client = ArangoClient(hosts=url)
        # Attempt to connect to the system database
        sys_db = client.db("_system", username=user, password=password)
        # Perform a simple operation to verify access
        collections = sys_db.collections()
        print(f"Connection Successful! Access to _system db granted.")
        print(f"Collections found: {collections}")
        return True
    except Exception as e:
        print(f"Connection Failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
