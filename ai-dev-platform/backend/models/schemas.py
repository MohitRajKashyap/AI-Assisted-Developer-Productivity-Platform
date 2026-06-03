from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class PromptStrategy(str, Enum):
    BASELINE = "baseline"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    FEW_SHOT = "few_shot"
    NEGATIVE_EXAMPLE = "negative_example"
    SELF_REFLECTION = "self_reflection"
    CONTEXT_WINDOW = "context_window"


class BugSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BugCategory(str, Enum):
    REGRESSION = "regression"
    NEW_BUG = "new_bug"
    PERFORMANCE = "performance"
    SECURITY = "security"


# ─── Prompt Lab ───────────────────────────────────────────────────────────────

class PromptTestRequest(BaseModel):
    task: str = Field(..., description="The coding task or question")
    code: str = Field(default="", description="Optional code to analyze")
    strategies: List[PromptStrategy] = Field(
        default=[s for s in PromptStrategy],
        description="Strategies to test"
    )
    model: str = Field(default="claude-sonnet-4-20250514")
    project_id: Optional[str] = None
    language: str = Field(default="Python")


class EvaluationResult(BaseModel):
    strategy: str
    model: str
    output: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    correctness_score: float
    relevance_score: float
    completeness_score: float
    consistency_score: float
    hallucination_score: float
    overall_score: float
    cost_usd: float


class PromptTestResponse(BaseModel):
    experiment_id: str
    task: str
    results: Dict[str, EvaluationResult]
    winner: str
    summary: str
    created_at: str


class PromptCompareRequest(BaseModel):
    experiment_ids: List[str]


# ─── Bug Triage ───────────────────────────────────────────────────────────────

class BugAnalyzeRequest(BaseModel):
    title: str
    description: str
    stack_trace: Optional[str] = None
    code_snippet: Optional[str] = None
    project_id: Optional[str] = "demo-proj-1"
    reporter_id: Optional[str] = "demo-user-1"


class AgentStep(BaseModel):
    agent: str
    input_summary: str
    output_summary: str
    duration_ms: int
    tokens_used: int


class BugAnalysisResult(BaseModel):
    bug_id: str
    execution_id: str
    title: str
    severity: str
    category: str
    root_cause: str
    affected_components: List[str]
    reproduction_steps: List[str]
    suggested_fixes: List[Dict[str, Any]]
    confidence_score: float
    report_markdown: str
    agent_steps: List[AgentStep]
    total_duration_ms: int


class BugClassifyRequest(BaseModel):
    bug_id: str
    override_category: Optional[str] = None


# ─── PR Review ────────────────────────────────────────────────────────────────

class PRReviewRequest(BaseModel):
    pr_number: Optional[int] = None
    title: str
    description: Optional[str] = ""
    diff: str
    base_branch: str = "main"
    head_branch: Optional[str] = "feature/new-change"
    author: Optional[str] = "developer"
    project_id: Optional[str] = "demo-proj-1"


class ReviewComment(BaseModel):
    file: str
    line: Optional[int]
    severity: str  # error, warning, suggestion, praise
    category: str  # bug, security, performance, style, logic
    message: str
    suggestion: Optional[str]


class PRReviewResponse(BaseModel):
    pr_id: str
    overall_verdict: str  # APPROVE, REQUEST_CHANGES, COMMENT
    score: float
    summary: str
    bugs_found: int
    security_issues: int
    performance_issues: int
    style_issues: int
    comments: List[ReviewComment]
    positive_aspects: List[str]
    review_markdown: str


# ─── Error Fix ────────────────────────────────────────────────────────────────

class ErrorFixRequest(BaseModel):
    error_message: str
    stack_trace: Optional[str] = None
    source_code: Optional[str] = None
    language: str = "Python"
    context: Optional[str] = None
    project_id: Optional[str] = "demo-proj-1"


class ErrorFixResponse(BaseModel):
    execution_id: str
    error_type: str
    root_cause: str
    explanation: str
    fix_code: str
    fix_explanation: str
    prevention_tips: List[str]
    confidence_score: float
    reasoning_chain: List[str]


# ─── Evaluations ─────────────────────────────────────────────────────────────

class RunEvaluationRequest(BaseModel):
    experiment_id: Optional[str] = None
    task: str
    expected_output: Optional[str] = None
    strategies: List[PromptStrategy] = Field(default=[s for s in PromptStrategy])
    runs_per_strategy: int = Field(default=1, ge=1, le=3)


class EvaluationHistoryItem(BaseModel):
    id: str
    experiment_id: str
    strategy: str
    model: str
    overall_score: float
    hallucination_score: float
    cost_usd: float
    latency_ms: int
    created_at: str


# ─── Dashboard ───────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_experiments: int
    total_bug_reports: int
    total_pr_reviews: int
    total_agent_executions: int
    avg_hallucination_rate: float
    avg_accuracy_score: float
    total_cost_usd: float
    best_strategy: str
    recent_experiments: List[Dict[str, Any]]
    strategy_comparison: Dict[str, Dict[str, float]]
    cost_by_model: Dict[str, float]
    bugs_by_severity: Dict[str, int]
    experiments_over_time: List[Dict[str, Any]]


# ─── Context Files ────────────────────────────────────────────────────────────

class ContextFileCreate(BaseModel):
    project_id: str
    filename: str
    content: str
    file_type: str


class ContextFileResponse(BaseModel):
    id: str
    project_id: str
    filename: str
    content: str
    file_type: str
    version: int
    updated_at: str
