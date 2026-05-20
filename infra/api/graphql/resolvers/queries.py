from typing import List, Optional
from infra.api.graphql.context import get_graphql_context
from infra.api.graphql.schema import (
    DreamSession,
    Hypothesis,
    Concept,
    ActionablePlan,
    BenchmarkResult,
    GroundingStatus,
    Task,
    TaskStatus,
    TaskDependency,
    SoterIncident,
    SoterReview,
    MemoryFragment,
    SovereignState
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

def resolve_tasks(project: Optional[str] = None, status: Optional[TaskStatus] = None) -> List[Task]:
    ctx = get_graphql_context()
    query = "FOR t IN tasks"
    bind_vars = {}
    filters = []
    if project:
        filters.append("t.project == @project")
        bind_vars["project"] = project
    if status:
        filters.append("t.status == @status")
        bind_vars["status"] = status.value
    if filters:
        query += " FILTER " + " AND ".join(filters)
    query += " RETURN t"
    results = ctx.execute_aql(query, bind_vars)
    return [Task.from_dict(r) for r in results]

def resolve_task_tree(task_id: str) -> List[TaskDependency]:
    ctx = get_graphql_context()
    query = "FOR e IN TASK_EDGES FILTER e._from == @id OR e._to == @id RETURN e"
    bind_vars = {"id": f"tasks/{task_id}"}
    results = ctx.execute_aql(query, bind_vars)
    return [
        TaskDependency(
            from_id=r["_from"].split("/")[-1],
            to_id=r["_to"].split("/")[-1],
            dep_type=r.get("type", "blocks")
        ) for r in results
    ]

def resolve_incident_log(min_score: int = 0) -> List[SoterIncident]:
    ctx = get_graphql_context()
    query = "FOR i IN incidents FILTER i.assessment.score >= @min_score SORT i.timestamp DESC RETURN i"
    bind_vars = {"min_score": min_score}
    results = ctx.execute_aql(query, bind_vars)
    return [SoterIncident.from_dict(r) for r in results]

def resolve_pending_reviews(priority: Optional[str] = None) -> List[SoterReview]:
    ctx = get_graphql_context()
    query = "FOR r IN reviews FILTER r.status == 'PENDING'"
    bind_vars = {}
    if priority:
        query += " FILTER r.priority == @priority"
        bind_vars["priority"] = priority
    query += " SORT r.createdAt DESC RETURN r"
    results = ctx.execute_aql(query, bind_vars)
    return [SoterReview.from_dict(r) for r in results]

def resolve_memory_recall(query: str) -> Optional[MemoryFragment]:
    ctx = get_graphql_context()
    aql = "FOR f IN fragments FILTER CONTAINS(LOWER(f.fragment), LOWER(@query)) OR f.id == @query LIMIT 1 RETURN f"
    results = ctx.execute_aql(aql, bind_vars={"query": query})
    return MemoryFragment.from_dict(results[0]) if results else None

def resolve_project_uncertainty() -> 'EpistemicHeatMap':
    ctx = get_graphql_context()
    # We analyze the benchmark_results collection's scores
    query = """
    FOR r IN benchmark_results
    COLLECT AGGREGATE 
        known_sum = SUM(r.scores.nl.known + r.scores.al.known),
        inf_sum = SUM(r.scores.nl.inferred + r.scores.al.inferred),
        unc_sum = SUM(r.scores.nl.uncertain + r.scores.al.uncertain),
        unk_sum = SUM(r.scores.nl.unknown + r.scores.al.unknown),
        drm_sum = SUM(r.scores.nl.dream + r.scores.al.dream)
    RETURN {
        known: known_sum,
        inferred: inf_sum,
        uncertain: unc_sum,
        unknown: unk_sum,
        dream: drm_sum
    }
    """
    results = ctx.execute_aql(query)
    if not results:
        return None # or a zeroed object

    data = results[0]
    total = data['known'] + data['inferred'] + data['uncertain'] + data['unknown'] + data['dream']
    
    # Sovereign Gap Index: Ratio of (Uncertain + Unknown) to Total
    # This represents the percentage of the project that is not yet anchored.
    gap_index = (data['uncertain'] + data['unknown']) / total if total > 0 else 0.0

    from schema import EpistemicHeatMap
    return EpistemicHeatMap(
        known=data['known'],
        inferred=data['inferred'],
        uncertain=data['uncertain'],
        unknown=data['unknown'],
        dream=data['dream'],
        total_samples=total,
        sovereign_gap_index=gap_index
    )

