"""
Unit Tests — Agent Workflows
Tests mock responses, agent handoffs, and output schemas.
Run: pytest tests/unit/test_agents.py -v
"""
import pytest
import asyncio
import json
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from unittest.mock import AsyncMock, patch, MagicMock
from backend.agents.bug_triage import (
    BugReportAnalyzerAgent,
    RegressionClassifierAgent,
    RootCauseIdentifierAgent,
    FixGeneratorAgent,
    TechnicalReportWriterAgent,
    BugTriageWorkflow,
)
from backend.agents.error_fix import synthesize_error_fix, _mock_root_cause, _mock_fix
from backend.agents.pr_reviewer import review_pull_request, _mock_review, _format_review_markdown


# ─── Mock LLM Response Helpers ───────────────────────────────────────────────

def make_llm_json_result(parsed: dict) -> dict:
    return {
        "output": json.dumps(parsed),
        "parsed": parsed,
        "input_tokens": 100,
        "output_tokens": 50,
        "latency_ms": 200,
        "cost_usd": 0.001,
        "success": True,
    }

def make_llm_text_result(text: str) -> dict:
    return {
        "output": text,
        "input_tokens": 100,
        "output_tokens": 80,
        "latency_ms": 300,
        "cost_usd": 0.002,
        "success": True,
    }


# ─── Bug Report Analyzer ─────────────────────────────────────────────────────

class TestBugReportAnalyzerAgent:
    @pytest.mark.asyncio
    async def test_returns_required_keys(self):
        mock_parsed = {
            "summary": "NullPointerException in UserService",
            "affected_components": ["UserService", "AuthController"],
            "error_type": "NullPointerException",
            "symptoms": ["500 error on /profile"],
            "reproduction_steps": ["Login", "Go to profile"],
            "environment_clues": [],
            "severity_indicators": ["Production"],
            "missing_information": [],
        }
        with patch("backend.agents.bug_triage.call_llm_json", return_value=make_llm_json_result(mock_parsed)):
            agent = BugReportAnalyzerAgent()
            result = await agent.run({
                "title": "NPE in UserService",
                "description": "500 errors on profile page",
                "stack_trace": "at UserService.java:87",
            })
        assert "agent" in result
        assert result["agent"] == "BugReportAnalyzer"
        assert "analysis" in result
        assert result["analysis"]["error_type"] == "NullPointerException"

    @pytest.mark.asyncio
    async def test_fallback_on_parse_error(self):
        with patch("backend.agents.bug_triage.call_llm_json", return_value={
            "output": "invalid json {{",
            "parsed": {"parse_error": True, "raw": "invalid json {{"},
            "input_tokens": 50, "output_tokens": 10, "latency_ms": 100,
        }):
            agent = BugReportAnalyzerAgent()
            result = await agent.run({"title": "Test Bug", "description": "Something broke"})
        # Should not raise, should have fallback
        assert "analysis" in result
        assert "affected_components" in result["analysis"]


# ─── Regression Classifier ───────────────────────────────────────────────────

class TestRegressionClassifierAgent:
    @pytest.mark.asyncio
    async def test_classification_output(self):
        mock_parsed = {
            "category": "regression",
            "severity": "high",
            "regression_probability": 0.85,
            "severity_justification": "Affects 5% of users",
            "is_regression": True,
            "regression_indicators": ["Introduced in v2.4.1"],
            "affected_user_percentage": "5%",
            "urgency": "immediate",
            "tags": ["regression", "production"],
        }
        with patch("backend.agents.bug_triage.call_llm_json", return_value=make_llm_json_result(mock_parsed)):
            agent = RegressionClassifierAgent()
            result = await agent.run({"analysis": {"error_type": "NPE"}})
        assert result["classification"]["severity"] == "high"
        assert result["classification"]["is_regression"] is True
        assert result["classification"]["regression_probability"] == 0.85


# ─── Error Fix Synthesis ──────────────────────────────────────────────────────

class TestErrorFixSynthesis:
    def test_mock_root_cause_null_pointer(self):
        result = _mock_root_cause("AttributeError: 'NoneType' object has no attribute 'email'", "")
        assert "None" in result["error_type"] or "Null" in result["error_type"] or "Attribute" in result["error_type"]
        assert len(result["reasoning_chain"]) >= 3

    def test_mock_root_cause_key_error(self):
        result = _mock_root_cause("KeyError: 'user_id'", "")
        assert "Key" in result["error_type"]
        assert "dictionary" in result["why_it_fails"].lower() or "key" in result["why_it_fails"].lower()

    def test_mock_root_cause_import_error(self):
        result = _mock_root_cause("ModuleNotFoundError: No module named 'pandas'", "")
        assert "Import" in result["error_type"] or "Module" in result["error_type"]

    def test_mock_fix_none_type(self):
        root_cause = {"error_type": "NullReferenceError", "root_cause": "None dereference"}
        fix = _mock_fix(root_cause, "Python")
        assert "fix_code" in fix
        assert "confidence" in fix
        assert 0.0 <= fix["confidence"] <= 1.0
        assert len(fix["prevention_tips"]) > 0

    @pytest.mark.asyncio
    async def test_full_synthesis_structure(self):
        mock_stage1 = {
            "output": "{}",
            "parsed": {
                "error_type": "AttributeError",
                "root_cause": "None dereference",
                "faulty_line": "user.email",
                "why_it_fails": "user is None",
                "reasoning_chain": ["Step 1", "Step 2"],
            },
            "input_tokens": 100, "output_tokens": 80, "latency_ms": 200,
        }
        mock_stage2 = {
            "output": "{}",
            "parsed": {
                "fix_code": "if user is None: raise ValueError()",
                "fix_explanation": "Add null check",
                "prevention_tips": ["Always validate return values"],
                "confidence": 0.88,
                "alternative_approaches": [],
            },
            "input_tokens": 120, "output_tokens": 100, "latency_ms": 250,
        }
        with patch("backend.agents.error_fix.call_llm_json", side_effect=[mock_stage1, mock_stage2]):
            result = await synthesize_error_fix(
                error_message="AttributeError: 'NoneType' object has no attribute 'email'",
                stack_trace="at user.py:45",
                source_code="user = get_user(id)\nreturn user.email",
                language="Python",
            )
        assert "execution_id" in result
        assert "root_cause" in result
        assert "fix_code" in result
        assert result["confidence_score"] == 0.88
        assert len(result["reasoning_chain"]) == 2


