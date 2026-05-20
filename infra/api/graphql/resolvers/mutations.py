import json
import os
from datetime import datetime, timezone
from typing import List, Optional
from infra.api.graphql.context import get_graphql_context
from infra.api.graphql.schema import (
    DreamSession,
    Hypothesis,
    HypothesisMetadataInput,
    Concept,
    ActionablePlan,
    ActionablePlanInput,
    BenchmarkResultInput,
    SovereignPivot,
    SovereignQuest,
    SovereignPivotInput,
    SovereignQuestInput,
    PivotStatus,
    QuestStatus,
    Task,
    TaskInput,
    TaskStatusInput,
    TaskStatus,
    TaskDependency,
    DependencyInput,
    SoterIncident,
    SoterReview,
    SoterIncidentInput,
    SoterReviewInput,
    ShadowEntry,
    ShadowEntryInput,
    SymbolNode,
    SymbolUpdateInput,
    AlchemicalStage,
    EpistemicMark,
    EpistemicMarkInput,
    EpistemicLabel,
)


def _load_sovereign_channels() -> set:
    env_channels = os.getenv("SOVEREIGN_CHANNELS")
    if env_channels:
        return set(c.strip() for c in env_channels.split(",") if c.strip())

    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "config", "sovereign-channels.json")
    try:
        with open(config_path) as f:
            data = json.load(f)
        return set(data.get("sovereignChannels", []))
    except Exception:
        return set()


SOVEREIGN_CHANNELS = _load_sovereign_channels()


def _validate_channel(channel_id: Optional[str]):
    if not channel_id:
        raise ValueError("Unauthorized: channelId is required for write operations")
    if channel_id not in SOVEREIGN_CHANNELS:
        raise ValueError(f"Unauthorized: channel {channel_id} is not authorized for write operations")


def resolve_start_dream_cycle(
    prompt: str, seed_concepts: Optional[List[str]], channel_id: str
) -> DreamSession:
    _validate_channel(channel_id)
    ctx = get_graphql_context()
    coll = ctx.db.collection("dream_sessions")
    doc = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "userPrompt": prompt,
        "seedConcepts": seed_concepts or [],
        "channelId": channel_id,
    }
    result = coll.insert(doc)
    return DreamSession.from_dict(result)


def resolve_create_hypothesis(
    session_id: str,
    raw_pattern_representation: str,
    metadata: HypothesisMetadataInput,
    channel_id: str,
) -> Hypothesis:
    _validate_channel(channel_id)
    ctx = get_graphql_context()

    session = ctx.document("dream_sessions", session_id)
    if session is None:
        raise ValueError("Session not found")

    meta_dict = {
        "noveltyScore": metadata.novelty_score,
        "coherenceScore": metadata.coherence_score,
        "creativeDrivers": [d.value for d in metadata.creative_drivers],
    }

    hypo_coll = ctx.db.collection("hypotheses")
    hypo_doc = {
        "rawPatternRepresentation": raw_pattern_representation,
        "metadata": meta_dict,
        "isValuable": False,
        "channelId": channel_id,
    }
    hypo_result = hypo_coll.insert(hypo_doc)

    edge_coll = ctx.db.collection("SESS_TO_HYPO")
    edge_coll.insert({
        "_from": f"dream_sessions/{session_id}",
        "_to": f"hypotheses/{hypo_result['_key']}",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    })

    return Hypothesis.from_dict({**hypo_result, **hypo_doc})


def resolve_translate_hypothesis_to_concept(
    hypothesis_id: str,
    name: str,
    description: str,
    channel_id: str,
) -> Concept:
    _validate_channel(channel_id)
    ctx = get_graphql_context()

    hypothesis = ctx.document("hypotheses", hypothesis_id)
    if hypothesis is None:
        raise ValueError("Hypothesis not found")

    concept_coll = ctx.db.collection("concepts")
    concept_doc = {
        "name": name,
        "description": description,
        "channelId": channel_id,
    }
    concept_result = concept_coll.insert(concept_doc)

    edge_coll = ctx.db.collection("HYPO_TO_CONCEPT")
    edge_coll.insert({
        "_from": f"hypotheses/{hypothesis_id}",
        "_to": f"concepts/{concept_result['_key']}",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    })

    return Concept.from_dict({**concept_result, **concept_doc})


