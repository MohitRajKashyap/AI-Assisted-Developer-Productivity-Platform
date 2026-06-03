"""
Prompt Evaluation Pipeline
Scores LLM outputs on: correctness, relevance, completeness, consistency, hallucination
"""
import re
import asyncio
from typing import Dict, List, Optional, Any
from backend.core.llm_client import call_llm_json, DEFAULT_MODEL


# ─── Heuristic Evaluators ─────────────────────────────────────────────────────

def score_completeness(output: str, task: str) -> float:
    """Check if output addresses key aspects of the task."""
    STOP_WORDS = {"the", "a", "an", "and", "or", "is", "are", "for", "this", "that", "in", "of", "to", "with", "on", "at", "by", "from", "be", "it"}
    task_keywords = {w for w in task.lower().split() if w not in STOP_WORDS and len(w) > 2}

    output_lower = output.lower()
    matched = sum(1 for kw in task_keywords if kw in output_lower)
    keyword_score = matched / max(len(task_keywords), 1)

    # Check structural completeness
    has_explanation = any(w in output_lower for w in ["because", "since", "reason", "cause", "issue"])
    has_suggestion = any(w in output_lower for w in ["suggest", "recommend", "should", "consider", "fix", "solution"])
    has_code = "```" in output or "def " in output or "return " in output

    structure_score = (
        (0.3 if has_explanation else 0.0) +
        (0.4 if has_suggestion else 0.0) +
        (0.3 if has_code else 0.1)
    )

    return min(0.5 * keyword_score + 0.5 * structure_score, 1.0)


def score_relevance(output: str, task: str, code: str = "") -> float:
    """Check if output stays on topic."""
    task_words = set(re.findall(r'\w+', task.lower()))
    output_words = set(re.findall(r'\w+', output.lower()))

    if not task_words:
        return 0.5

    overlap = len(task_words & output_words) / len(task_words)

    # Check for off-topic rambling
    output_len = len(output.split())
    if output_len > 2000:
        overlap *= 0.8  # Penalize overly verbose outputs slightly

    return min(overlap * 1.5, 1.0)  # Scale up a bit since perfect overlap isn't expected


def detect_hallucinations(output: str, code: str = "") -> float:
    """
    Heuristic hallucination detection.
    Returns hallucination score (higher = more hallucinated).
    """
    hallucination_score = 0.0
    output_lower = output.lower()

    # Patterns that suggest hallucination
    hallucination_patterns = [
        (r'\baccording to (?:the )?(?:docs?|documentation|manual)\b', 0.15),
        (r'\bin (?:python|java|js) \d+\.\d+\b', 0.05),  # Often wrong version claims
        (r'\bthis (?:function|method|class) (?:was )?(?:deprecated|removed) in\b', 0.1),
        (r'\bthe official (?:docs?|documentation) (?:says?|states?|recommends?)\b', 0.1),
        (r'\bas (?:per|of) (?:python|fastapi|react|django) \d', 0.08),
    ]

    for pattern, weight in hallucination_patterns:
        if re.search(pattern, output_lower):
            hallucination_score += weight

    # Check if code references in output match code given
    if code:
        # Extract function/class names from code
        defined_names = set(re.findall(r'def (\w+)|class (\w+)', code))
        defined_flat = {n for pair in defined_names for n in pair if n}

        # Check if output references names not in code
        output_code_refs = set(re.findall(r'`(\w+)`', output))
        false_refs = output_code_refs - defined_flat - {"None", "True", "False"}
        if false_refs and defined_flat:
            # Ratio of potentially false references
            false_ratio = len(false_refs) / max(len(output_code_refs), 1)
            hallucination_score += false_ratio * 0.2

    # Check for contradictory statements
    if "always" in output_lower and "never" in output_lower:
        hallucination_score += 0.05

    return min(hallucination_score, 1.0)


