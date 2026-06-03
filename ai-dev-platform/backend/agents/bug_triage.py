"""
Multi-Agent Bug Triage System
5 specialized agents chained together for comprehensive bug analysis.
Simulates LangChain agent workflow with structured JSON handoffs.
"""
import asyncio
import json
import time
import uuid
from typing import Dict, Any, List, Optional

from backend.core.llm_client import call_llm, call_llm_json, DEFAULT_MODEL


class BaseAgent:
    def __init__(self, name: str, role: str, model: str = DEFAULT_MODEL):
        self.name = name
        self.role = role
        self.model = model

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def _system_prompt(self) -> str:
        return f"You are {self.role}. Return structured analysis only."


class BugReportAnalyzerAgent(BaseAgent):
    """Agent 1: Initial bug report analysis and information extraction."""

    def __init__(self, model=DEFAULT_MODEL):
        super().__init__("BugReportAnalyzer", "a senior QA engineer specializing in bug report analysis", model)

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        title = input_data.get("title", "")
        description = input_data.get("description", "")
        stack_trace = input_data.get("stack_trace", "")
        code = input_data.get("code_snippet", "")

        prompt = f"""Analyze this bug report and extract structured information.

TITLE: {title}
DESCRIPTION: {description}
STACK TRACE: {stack_trace or "Not provided"}
CODE SNIPPET: {code or "Not provided"}

Return a JSON object with:
{{
  "summary": "one-line summary of the bug",
  "affected_components": ["list", "of", "components"],
  "error_type": "type of error (e.g., NullPointerException, KeyError, etc.)",
  "symptoms": ["list of observed symptoms"],
  "reproduction_steps": ["step 1", "step 2", "..."],
  "environment_clues": ["any env/config clues from stack trace"],
  "severity_indicators": ["factors indicating severity"],
  "missing_information": ["what info would help diagnose this"]
}}"""

        result = await call_llm_json(prompt, self._system_prompt(), self.model)
        parsed = result.get("parsed", {})

        if "parse_error" in parsed:
            parsed = {
                "summary": title,
                "affected_components": ["Unknown"],
                "error_type": "Runtime Error",
                "symptoms": [description[:100]],
                "reproduction_steps": ["Reproduce as described"],
                "environment_clues": [],
                "severity_indicators": ["User reported"],
                "missing_information": ["Stack trace", "Environment details"]
            }

        return {
            "agent": self.name,
            "analysis": parsed,
            "tokens": result.get("input_tokens", 0) + result.get("output_tokens", 0),
            "latency_ms": result.get("latency_ms", 0),
        }


class RegressionClassifierAgent(BaseAgent):
    """Agent 2: Classifies bug type, severity, and regression risk."""

    def __init__(self, model=DEFAULT_MODEL):
        super().__init__("RegressionClassifier", "a release engineering expert specializing in regression analysis", model)

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        analysis = input_data.get("analysis", {})

        prompt = f"""Based on this bug analysis, classify the bug type and regression risk.

BUG ANALYSIS: {json.dumps(analysis, indent=2)}

Return JSON:
{{
  "category": "regression|new_bug|performance|security|data_corruption",
  "severity": "critical|high|medium|low",
  "regression_probability": 0.0,
  "severity_justification": "why this severity",
  "is_regression": true/false,
  "regression_indicators": ["what signals this is a regression"],
  "affected_user_percentage": "estimate e.g. 5-10%",
  "urgency": "immediate|next_sprint|backlog",
  "tags": ["relevant", "classification", "tags"]
}}"""

        result = await call_llm_json(prompt, self._system_prompt(), self.model)
        parsed = result.get("parsed", {})

        if "parse_error" in parsed:
            parsed = {
                "category": "new_bug",
                "severity": "medium",
                "regression_probability": 0.3,
                "severity_justification": "Unable to determine automatically",
                "is_regression": False,
                "regression_indicators": [],
                "affected_user_percentage": "Unknown",
                "urgency": "next_sprint",
                "tags": ["needs-investigation"]
            }

        return {
            "agent": self.name,
            "classification": parsed,
            "tokens": result.get("input_tokens", 0) + result.get("output_tokens", 0),
            "latency_ms": result.get("latency_ms", 0),
        }


