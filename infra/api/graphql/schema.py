import strawberry
from enum import Enum
from typing import List, Optional


@strawberry.enum
class CreativeDriver(Enum):
    ANALOGICAL_LEAP = "ANALOGICAL_LEAP"
    SYSTEMIC_INVERSION = "SYSTEMIC_INVERSION"
    EMERGENT_SYNTHESIS = "EMERGENT_SYNTHESIS"


@strawberry.enum
class GuardrailID(Enum):
    EPISTEMIC_HUMILITY = "EPISTEMIC_HUMILITY"
    VERIFIABILITY = "VERIFIABILITY"
    CORRIGIBILITY = "CORRIGIBILITY"
    CONSENT_SEEKING = "CONSENT_SEEKING"
    PROCESS_TRANSPARENCY = "PROCESS_TRANSPARENCY"


@strawberry.enum
class CheckResult(Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@strawberry.enum
class TaskStatus(Enum):
    OPEN = "open"
    READY = "ready"
    TESTING = "testing"
    CLOSED = "closed"

@strawberry.enum
class EpistemicLabel(Enum):
    KNOWN = "[KNOWN]"
    INFERRED = "[INFERRED]"
    UNCERTAIN = "[UNCERTAIN]"
    UNKNOWN = "[UNKNOWN]"

@strawberry.type
class Task:
    id: str
    title: str
    status: TaskStatus
    priority: Optional[str] = None
    project: Optional[str] = None
    scope: Optional[str] = None
    created_at: Optional[str] = strawberry.field(name="createdAt")
    updated_at: Optional[str] = strawberry.field(name="updatedAt")

    @classmethod
    def from_dict(cls, d: dict) -> "Task":
        key = d.get("_key", d.get("_id", "").split("/")[-1])
        return cls(
            id=key,
            title=d.get("title", ""),
            status=TaskStatus(d.get("status", "open")),
            priority=d.get("priority"),
            project=d.get("project"),
            scope=d.get("scope"),
            created_at=d.get("createdAt"),
            updated_at=d.get("updatedAt"),
        )

@strawberry.type
class TaskDependency:
    from_id: str = strawberry.field(name="from")
    to_id: str = strawberry.field(name="to")
    dep_type: str = strawberry.field(name="type")

@strawberry.type
class GuardrailCheck:
    guardrail: GuardrailID
    result: CheckResult
    notes: Optional[str] = None

    @classmethod
    def from_dict(cls, d: dict) -> "GuardrailCheck":
        return cls(
            guardrail=GuardrailID(d["guardrail"]),
            result=CheckResult(d["result"]),
            notes=d.get("notes"),
        )


@strawberry.type
class SoterIncident:
    id: str
    request: str
    score: int = strawberry.field(name="riskScore")
    resolved: bool
    timestamp: str
    patterns: List[GuardrailCheck] = strawberry.field(default_factory=list)
    response: Optional[str] = None

    @classmethod
    def from_dict(cls, d: dict) -> "SoterIncident":
        key = d.get("_key", d.get("_id", "").split("/")[-1])
        assessment = d.get("assessment", {})
        return cls(
            id=key,
            request=d.get("request", ""),
            score=assessment.get("score", 0),
            resolved=d.get("resolved", False),
            timestamp=d.get("timestamp", ""),
            patterns=[GuardrailCheck.from_dict(p) for p in d.get("patterns", [])],
            response=d.get("response"),
        )

@strawberry.type
class MemoryFragment:
    id: str
    fragment: str
    provenance: str
    timestamp: str

    @classmethod
    def from_dict(cls, d: dict) -> "MemoryFragment":
        return cls(
            id=d.get("id", d.get("_key", "")),
            fragment=d.get("fragment", ""),
            provenance=d.get("provenance", ""),
            timestamp=d.get("timestamp", ""),
        )

@strawberry.type
class SovereignState:
    unresolved_incidents: int = strawberry.field(name="unresolvedIncidents")
    ready_tasks: List[Task] = strawberry.field(name="readyTasks")
    recent_memory: Optional[MemoryFragment] = strawberry.field(name="recentMemory")


@strawberry.type
class HypothesisMetadata:
    novelty_score: float = strawberry.field(name="noveltyScore")
    coherence_score: float = strawberry.field(name="coherenceScore")
    creative_drivers: List[CreativeDriver] = strawberry.field(name="creativeDrivers")

    @classmethod
    def from_dict(cls, d: dict) -> "HypothesisMetadata":
        drivers = d.get("creativeDrivers", [])
        return cls(
            novelty_score=float(d.get("noveltyScore", 0)),
            coherence_score=float(d.get("coherenceScore", 0)),
            creative_drivers=[CreativeDriver(x) for x in drivers],
        )


@strawberry.type
class EdgeInfo:
    id: str
    _from: str = strawberry.field(name="from")
    _to: str = strawberry.field(name="to")
    created_at: Optional[str] = strawberry.field(name="createdAt")

    @classmethod
    def from_dict(cls, d: dict) -> "EdgeInfo":
        return cls(
            id=d.get("_key", d.get("_id", "").split("/")[-1]),
            _from=d.get("_from", ""),
            _to=d.get("_to", ""),
            created_at=d.get("createdAt"),
        )


@strawberry.type
class GuardrailCheck:
    guardrail: GuardrailID
    result: CheckResult
    notes: Optional[str] = None

    @classmethod
    def from_dict(cls, d: dict) -> "GuardrailCheck":
        return cls(
            guardrail=GuardrailID(d["guardrail"]),
            result=CheckResult(d["result"]),
            notes=d.get("notes"),
        )


@strawberry.type
class Hypothesis:
    id: str
    raw_pattern_representation: str = strawberry.field(name="rawPatternRepresentation")
    metadata: HypothesisMetadata
    is_valuable: bool = strawberry.field(name="isValuable", default=False)

    @classmethod
    def from_dict(cls, d: dict) -> "Hypothesis":
        key = d.get("_key", d.get("_id", "").split("/")[-1])
        meta = d.get("metadata")
        if isinstance(meta, dict):
            meta = HypothesisMetadata.from_dict(meta)
        elif meta is None:
            meta = HypothesisMetadata(novelty_score=0, coherence_score=0, creative_drivers=[])
        return cls(
            id=key,
            raw_pattern_representation=d.get("rawPatternRepresentation", ""),
            metadata=meta,
            is_valuable=d.get("isValuable", False),
        )


@strawberry.type
class Concept:
    id: str
    name: str
    description: str

    @classmethod
    def from_dict(cls, d: dict) -> "Concept":
        key = d.get("_key", d.get("_id", "").split("/")[-1])
        return cls(
            id=key,
            name=d.get("name", ""),
            description=d.get("description", ""),
        )


@strawberry.type
class ActionablePlan:
    id: str
    summary: str
    steps: List[str]
    risk_assessment: str = strawberry.field(name="riskAssessment")
    grounding_status: GroundingStatus = strawberry.field(name="groundingStatus")

    @classmethod
    def from_dict(cls, d: dict) -> "ActionablePlan":
        key = d.get("_key", d.get("_id", "").split("/")[-1])
        return cls(
            id=key,
            summary=d.get("summary", ""),
            steps=d.get("steps", []),
            risk_assessment=d.get("riskAssessment", ""),
            grounding_status=GroundingStatus(d.get("groundingStatus", "PENDING")),
        )


@strawberry.type
class DreamSession:
    id: str
    timestamp: str
    user_prompt: str = strawberry.field(name="userPrompt")
    seed_concepts: List[str] = strawberry.field(name="seedConcepts")

    @classmethod
    def from_dict(cls, d: dict) -> "DreamSession":
        key = d.get("_key", d.get("_id", "").split("/")[-1])
        return cls(
            id=key,
            timestamp=d.get("timestamp", ""),
            user_prompt=d.get("userPrompt", ""),
            seed_concepts=d.get("seedConcepts", []),
        )


@strawberry.type
class ProvenanceChain:
    plan: ActionablePlan
    plan_to_concept_edge: EdgeInfo = strawberry.field(name="planToConceptEdge")
    concept: Concept
    concept_to_hypothesis_edge: EdgeInfo = strawberry.field(name="conceptToHypothesisEdge")
    hypothesis: Hypothesis
    hypothesis_to_session_edge: EdgeInfo = strawberry.field(name="hypothesisToSessionEdge")
    session: DreamSession


@strawberry.type
class ScoreDistribution:
    known: float
    inferred: float
    uncertain: float
    unknown: float
    dream: float


@strawberry.type
class BenchmarkScores:
    nl: ScoreDistribution
    al: ScoreDistribution


@strawberry.type
class BenchmarkResult:
    id: Optional[str] = None
    query_id: int = strawberry.field(name="queryId")
    category: str
    query_text: str = strawberry.field(name="queryText")
    normal_response: str = strawberry.field(name="normalResponse")
    abraxas_response: str = strawberry.field(name="abraxasResponse")
    scores: BenchmarkScores
    model_id: str = strawberry.field(name="modelId")
    timestamp: str

    @classmethod
    def from_dict(cls, d: dict) -> "BenchmarkResult":
        scores = d.get("scores", {})
        nl = scores.get("nl", {})
        al = scores.get("al", {})
        return cls(
            id=d.get("_key", d.get("_id", "").split("/")[-1]),
            query_id=d.get("queryId", 0),
            category=d.get("category", ""),
            query_text=d.get("queryText", ""),
            normal_response=d.get("normalResponse", ""),
            abraxas_response=d.get("abraxasResponse", ""),
            scores=BenchmarkScores(
                nl=ScoreDistribution(
                    known=nl.get("known", 0),
                    inferred=nl.get("inferred", 0),
                    uncertain=nl.get("uncertain", 0),
                    unknown=nl.get("unknown", 0),
                    dream=nl.get("dream", 0),
                ),
                al=ScoreDistribution(
                    known=al.get("known", 0),
                    inferred=al.get("inferred", 0),
                    uncertain=al.get("uncertain", 0),
                    unknown=al.get("unknown", 0),
                    dream=al.get("dream", 0),
                ),
            ),
            model_id=d.get("modelId", ""),
            timestamp=d.get("timestamp", ""),
        )


@strawberry.input
class HypothesisMetadataInput:
    novelty_score: float = strawberry.field(name="noveltyScore")
    coherence_score: float = strawberry.field(name="coherenceScore")
    creative_drivers: List[CreativeDriver] = strawberry.field(name="creativeDrivers")


@strawberry.input
class ActionablePlanInput:
    summary: str
    steps: List[str] = strawberry.field(default_factory=list)
    risk_assessment: str = strawberry.field(name="riskAssessment", default="")


@strawberry.input
class ScoreDistributionInput:
    known: float
    inferred: float
    uncertain: float
    unknown: float
    dream: float


@strawberry.input
class BenchmarkResultInput:
    query_id: int = strawberry.field(name="queryId")
    category: str
    query_text: str = strawberry.field(name="queryText")
    normal_response: str = strawberry.field(name="normalResponse")
    abraxas_response: str = strawberry.field(name="abraxasResponse")
    nl: ScoreDistributionInput
    al: ScoreDistributionInput