def score_correctness_heuristic(output: str, task: str, code: str = "") -> float:
    """Heuristic correctness scoring."""
    score = 0.5  # Start neutral

    output_lower = output.lower()

    # Good signs
    if "```" in output:
        score += 0.15  # Provides code examples
    if any(w in output_lower for w in ["line", "line ", "l."]):
        score += 0.1  # References specific lines
    if re.search(r'\b(critical|high|medium|low)\b', output_lower):
        score += 0.1  # Provides severity
    if re.search(r'\b(o\(n\)|o\(1\)|o\(log|complexity)\b', output_lower):
        score += 0.05  # Complexity analysis

    # Bad signs (deductions)
    if len(output.split()) < 20:
        score -= 0.2  # Too brief
    if "i'm not sure" in output_lower or "i don't know" in output_lower:
        score -= 0.15  # Expresses uncertainty
    if "hallucination_score" not in output_lower:
        halluc = detect_hallucinations(output, code)
        score -= halluc * 0.3

    return max(min(score, 1.0), 0.0)


# ─── LLM-Assisted Scoring ─────────────────────────────────────────────────────

EVAL_SYSTEM = """You are an expert evaluator of AI-generated code analysis.
Score the output on each dimension from 0.0 to 1.0.
Return ONLY valid JSON, no explanation outside the JSON."""

EVAL_PROMPT_TEMPLATE = """Evaluate this AI output for a code analysis task.

ORIGINAL TASK: {task}

CODE ANALYZED:
{code}

AI OUTPUT:
{output}

Score each dimension from 0.0 to 1.0:

{{
  "correctness": <float: Is the analysis technically accurate?>,
  "relevance": <float: Does it address the specific task?>,
  "completeness": <float: Does it cover all important aspects?>,
  "consistency": <float: Is it internally consistent, no contradictions?>,
  "hallucination": <float: 0.0=no hallucinations, 1.0=major hallucinations>,
  "reasoning": "<brief explanation>"
}}"""


async def evaluate_with_llm(
    output: str,
    task: str,
    code: str = "",
    model: str = DEFAULT_MODEL,
) -> Dict[str, float]:
    """Use LLM to evaluate output quality."""
    prompt = EVAL_PROMPT_TEMPLATE.format(task=task, code=code or "N/A", output=output[:3000])
    result = await call_llm_json(prompt, EVAL_SYSTEM, model=model, max_tokens=500)
    parsed = result.get("parsed", {})

    if "parse_error" in parsed:
        # Fall back to heuristics
        return _heuristic_scores(output, task, code)

    return {
        "correctness": float(parsed.get("correctness", 0.7)),
        "relevance": float(parsed.get("relevance", 0.7)),
        "completeness": float(parsed.get("completeness", 0.7)),
        "consistency": float(parsed.get("consistency", 0.8)),
        "hallucination": float(parsed.get("hallucination", 0.1)),
    }


def _heuristic_scores(output: str, task: str, code: str) -> Dict[str, float]:
    return {
        "correctness": score_correctness_heuristic(output, task, code),
        "relevance": score_relevance(output, task, code),
        "completeness": score_completeness(output, task),
        "consistency": 0.75,
        "hallucination": detect_hallucinations(output, code),
    }


def compute_overall_score(scores: Dict[str, float]) -> float:
    """Weighted aggregate score."""
    weights = {
        "correctness": 0.35,
        "relevance": 0.20,
        "completeness": 0.20,
        "consistency": 0.10,
        "hallucination": 0.15,  # Inverted
    }
    total = 0.0
    for metric, weight in weights.items():
        val = scores.get(metric, 0.5)
        if metric == "hallucination":
            val = 1.0 - val  # Lower hallucination = better score
        total += val * weight
    return round(total, 4)


async def evaluate_output(
    output: str,
    task: str,
    code: str = "",
    use_llm_eval: bool = True,
) -> Dict[str, Any]:
    """Full evaluation pipeline."""
    if use_llm_eval:
        scores = await evaluate_with_llm(output, task, code)
    else:
        scores = _heuristic_scores(output, task, code)

    overall = compute_overall_score(scores)
    return {**scores, "overall": overall}
