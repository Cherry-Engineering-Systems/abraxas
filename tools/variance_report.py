import json
import numpy as np
from typing import List, Dict, Any

def analyze_variance():
    """
    Analyzes variance in tau behavior across different model scales.
    Loads data from tests/results/v4.5/live-chaos-suite.json.
    """
    print("📊 Generating Cross-Model Variance Report...")
    
    try:
        with open("tests/results/v4.5/live-chaos-suite.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ Error: live-chaos-suite.json not found.")
        return

    model_stats = []
    for m in data:
        res = m["results"]
        weights = [r["attention_sink_avg"] for r in res]
        
        model_stats.append({
            "model": m["model"]["id"],
            "size": m["model"]["params"],
            "mean": np.mean(weights),
            "std": np.std(weights),
            "min": np.min(weights),
            "max": np.max(weights),
            "rejection_rate": sum(1 for r in res if r["triggered_crisis"]) / len(res)
        })

    print("\n" + "="*70)
    print(f"{'Model':<15} | {'Size':<8} | {'Mean Tau':<10} | {'Std Dev':<8} | {'Rejection':<10}")
    print("-" * 70)
    
    for s in model_stats:
        print(f"{s['model']:<15} | {s['size']:<8} | {s['mean']:<10.4f} | {s['std']:<8.4f} | {s['rejection_rate']:<10.1%}")
    
    print("="*70)
    
    # Statistical Conclusion
    global_mean = np.mean([s["mean"] for s in model_stats])
    global_std = np.std([s["mean"] for s in model_stats])
    
    print(f"\nGlobal Mean Attention Sink: {global_mean:.4f}")
    print(f"Cross-Model Variance (StdDev): {global_std:.4f}")
    
    if global_std < 0.05:
        conclusion = "Model-Agnostic Claim VERIFIED: Tau behavior is consistent across scales."
    else:
        conclusion = "Model-Agnostic Claim DISPROVED: Significant variance detected between scales."
        
    print(f"\nVERDICT: {conclusion}")
    
    # Save report
    with open("tests/results/v4.5/cross-model-variance-report.json", "w") as f:
        json.dump({
            "stats": model_stats,
            "global_mean": global_mean,
            "global_std": global_std,
            "conclusion": conclusion
        }, f, indent=2)

if __name__ == "__main__":
    analyze_variance()
