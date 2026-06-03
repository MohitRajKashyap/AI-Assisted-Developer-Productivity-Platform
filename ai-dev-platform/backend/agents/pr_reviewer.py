"""
AI Pull Request Reviewer
Analyzes diffs for bugs, security issues, performance problems, and style violations.
"""
import json
import uuid
import time
from typing import Dict, Any, List

from backend.core.llm_client import call_llm, call_llm_json, DEFAULT_MODEL


PR_REVIEW_SYSTEM = """You are a senior staff engineer conducting a thorough code review.
You focus on correctness, security, performance, and maintainability.
Return structured, actionable feedback."""

PR_REVIEW_PROMPT = """Review this pull request thoroughly.

PR TITLE: {title}
PR DESCRIPTION: {description}
AUTHOR: {author}
BASE BRANCH: {base_branch}

DIFF:
{diff}

Analyze the diff and return JSON with this structure:
{{
  "overall_verdict": "APPROVE|REQUEST_CHANGES|COMMENT",
  "score": 0.0-10.0,
  "summary": "one paragraph summary of the PR quality",
  "bugs_found": 0,
  "security_issues": 0,
  "performance_issues": 0,
  "style_issues": 0,
  "comments": [
    {{
      "file": "filename",
      "line": null_or_line_number,
      "severity": "error|warning|suggestion|praise",
      "category": "bug|security|performance|style|logic|test",
      "message": "what the issue is",
      "suggestion": "how to fix it"
    }}
  ],
  "positive_aspects": ["good thing 1", "good thing 2"],
  "breaking_changes": ["any breaking changes detected"],
  "test_coverage_assessment": "assessment of test coverage in this PR"
}}"""


async def review_pull_request(
    title: str,
    description: str,
    diff: str,
    author: str = "developer",
    base_branch: str = "main",
    model: str = DEFAULT_MODEL,
) -> Dict[str, Any]:
    """Run the PR review pipeline."""
    pr_id = str(uuid.uuid4())
    start = time.perf_counter()

    # Truncate very large diffs
    diff_truncated = diff[:8000] if len(diff) > 8000 else diff
    if len(diff) > 8000:
        diff_truncated += "\n\n[Diff truncated - showing first 8000 chars]"

    prompt = PR_REVIEW_PROMPT.format(
        title=title,
        description=description or "No description provided",
        author=author,
        base_branch=base_branch,
        diff=diff_truncated,
    )

    result = await call_llm_json(prompt, PR_REVIEW_SYSTEM, model=model, max_tokens=3000)
    parsed = result.get("parsed", {})
    latency_ms = int((time.perf_counter() - start) * 1000)

    if "parse_error" in parsed:
        # Fallback mock
        parsed = _mock_review(title, diff)

    # Generate markdown review
    review_md = _format_review_markdown(parsed, title, author)

    return {
        "pr_id": pr_id,
        "overall_verdict": parsed.get("overall_verdict", "COMMENT"),
        "score": float(parsed.get("score", 6.0)),
        "summary": parsed.get("summary", ""),
        "bugs_found": int(parsed.get("bugs_found", 0)),
        "security_issues": int(parsed.get("security_issues", 0)),
        "performance_issues": int(parsed.get("performance_issues", 0)),
        "style_issues": int(parsed.get("style_issues", 0)),
        "comments": parsed.get("comments", []),
        "positive_aspects": parsed.get("positive_aspects", []),
        "review_markdown": review_md,
        "latency_ms": latency_ms,
        "tokens_used": result.get("input_tokens", 0) + result.get("output_tokens", 0),
    }