def resolve_archive_hypothesis(
    hypothesis_id: str, is_valuable: bool, channel_id: str
) -> Hypothesis:
    _validate_channel(channel_id)
    ctx = get_graphql_context()

    doc = ctx.document("hypotheses", hypothesis_id)
    if doc is None:
        raise ValueError("Hypothesis not found")

    doc["isValuable"] = is_valuable
    ctx.db.collection("hypotheses").update(hypothesis_id, doc)
    return Hypothesis.from_dict(doc)


def resolve_ground_concept(
    concept_id: str,
    plan: ActionablePlanInput,
    channel_id: str,
) -> ActionablePlan:
    _validate_channel(channel_id)
    ctx = get_graphql_context()

    concept = ctx.document("concepts", concept_id)
    if concept is None:
        raise ValueError("Concept not found")

    plan_coll = ctx.db.collection("actionable_plans")
    plan_doc = {
        "summary": plan.summary,
        "steps": plan.steps,
        "riskAssessment": plan.risk_assessment,
        "groundingStatus": "ANCHORED",
        "guardrailChecks": [],
        "channelId": channel_id,
    }
    plan_result = plan_coll.insert(plan_doc)

    edge_coll = ctx.db.collection("CONCEPT_TO_PLAN")
    edge_coll.insert({
        "_from": f"concepts/{concept_id}",
        "_to": f"actionable_plans/{plan_result['_key']}",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    })

    return ActionablePlan.from_dict({**plan_result, **plan_doc})


