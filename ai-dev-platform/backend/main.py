"""
AI Developer Productivity Platform — FastAPI Backend
"""
import asyncio
import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.database.db import init_db, get_db, row_to_dict, rows_to_list
from backend.models.schemas import (
    PromptTestRequest, PromptTestResponse, EvaluationResult,
    BugAnalyzeRequest, BugAnalysisResult, AgentStep,
    PRReviewRequest, PRReviewResponse, ReviewComment,
    ErrorFixRequest, ErrorFixResponse,
    RunEvaluationRequest, DashboardStats,
    ContextFileCreate, ContextFileResponse,
)
from backend.prompts.templates import build_prompt, SYSTEM_PROMPTS
from backend.core.llm_client import call_llm, DEFAULT_MODEL
from backend.evaluation.evaluator import evaluate_output
from backend.agents.bug_triage import BugTriageWorkflow
from backend.agents.pr_reviewer import review_pull_request
from backend.agents.error_fix import synthesize_error_fix

app = FastAPI(
    title="AI Developer Productivity Platform",
    description="Multi-agent platform for bug triage, PR review, and prompt engineering research",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    init_db()


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0", "timestamp": datetime.utcnow().isoformat()}


# ─── Prompt Lab ───────────────────────────────────────────────────────────────

@app.post("/prompts/test", response_model=PromptTestResponse)
async def test_prompts(req: PromptTestRequest):
    """Test multiple prompting strategies on a given task."""
    experiment_id = str(uuid.uuid4())
    results = {}
    winner = None
    best_score = -1

    tasks = []
    for strategy in req.strategies:
        tasks.append(_run_strategy(strategy.value, req.task, req.code, req.language, req.model))

    strategy_results = await asyncio.gather(*tasks, return_exceptions=True)

    for strategy, result in zip(req.strategies, strategy_results):
        if isinstance(result, Exception):
            continue
        results[strategy.value] = result
        if result["overall_score"] > best_score:
            best_score = result["overall_score"]
            winner = strategy.value

    # Persist experiment
    with get_db() as conn:
        conn.execute("""
            INSERT INTO prompt_experiments (id, task, input_code, strategies, results, winner, project_id, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            experiment_id,
            req.task,
            req.code,
            json.dumps([s.value for s in req.strategies]),
            json.dumps({k: v for k, v in results.items()}),
            winner,
            req.project_id or "demo-proj-1",
            "demo-user-1",
        ))

        # Persist individual evaluations
        for strategy, r in results.items():
            eval_id = str(uuid.uuid4())
            conn.execute("""
                INSERT INTO evaluations (
                    id, experiment_id, strategy, model, prompt_tokens, completion_tokens,
                    latency_ms, correctness_score, relevance_score, completeness_score,
                    consistency_score, hallucination_score, overall_score, cost_usd, raw_output
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                eval_id, experiment_id, strategy, req.model,
                r["prompt_tokens"], r["completion_tokens"], r["latency_ms"],
                r["correctness_score"], r["relevance_score"], r["completeness_score"],
                r["consistency_score"], r["hallucination_score"], r["overall_score"],
                r["cost_usd"], r["output"][:5000],
            ))

    # Build summary
    sorted_results = sorted(results.items(), key=lambda x: x[1]["overall_score"], reverse=True)
    summary = f"Tested {len(results)} strategies. Winner: **{winner}** (score: {best_score:.2f}). "
    if len(sorted_results) > 1:
        summary += f"Range: {sorted_results[-1][1]['overall_score']:.2f} - {sorted_results[0][1]['overall_score']:.2f}."

    return PromptTestResponse(
        experiment_id=experiment_id,
        task=req.task,
        results={k: EvaluationResult(**v) for k, v in results.items()},
        winner=winner or "baseline",
        summary=summary,
        created_at=datetime.utcnow().isoformat(),
    )


async def _run_strategy(strategy: str, task: str, code: str, language: str, model: str) -> Dict:
    prompt = build_prompt(strategy, task, code, language)
    system = SYSTEM_PROMPTS.get(strategy, "You are a senior software engineer.")
    llm_result = await call_llm(prompt, system, model)
    output = llm_result["output"]

    # Evaluate
    eval_scores = await evaluate_output(output, task, code, use_llm_eval=True)

    return EvaluationResult(
        strategy=strategy,
        model=model,
        output=output,
        prompt_tokens=llm_result["input_tokens"],
        completion_tokens=llm_result["output_tokens"],
        latency_ms=llm_result["latency_ms"],
        correctness_score=eval_scores["correctness"],
        relevance_score=eval_scores["relevance"],
        completeness_score=eval_scores["completeness"],
        consistency_score=eval_scores["consistency"],
        hallucination_score=eval_scores["hallucination"],
        overall_score=eval_scores["overall"],
        cost_usd=llm_result["cost_usd"],
    ).dict()


@app.get("/prompts/experiments")
async def list_experiments(limit: int = 20):
    with get_db() as conn:
        rows = conn.execute("""
            SELECT id, task, strategies, winner, created_at
            FROM prompt_experiments ORDER BY created_at DESC LIMIT ?
        """, (limit,)).fetchall()
    return rows_to_list(rows)


@app.get("/prompts/experiments/{experiment_id}")
async def get_experiment(experiment_id: str):
    with get_db() as conn:
        exp = conn.execute(
            "SELECT * FROM prompt_experiments WHERE id = ?", (experiment_id,)
        ).fetchone()
        if not exp:
            raise HTTPException(404, "Experiment not found")
        evals = conn.execute(
            "SELECT * FROM evaluations WHERE experiment_id = ?", (experiment_id,)
        ).fetchall()
    return {"experiment": row_to_dict(exp), "evaluations": rows_to_list(evals)}


# ─── Bug Triage ───────────────────────────────────────────────────────────────

@app.post("/bugs/analyze")
async def analyze_bug(req: BugAnalyzeRequest):
    """Run 5-agent bug triage workflow."""
    workflow = BugTriageWorkflow()
    result = await workflow.run(req.dict())

    bug_id = str(uuid.uuid4())
    exec_id = result["execution_id"]

    with get_db() as conn:
        conn.execute("""
            INSERT INTO bug_reports (id, title, description, stack_trace, severity, category,
                project_id, reporter_id, analysis_result, fix_suggestions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            bug_id, req.title, req.description, req.stack_trace,
            result["severity"], result["category"],
            req.project_id, req.reporter_id,
            json.dumps({"root_cause": result["root_cause"], "components": result["affected_components"]}),
            json.dumps(result["suggested_fixes"]),
        ))

        conn.execute("""
            INSERT INTO agent_executions (id, workflow_type, input_data, agent_steps, final_output,
                status, total_duration_ms, total_tokens, project_id, completed_at)
            VALUES (?, 'bug_triage', ?, ?, ?, 'completed', ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            exec_id,
            json.dumps(req.dict()),
            json.dumps(result["agent_steps"]),
            json.dumps({"bug_id": bug_id, "severity": result["severity"]}),
            result["total_duration_ms"],
            result["total_tokens"],
            req.project_id,
        ))

    return {**result, "bug_id": bug_id}


@app.get("/bugs/list")
async def list_bugs(status: Optional[str] = None, limit: int = 20):
    with get_db() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM bug_reports WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM bug_reports ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
    return rows_to_list(rows)


# ─── PR Review ────────────────────────────────────────────────────────────────

@app.post("/pr/review")
async def review_pr(req: PRReviewRequest):
    """Review a pull request diff."""
    result = await review_pull_request(
        title=req.title,
        description=req.description or "",
        diff=req.diff,
        author=req.author or "developer",
        base_branch=req.base_branch,
    )

    pr_id = result["pr_id"]
    with get_db() as conn:
        conn.execute("""
            INSERT INTO pull_requests (id, pr_number, title, description, diff, base_branch,
                head_branch, author, project_id, review_result, review_status, reviewed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            pr_id, req.pr_number, req.title, req.description, req.diff[:10000],
            req.base_branch, req.head_branch, req.author, req.project_id,
            json.dumps(result),
            "approved" if result["overall_verdict"] == "APPROVE" else "changes_requested",
        ))

    return result


@app.get("/pr/list")
async def list_prs(limit: int = 20):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, pr_number, title, author, review_status, reviewed_at FROM pull_requests ORDER BY reviewed_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return rows_to_list(rows)


# ─── Error Fix ────────────────────────────────────────────────────────────────

@app.post("/errors/fix")
async def fix_error(req: ErrorFixRequest):
    """Synthesize a fix from error/stack trace."""
    result = await synthesize_error_fix(
        error_message=req.error_message,
        stack_trace=req.stack_trace or "",
        source_code=req.source_code or "",
        language=req.language,
        context=req.context or "",
    )
    return result


# ─── Evaluations ─────────────────────────────────────────────────────────────

@app.post("/evaluations/run")
async def run_evaluation(req: RunEvaluationRequest):
    """Run a fresh evaluation batch."""
    test_req = PromptTestRequest(
        task=req.task,
        strategies=req.strategies,
        model=DEFAULT_MODEL,
    )
    return await test_prompts(test_req)


@app.get("/evaluations/history")
async def evaluation_history(limit: int = 50):
    with get_db() as conn:
        rows = conn.execute("""
            SELECT e.id, e.experiment_id, e.strategy, e.model, e.overall_score,
                   e.hallucination_score, e.cost_usd, e.latency_ms, e.created_at
            FROM evaluations e
            ORDER BY e.created_at DESC LIMIT ?
        """, (limit,)).fetchall()
    return rows_to_list(rows)


@app.get("/evaluations/strategy-comparison")
async def strategy_comparison():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT strategy,
                   AVG(overall_score) as avg_score,
                   AVG(hallucination_score) as avg_hallucination,
                   AVG(correctness_score) as avg_correctness,
                   AVG(latency_ms) as avg_latency,
                   AVG(cost_usd) as avg_cost,
                   COUNT(*) as run_count
            FROM evaluations
            GROUP BY strategy
        """).fetchall()
    return rows_to_list(rows)


# ─── Dashboard ───────────────────────────────────────────────────────────────

@app.get("/dashboard/stats")
async def dashboard_stats():
    with get_db() as conn:
        total_exp = conn.execute("SELECT COUNT(*) FROM prompt_experiments").fetchone()[0]
        total_bugs = conn.execute("SELECT COUNT(*) FROM bug_reports").fetchone()[0]
        total_prs = conn.execute("SELECT COUNT(*) FROM pull_requests").fetchone()[0]
        total_agents = conn.execute("SELECT COUNT(*) FROM agent_executions").fetchone()[0]

        avg_hallucination = conn.execute(
            "SELECT AVG(hallucination_score) FROM evaluations"
        ).fetchone()[0] or 0.0

        avg_accuracy = conn.execute(
            "SELECT AVG(overall_score) FROM evaluations"
        ).fetchone()[0] or 0.0

        total_cost = conn.execute(
            "SELECT SUM(cost_usd) FROM evaluations"
        ).fetchone()[0] or 0.0

        best_strategy_row = conn.execute("""
            SELECT strategy, AVG(overall_score) as avg
            FROM evaluations GROUP BY strategy ORDER BY avg DESC LIMIT 1
        """).fetchone()
        best_strategy = best_strategy_row[0] if best_strategy_row else "chain_of_thought"

        recent_exps = conn.execute("""
            SELECT id, task, winner, created_at FROM prompt_experiments
            ORDER BY created_at DESC LIMIT 5
        """).fetchall()

        strategy_rows = conn.execute("""
            SELECT strategy, AVG(overall_score) as score, AVG(hallucination_score) as halluc,
                   AVG(cost_usd) as cost, AVG(latency_ms) as latency
            FROM evaluations GROUP BY strategy
        """).fetchall()

        bugs_severity = conn.execute("""
            SELECT severity, COUNT(*) as cnt FROM bug_reports GROUP BY severity
        """).fetchall()

        cost_by_model = conn.execute("""
            SELECT model, SUM(cost_usd) FROM evaluations GROUP BY model
        """).fetchall()

        time_series = conn.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM prompt_experiments
            GROUP BY DATE(created_at)
            ORDER BY date DESC LIMIT 30
        """).fetchall()

    strategy_comparison = {}
    for row in strategy_rows:
        d = dict(row)
        strategy_comparison[d["strategy"]] = {
            "avg_score": round(d.get("score") or 0, 3),
            "avg_hallucination": round(d.get("halluc") or 0, 3),
            "avg_cost": round(d.get("cost") or 0, 5),
            "avg_latency": round(d.get("latency") or 0, 0),
        }

    return DashboardStats(
        total_experiments=total_exp,
        total_bug_reports=total_bugs,
        total_pr_reviews=total_prs,
        total_agent_executions=total_agents,
        avg_hallucination_rate=round(avg_hallucination, 4),
        avg_accuracy_score=round(avg_accuracy, 4),
        total_cost_usd=round(total_cost, 6),
        best_strategy=best_strategy,
        recent_experiments=rows_to_list(recent_exps),
        strategy_comparison=strategy_comparison,
        cost_by_model={row[0]: round(row[1] or 0, 6) for row in cost_by_model},
        bugs_by_severity={row[0]: row[1] for row in bugs_severity},
        experiments_over_time=[{"date": row[0], "count": row[1]} for row in time_series],
    )


# ─── Context Files ────────────────────────────────────────────────────────────

@app.get("/context/{project_id}")
async def get_context_files(project_id: str):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM context_files WHERE project_id = ? ORDER BY file_type",
            (project_id,)
        ).fetchall()
    return rows_to_list(rows)


@app.post("/context")
async def save_context_file(req: ContextFileCreate):
    file_id = str(uuid.uuid4())
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM context_files WHERE project_id = ? AND filename = ?",
            (req.project_id, req.filename)
        ).fetchone()

        if existing:
            conn.execute("""
                UPDATE context_files SET content = ?, version = version + 1,
                updated_at = CURRENT_TIMESTAMP WHERE id = ?
            """, (req.content, existing[0]))
            file_id = existing[0]
        else:
            conn.execute("""
                INSERT INTO context_files (id, project_id, filename, content, file_type)
                VALUES (?, ?, ?, ?, ?)
            """, (file_id, req.project_id, req.filename, req.content, req.file_type))

    with get_db() as conn:
        row = conn.execute("SELECT * FROM context_files WHERE id = ?", (file_id,)).fetchone()
    return row_to_dict(row)


# ─── Agent Executions ─────────────────────────────────────────────────────────

@app.get("/agents/executions")
async def list_agent_executions(limit: int = 20):
    with get_db() as conn:
        rows = conn.execute("""
            SELECT id, workflow_type, status, total_duration_ms, total_tokens,
                   total_cost_usd, created_at FROM agent_executions
            ORDER BY created_at DESC LIMIT ?
        """, (limit,)).fetchall()
    return rows_to_list(rows)
