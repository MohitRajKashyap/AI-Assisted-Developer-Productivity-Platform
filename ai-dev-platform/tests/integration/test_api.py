"""
Integration Tests — FastAPI Endpoints
Tests all API routes with test client (no real LLM calls).
Run: pytest tests/integration/ -v
"""
import pytest
import json
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

# Set test DB before importing app
os.environ["DATABASE_URL"] = "sqlite:///./test_platform.db"

from backend.main import app

client = TestClient(app)


# ─── Mock LLM Helpers ─────────────────────────────────────────────────────────

MOCK_LLM_RESULT = {
    "output": "This code has a SQL injection vulnerability. Use parameterized queries instead.",
    "input_tokens": 150,
    "output_tokens": 80,
    "latency_ms": 320,
    "cost_usd": 0.0015,
    "model": "claude-sonnet-4-20250514",
    "success": True,
    "mock": True,
}

MOCK_EVAL_SCORES = {
    "correctness": 0.82,
    "relevance": 0.78,
    "completeness": 0.75,
    "consistency": 0.88,
    "hallucination": 0.08,
    "overall": 0.81,
}

MOCK_BUG_WORKFLOW_RESULT = {
    "execution_id": "test-exec-123",
    "severity": "high",
    "category": "regression",
    "root_cause": "Null dereference in UserService",
    "affected_components": ["UserService"],
    "reproduction_steps": ["Step 1", "Step 2"],
    "suggested_fixes": [{"approach": "Null check", "description": "Add null guard", "code_diff": "if x is None:", "effort": "1h", "risk": "low", "side_effects": []}],
    "confidence_score": 0.87,
    "report_markdown": "# Bug Triage Report\n## Summary\nHigh severity regression.",
    "agent_steps": [
        {"agent": "BugReportAnalyzer", "input_summary": "bug input", "output_summary": "NPE found", "duration_ms": 200, "tokens_used": 150},
        {"agent": "RegressionClassifier", "input_summary": "analysis", "output_summary": "Regression - High", "duration_ms": 180, "tokens_used": 130},
        {"agent": "RootCauseIdentifier", "input_summary": "classification", "output_summary": "Null dereference", "duration_ms": 220, "tokens_used": 160},
        {"agent": "FixGenerator", "input_summary": "root cause", "output_summary": "1 fix generated", "duration_ms": 240, "tokens_used": 180},
        {"agent": "TechnicalReportWriter", "input_summary": "all data", "output_summary": "Report generated", "duration_ms": 280, "tokens_used": 200},
    ],
    "total_duration_ms": 1120,
    "total_tokens": 820,
}

MOCK_PR_REVIEW_RESULT = {
    "pr_id": "test-pr-123",
    "overall_verdict": "REQUEST_CHANGES",
    "score": 5.5,
    "summary": "Security issues detected.",
    "bugs_found": 1,
    "security_issues": 2,
    "performance_issues": 0,
    "style_issues": 1,
    "comments": [
        {"file": "auth.py", "line": 12, "severity": "error", "category": "security",
         "message": "SQL injection vulnerability", "suggestion": "Use parameterized queries"}
    ],
    "positive_aspects": ["Good structure"],
    "review_markdown": "## ❌ PR Review\n**Verdict:** REQUEST_CHANGES",
    "latency_ms": 450,
    "tokens_used": 350,
}

MOCK_ERROR_FIX_RESULT = {
    "execution_id": "test-err-123",
    "error_type": "AttributeError",
    "root_cause": "None dereference on user object",
    "explanation": "get_user() returns None for missing users",
    "fix_code": "if user is None:\n    raise ValueError('User not found')",
    "fix_explanation": "Add null check before attribute access",
    "prevention_tips": ["Use Optional typing", "Add null checks"],
    "confidence_score": 0.85,
    "reasoning_chain": ["Error is AttributeError", "Caused by None value", "Fix: null check"],
    "alternative_approaches": [],
    "latency_ms": 580,
    "tokens_used": 420,
}


# ─── Health Check ─────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_check(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data


# ─── Dashboard ────────────────────────────────────────────────────────────────

