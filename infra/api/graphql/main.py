from typing import List, Optional

import strawberry
from fastapi import FastAPI, Response
from strawberry.fastapi import GraphQLRouter
import uvicorn

from context import get_graphql_context, GraphQLContext
from schema import (
    GroundingStatus,
    Task,
    TaskStatus,
    SoterIncident,
    SoterReview,
    DreamSession,
    Hypothesis,
    Concept,
    ActionablePlan,
    EdgeInfo,
    GuardrailCheck,
    ProvenanceChain,
    BenchmarkResult,
    HypothesisMetadata,
    HypothesisMetadataInput,
    CheckResult,
    BenchmarkScores,
    ScoreDistribution,
    ScoreDistributionInput,
    GuardrailID,
    CreativeDriver,
    ActionablePlanInput,
    SovereignState,
    MemoryFragment, BenchmarkResultInput
)
from resolvers.queries import (
    resolve_dream_session,
    resolve_hypothesis,
    resolve_concept,
    resolve_actionable_plans,
    resolve_benchmark_results,
    resolve_tasks,
    resolve_task_tree,
    resolve_incident_log,
    resolve_pending_reviews,
    resolve_memory_recall, resolve_project_uncertainty,
)
from resolvers.mutations import (
    resolve_start_dream_cycle,
    resolve_create_hypothesis,
    resolve_translate_hypothesis_to_concept,
    resolve_archive_hypothesis,
    resolve_ground_concept,
    resolve_upload_benchmark_batch,
)
from resolvers.search import (
    resolve_search,
    resolve_related_to,
    resolve_recent,
    resolve_explore,
    resolve_stats,
    SearchResult,
    StatsResult,
)


def _ctx() -> GraphQLContext:
    return get_graphql_context()


@strawberry.type
class EpistemicHeatMap:
    known: int = strawberry.field(description="Total verified ground-truth counts")
    inferred: int = strawberry.field(description="Total logically derived counts")
    uncertain: int = strawberry.field(description="Total confidence-gap counts")
    unknown: int = strawberry.field(description="Total identified gaps")
    dream: int = strawberry.field(description="Total speculative/creative counts")
    total_samples: int = strawberry.field(description="Total data points analyzed")
    sovereign_gap_index: float = strawberry.field(description="The delta between confidence and grounding")


@strawberry.type
class Query:
    # ... existing queries ...
    @strawberry.field
    def project_uncertainty(self) -> EpistemicHeatMap:
        return resolve_project_uncertainty()

    @strawberry.field
    def search(
            self,
            query: str,
            collections: Optional[List[str]] = None,
            limit: int = 10,
    ) -> List[SearchResult]:
        return resolve_search(query, collections, limit)

    @strawberry.field
    def related_to(self, id: strawberry.ID, depth: int = 1) -> List["RelatedNode"]:
        nodes = resolve_related_to(str(id), depth)
        return [RelatedNode.from_dict(n) for n in nodes]

    @strawberry.field
    def recent(
            self, limit: int = 10, collection: Optional[str] = None
    ) -> List["RecentNode"]:
        nodes = resolve_recent(limit, collection)
        return [RecentNode.from_dict(n) for n in nodes]

    @strawberry.field
    def explore(self, name: str) -> List[ProvenanceChain]:
        paths = resolve_explore(name)
        result = []
        for p in paths:
            chain = _build_provenance_chain(p)
            if chain:
                result.append(chain)
        return result

    @strawberry.field
    def stats(self) -> StatsResult:
        return resolve_stats()


@strawberry.type
class RelatedNode:
    id: str
    collection: str
    label: str
    edge_id: Optional[str] = strawberry.field(name="edgeId")

    @classmethod
    def from_dict(cls, d: dict) -> "RelatedNode":
        doc = d.get("document", {})
        label = doc.get("name") or doc.get("summary") or doc.get("userPrompt") or d.get("id", "")
        return cls(
            id=d.get("id", ""),
            collection=d.get("collection", ""),
            label=label,
            edge_id=d.get("edge_id"),
        )


@strawberry.type
class RecentNode:
    id: str
    collection: str
    timestamp: Optional[str] = None
    label: str

    @classmethod
    def from_dict(cls, d: dict) -> "RecentNode":
        doc = d.get("document", {})
        label = doc.get("name") or doc.get("summary") or doc.get("userPrompt") or d.get("id", "")
        return cls(
            id=d.get("id", ""),
            collection=d.get("collection", ""),
            timestamp=doc.get("timestamp"),
            label=label,
        )


