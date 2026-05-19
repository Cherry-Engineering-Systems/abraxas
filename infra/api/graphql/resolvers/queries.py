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

def resolve_sovereign_state() -> SovereignState:
    ctx = get_graphql_context()
    # Unresolved incidents
    inc_query = "FOR i IN incidents FILTER i.resolved == false RETURN i"
    unresolved_count = len(ctx.execute_aql(inc_query))
    
    # Ready tasks
    task_query = "FOR t IN tasks FILTER t.status == 'ready' LIMIT 5 RETURN t"
    ready_tasks_raw = ctx.execute_aql(task_query)
    ready_tasks = [Task.from_dict(t) for t in ready_tasks_raw]
    
    # Recent memory
    mem_query = "FOR f IN fragments SORT f.timestamp DESC LIMIT 1 RETURN f"
    mem_res = ctx.execute_aql(mem_query)
    recent_mem = MemoryFragment.from_dict(mem_res[0]) if mem_res else None
    
    return SovereignState(
        unresolved_incidents=unresolved_count,
        ready_tasks=ready_tasks,
        recent_memory=recent_mem
    )

