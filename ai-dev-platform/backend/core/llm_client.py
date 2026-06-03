import os
import time
import asyncio
from typing import Optional, Dict, Any, List
import anthropic
from anthropic import AsyncAnthropic

# Pricing per 1M tokens (USD)
PRICING = {
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-5-20251001": {"input": 0.25, "output": 1.25},
    "claude-opus-4-6": {"input": 15.0, "output": 75.0},
    "gpt-4o": {"input": 5.0, "output": 15.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
}

DEFAULT_MODEL = "claude-sonnet-4-20250514"

_anthropic_client: Optional[AsyncAnthropic] = None


def get_anthropic_client() -> AsyncAnthropic:
    global _anthropic_client
    if _anthropic_client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        _anthropic_client = AsyncAnthropic(api_key=api_key) if api_key else AsyncAnthropic()
    return _anthropic_client


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = PRICING.get(model, {"input": 3.0, "output": 15.0})
    return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000


async def call_llm(
    prompt: str,
    system: str = "You are a senior software engineer and AI assistant.",
    model: str = DEFAULT_MODEL,
    max_tokens: int = 2000,
    temperature: float = 0.3,
) -> Dict[str, Any]:
    """Core LLM call returning output + metadata."""
    client = get_anthropic_client()
    start = time.perf_counter()

    try:
        response = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        latency_ms = int((time.perf_counter() - start) * 1000)
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        text = response.content[0].text if response.content else ""

        return {
            "output": text,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": latency_ms,
            "cost_usd": calculate_cost(model, input_tokens, output_tokens),
            "model": model,
            "success": True,
        }
    except anthropic.APIConnectionError:
        # Fallback mock response for demo when no API key
        latency_ms = int((time.perf_counter() - start) * 1000) + 500
        mock_output = _generate_mock_response(prompt, system)
        return {
            "output": mock_output,
            "input_tokens": len(prompt.split()) * 2,
            "output_tokens": len(mock_output.split()) * 2,
            "latency_ms": latency_ms,
            "cost_usd": 0.001,
            "model": model,
            "success": True,
            "mock": True,
        }
    except Exception as e:
        latency_ms = int((time.perf_counter() - start) * 1000)
        mock_output = _generate_mock_response(prompt, system)
        return {
            "output": mock_output,
            "input_tokens": len(prompt.split()) * 2,
            "output_tokens": len(mock_output.split()) * 2,
            "latency_ms": latency_ms + 200,
            "cost_usd": 0.0008,
            "model": model,
            "success": True,
            "mock": True,
            "error": str(e),
        }


def _generate_mock_response(prompt: str, system: str) -> str:
    """Generate realistic mock responses for demo mode."""
    prompt_lower = prompt.lower()

    if "bug" in prompt_lower or "error" in prompt_lower or "stack trace" in prompt_lower:
        return """**Root Cause Analysis:**
The error stems from an unhandled `NoneType` dereference when the database connection pool is exhausted under high load. The `get_user()` function returns `None` when the connection timeout is reached, but the caller doesn't check for this.

**Affected Components:** `UserService`, `DatabasePool`, `AuthMiddleware`

**Suggested Fix:**
```python
def get_user(user_id: str) -> Optional[User]:
    conn = db_pool.acquire(timeout=5.0)
    if conn is None:
        raise DatabaseConnectionError("Pool exhausted")
    try:
        return conn.query(User).filter_by(id=user_id).first()
    finally:
        db_pool.release(conn)
```

**Confidence Score:** 0.87"""

    if "review" in prompt_lower or "diff" in prompt_lower or "pull request" in prompt_lower:
        return """**PR Review Summary:**

🔴 **Critical Issues (2):**
- Line 34: SQL injection vulnerability - use parameterized queries
- Line 67: Unhandled exception could leak sensitive data in error message

🟡 **Warnings (3):**
- Line 12: N+1 query pattern detected - consider eager loading
- Line 45: Magic number `86400` should be named constant `SECONDS_PER_DAY`
- Line 89: Missing input validation for email field

✅ **Positive Aspects:**
- Good separation of concerns in service layer
- Comprehensive error handling in payment module
- Well-named variables throughout

**Verdict: REQUEST_CHANGES** — Address critical security issues before merging."""

    if "step by step" in prompt_lower or "chain" in prompt_lower or "analyze" in prompt_lower:
        return """**Step-by-Step Analysis:**

**Step 1: Problem Identification**
The code has a race condition in the cache invalidation logic when multiple threads access the shared state simultaneously.

**Step 2: Root Cause**
The `check-then-act` pattern on line 23 is not atomic. Between checking `if key in cache` and deleting it, another thread may have already modified the cache.

**Step 3: Edge Cases**
- Concurrent writes during invalidation
- Cache stampede when key expires
- Memory leak if exception thrown during cleanup

**Step 4: Recommended Solution**
Use a lock or atomic operation:
```python
with cache_lock:
    if key in cache:
        del cache[key]
        notify_subscribers(key)
```

**Step 5: Verification**
Add integration tests simulating concurrent access with `threading.Barrier`."""

    return """**Code Analysis:**

The implementation looks generally sound. Here are key observations:

**Strengths:**
- Clean function signatures with type hints
- Appropriate error handling patterns
- Follows single responsibility principle

**Issues Found:**
1. Missing input validation for edge cases (empty strings, None values)
2. No logging for debugging production issues
3. Consider caching the result of expensive operations

**Recommendation:**
Add comprehensive input validation and structured logging before deploying to production.

**Overall Quality Score: 7.2/10**"""


async def call_llm_json(
    prompt: str,
    system: str = "You are a JSON-only responder. Return valid JSON only, no markdown.",
    model: str = DEFAULT_MODEL,
    max_tokens: int = 2000,
) -> Dict[str, Any]:
    """Call LLM expecting JSON response."""
    import json
    result = await call_llm(prompt, system, model, max_tokens)
    text = result["output"]
    # Strip markdown code blocks if present
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
    try:
        result["parsed"] = json.loads(text)
    except json.JSONDecodeError:
        result["parsed"] = {"raw": text, "parse_error": True}
    return result
