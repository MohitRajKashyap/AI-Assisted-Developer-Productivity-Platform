import sqlite3
import json
import os
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./dev_platform.db").replace("sqlite:///", "")


def get_db_path() -> str:
    return DB_PATH


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    schema_path = Path(__file__).parent / "schema.sql"
    with get_db() as conn:
        with open(schema_path) as f:
            conn.executescript(f.read())
    _seed_demo_data()


def _seed_demo_data():
    """Seed minimal demo data for the platform."""
    with get_db() as conn:
        # Demo user
        conn.execute("""
            INSERT OR IGNORE INTO users (id, email, name, role)
            VALUES ('demo-user-1', 'demo@devplatform.ai', 'Demo Engineer', 'admin')
        """)
        # Demo project
        conn.execute("""
            INSERT OR IGNORE INTO projects (id, name, description, language, owner_id)
            VALUES ('demo-proj-1', 'E-Commerce Platform', 'Main product monorepo', 'Python/TypeScript', 'demo-user-1')
        """)
        # Seed prompt templates
        templates = [
            ("tpl-baseline", "Baseline Prompt", "baseline",
             "You are a senior software engineer. {task}\n\nCode:\n{code}"),
            ("tpl-cot", "Chain-of-Thought Prompt", "chain_of_thought",
             "You are a senior software engineer. Think step by step before answering.\n\nTask: {task}\n\nLet's analyze this carefully:\n1. First, understand the problem\n2. Identify key components\n3. Consider edge cases\n4. Formulate solution\n\nCode:\n{code}\n\nStep-by-step analysis:"),
            ("tpl-fewshot", "Few-Shot Prompt", "few_shot",
             "You are a senior software engineer. Here are examples of good code reviews:\n\nExample 1:\nCode: `def add(a,b): return a+b`\nReview: Missing type hints, no docstring, no input validation.\n\nExample 2:\nCode: `for i in range(len(lst)): print(lst[i])`\nReview: Use enumerate() instead. Prefer `for item in lst`.\n\nNow review this:\nTask: {task}\nCode:\n{code}"),
            ("tpl-negative", "Negative Example Prompt", "negative_example",
             "You are a senior software engineer.\n\nDO NOT:\n- Suggest vague improvements without specifics\n- Ignore security vulnerabilities\n- Miss performance bottlenecks\n- Skip error handling issues\n- Provide hallucinated API references\n\nTask: {task}\nCode:\n{code}\n\nProvide specific, accurate analysis:"),
            ("tpl-selfreflect", "Self-Reflection Prompt", "self_reflection",
             "You are a senior software engineer.\n\nTask: {task}\nCode:\n{code}\n\nFirst, provide your initial analysis.\nThen, critically review your own analysis:\n- Did I miss any edge cases?\n- Are my suggestions accurate and verifiable?\n- Could any suggestion introduce new bugs?\n- Am I confident in each recommendation?\n\nRevised final analysis:"),
            ("tpl-context", "Context Window Prompt", "context_window",
             "You are a senior software engineer working on a {language} project.\n\nPROJECT CONTEXT:\n{project_context}\n\nCODING STANDARDS:\n{coding_standards}\n\nTASK: {task}\n\nCODE TO ANALYZE:\n{code}\n\nGiven the project context and standards above, provide your analysis:"),
        ]
        for tpl in templates:
            conn.execute("""
                INSERT OR IGNORE INTO prompt_templates (id, name, strategy, template, project_id, created_by)
                VALUES (?, ?, ?, ?, 'demo-proj-1', 'demo-user-1')
            """, tpl)


def row_to_dict(row) -> dict:
    if row is None:
        return None
    d = dict(row)
    # Parse JSON fields
    for k, v in d.items():
        if isinstance(v, str) and v and v[0] in ('{', '['):
            try:
                d[k] = json.loads(v)
            except Exception:
                pass
    return d


def rows_to_list(rows) -> list:
    return [row_to_dict(r) for r in rows]
