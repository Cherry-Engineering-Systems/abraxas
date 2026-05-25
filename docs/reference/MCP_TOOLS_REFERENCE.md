# Abraxas MCP Tools Reference

**Source:** Auto-generated from ~/abraxas/skills/*/mcp_tools.py  
**Generated:** 2026-05-25  
**Repo:** github.com/Cherry-Engineering-Systems/abraxas

## Tool Counts
- 32 skill directories with mcp_tools.py
- Total functions: ~75+

## All Tools by Skill

### chronos
- `index_claim` — Temporal claim indexing
- `detect_drift` — Drift detection
- `resolve_conflict` — Temporal conflict resolution

### config_registry
- `config_get` — Get config value
- `config_get_all` — Get all config
- `config_get_section` — Get config section
- `config_reload` — Reload configuration

### cvp
- `resolve_consensus` — N-of-M consensus
- `log_sovereign_gap` — Log divergence

### dianoia
- `quantify_uncertainty` — Uncertainty quantification
- `calculate_brier_score` — Brier score calculation

### episteme
- `episteme_trace` — Trace epistemic origin
- `episteme_audit` — Session-wide epistemic audit

### epistemic-atlas
- `trace_artifact` — Trace claim provenance
- `query_epistemic_map` — Query knowledge graph

### ethos
- `ethos_score` — Source credibility tier
- `ethos_resolve` — Source conflict resolution

### guardrail
- `guardrail_audit` — Final output audit
- `guardrail_veto` — Block and retry

### guardrail_monitor
- `check_value_saliency` — Value saliency check
- `verify_ground_truth` — Ground truth verification
- `arbitrate_conflict` — Conflict arbitration

### harmonia
- `compose_workflow` — Workflow composition
- `execute_sequence` — Execute sequence
- `check_conflict` — Check DAG conflicts

### hermes
- `add_agent_position` — Record agent position
- `compute_consensus` — Weighted consensus
- `weight_record` — Update agent weight

### kairos
- `kairos_filter` — Filter by relevance
- `kairos_urgency` — Determine urgency

### ledger
- `create_task` — Create task
- `get_ready_tasks` — Get ready tasks
- `update_task_status` — Update status
- `add_dependency` — Add dependency
- `get_task` — Get task
- `delete_task` — Delete task
- `get_tasks_by_project` — Get project tasks

### metanoia (async)
- `metanoia_agon_audit`
- `metanoia_agon_evolve`
- `metanoia_harmonia_audit`
- `metanoia_harmonia_refine`

### mnemon
- `record_belief` — Record belief
- `track_revision` — Track belief revision
- `flag_prompted` — Flag prompted belief

### mnemosyne
- `mnemosyne_recall` — Recall memories
- `mnemosyne_store` — Store memories

### omniscient-auditor
- `decompose_document` — Decompose to propositions
- `generate_heat_map` — Generate heat map

### oneironautics
- `log_dream` — Log dream entry
- `witness_symbol` — Witness symbol
- `update_shadow_ledger` — Update shadow ledger

### pheme
- `verify_claim` — Verify claim
- `update_source_trust` — Update source trust

### plan
- `start_clarity_session` — Start clarity session
- `extract_unknowns` — Extract unknowns
- `export_map` — Export clarity map

### prognosis (async)
- `prognosis_forecast`
- `prognosis_signal_anticipate`
- `prognosis_calibrate`

### project_bridge
- `cross_project_search` — Search across projects
- `unified_retrospective` — Unified retro
- `project_mapping` — Project relationships
- `project_bridge_health_check` — Health check

### prometheus
- `get_profile` — Get user profile
- `set_preference` — Set preference
- `record_signal` — Record signal

### research_engine
- `web_search` — Web search
- `web_fetch` — Fetch URL
- `synthesize_report` — Synthesize report
- `deep_dive_research` — Deep dive research
- `research_engine_health_check` — Health check

### retrospectives
- `save_retro` — Save retrospective
- `get_retros_for_period` — Get retros for period
- `create_ledger_task` — Create ledger task

### scribe
- `ingest_fragment` — Ingest fragment

### soter
- `verify_claim` — Verify claim
- `run_soter_query` — Run Soter query
- `check_constitution_adherence` — Constitution check
- `soter_assess` — Soter assessment
- `soter_trigger` — Trigger Soter

### sovereign_core
- `sovereign_patcher` — Apply patches
- `config_management` — Config management
- `system_state_audit` — System state audit
- `sovereign_core_health_check` — Health check

### sovereign_engine
- `calculate_sovereign_weight` — Calculate weight
- `compute_integrated_confidence` — Compute confidence
- `calculate_rlcr` — Calculate RLCR
- `verify_consensus` — Verify consensus
- `get_epistemic_label` — Get epistemic label

### sovereign_scribe
- `ingest_fragment` — Ingest fragment

### stochasmos (async)
- `stochasmos_pressure_point`
- `stochasmos_seed`
- `stochasmos_assess_risk`

### synesis (async)
- `synesis_map`
- `synesis_theorize`
- `synesis_validate`

---

## MCP Server Info
- **URL:** `http://abraxas-mcp:9900/mcp`
- **Transport:** streamable-http
- **Status:** Sovereign Mode (24 skills loaded, database connected)

## OpenClaw Integration
Tools are available as `abraxas_mcp__tool_name` via the MCP bundle.