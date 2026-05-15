# Sub-Agent Content Strategy: Delegation vs. Direct Synthesis

This document defines the operational policy for when the Sovereign Brain should delegate tasks to specialized sub-agents versus when the primary agent should perform direct synthesis.

## 1. Core Principle: The Token-Complexity Threshold

The primary determinant for delegation is the **Source Token Volume** and the **Surgicality** of the required operation.

### 1.1 The 20K Token Rule
- **Surgical Tasks (< 20K source tokens):** Use sub-agents. When the scope of the task involves analyzing or modifying a limited set of files, a specialized sub-agent provides higher precision and reduces the risk of context pollution.
- **Synthesis Tasks (> 20K source tokens):** Use direct writing/synthesis. When the task requires holistic understanding across a massive codebase or synthesizing multiple high-volume documents, the primary agent should handle the synthesis to maintain a unified global state and avoid "fragmentation loss" during handoffs.

## 2. Delegation Matrix

| Task Type | Scale | Recommended Approach | Reasoning |
| :--- | :--- | :--- | :--- |
| **Bug Fix** | Single file / Small module | $\rightarrow$ Sub-agent | Surgical precision, isolated impact |
| **Feature Add** | Across 2-3 files | $\rightarrow$ Sub-agent | Controlled implementation, focused testing |
| **Architecture Review** | Project-wide | $\rightarrow$ Direct Synthesis | Global context requirement, holistic alignment |
| **Documentation** | Site-wide / Multi-volume | $\rightarrow$ Direct Synthesis | Narrative consistency, cross-volume coherence |
| **Refactoring** | Wide-scale (e.g., path migration) | $\rightarrow$ Direct Synthesis | Need for global search-and-replace consistency |
| **Research Deep-Dive** | Specific domain | $\rightarrow$ Sub-agent | Deep-dive specialization, iterative refinement |

## 3. Quality Control & Handoffs

### 3.1 The "Zero-Failure" Mandate
Sub-agents must not fail in a sequence of three (0-for-3). If a sub-agent fails to achieve the objective after three attempts, the primary agent must:
1. Immediately terminate the sub-agent session.
2 import the sub-agent's context.
3 Perform direct synthesis to solve the bottleneck.

### 3.2 Handoff Protocol
When delegating to a sub-agent, the primary agent must provide:
- **Surgical Scope**: Exact file paths and line ranges.
- **Success Criteria**: A deterministic Definition of Done (DoD).
- **Constraint Set**: Explicit "What NOT to do" instructions to prevent over-reach.

## 4. Operational Summary

- **Delegate** for surgery.
- **Synthesize** for architecture.
- **Intervene** when sub-agents spiral.
