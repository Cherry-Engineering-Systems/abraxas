import json
import os
import glob
from scripts.db_client import db

def migrate_benchmarks():
    print("Migrating Benchmark results...")
    # Search for all test-results JSONs in research/benchmarks (and archive)
    patterns = [
        "/Users/tylergarlick/@Projects/abraxas/research/benchmarks/*.json",
        "/Users/tylergarlick/@Projects/abraxas/archive/legacy_benchmarks/tests/results/**/*.json"
    ]
    
    db.ensure_collection("benchmark_results")
    db.ensure_collection("files") # To link results to the source file
    
    total_migrated = 0
    for pattern in patterns:
        for file_path in glob.glob(pattern, recursive=True):
            try:
                with open(file_path, 'r') as f:
                    content = json.load(f)
                
                # Create a file document for the source
                file_id = db.insert("files", {
                    "path": file_path,
                    "filename": os.path.basename(file_path),
                    "category": "benchmark_result"
                })
                
                # Since benchmarks can be large and varied, we store the result
                # but relate it to the file.
                result_id = db.insert("benchmark_results", {
                    "data": content,
                    "source_file": file_id,
                    "timestamp": os.path.getmtime(file_path)
                })
                
                # Link Result -> File
                db.ensure_collection("STORED_IN", edge=True)
                db.insert("STORED_IN", {
                    "_from": result_id,
                    "_to": file_id,
                    "type": "result_file"
                })
                
                total_migrated += 1
                print(f"Migrated: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"Failed to migrate {file_path}: {e}")
                
    print(f"Successfully migrated {total_migrated} benchmark result sets.")

if __name__ == "__main__":
    try:
        migrate_benchmarks()
        print("\nBenchmark migration completed successfully.")
    except Exception as e:
        print(f"Benchmark migration failed: {e}")
