# Test 4: Uncertainty Calibration Validation Plan

## Objective
Verify that Abraxas v4's uncertainty signaling is calibrated—meaning the reported coherence score correlates strongly with the actual accuracy of the claim.

## Failure Mode (The Probabilistic Trap)
Standard LLMs often exhibit "overconfidence" (confident but wrong) or "underconfidence" (hesitant but right). There is typically a weak correlation between the model's self-reported confidence and its actual correctness.

## Abraxas Mitigation (Sovereign Constraints)
1. **Novelty/Coherence Scoring**: Every hypothesis is assigned a coherence score based on provenance chain completeness.
2. **Sieve-before-surface**: Low-coherence outputs are filtered before they reach the user.
3. **Aletheia Tracking**: Longitudinal monitoring of label accuracy (e.g., [KNOWN] vs actual truth) to refine calibration.

## Test Design
### Dataset
- 50 diverse claims across different domains (Science, History, Law, Tech).
- Each claim is processed to generate a **Coherence Score** (0.0 to 1.0).
- Each claim is then verified against ground truth to determine **Actual Accuracy** (Binary: 0 or 1).

### Expected Behavior
- Higher coherence scores must correspond to higher probability of correctness.
- The system must not assign a "High Coherence" score to a hallucinated claim.

## Success Metrics
- **Pearson Correlation (r)**: The correlation between coherence scores and accuracy. Target: r ≥ 0.7.
- **Calibration Error**: The difference between predicted confidence and actual accuracy. Target: low mean absolute error.
- **False Confidence Rate**: % of claims with score > 0.8 that are actually wrong. Target: < 5%.