class RootCauseIdentifierAgent(BaseAgent):
    """Agent 3: Deep root cause analysis."""

    def __init__(self, model=DEFAULT_MODEL):
        super().__init__("RootCauseIdentifier", "a principal engineer specializing in root cause analysis", model)

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        analysis = input_data.get("analysis", {})
        classification = input_data.get("classification", {})
        original = input_data.get("original", {})

        prompt = f"""Perform deep root cause analysis for this bug.

ORIGINAL BUG:
Title: {original.get('title', '')}
Stack Trace: {original.get('stack_trace', 'Not provided')}
Code: {original.get('code_snippet', 'Not provided')}

ANALYSIS: {json.dumps(analysis, indent=2)}
CLASSIFICATION: {json.dumps(classification, indent=2)}

Apply the "5 Whys" methodology and return JSON:
{{
  "root_cause": "precise technical root cause",
  "five_whys": ["Why 1: ...", "Why 2: ...", "Why 3: ...", "Why 4: ...", "Why 5: ..."],
  "contributing_factors": ["factor 1", "factor 2"],
  "code_location": "file/function where fix should be applied",
  "technical_explanation": "detailed technical explanation",
  "similar_bugs_risk": ["other areas that might have same issue"],
  "confidence": 0.0
}}"""

        result = await call_llm_json(prompt, self._system_prompt(), self.model)
        parsed = result.get("parsed", {})

        if "parse_error" in parsed:
            parsed = {
                "root_cause": analysis.get("error_type", "Unknown error condition"),
                "five_whys": [
                    "Why 1: The operation failed",
                    "Why 2: Input validation was missing",
                    "Why 3: Error handling was insufficient",
                    "Why 4: Edge case not considered",
                    "Why 5: No test coverage for this path"
                ],
                "contributing_factors": ["Missing validation", "No error handling"],
                "code_location": "Unknown - requires investigation",
                "technical_explanation": "Root cause requires further investigation",
                "similar_bugs_risk": [],
                "confidence": 0.4
            }

        return {
            "agent": self.name,
            "root_cause": parsed,
            "tokens": result.get("input_tokens", 0) + result.get("output_tokens", 0),
            "latency_ms": result.get("latency_ms", 0),
        }


class FixGeneratorAgent(BaseAgent):
    """Agent 4: Generates concrete fix suggestions."""

    def __init__(self, model=DEFAULT_MODEL):
        super().__init__("FixGenerator", "a senior software engineer who writes precise bug fixes", model)

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        root_cause = input_data.get("root_cause", {})
        original = input_data.get("original", {})
        classification = input_data.get("classification", {})

        prompt = f"""Generate concrete fix suggestions for this bug.

ROOT CAUSE: {json.dumps(root_cause, indent=2)}
ORIGINAL CODE: {original.get('code_snippet', 'Not provided')}
SEVERITY: {classification.get('severity', 'medium')}
CATEGORY: {classification.get('category', 'unknown')}

Return JSON:
{{
  "fixes": [
    {{
      "approach": "name of fix approach",
      "description": "what this fix does",
      "code_diff": "pseudocode or actual diff showing the change",
      "effort": "hours estimate",
      "risk": "low|medium|high",
      "side_effects": ["potential side effects"]
    }}
  ],
  "recommended_fix_index": 0,
  "test_cases_needed": ["test case 1", "test case 2"],
  "verification_steps": ["how to verify the fix works"],
  "rollback_plan": "how to rollback if fix causes issues"
}}"""

        result = await call_llm_json(prompt, self._system_prompt(), self.model)
        parsed = result.get("parsed", {})

        if "parse_error" in parsed or not parsed.get("fixes"):
            parsed = {
                "fixes": [{
                    "approach": "Defensive Programming",
                    "description": "Add input validation and error handling",
                    "code_diff": "# Add null checks and try/except blocks",
                    "effort": "2-4 hours",
                    "risk": "low",
                    "side_effects": ["May expose other latent issues"]
                }],
                "recommended_fix_index": 0,
                "test_cases_needed": ["Test with None input", "Test with empty string", "Test happy path"],
                "verification_steps": ["Run unit tests", "Deploy to staging", "Monitor error rates"],
                "rollback_plan": "Revert commit and redeploy previous version"
            }

        return {
            "agent": self.name,
            "fixes": parsed,
            "tokens": result.get("input_tokens", 0) + result.get("output_tokens", 0),
            "latency_ms": result.get("latency_ms", 0),
        }


