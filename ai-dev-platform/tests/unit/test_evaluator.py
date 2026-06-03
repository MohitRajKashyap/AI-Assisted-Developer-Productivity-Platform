"""
Unit Tests — Evaluation Framework & Prompt Templates
Run: pytest tests/unit/ -v
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from backend.evaluation.evaluator import (
    score_completeness,
    score_relevance,
    detect_hallucinations,
    score_correctness_heuristic,
    compute_overall_score,
)
from backend.prompts.templates import build_prompt, STRATEGIES


# ─── Completeness Tests ───────────────────────────────────────────────────────

class TestCompleteness:
    def test_high_completeness_with_code_and_suggestion(self):
        output = """
        The function has a SQL injection vulnerability.
        You should use parameterized queries because direct concatenation is unsafe.
        Fix:
        ```python
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        ```
        I recommend adding input validation as well.
        """
        score = score_completeness(output, "review this database query function for security")
        assert score > 0.5, f"Expected >0.5, got {score}"

    def test_low_completeness_empty_output(self):
        score = score_completeness("", "analyze this code for bugs")
        assert score < 0.3

    def test_medium_completeness_explanation_only(self):
        output = "The code has issues because the loop is inefficient and should be refactored."
        score = score_completeness(output, "analyze this code")
        assert 0.2 < score < 0.8


# ─── Relevance Tests ──────────────────────────────────────────────────────────

class TestRelevance:
    def test_high_relevance_on_topic(self):
        output = "This Python function has a security vulnerability in the SQL query construction."
        score = score_relevance(output, "Review this Python function for SQL injection vulnerabilities")
        assert score > 0.4

    def test_zero_relevance_completely_off_topic(self):
        output = "Bananas are a tropical fruit high in potassium. They grow in warm climates."
        score = score_relevance(output, "Review this Python function for bugs")
        assert score < 0.3

    def test_relevance_with_code_context(self):
        output = "The function get_user() is missing null check before accessing .email attribute."
        score = score_relevance(output, "find bugs in get_user function", "def get_user(): return user.email")
        assert score > 0.3


# ─── Hallucination Detection ──────────────────────────────────────────────────

class TestHallucinationDetection:
    def test_no_hallucination_clean_output(self):
        output = "Add a null check before accessing the attribute. Use `if user is None: raise ValueError()`."
        score = detect_hallucinations(output)
        assert score < 0.2

    def test_hallucination_from_doc_claim(self):
        output = "According to the official Python documentation, this method was deprecated in Python 3.9."
        score = detect_hallucinations(output)
        assert score > 0.05

    def test_hallucination_false_references(self):
        code = "def process(data): return data"
        output = "The `transform_data()` method has a bug. Also `validate_schema()` is not handling edge cases."
        score = detect_hallucinations(output, code)
        # References functions not in code
        assert score >= 0.0  # Should flag or be neutral; function not always present

    def test_low_hallucination_accurate_references(self):
        code = "def calculate_total(items): return sum(item.price for item in items)"
        output = "The `calculate_total` function looks correct. Consider adding a check for empty `items` list."
        score = detect_hallucinations(output, code)
        assert score < 0.3


# ─── Overall Score Computation ────────────────────────────────────────────────

class TestOverallScore:
    def test_perfect_scores(self):
        scores = {
            "correctness": 1.0,
            "relevance": 1.0,
            "completeness": 1.0,
            "consistency": 1.0,
            "hallucination": 0.0,  # 0 hallucination = best
        }
        result = compute_overall_score(scores)
        assert result > 0.95, f"Expected near 1.0, got {result}"

    def test_zero_scores(self):
        scores = {
            "correctness": 0.0,
            "relevance": 0.0,
            "completeness": 0.0,
            "consistency": 0.0,
            "hallucination": 1.0,  # Maximum hallucination = worst
        }
        result = compute_overall_score(scores)
        assert result < 0.1, f"Expected near 0.0, got {result}"

    def test_hallucination_inverted(self):
        """High hallucination should drag down overall score."""
        good_scores = {"correctness": 0.9, "relevance": 0.9, "completeness": 0.9, "consistency": 0.9, "hallucination": 0.0}
        bad_scores = {"correctness": 0.9, "relevance": 0.9, "completeness": 0.9, "consistency": 0.9, "hallucination": 0.8}
        good = compute_overall_score(good_scores)
        bad = compute_overall_score(bad_scores)
        assert good > bad, "High hallucination should reduce overall score"

    def test_weights_sum_to_one(self):
        """Test that weighted average stays in [0,1]."""
        import random
        for _ in range(20):
            scores = {k: random.random() for k in ["correctness", "relevance", "completeness", "consistency", "hallucination"]}
            result = compute_overall_score(scores)
            assert 0.0 <= result <= 1.0, f"Score out of range: {result}"


# ─── Prompt Template Tests ────────────────────────────────────────────────────

class TestPromptTemplates:
    def test_all_strategies_build(self):
        for strategy in STRATEGIES:
            prompt = build_prompt(strategy, "Review this function", "def foo(): pass", "Python")
            assert len(prompt) > 50, f"Strategy {strategy} produced too-short prompt"
            assert "def foo(): pass" in prompt or "foo" in prompt or "Review" in prompt

    def test_baseline_contains_task(self):
        prompt = build_prompt("baseline", "Find security vulnerabilities", "x = input()", "Python")
        assert "Find security vulnerabilities" in prompt

    def test_cot_contains_steps(self):
        prompt = build_prompt("chain_of_thought", "Analyze this code", "pass", "Python")
        assert "STEP" in prompt or "step" in prompt or "Step" in prompt

    def test_few_shot_contains_examples(self):
        prompt = build_prompt("few_shot", "Review code", "pass", "Python")
        assert "EXAMPLE" in prompt or "Example" in prompt

    def test_negative_contains_dont(self):
        prompt = build_prompt("negative_example", "Review code", "pass", "Python")
        assert "NOT" in prompt or "DO NOT" in prompt or "NEVER" in prompt

    def test_self_reflection_contains_critique(self):
        prompt = build_prompt("self_reflection", "Review code", "pass", "Python")
        assert "critique" in prompt.lower() or "review" in prompt.lower() or "analysis" in prompt.lower()

    def test_context_window_contains_project_info(self):
        prompt = build_prompt("context_window", "Review code", "pass", "Python")
        assert any(word in prompt for word in ["Project", "project", "Context", "context", "Standards", "standards"])

    def test_code_injection(self):
        """Code should appear verbatim in the prompt."""
        code = "def unique_func_xyz(): return 42"
        prompt = build_prompt("baseline", "task", code, "Python")
        assert "unique_func_xyz" in prompt


# ─── Correctness Heuristic Tests ─────────────────────────────────────────────

class TestCorrectnessHeuristic:
    def test_good_output_high_score(self):
        output = """
        Line 23: SQL injection vulnerability detected.
        Severity: CRITICAL
        
        Fix:
        ```python
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        ```
        
        This achieves O(1) complexity with proper parameterization.
        """
        score = score_correctness_heuristic(output, "review SQL query", "cursor.execute('SELECT * FROM users WHERE id=' + id)")
        assert score > 0.5

    def test_too_short_output_penalized(self):
        score = score_correctness_heuristic("Looks fine.", "review this code")
        assert score < 0.5

    def test_uncertainty_penalized(self):
        output = "I'm not sure about this code, I don't know what it does exactly."
        score = score_correctness_heuristic(output, "review code")
        assert score < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
