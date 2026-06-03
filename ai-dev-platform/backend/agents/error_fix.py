"""
Error-to-Fix Synthesis Engine
Chain-based reasoning: Error → Root Cause → Explanation → Fix → Confidence
"""
import uuid
import time
import json
from typing import Dict, Any, List

from backend.core.llm_client import call_llm, call_llm_json, DEFAULT_MODEL


ERROR_ANALYSIS_SYSTEM = """You are a debugging expert. Analyze errors with a chain of reasoning.
Be precise, cite the exact line/function causing the issue, and provide working fix code."""

STAGE1_PROMPT = """Analyze this error and identify the root cause.

ERROR: {error_message}
STACK TRACE:
{stack_trace}

SOURCE CODE:
```{language}
{source_code}
```

CONTEXT: {context}

Return JSON:
{{
  "error_type": "specific error class/type",
  "root_cause": "precise one-sentence root cause",
  "faulty_line": "the specific line or code that causes the error",
  "why_it_fails": "technical explanation of why this fails",
  "reasoning_chain": ["step 1 reasoning", "step 2", "step 3"]
}}"""

STAGE2_PROMPT = """Given this error analysis, generate the fix.

ORIGINAL ERROR: {error_message}
LANGUAGE: {language}
SOURCE CODE:
```{language}
{source_code}
```

ROOT CAUSE ANALYSIS: {root_cause_json}

Generate a comprehensive fix. Return JSON:
{{
  "fix_code": "complete corrected code or code snippet",
  "fix_explanation": "step-by-step explanation of what changed and why",
  "prevention_tips": ["tip 1: how to avoid this in future", "tip 2", "tip 3"],
  "confidence": 0.0-1.0,
  "alternative_approaches": ["alternative fix approach if applicable"]
}}"""


async def synthesize_error_fix(
    error_message: str,
    stack_trace: str = "",
    source_code: str = "",
    language: str = "Python",
    context: str = "",
    model: str = DEFAULT_MODEL,
) -> Dict[str, Any]:
    """Two-stage chain: (1) Analyze error → (2) Generate fix."""
    execution_id = str(uuid.uuid4())
    start = time.perf_counter()

    # Stage 1: Root Cause Analysis
    stage1_prompt = STAGE1_PROMPT.format(
        error_message=error_message,
        stack_trace=stack_trace or "Not provided",
        language=language,
        source_code=source_code[:3000] or "Not provided",
        context=context or "No additional context",
    )

    stage1_result = await call_llm_json(stage1_prompt, ERROR_ANALYSIS_SYSTEM, model=model)
    root_cause_data = stage1_result.get("parsed", {})

    if "parse_error" in root_cause_data:
        root_cause_data = _mock_root_cause(error_message, stack_trace)

    # Stage 2: Fix Generation
    stage2_prompt = STAGE2_PROMPT.format(
        error_message=error_message,
        language=language,
        source_code=source_code[:2000] or "Not provided",
        root_cause_json=json.dumps(root_cause_data, indent=2),
    )

    stage2_result = await call_llm_json(stage2_prompt, ERROR_ANALYSIS_SYSTEM, model=model)
    fix_data = stage2_result.get("parsed", {})

    if "parse_error" in fix_data:
        fix_data = _mock_fix(root_cause_data, language)

    total_latency = int((time.perf_counter() - start) * 1000)

    return {
        "execution_id": execution_id,
        "error_type": root_cause_data.get("error_type", "Unknown Error"),
        "root_cause": root_cause_data.get("root_cause", "Unable to determine root cause"),
        "explanation": root_cause_data.get("why_it_fails", ""),
        "fix_code": fix_data.get("fix_code", "# Fix requires manual investigation"),
        "fix_explanation": fix_data.get("fix_explanation", ""),
        "prevention_tips": fix_data.get("prevention_tips", []),
        "confidence_score": float(fix_data.get("confidence", 0.7)),
        "reasoning_chain": root_cause_data.get("reasoning_chain", []),
        "alternative_approaches": fix_data.get("alternative_approaches", []),
        "latency_ms": total_latency,
        "tokens_used": (
            stage1_result.get("input_tokens", 0) + stage1_result.get("output_tokens", 0) +
            stage2_result.get("input_tokens", 0) + stage2_result.get("output_tokens", 0)
        ),
    }