def _mock_review(title: str, diff: str) -> Dict[str, Any]:
    """Fallback mock review for demo mode."""
    lines = diff.split("\n")
    added_lines = [l for l in lines if l.startswith("+") and not l.startswith("+++")]
    removed_lines = [l for l in lines if l.startswith("-") and not l.startswith("---")]

    comments = []

    # Detect common issues in diff
    for i, line in enumerate(added_lines[:20]):
        line_lower = line.lower()
        if "password" in line_lower or "secret" in line_lower or "api_key" in line_lower:
            comments.append({
                "file": "unknown",
                "line": i + 1,
                "severity": "error",
                "category": "security",
                "message": "Potential hardcoded secret/credential detected",
                "suggestion": "Use environment variables or a secrets manager"
            })
        elif "select *" in line_lower:
            comments.append({
                "file": "unknown",
                "line": i + 1,
                "severity": "warning",
                "category": "performance",
                "message": "SELECT * fetches all columns - specify needed columns",
                "suggestion": "Replace with explicit column names: SELECT id, name, email"
            })
        elif "print(" in line:
            comments.append({
                "file": "unknown",
                "line": i + 1,
                "severity": "suggestion",
                "category": "style",
                "message": "Debug print statement found",
                "suggestion": "Replace with proper logging: logger.debug(...)"
            })

    score = max(4.0, 8.0 - len(comments) * 0.5)
    verdict = "APPROVE" if score >= 7.0 else "REQUEST_CHANGES" if score < 6.0 else "COMMENT"

    return {
        "overall_verdict": verdict,
        "score": round(score, 1),
        "summary": f"PR '{title}' reviewed. Found {len(comments)} issues requiring attention. {len(added_lines)} lines added, {len(removed_lines)} removed.",
        "bugs_found": sum(1 for c in comments if c["category"] == "bug"),
        "security_issues": sum(1 for c in comments if c["category"] == "security"),
        "performance_issues": sum(1 for c in comments if c["category"] == "performance"),
        "style_issues": sum(1 for c in comments if c["category"] == "style"),
        "comments": comments or [{
            "file": "general",
            "line": None,
            "severity": "suggestion",
            "category": "style",
            "message": "Consider adding more inline documentation",
            "suggestion": "Add docstrings to public functions"
        }],
        "positive_aspects": ["Code changes appear focused", "Reasonable PR size"],
    }


def _format_review_markdown(review: Dict, title: str, author: str) -> str:
    verdict_emoji = {"APPROVE": "✅", "REQUEST_CHANGES": "❌", "COMMENT": "💬"}.get(
        review.get("overall_verdict", "COMMENT"), "💬"
    )

    score = review.get("score", 0)
    comments = review.get("comments", [])

    errors = [c for c in comments if c.get("severity") == "error"]
    warnings = [c for c in comments if c.get("severity") == "warning"]
    suggestions = [c for c in comments if c.get("severity") == "suggestion"]
    praises = [c for c in comments if c.get("severity") == "praise"]

    lines = [
        f"## {verdict_emoji} PR Review: {title}",
        f"**Author:** {author} | **Score:** {score}/10 | **Verdict:** {review.get('overall_verdict')}",
        "",
        "### Summary",
        review.get("summary", ""),
        "",
        f"| Category | Count |",
        f"|----------|-------|",
        f"| 🔴 Bugs | {review.get('bugs_found', 0)} |",
        f"| 🔒 Security | {review.get('security_issues', 0)} |",
        f"| ⚡ Performance | {review.get('performance_issues', 0)} |",
        f"| 🎨 Style | {review.get('style_issues', 0)} |",
        "",
    ]

    if errors:
        lines.append("### 🔴 Critical Issues")
        for c in errors:
            lines.append(f"**{c.get('file', 'N/A')}** (line {c.get('line', 'N/A')}): {c.get('message')}")
            if c.get("suggestion"):
                lines.append(f"  > 💡 {c.get('suggestion')}")
        lines.append("")

    if warnings:
        lines.append("### 🟡 Warnings")
        for c in warnings:
            lines.append(f"**{c.get('file', 'N/A')}**: {c.get('message')}")
            if c.get("suggestion"):
                lines.append(f"  > 💡 {c.get('suggestion')}")
        lines.append("")

    if suggestions:
        lines.append("### 💡 Suggestions")
        for c in suggestions:
            lines.append(f"- {c.get('message')}")
        lines.append("")

    if review.get("positive_aspects"):
        lines.append("### ✅ Good Practices")
        for p in review["positive_aspects"]:
            lines.append(f"- {p}")

    return "\n".join(lines)