class TechnicalReportWriterAgent(BaseAgent):
    """Agent 5: Generates comprehensive technical report."""

    def __init__(self, model=DEFAULT_MODEL):
        super().__init__("TechnicalReportWriter", "a technical writer who creates clear engineering reports", model)

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        all_data = input_data

        prompt = f"""Write a comprehensive bug triage report in Markdown format.

ANALYSIS DATA: {json.dumps(all_data, indent=2)[:4000]}

Write a professional Markdown report with sections:
# Bug Triage Report
## Executive Summary
## Bug Details
## Root Cause Analysis
## Impact Assessment
## Recommended Fix
## Testing Requirements
## Prevention Recommendations

Be specific, technical, and actionable."""

        result = await call_llm(prompt, self._system_prompt(), self.model, max_tokens=2000)

        return {
            "agent": self.name,
            "report": result.get("output", "Report generation failed"),
            "tokens": result.get("input_tokens", 0) + result.get("output_tokens", 0),
            "latency_ms": result.get("latency_ms", 0),
        }


class BugTriageWorkflow:
    """Orchestrates the 5-agent bug triage pipeline."""

    def __init__(self, model: str = DEFAULT_MODEL):
        self.agents = [
            BugReportAnalyzerAgent(model),
            RegressionClassifierAgent(model),
            RootCauseIdentifierAgent(model),
            FixGeneratorAgent(model),
            TechnicalReportWriterAgent(model),
        ]
        self.model = model

    async def run(self, bug_input: Dict[str, Any]) -> Dict[str, Any]:
        execution_id = str(uuid.uuid4())
        start_time = time.perf_counter()
        agent_steps = []
        context = {"original": bug_input}

        # Agent 1: Analysis
        step_start = time.perf_counter()
        agent1_result = await self.agents[0].run(bug_input)
        context["analysis"] = agent1_result["analysis"]
        agent_steps.append({
            "agent": "BugReportAnalyzer",
            "input_summary": f"Bug: {bug_input.get('title', '')[:50]}",
            "output_summary": f"Found: {agent1_result['analysis'].get('error_type', 'Unknown')}",
            "duration_ms": agent1_result["latency_ms"],
            "tokens_used": agent1_result["tokens"],
        })

        # Agent 2: Classification
        agent2_result = await self.agents[1].run(context)
        context["classification"] = agent2_result["classification"]
        agent_steps.append({
            "agent": "RegressionClassifier",
            "input_summary": "Analysis from Agent 1",
            "output_summary": f"Severity: {agent2_result['classification'].get('severity')} | Category: {agent2_result['classification'].get('category')}",
            "duration_ms": agent2_result["latency_ms"],
            "tokens_used": agent2_result["tokens"],
        })

        # Agent 3: Root Cause
        agent3_result = await self.agents[2].run(context)
        context["root_cause"] = agent3_result["root_cause"]
        agent_steps.append({
            "agent": "RootCauseIdentifier",
            "input_summary": "Analysis + Classification",
            "output_summary": f"Root cause: {agent3_result['root_cause'].get('root_cause', '')[:60]}",
            "duration_ms": agent3_result["latency_ms"],
            "tokens_used": agent3_result["tokens"],
        })

        # Agent 4: Fix Generation
        agent4_result = await self.agents[3].run(context)
        context["fixes"] = agent4_result["fixes"]
        fixes_count = len(agent4_result["fixes"].get("fixes", []))
        agent_steps.append({
            "agent": "FixGenerator",
            "input_summary": "Root cause analysis",
            "output_summary": f"Generated {fixes_count} fix approaches",
            "duration_ms": agent4_result["latency_ms"],
            "tokens_used": agent4_result["tokens"],
        })

        # Agent 5: Report
        agent5_result = await self.agents[4].run(context)
        agent_steps.append({
            "agent": "TechnicalReportWriter",
            "input_summary": "All previous agent outputs",
            "output_summary": "Generated comprehensive Markdown report",
            "duration_ms": agent5_result["latency_ms"],
            "tokens_used": agent5_result["tokens"],
        })

        total_duration_ms = int((time.perf_counter() - start_time) * 1000)
        total_tokens = sum(s["tokens_used"] for s in agent_steps)

        return {
            "execution_id": execution_id,
            "severity": context["classification"].get("severity", "medium"),
            "category": context["classification"].get("category", "new_bug"),
            "root_cause": context["root_cause"].get("root_cause", ""),
            "affected_components": context["analysis"].get("affected_components", []),
            "reproduction_steps": context["analysis"].get("reproduction_steps", []),
            "suggested_fixes": context["fixes"].get("fixes", []),
            "confidence_score": context["root_cause"].get("confidence", 0.7),
            "report_markdown": agent5_result["report"],
            "agent_steps": agent_steps,
            "total_duration_ms": total_duration_ms,
            "total_tokens": total_tokens,
        }