def resolve_upload_benchmark_batch(
    model_id: str,
    results: List[BenchmarkResultInput],
    channel_id: str,
) -> int:
    _validate_channel(channel_id)
    ctx = get_graphql_context()
    coll = ctx.db.collection("benchmark_results")

    for res in results:
        doc = {
            "queryId": res.query_id,
            "category": res.category,
            "queryText": res.query_text,
            "normalResponse": res.normal_response,
            "abraxasResponse": res.abraxas_response,
            "scores": {
                "nl": {
                    "known": res.nl.known,
                    "inferred": res.nl.inferred,
                    "uncertain": res.nl.uncertain,
                    "unknown": res.nl.unknown,
                    "dream": res.nl.dream,
                },
                "al": {
                    "known": res.al.known,
                    "inferred": res.al.inferred,
                    "uncertain": res.nl.uncertain,
                    "unknown": res.al.unknown,
                    "dream": res.al.dream,
                },
            },
            "modelId": model_id,
            "channelId": channel_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        coll.insert(doc)

    return len(results)


def resolve_propose_sovereign_pivot(
    input: SovereignPivotInput,
) -> SovereignPivot:
    _validate_channel(input.channel_id)
    ctx = get_graphql_context()
    
    coll = ctx.db.collection("pivots")
    pivot_doc = {
        "ruptureId": input.rupture_id,
        "proposal": input.proposal,
        "expectedDelta": input.expected_delta,
        "status": PivotStatus.PROPOSED.value,
        "channelId": input.channel_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    result = coll.insert(pivot_doc)
    return SovereignPivot.from_dict({**result, **pivot_doc})


def resolve_trigger_sovereign_quest(
    input: SovereignQuestInput,
) -> SovereignQuest:
    _validate_channel(input.channel_id)
    ctx = get_graphql_context()
    
    coll = ctx.db.collection("quests")
    quest_doc = {
        "unknownId": input.unknown_id,
        "focusArea": input.focus_area,
        "status": QuestStatus.ACTIVE.value,
        "discoveredEvidence": [],
        "channelId": input.channel_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    result = coll.insert(quest_doc)
    return SovereignQuest.from_dict({**result, **quest_doc})

def resolve_create_task(input: TaskInput) -> Task:
    ctx = get_graphql_context()
    coll = ctx.db.collection("tasks")
    doc = {
        "title": input.title,
        "project": input.project,
        "scope": input.scope,
        "priority": input.priority,
        "status": TaskStatus.OPEN.value,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }
    result = coll.insert(doc)
    return Task.from_dict({**result, **doc})

def resolve_update_task_status(input: TaskStatusInput) -> Task:
    ctx = get_graphql_context()
    coll = ctx.db.collection("tasks")
    
    doc = coll.get(input.id)
    if doc is None:
        raise ValueError(f"Task {input.id} not found")
    
    doc["status"] = input.status.value
    doc["updatedAt"] = datetime.now(timezone.utc).isoformat()
    coll.update(input.id, doc)
    return Task.from_dict(doc)

def resolve_add_dependency(input: DependencyInput) -> TaskDependency:
    ctx = get_graphql_context()
    edge_coll = ctx.db.collection("task_edges")
    
    # Ensure both tasks exist (basic validation)
    if not ctx.document("tasks", input.from_id) or not ctx.document("tasks", input.to_id):
        raise ValueError("One or both task IDs are invalid")
        
    edge_doc = {
        "_from": f"tasks/{input.from_id}",
        "_to": f"tasks/{input.to_id}",
        "type": input.dep_type,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    result = edge_coll.insert(edge_doc)
    return TaskDependency.from_dict({**result, **edge_doc})

def resolve_report_soter_incident(input: SoterIncidentInput, channel_id: str) -> SoterIncident:
    _validate_channel(channel_id)
    ctx = get_graphql_context()
    coll = ctx.db.collection("incidents")
    
    incident_doc = {
        "request": input.request,
        "assessment": {"score": input.score},
        "resolved": input.resolved,
        "timestamp": input.timestamp or datetime.now(timezone.utc).isoformat(),
        "patterns": [p.from_dict(p) if hasattr(p, 'from_dict') else p for p in input.patterns],
        "channelId": channel_id,
    }
    result = coll.insert(incident_doc)
    return SoterIncident.from_dict({**result, **incident_doc})

def resolve_soter_review(input: SoterReviewInput, channel_id: str) -> SoterReview:
    _validate_channel(channel_id)
    ctx = get_graphql_context()
    coll = ctx.db.collection("reviews")
    
    review_doc = {
        "incidentId": input.incident_id,
        "status": input.status,
        "priority": input.priority,
        "decision": input.decision,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "channelId": channel_id,
    }
    result = coll.insert(review_doc)
    return SoterReview.from_dict({**result, **review_doc})

def resolve_log_shadow_entry(input: ShadowEntryInput, channel_id: str) -> ShadowEntry:
    _validate_channel(channel_id)
    ctx = get_graphql_context()
    coll = ctx.db.collection("shadow_ledger")
    
    doc = {
        "category": input.category,
        "content": input.content,
        "sessionId": input.session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "channelId": channel_id,
    }
    result = coll.insert(doc)
    return ShadowEntry.from_dict({**result, **doc})

def resolve_update_symbol_stage(input: SymbolUpdateInput, channel_id: str) -> SymbolNode:
    _validate_channel(channel_id)
    ctx = get_graphql_context()
    coll = ctx.db.collection("symbols")
    
    doc = coll.get(input.id)
    if doc is None:
        raise ValueError(f"Symbol {input.id} not found")
        
    doc["stage"] = input.stage.value
    doc["intention"] = input.intention
    doc["updatedAt"] = datetime.now(timezone.utc).isoformat()
    coll.update(input.id, doc)
    return SymbolNode.from_dict(doc)

def resolve_log_epistemic_mark(input: EpistemicMarkInput, channel_id: str) -> EpistemicMark:
    _validate_channel(channel_id)
    ctx = get_graphql_context()
    coll = ctx.db.collection("epistemic_ledger")
    
    doc = {
        "label": input.label.value,
        "topic": input.topic,
        "reasoningChain": input.reasoning_chain,
        "sessionId": input.session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "channelId": channel_id,
    }
    result = coll.insert(doc)
    return EpistemicMark.from_dict({**result, **doc})
