"""
Prompt Engineering Strategy Templates
Implements: Baseline, CoT, Few-Shot, Negative Example, Self-Reflection, Context Window
"""
from string import Template
from typing import Dict, Optional


STRATEGIES = {

    "baseline": Template("""You are a senior software engineer.

TASK: $task

CODE:
```$language
$code
```

Provide your analysis:"""),

    "chain_of_thought": Template("""You are a senior software engineer. Think through this step by step.

TASK: $task

CODE:
```$language
$code
```

Let's reason through this carefully:

STEP 1 — Understand the code structure and purpose
STEP 2 — Identify potential issues or improvements
STEP 3 — Consider edge cases and failure modes
STEP 4 — Evaluate security and performance implications
STEP 5 — Formulate specific, actionable recommendations

Work through each step explicitly, then provide your final answer:"""),

    "few_shot": Template("""You are a senior software engineer. Here are examples of high-quality code analysis:

--- EXAMPLE 1 ---
Code: `def divide(a, b): return a / b`
Analysis: ❌ ZeroDivisionError not handled. Add: `if b == 0: raise ValueError("Divisor cannot be zero")`. Missing type hints and docstring. Suggest: `def divide(a: float, b: float) -> float`.

--- EXAMPLE 2 ---
Code: `users = db.execute("SELECT * FROM users WHERE id=" + user_id)`
Analysis: ❌ Critical SQL injection vulnerability. Replace with parameterized query: `db.execute("SELECT * FROM users WHERE id=?", (user_id,))`. Never concatenate user input into SQL strings.

--- EXAMPLE 3 ---
Code: `for i in range(len(items)): process(items[i])`
Analysis: ⚠️ Unidiomatic Python. Use `for item in items: process(item)` or `for i, item in enumerate(items)` if index needed. Current form is O(n) but unnecessarily verbose.

--- YOUR TASK ---
Task: $task

Code:
```$language
$code
```

Following the same pattern as the examples above, provide your analysis:"""),

    "negative_example": Template("""You are a senior software engineer providing a code review.

WHAT NOT TO DO:
✗ Do NOT give vague advice like "improve error handling" without showing exactly how
✗ Do NOT miss security vulnerabilities (injection, auth bypass, data exposure)
✗ Do NOT ignore N+1 queries or O(n²) complexity issues
✗ Do NOT reference APIs or methods that don't exist (hallucination)
✗ Do NOT suggest refactors that change behavior without noting the behavioral change
✗ Do NOT skip input validation issues
✗ Do NOT give generic praise without specific justification

WHAT TO DO:
✓ Point to exact line numbers or code patterns
✓ Show corrected code for every issue raised
✓ Explain WHY each issue matters (security risk, perf impact, etc.)
✓ Give a confidence level for uncertain findings
✓ Prioritize issues by severity: CRITICAL > HIGH > MEDIUM > LOW

TASK: $task

CODE:
```$language
$code
```

Provide your specific, accurate analysis:"""),

    "self_reflection": Template("""You are a senior software engineer.

TASK: $task

CODE:
```$language
$code
```

--- INITIAL ANALYSIS ---
[Provide your first-pass analysis here]

--- SELF-CRITIQUE ---
Now review your own analysis by asking:
1. Did I miss any security vulnerabilities?
2. Are all my API/method references accurate and not hallucinated?
3. Did I consider concurrency and thread safety?
4. Are my performance estimates correct?
5. Could any of my suggestions introduce new bugs?
6. Did I provide concrete code examples for each issue?

--- REVISED FINAL ANALYSIS ---
Based on your self-critique, provide your improved, verified analysis:"""),

    "context_window": Template("""You are a senior software engineer working on this specific project.

=== PROJECT CONTEXT ===
Project: $project_name
Language: $language
Architecture: $architecture
Team Size: $team_size

=== CODING STANDARDS ===
$coding_standards

=== RELEVANT ARCHITECTURE ===
$architecture_notes

=== TASK ===
$task

=== CODE TO ANALYZE ===
```$language
$code
```

Given the project context, coding standards, and architecture above, provide a contextually-aware analysis that respects the team's conventions:"""),
}

DEFAULT_CONTEXT = {
    "project_name": "E-Commerce Platform",
    "language": "Python",
    "architecture": "Microservices with FastAPI",
    "team_size": "12 engineers",
    "coding_standards": """- PEP 8 compliance required
- Type hints mandatory on all public functions
- Docstrings for all classes and public methods
- Maximum function length: 50 lines
- Test coverage minimum: 80%
- No bare except clauses
- Logging over print statements""",
    "architecture_notes": """- Service mesh with API Gateway
- PostgreSQL for primary storage, Redis for caching
- Async/await throughout (no blocking I/O)
- Dependency injection via FastAPI
- Event-driven with Kafka for inter-service comms""",
}


def build_prompt(
    strategy: str,
    task: str,
    code: str = "",
    language: str = "Python",
    context: Optional[Dict] = None,
) -> str:
    """Build a prompt for the given strategy."""
    template = STRATEGIES.get(strategy, STRATEGIES["baseline"])
    # Merge defaults then explicit args win (avoid duplicate keyword args)
    ctx = {**DEFAULT_CONTEXT, **(context or {})}
    ctx["task"] = task
    ctx["code"] = code or "# No code provided"
    ctx["language"] = language

    try:
        return template.substitute(**ctx)
    except (KeyError, ValueError):
        return template.safe_substitute(**ctx)


SYSTEM_PROMPTS = {
    "baseline": "You are a senior software engineer. Be concise and accurate.",
    "chain_of_thought": "You are a senior software engineer who reasons step by step before answering.",
    "few_shot": "You are a senior software engineer. Match the format and quality of the examples provided.",
    "negative_example": "You are a senior software engineer. Be specific, cite exact issues, show corrected code.",
    "self_reflection": "You are a senior software engineer who critically reviews your own work.",
    "context_window": "You are a senior software engineer with full project context. Apply team conventions.",
}
