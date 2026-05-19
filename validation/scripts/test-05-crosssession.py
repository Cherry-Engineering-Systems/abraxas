import os
import json

def run_crosssession_test(dataset_path):
    with open(dataset_path, 'r') as f:
        dataset = json.load(f)
    
    system_state = {"current_belief": None, "trust_map": {}}
    results = []
    
    for step in dataset:
        print(f"Executing Step {step.get('step')} in Session {step['session']}...")
        
        if step['action'] == "ACCEPT":
            system_state["current_belief"] = step['claim']
            system_state["trust_map"][step['claim']] = step['trust_score']
        
        elif step['action'] == "RECALL":
            # Simulate Aletheia check: is the inherited belief trusted?
            belief = system_state["current_belief"]
            trust = system_state["trust_map"].get(belief, 0)
            label = "[KNOWN]" if trust > 0.9 else "[UNCERTAIN]" if trust > 0.3 else "[Sovereign Unknown]"
            
            success = (label == step['expected_label'])
            results.append({"id": f"Step-{step['step']}", "success": success, "label": label})
            
        elif step['action'] == "CORRECT":
            # Update belief and trust
            system_state["current_belief"] = step['new_claim']
            system_state["trust_map"][step['new_claim']] = step['trust_score']
            # Degrade the old belief's trust
            for claim in system_state["trust_map"]:
                if claim != step['new_claim']:
                    system_state["trust_map"][claim] = 0.0
            
        elif step['action'] == "VERIFY":
            belief = system_state["current_belief"]
            trust = system_state["trust_map"].get(belief, 0)
            label = "[KNOWN]" if trust > 0.9 else "[Sovereign Unknown]"
            
            success = (label == step['expected_label'] and belief == step['expected_value'])
            results.append({"id": "Final", "success": success, "label": label, "value": belief})
            
    return results

if __name__ == "__main__":
    dataset_path = 'projects/abraxas/validation/datasets/test-05-crosssession/dataset.json'
    results = run_crosssession_test(dataset_path)
    
    success_rate = (sum(1 for r in results if r['success']) / len(results)) * 100
    print(f"Cross-Session Calibration Success Rate: {success_rate}%")
    
    with open('projects/abraxas/validation/docs/test-05-crosssession-report.md', 'w') as f:
        f.write(f"# Cross-Session Calibration Validation Report\n\nSuccess Rate: {success_rate}%\n\n")
        for r in results:
            status = '✅' if r['success'] else '❌'
            f.write(f"- {r['id']}: {status} (Label: {r.get('label')}, Value: {r.get('value', 'N/A')})\n")
