import json
import os
from infra.api.src.core.graph import SovereignGraphClient
from infra.api.src.core.anchor import SovereignAnchor

def populate_vault():
    """
    Migrates fragments from sovereign_vault.json to ArangoDB
    and injects mandatory Genesis Blocks for v4.5.
    """
    print("🚀 Starting Vault Population...")
    
    graph_client = SovereignGraphClient()
    graph_client.ensure_skeleton_collections()
    anchor = SovereignAnchor(graph_client)
    
    # 1. Migrate sovereign_vault.json
    vault_path = "vault/sovereign_vault.json"
    if os.path.exists(vault_path):
        with open(vault_path, 'r') as f:
            data = json.load(f)
            for frag in data.get("fragments", []):
                print(f"Anchoring fragment: {frag['id']}")
                anchor.anchor_truth(frag["fragment"], frag["provenance"])
    else:
        print(f"⚠️ vault/sovereign_vault.json not found. Skipping migration.")

    # 2. Inject v4.5 Mandatory Genesis Blocks
    genesis_blocks = [
        {"content": "Sovereign Trigger tau = 0.15: The critical threshold for attention-sink detection.", "provenance": "v4.5 Constitutional Spec"},
        {"content": "Hash-Chain Mechanics: Every Genesis Block is linked via a SHA-256 chain to the root node.", "provenance": "v4.5 Consensus Spec"},
        {"content": "Divine Priority: Genesis Blocks override all AI-derived probabilistic weights.", "provenance": "Sovereign Hierarchy Protocol"},
        {"content": "Epistemic Lens 1: The Skeptic (Detects sycophancy and fluent lies).", "provenance": "Janus Lenses Spec"},
        {"content": "Epistemic Lens 2: The Expert (Rigorous domain-specific validation).", "provenance": "Janus Lenses Spec"},
        {"content": "Epistemic Lens 3: The Adversary (Active stress-testing and red-teaming).", "provenance": "Janus Lenses Spec"},
        {"content": "Epistemic Lens 4: The Archivist (Historical provenance and truth-tracking).", "provenance": "Janus Lenses Spec"},
        {"content": "Epistemic Lens 5: The Generalist (Cross-domain synthesis and pattern matching).", "provenance": "Janus Lenses Spec"},
    ]
    
    for block in genesis_blocks:
        print(f"Injecting Genesis Block: {block['content'][:50]}...")
        anchor.anchor_truth(block["content"], block["provenance"])
        
    print("🌟 Vault population complete. 20+ fragments (estimate) now in ArangoDB.")

if __name__ == "__main__":
    populate_vault()
