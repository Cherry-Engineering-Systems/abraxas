# Implementation Plan: Epistemic Chain-of-Thought (eCoT)

## 1. Overview
The Epistemic Chain-of-Thought (eCoT) system is a dynamic reasoning graph designed for the Abraxas architecture. Unlike traditional linear CoT, eCoT treats every step of reasoning as a node in a directed acyclic graph (DAG) with explicit epistemic labels. This allows the system to track the "provenance of truth," enabling the dynamic pruning of failed hypotheses and the expansion of verified paths while preserving the genesis of every idea.

## 2. Epistemic Labeling System
We extend the existing Janus/Episteme labels to support a lifecycle of reasoning.

### 2.1 Core Labels
- **`[KNOWN]`**: Verifiable fact. Grounded in `[RET]` (Vault) or `[DIR]` (Parametric) with high confidence.
- **`[INFERRED]`**: Logically derived from `[KNOWN]` or other `[INFERRED]` nodes.
- **`[HYPOTHESIS]`**: A proposed explanation or bridge. Not yet verified.
- **`[UNCERTAIN]`**: Material that is relevant but lacks sufficient grounding to be `[KNOWN]`.
- **`[UNKNOWN]`**: Explicit gap in knowledge. A "null" node that triggers research.
- **`[SKEPTIC]`**: A counter-argument or challenge to a node.

### 2.2 Label Transition Logic
Nodes are not static; they evolve as the reasoning process progresses:
- **`[HYPOTHESIS]` $\rightarrow$ `[INFERRED]`**: When a logical bridge is successfully constructed.
- **`[HYPOTHESIS]` $\rightarrow$ `[KNOWN]`**: When empirical evidence is retrieved (`[RET]`).
- **`[INFERRED]` $\rightarrow$ `[SKEPTIC]`**: When a downstream contradiction is found.
- **`[UNKNOWN]` $\rightarrow$ `[HYPOTHESIS]`**: After a research-engine run provides a plausible lead.

## 3. Graph Structure & Dynamics

### 3.1 Node Anatomy
Each node in the eCoT graph contains:
- **ID**: Unique identifier.
- **Content**: The specific claim or step.
- **Label**: Current epistemic status.
- **Genesis**: The original label and timestamp (preserves the "how I got here").
- **Edges**:
    - **Parents**: Nodes that support this claim.
    - **Children**: Nodes derived from this claim.
- **Confidence Score**: 0.0 to 1.0.

### 3.2 Dynamic Pruning and Addition
- **Addition**: New nodes are added as the agent explores. If a node is `[UNKNOWN]`, it spawns a `research-engine` call.
- **Pruning (Rupture Protocol)**: If a node is marked `[SKEPTIC]` and its confidence drops below a threshold, the system performs a **downstream prune**. All child nodes derived from a failed premise are marked as `[INVALID]` or removed, triggering a re-evaluation of the reasoning path.
- **Preservation**: Even when pruned, nodes are moved to a `shadow_graph` (similar to Janus's Nox face) to prevent the system from repeating the same logical error.

## 4. Technical Implementation Plan

### 4.1 Data Model
- **Storage**: Use a Graph database (ArangoDB) to store the eCoT.
- **Schema**: 
    - **Collection `nodes`**: `{ id, content, label, genesis_label, confidence, timestamp }`
    - **Collection `edges`**: `{ from, to, relationship_type (supports/contradicts/derives) }`

### 4.2 Integration with Abraxas Skills
1. **`episteme` Skill**: The source of truth for label transitions. `episteme_trace` will be used to determine if a node can move from `[HYPOTHESIS]` to `[KNOWN]`.
2. **`logos-math` Skill**: Used to verify `[INFERRED]` nodes involving quantitative reasoning.
3. **`janus-system`**: The Threshold will dictate which "face" (Sol/Nox) generates the initial `[HYPOTHESIS]` nodes.

### 4.3 Execution Workflow
1. **Initialization**: Query $\rightarrow$ Sol $\rightarrow$ Initial `[KNOWN]` nodes (from Vault).
2. **Expansion**: `[KNOWN]` $\rightarrow$ `[HYPOTHESIS]` $\rightarrow$ `[INFERRED]`.
3. **Verification**: If confidence is low, trigger `episteme_audit`.
4. **Closure**: Final result is the path of highest confidence from the root to the conclusion.

## 5. Success Criteria (DoD)
- [ ] System can generate a CoT where each step has a valid epistemic label.
- [ ] System can demonstrate a "pivot" (pruning a child node when a parent is refuted).
- [ ] The final output includes the "Genesis Path," showing how a `[HYPOTHESIS]` became `[KNOWN]`.
- [ ] Integration with ArangoDB for persistence across sessions.