# ─── PR Reviewer ─────────────────────────────────────────────────────────────

class TestPRReviewer:
    def test_mock_review_detects_secret(self):
        diff = '+SECRET_KEY = "hardcoded_secret_abc123"\n+password = "admin123"'
        result = _mock_review("test PR", diff)
        security_comments = [c for c in result["comments"] if c["category"] == "security"]
        assert len(security_comments) > 0

    def test_mock_review_detects_sql_star(self):
        diff = '+query = "SELECT * FROM users"'
        result = _mock_review("test PR", diff)
        perf_comments = [c for c in result["comments"] if c["category"] == "performance"]
        assert len(perf_comments) > 0

    def test_mock_review_detects_print(self):
        diff = '+print("debug: user_id =", user_id)'
        result = _mock_review("test PR", diff)
        style_comments = [c for c in result["comments"] if c["category"] == "style"]
        assert len(style_comments) > 0

    def test_mock_review_structure(self):
        diff = "+def hello(): pass"
        result = _mock_review("Simple PR", diff)
        assert "overall_verdict" in result
        assert result["overall_verdict"] in ["APPROVE", "REQUEST_CHANGES", "COMMENT"]
        assert 0 <= result["score"] <= 10
        assert isinstance(result["comments"], list)

    def test_format_markdown_approve(self):
        review = {
            "overall_verdict": "APPROVE",
            "score": 8.5,
            "summary": "Good PR",
            "bugs_found": 0,
            "security_issues": 0,
            "performance_issues": 0,
            "style_issues": 1,
            "comments": [],
            "positive_aspects": ["Clean code", "Good tests"],
        }
        md = _format_review_markdown(review, "feat: add caching", "alice")
        assert "APPROVE" in md or "✅" in md
        assert "8.5" in md
        assert "alice" in md

    def test_format_markdown_request_changes(self):
        review = {
            "overall_verdict": "REQUEST_CHANGES",
            "score": 4.0,
            "summary": "Critical issues found",
            "bugs_found": 2,
            "security_issues": 1,
            "performance_issues": 0,
            "style_issues": 0,
            "comments": [
                {"severity": "error", "file": "auth.py", "line": 12,
                 "category": "security", "message": "SQL injection", "suggestion": "Use parameterized queries"},
            ],
            "positive_aspects": [],
        }
        md = _format_review_markdown(review, "fix: auth", "bob")
        assert "REQUEST_CHANGES" in md or "❌" in md
        assert "SQL injection" in md


# ─── Full Workflow Integration (mocked) ──────────────────────────────────────

class TestBugTriageWorkflow:
    @pytest.mark.asyncio
    async def test_workflow_produces_all_fields(self):
        mock_analysis = {
            "summary": "NPE in UserService", "affected_components": ["UserService"],
            "error_type": "NullPointerException", "symptoms": ["500 error"],
            "reproduction_steps": ["Step 1"], "environment_clues": [],
            "severity_indicators": ["Production"], "missing_information": [],
        }
        mock_classification = {
            "category": "regression", "severity": "high", "regression_probability": 0.8,
            "severity_justification": "Production impact", "is_regression": True,
            "regression_indicators": ["New in v2.4"], "affected_user_percentage": "5%",
            "urgency": "immediate", "tags": ["regression"],
        }
        mock_root_cause = {
            "root_cause": "User not validated before attribute access",
            "five_whys": ["Why1", "Why2", "Why3", "Why4", "Why5"],
            "contributing_factors": ["Missing null check"],
            "code_location": "UserService.java:87",
            "technical_explanation": "NPE due to null user object",
            "similar_bugs_risk": [],
            "confidence": 0.87,
        }
        mock_fixes = {
            "fixes": [{"approach": "Null check", "description": "Add if null check",
                       "code_diff": "if user == null return", "effort": "1h", "risk": "low", "side_effects": []}],
            "recommended_fix_index": 0,
            "test_cases_needed": ["Test null user"],
            "verification_steps": ["Run tests"],
            "rollback_plan": "Revert commit",
        }

        json_responses = [mock_analysis, mock_classification, mock_root_cause, mock_fixes]
        call_count = {"n": 0}

        async def mock_call_json(*args, **kwargs):
            idx = min(call_count["n"], len(json_responses) - 1)
            call_count["n"] += 1
            return make_llm_json_result(json_responses[idx])

        async def mock_call_text(*args, **kwargs):
            return make_llm_text_result("# Bug Report\n## Executive Summary\nNPE issue found.")

        with patch("backend.agents.bug_triage.call_llm_json", side_effect=mock_call_json), \
             patch("backend.agents.bug_triage.call_llm", side_effect=mock_call_text):
            workflow = BugTriageWorkflow()
            result = await workflow.run({
                "title": "NPE in prod",
                "description": "500 errors",
                "stack_trace": "at UserService.java:87",
            })

        assert "execution_id" in result
        assert "severity" in result
        assert "root_cause" in result
        assert "suggested_fixes" in result
        assert "agent_steps" in result
        assert len(result["agent_steps"]) == 5
        assert result["total_duration_ms"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
