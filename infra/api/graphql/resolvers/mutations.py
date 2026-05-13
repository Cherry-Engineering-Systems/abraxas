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
                    "uncertain": res.al.uncertain,
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