class TestDashboard:
    def test_dashboard_stats_returns_expected_shape(self):
        resp = client.get("/dashboard/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_experiments" in data
        assert "total_bug_reports" in data
        assert "total_pr_reviews" in data
        assert "avg_hallucination_rate" in data
        assert "strategy_comparison" in data

    def test_dashboard_stats_numeric_values(self):
        resp = client.get("/dashboard/stats")
        data = resp.json()
        assert isinstance(data["total_experiments"], int)
        assert isinstance(data["total_bug_reports"], int)
        assert isinstance(data["avg_accuracy_score"], float)
        assert 0.0 <= data["avg_hallucination_rate"] <= 1.0


# ─── Prompt Lab ───────────────────────────────────────────────────────────────

class TestPromptLab:
    def test_prompt_test_single_strategy(self):
        async def mock_run_strategy(*args, **kwargs):
            return {
                "strategy": args[0],
                "model": "claude-sonnet-4-20250514",
                "output": "Analysis: SQL injection found.",
                "prompt_tokens": 150,
                "completion_tokens": 80,
                "latency_ms": 300,
                "correctness_score": 0.82,
                "relevance_score": 0.78,
                "completeness_score": 0.75,
                "consistency_score": 0.88,
                "hallucination_score": 0.08,
                "overall_score": 0.81,
                "cost_usd": 0.0015,
            }

        with patch("backend.main._run_strategy", side_effect=mock_run_strategy):
            resp = client.post("/prompts/test", json={
                "task": "Review this SQL query for security vulnerabilities",
                "code": "SELECT * FROM users WHERE id=" + "' OR 1=1 --",
                "strategies": ["baseline"],
                "model": "claude-sonnet-4-20250514",
            })

        assert resp.status_code == 200
        data = resp.json()
        assert "experiment_id" in data
        assert "results" in data
        assert "baseline" in data["results"]
        assert "winner" in data
        assert data["winner"] == "baseline"

    def test_prompt_experiments_list(self):
        resp = client.get("/prompts/experiments")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_prompt_test_missing_task(self):
        resp = client.post("/prompts/test", json={"code": "x = 1"})
        assert resp.status_code == 422  # Validation error


# ─── Bug Triage ───────────────────────────────────────────────────────────────

class TestBugTriage:
    def test_analyze_bug_returns_structure(self):
        with patch("backend.main.BugTriageWorkflow") as MockWorkflow:
            instance = MockWorkflow.return_value
            instance.run = AsyncMock(return_value=MOCK_BUG_WORKFLOW_RESULT)

            resp = client.post("/bugs/analyze", json={
                "title": "NullPointerException in production",
                "description": "500 errors on /profile endpoint",
                "stack_trace": "at UserService.java:87",
                "code_snippet": "User user = repo.findById(id); return user.getEmail();",
            })

        assert resp.status_code == 200
        data = resp.json()
        assert "bug_id" in data
        assert "severity" in data
        assert "agent_steps" in data
        assert len(data["agent_steps"]) == 5

    def test_analyze_bug_missing_required_fields(self):
        resp = client.post("/bugs/analyze", json={"title": "Bug"})
        assert resp.status_code == 422

    def test_bug_list(self):
        resp = client.get("/bugs/list")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_bug_list_with_status_filter(self):
        resp = client.get("/bugs/list?status=open")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ─── PR Review ────────────────────────────────────────────────────────────────

class TestPRReview:
    def test_review_pr_returns_comments(self):
        async def mock_review(*args, **kwargs):
            return MOCK_PR_REVIEW_RESULT
        with patch("backend.main.review_pull_request", side_effect=mock_review):
            resp = client.post("/pr/review", json={
                "title": "feat: Add JWT auth",
                "description": "Implements authentication",
                "diff": '+SECRET_KEY = "hardcoded"\n+sql = "SELECT * FROM users WHERE id=" + user_id',
                "author": "alice",
            })

        assert resp.status_code == 200
        data = resp.json()
        assert "overall_verdict" in data
        assert "score" in data
        assert "comments" in data

    def test_pr_list(self):
        resp = client.get("/pr/list")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_review_pr_missing_diff(self):
        resp = client.post("/pr/review", json={"title": "test"})
        assert resp.status_code == 422


# ─── Error Fix ────────────────────────────────────────────────────────────────

class TestErrorFix:
    def test_error_fix_returns_fix_code(self):
        with patch("backend.agents.error_fix.call_llm_json") as mock_llm:
            mock_llm.side_effect = [
                {"output": "{}", "parsed": {
                    "error_type": "AttributeError",
                    "root_cause": "None dereference",
                    "faulty_line": "user.email",
                    "why_it_fails": "user is None",
                    "reasoning_chain": ["Step 1", "Step 2"],
                }, "input_tokens": 100, "output_tokens": 80, "latency_ms": 200},
                {"output": "{}", "parsed": {
                    "fix_code": "if user is None: raise ValueError()",
                    "fix_explanation": "Add null check",
                    "prevention_tips": ["Validate return values"],
                    "confidence": 0.88,
                    "alternative_approaches": [],
                }, "input_tokens": 120, "output_tokens": 100, "latency_ms": 250},
            ]
            resp = client.post("/errors/fix", json={
                "error_message": "AttributeError: 'NoneType' object has no attribute 'email'",
                "stack_trace": "at user.py:45",
                "source_code": "return user.email",
                "language": "Python",
            })

        assert resp.status_code == 200
        data = resp.json()
        assert "fix_code" in data
        assert "root_cause" in data
        assert "confidence_score" in data
        assert 0.0 <= data["confidence_score"] <= 1.0

    def test_error_fix_missing_error_message(self):
        resp = client.post("/errors/fix", json={"language": "Python"})
        assert resp.status_code == 422


# ─── Evaluations ─────────────────────────────────────────────────────────────

class TestEvaluations:
    def test_evaluation_history_returns_list(self):
        resp = client.get("/evaluations/history")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_strategy_comparison_returns_list(self):
        resp = client.get("/evaluations/strategy-comparison")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ─── Context Files ────────────────────────────────────────────────────────────

class TestContextFiles:
    def test_get_context_files(self):
        resp = client.get("/context/demo-proj-1")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_save_context_file(self):
        resp = client.post("/context", json={
            "project_id": "demo-proj-1",
            "filename": "test_context.md",
            "content": "# Test Context\nThis is test content.",
            "file_type": "overview",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["filename"] == "test_context.md"

    def test_save_and_update_context_file(self):
        # Save
        client.post("/context", json={
            "project_id": "demo-proj-1",
            "filename": "update_test.md",
            "content": "Version 1",
            "file_type": "overview",
        })
        # Update
        resp = client.post("/context", json={
            "project_id": "demo-proj-1",
            "filename": "update_test.md",
            "content": "Version 2 - updated",
            "file_type": "overview",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["content"] == "Version 2 - updated"


# ─── Agent Executions ─────────────────────────────────────────────────────────

class TestAgentExecutions:
    def test_list_agent_executions(self):
        resp = client.get("/agents/executions")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ─── Cleanup ──────────────────────────────────────────────────────────────────

def pytest_sessionfinish(session, exitstatus):
    """Clean up test database."""
    if os.path.exists("test_platform.db"):
        os.remove("test_platform.db")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