def _build_provenance_chain(p: dict) -> Optional[ProvenanceChain]:
    session = p.get("session")
    hypothesis = p.get("hypothesis")
    concept = p.get("concept")
    plan = p.get("plan")

    if not session or not hypothesis or not concept:
        return None

    plan_edge = p.get("plan_edge") or p.get("planToConceptEdge")
    concept_edge = p.get("concept_edge") or p.get("conceptToHypothesisEdge")
    hypo_edge = p.get("hypo_edge") or p.get("hypothesisToSessionEdge")

    plan_obj = plan if plan and isinstance(plan, dict) and plan.get("summary") else None

    return ProvenanceChain(
        plan=ActionablePlan.from_dict(plan_obj) if plan_obj else ActionablePlan(
            id="", summary="", steps=[], risk_assessment="", grounding_status=GroundingStatus.PENDING
        ),
        plan_to_concept_edge=EdgeInfo.from_dict(plan_edge) if plan_edge else EdgeInfo(id="", _from="", _to="",
                                                                                      created_at=None),
        concept=Concept.from_dict(concept),
        concept_to_hypothesis_edge=EdgeInfo.from_dict(concept_edge) if concept_edge else EdgeInfo(id="", _from="",
                                                                                                  _to="",
                                                                                                  created_at=None),
        hypothesis=Hypothesis.from_dict(hypothesis),
        hypothesis_to_session_edge=EdgeInfo.from_dict(hypo_edge) if hypo_edge else EdgeInfo(id="", _from="", _to="",
                                                                                            created_at=None),
        session=DreamSession.from_dict(session),
    )





@strawberry.type
class Mutation:
    @strawberry.mutation
    def start_dream_cycle(
            self, prompt: str, seed_concepts: Optional[List[str]] = None, channel_id: str = ""
    ) -> DreamSession:
        return resolve_start_dream_cycle(prompt, seed_concepts, channel_id)

    @strawberry.mutation
    def create_hypothesis(
            self,
            session_id: strawberry.ID,
            raw_pattern_representation: str,
            metadata: "HypothesisMetadataInput",
            channel_id: str = "",
    ) -> Hypothesis:
        return resolve_create_hypothesis(
            str(session_id), raw_pattern_representation, metadata, channel_id
        )

    @strawberry.mutation
    def translate_hypothesis_to_concept(
            self,
            hypothesis_id: strawberry.ID,
            name: str,
            description: str,
            channel_id: str = "",
    ) -> Concept:
        return resolve_translate_hypothesis_to_concept(
            str(hypothesis_id), name, description, channel_id
        )

    @strawberry.mutation
    def archive_hypothesis(
            self, hypothesis_id: strawberry.ID, is_valuable: bool, channel_id: str = ""
    ) -> Hypothesis:
        return resolve_archive_hypothesis(str(hypothesis_id), is_valuable, channel_id)

    @strawberry.mutation
    def ground_concept(
            self, concept_id: strawberry.ID, plan: "ActionablePlanInput", channel_id: str = ""
    ) -> ActionablePlan:
        return resolve_ground_concept(str(concept_id), plan, channel_id)

    @strawberry.mutation
    def upload_benchmark_batch(
            self, model_id: str, results: List["BenchmarkResultInput"], channel_id: str = ""
    ) -> int:
        return resolve_upload_benchmark_batch(model_id, results, channel_id)


def _resolve_edge_outbound(parent_id: str, edge_collection: str) -> Optional[dict]:
    ctx = _ctx()
    results = ctx.execute_aql(
        f"""
        FOR vertex, edge IN 1..1 OUTBOUND @id {edge_collection}
            RETURN vertex
        """,
        {"id": parent_id},
    )
    return results[0] if results else None


def _resolve_edge_inbound(parent_id: str, edge_collection: str) -> Optional[dict]:
    ctx = _ctx()
    results = ctx.execute_aql(
        f"""
        FOR vertex, edge IN 1..1 INBOUND @id {edge_collection}
            RETURN vertex
        """,
        {"id": parent_id},
    )
    return results[0] if results else None


@strawberry.type
class DreamSessionGraph(DreamSession):
    @strawberry.field
    def hypotheses(self) -> List[Hypothesis]:
        ctx = _ctx()
        results = ctx.execute_aql(
            "FOR vertex, edge IN 1..1 OUTBOUND @id SESS_TO_HYPO RETURN vertex",
            {"id": f"dream_sessions/{self.id}"},
        )
        return [Hypothesis.from_dict(r) for r in results]

    @strawberry.field
    def inspired_by(self) -> Optional[List[Hypothesis]]:
        ctx = _ctx()
        results = ctx.execute_aql(
            """
            FOR hypo IN 1..1 OUTBOUND @id SESS_TO_HYPO
                FOR concept IN 1..1 OUTBOUND hypo._id HYPO_TO_CONCEPT
                    FOR otherHypo IN 1..1 INBOUND concept._id HYPO_TO_CONCEPT
                        FILTER otherHypo._id != hypo._id
                        FOR otherSession IN 1..1 INBOUND otherHypo._id SESS_TO_HYPO
                            FILTER otherSession._id != @id
                            RETURN DISTINCT otherHypo
            """,
            {"id": f"dream_sessions/{self.id}"},
        )
        if not results:
            return None
        return [Hypothesis.from_dict(r) for r in results]


