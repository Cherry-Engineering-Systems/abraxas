import json
import os
from scripts.db_client import db

def migrate_vault():
    print("Migrating Sovereign Vault...")
    path = "/Users/tylergarlick/@Projects/abraxas/vault/sovereign_vault.json"
    with open(path, 'r') as f:
        data = json.load(f)
    
    db.ensure_collection("fragments")
    for frag in data['fragments']:
        db.insert("fragments", frag)
    print(f"Successfully migrated {len(data['fragments'])} fragments.")

def migrate_codex():
    print("Migrating Sovereign Codex Ledger...")
    path = "/Users/tylergarlick/@Projects/abraxas/Sovereign_Codex_Ledger.json"
    with open(path, 'r') as f:
        data = json.load(f)
    
    db.ensure_collection("tasks")
    db.ensure_collection("DEPENDS_ON", edge=True)
    
    for task in data['tasks']:
        subtasks = task.pop('subtasks', [])
        task_id = db.insert("tasks", task)
        
        for sub in subtasks:
            sub_id = db.insert("tasks", sub)
            db.insert("DEPENDS_ON", {
                "_from": sub_id,
                "_to": task_id,
                "type": "subtask_of"
            })
    print("Successfully migrated Codex Ledger.")

def migrate_ethos():
    print("Migrating Ethos Registry...")
    path = "/Users/tylergarlick/@Projects/abraxas/skills/ethos/sources.json"
    with open(path, 'r') as f:
        data = json.load(f)
    
    db.ensure_collection("sources")
    count = 0
    for tier_id, tier_info in data['tiers'].items():
        for source in tier_info['sources']:
            source_doc = {
                **source,
                "tier": int(tier_id),
                "tier_name": tier_info['name'],
                "weight": tier_info['weight'],
                "tier_description": tier_info['description']
            }
            db.insert("sources", source_doc)
            count += 1
    print(f"Successfully migrated {count} Ethos Sources.")

def migrate_soter():
    print("Migrating Soter Review Queue...")
    path = "/Users/tylergarlick/@Projects/abraxas/skills/soter/storage/human-review-queue.json"
    with open(path, 'r') as f:
        data = json.load(f)
    
    db.ensure_collection("incidents")
    for review in data['reviews']:
        db.insert("incidents", review)
    print(f"Successfully migrated {len(data['reviews'])} Soter reviews.")

if __name__ == "__main__":
    try:
        migrate_vault()
        migrate_codex()
        migrate_ethos()
        migrate_soter()
        print("\nCore migration completed successfully.")
    except Exception as e:
        print(f"Migration failed: {e}")
