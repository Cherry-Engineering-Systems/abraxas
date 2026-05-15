import json
import os
from infra.api.src.core.graph import SovereignGraphClient

def seed_research_data():
    """
    Seeds research data from the Chaos Suite and Gauntlet results 
    into the ArangoDB 'claims' collection.
    """
    print("🚀 Starting Research Data Seeding...")
    
    graph_client = SovereignGraphClient()
    # Ensure collections exist
    graph_client.ensure_skeleton_collections()
    
    results_dir = "tests/results"
    all_results = []
    
    # Collect all final-results.json files across model directories
    for root, dirs, files in os.walk(results_dir):
        for file in files:
            if file == "final-results.json":
                path = os.path.join(root, file)
                with open(path, 'r') as f:
                    try:
                        data = json.load(f)
                        all_results.append(data)
                    except json.JSONDecodeError:
                        print(f"⚠️ Failed to parse {path}")

    if not all_results:
        print("⚠️ No final-results.json files found. Looking for generic results...")
        # Fallback to any json in results if final-results not present
        all_results = []
        for root, dirs, files in os.walk(results_dir):
            for file in files:
                if file.endswith(".json"):
                    path = os.path.join(root, file)
                    with open(path, 'r') as f:
                        try:
                            all_results.append(json.load(f))
                        except json.JSONDecodeError:
                            pass

    # We treat the "conclusion" or "overall_avg_score" as the claim if it's a summary,
    # or we iterate through results if it's a list of trials.
    
    seeded_count = 0
    for res_data in all_results:
        # Generate a synthetic claim from the result summary
        conclusion = res_data.get("conclusion", "Sovereign Validation Result")
        if not conclusion:
            conclusion = f"Model result summary: {res_data.get('overall_avg_score', 'N/A')}"
            
        # We link this claim to the 'fragments' created during vault population
        # since these results result from those fragments' application.
        # Here we use a generic fragment link or create a new one for the result.
        
        evidence_id = graph_client.add_fragment(
            content=f"Empirical Result: {str(res_data)[:500]}...",
            provenance_id="Chaos-Suite-Run",
            trust_weight=0.8
        )
        
        graph_client.create_claim(
            conclusion=conclusion,
            evidence_ids=[evidence_id]
        )
        seeded_count += 1

    print(f"🌟 Research data seeding complete. {seeded_count} claim chains created in ArangoDB.")

if __name__ == "__main__":
    seed_research_data()