@strawberry.type
class HypothesisGraph(Hypothesis):
    @strawberry.field
    def dream_session(self) -> Optional[DreamSession]:
        result = _resolve_edge_inbound(f"hypotheses/{self.id}", "SESS_TO_HYPO")
        return DreamSession.from_dict(result) if result else None

    @strawberry.field
    def translated_to(self) -> Optional[Concept]:
        result = _resolve_edge_outbound(f"hypotheses/{self.id}", "HYPO_TO_CONCEPT")
        return Concept.from_dict(result) if result else None

    @strawberry.field
    def inspired_dreams(self) -> Optional[List[DreamSession]]:
        ctx = _ctx()
        results = ctx.execute_aql(
            """
            FOR concept IN 1..1 OUTBOUND @id HYPO_TO_CONCEPT
                FOR otherHypo IN 1..1 INBOUND concept._id HYPO_TO_CONCEPT
                    FILTER otherHypo._id != @id
                    FOR session IN 1..1 INBOUND otherHypo._id SESS_TO_HYPO
                        RETURN DISTINCT session
            """,
            {"id": f"hypotheses/{self.id}"},
        )
        if not results:
            return None
        return [DreamSession.from_dict(r) for r in results]

    @strawberry.field
    def inspired_by(self) -> Optional[List[Hypothesis]]:
        ctx = _ctx()
        results = ctx.execute_aql(
            """
            FOR concept IN 1..1 OUTBOUND @id HYPO_TO_CONCEPT
                FOR otherHypo IN 1..1 INBOUND concept._id HYPO_TO_CONCEPT
                    FILTER otherHypo._id != @id
                    RETURN DISTINCT otherHypo
            """,
            {"id": f"hypotheses/{self.id}"},
        )
        if not results:
            return None
        return [Hypothesis.from_dict(r) for r in results]


@strawberry.type
class ConceptGraph(Concept):
    @strawberry.field
    def source_hypothesis(self) -> Optional[Hypothesis]:
        result = _resolve_edge_inbound(f"concepts/{self.id}", "HYPO_TO_CONCEPT")
        return Hypothesis.from_dict(result) if result else None

    @strawberry.field
    def grounded_as(self) -> Optional[ActionablePlan]:
        result = _resolve_edge_outbound(f"concepts/{self.id}", "CONCEPT_TO_PLAN")
        return ActionablePlan.from_dict(result) if result else None


@strawberry.type
class ActionablePlanGraph(ActionablePlan):
    @strawberry.field
    def source_concept(self) -> Optional[Concept]:
        result = _resolve_edge_inbound(f"actionable_plans/{self.id}", "CONCEPT_TO_PLAN")
        return Concept.from_dict(result) if result else None

    @strawberry.field
    def guardrail_checks(self) -> List[GuardrailCheck]:
        return []

    @strawberry.field
    def provenance_chain(self) -> Optional[ProvenanceChain]:
        ctx = _ctx()
        plan_doc = ctx.document("actionable_plans", self.id)
        if plan_doc is None:
            return None

        results = ctx.execute_aql(
            """
            FOR concept, plan_edge IN 1..1 INBOUND @id CONCEPT_TO_PLAN
                FOR hypothesis, concept_edge IN 1..1 INBOUND concept._id HYPO_TO_CONCEPT
                    FOR session, hypo_edge IN 1..1 INBOUND hypothesis._id SESS_TO_HYPO
                        RETURN {
                            plan: @plan_doc,
                            planToConceptEdge: plan_edge,
                            concept: concept,
                            conceptToHypothesisEdge: concept_edge,
                            hypothesis: hypothesis,
                            hypothesisToSessionEdge: hypo_edge,
                            session: session
                        }
            """,
            {
                "id": f"actionable_plans/{self.id}",
                "plan_doc": plan_doc,
            },
        )
        if not results:
            return None
        return _build_provenance_chain(results[0])


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    types=[
        DreamSessionGraph,
        HypothesisGraph,
        ConceptGraph,
        ActionablePlanGraph,
    ],
)

graphql_app = GraphQLRouter(schema)

app = FastAPI(title="Abraxas GraphQL API")
app.include_router(graphql_app, prefix="/graphql")


@app.get("/health")
async def health_check():
    ctx = _ctx()
    try:
        ctx.db.version()
        return {"status": "healthy", "db": "connected"}
    except Exception:
        return Response(
            content='{"status": "unhealthy", "db": "disconnected"}',
            status_code=503,
            media_type="application/json",
        )


def main():
    ctx = get_graphql_context()
    ctx.ensure_db()
    print("Starting Abraxas GraphQL Server on port 4000...")
    uvicorn.run(app, host="0.0.0.0", port=4000, log_level="info")


if __name__ == "__main__":
    main()
