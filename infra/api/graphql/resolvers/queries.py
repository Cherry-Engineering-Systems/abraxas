from typing import List, Optional
from infra.api.graphql.context import get_graphql_context
from infra.api.graphql.schema import (
    DreamSession,
    Hypothesis,
    Concept,
    ActionablePlan,
    BenchmarkResult,
    GroundingStatus,
)


def resolve_dream_session(id: str) -> Optional[DreamSession]:
    ctx = get_graphql_context()
    doc = ctx.document("dream_sessions", id)
    if doc is None:
        return None
    return DreamSession.from_dict(doc)


def resolve_hypothesis(id: str) -> Optional[Hypothesis]:
    ctx = get_graphql_context()
    doc = ctx.document("hypotheses", id)
    if doc is None:
        return None
    return Hypothesis.from_dict(doc)


def resolve_concept(id: str) -> Optional[Concept]:
    ctx = get_graphql_context()
    doc = ctx.document("concepts", id)
    if doc is None:
        return None
    return Concept.from_dict(doc)


def resolve_actionable_plans(status: Optional[GroundingStatus] = None) -> List[ActionablePlan]:
    ctx = get_graphql_context()
    if status:
        query = "FOR p IN actionable_plans FILTER p.groundingStatus == @status RETURN p"
        bind_vars = {"status": str(status)}
    else:
        query = "FOR p IN actionable_plans RETURN p"
        bind_vars = {}
    results = ctx.execute_aql(query, bind_vars)
    return [ActionablePlan.from_dict(r) for r in results]


def resolve_benchmark_results(model_id: Optional[str] = None) -> List[BenchmarkResult]:
    ctx = get_graphql_context()
    if model_id:
        query = "FOR r IN benchmark_results FILTER r.modelId == @model_id RETURN r"
        bind_vars = {"model_id": model_id}
    else:
        query = "FOR r IN benchmark_results RETURN r"
        bind_vars = {}
    results = ctx.execute_aql(query, bind_vars)
    return [BenchmarkResult.from_dict(r) for r in results]