def _mock_root_cause(error_message: str, stack_trace: str) -> Dict[str, Any]:
    """Infer root cause from error message patterns."""
    error_lower = error_message.lower()

    if "nonetype" in error_lower or "none" in error_lower or "null" in error_lower:
        return {
            "error_type": "NullReferenceError / AttributeError",
            "root_cause": "A variable expected to contain a value is None/null",
            "faulty_line": stack_trace.split("\n")[-2] if stack_trace else "Unknown",
            "why_it_fails": "The code attempts to access an attribute or call a method on a None value",
            "reasoning_chain": [
                "Error message indicates NoneType operation",
                "Stack trace shows the call that triggered the error",
                "The value was expected to be initialized but was not",
                "Missing null check before attribute access"
            ]
        }
    elif "keyerror" in error_lower or "key" in error_lower:
        return {
            "error_type": "KeyError",
            "root_cause": "Dictionary access with a key that does not exist",
            "faulty_line": "dict_variable[key] — key not in dict",
            "why_it_fails": "Using dict[key] raises KeyError if key is absent; use dict.get(key) for safe access",
            "reasoning_chain": [
                "KeyError raised on dictionary access",
                "The key was expected but not present",
                "Data structure may have changed or key name is wrong",
                "Use .get() with default value for safe access"
            ]
        }
    elif "import" in error_lower or "module" in error_lower:
        return {
            "error_type": "ImportError / ModuleNotFoundError",
            "root_cause": "Required module or package is not installed or not in path",
            "faulty_line": "import statement",
            "why_it_fails": "Python cannot find the specified module in sys.path or virtual environment",
            "reasoning_chain": [
                "ImportError indicates missing module",
                "Check if package is in requirements.txt",
                "Verify virtual environment is activated",
                "Run: pip install <package-name>"
            ]
        }
    else:
        return {
            "error_type": "Runtime Error",
            "root_cause": f"Unexpected condition: {error_message[:100]}",
            "faulty_line": "See stack trace",
            "why_it_fails": "An unexpected runtime condition caused the error",
            "reasoning_chain": [
                f"Error: {error_message[:80]}",
                "Examine the stack trace for the exact failure point",
                "Check input validation and boundary conditions",
                "Review recent code changes that may have introduced this"
            ]
        }


def _mock_fix(root_cause: Dict, language: str) -> Dict[str, Any]:
    error_type = root_cause.get("error_type", "")

    if "None" in error_type or "Null" in error_type:
        return {
            "fix_code": """# Before (buggy)
result = get_user(user_id).name

# After (fixed)
user = get_user(user_id)
if user is None:
    raise ValueError(f"User {user_id} not found")
result = user.name""",
            "fix_explanation": "Add None check before attribute access. The function may return None when the resource is not found.",
            "prevention_tips": [
                "Always check return values that might be None",
                "Use Optional[Type] type hints to make None-ability explicit",
                "Consider raising exceptions instead of returning None for not-found cases",
                "Use walrus operator: if (user := get_user(id)) is not None:"
            ],
            "confidence": 0.85,
            "alternative_approaches": ["Use Optional chaining pattern", "Raise NotFoundException instead of returning None"]
        }
    elif "Key" in error_type:
        return {
            "fix_code": """# Before (buggy)
value = data["key"]

# After (safe access)
value = data.get("key", default_value)

# Or with explicit error
if "key" not in data:
    raise KeyError(f"Expected key 'key' in data, got: {list(data.keys())}")
value = data["key"]""",
            "fix_explanation": "Use .get() for safe dictionary access or validate key presence before access.",
            "prevention_tips": [
                "Prefer dict.get(key, default) over dict[key]",
                "Use TypedDict or dataclasses for structured data",
                "Validate incoming data structure at API boundaries",
                "Write tests with missing keys to catch this early"
            ],
            "confidence": 0.90,
            "alternative_approaches": ["Use dataclasses/Pydantic for type-safe data access", "Use collections.defaultdict"]
        }
    else:
        return {
            "fix_code": "# Add appropriate error handling based on root cause\ntry:\n    # your code here\nexcept Exception as e:\n    logger.error(f'Operation failed: {e}')\n    raise",
            "fix_explanation": "Add proper error handling and logging to catch and diagnose the issue.",
            "prevention_tips": [
                "Add input validation at function entry points",
                "Use structured logging for easier debugging",
                "Write unit tests covering error conditions",
                "Add monitoring/alerting for production errors"
            ],
            "confidence": 0.6,
            "alternative_approaches": []
        }
