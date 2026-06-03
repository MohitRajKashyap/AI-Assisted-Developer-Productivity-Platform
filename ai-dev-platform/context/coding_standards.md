# Coding Standards

## Python Backend
- PEP 8 enforced via Black (line length 100) + isort + flake8
- Type hints MANDATORY on all public functions and class attributes
- Docstrings required for all public classes and methods (Google style)
- No bare `except:` — always catch specific exceptions
- Logging over print — `logger = logging.getLogger(__name__)`
- Async by default for all I/O (aiohttp, asyncpg, aioredis)
- Maximum function length: 50 lines — extract helpers if exceeded
- Minimum test coverage: 80% per module, 90% for payment/auth modules
- No hardcoded secrets — use environment variables or AWS Secrets Manager

## TypeScript/React Frontend  
- Strict TypeScript mode enabled in tsconfig
- No `any` types — use proper generics or `unknown`
- Hooks must start with `use`, custom hooks in `src/hooks/`
- Functional components only — no class components
- State management: Zustand for global state, useState for local

## SQL
- Always use parameterized queries — NEVER string concatenation
- Transactions for multi-table writes
- Add indexes for all foreign keys and commonly filtered columns
- EXPLAIN ANALYZE before deploying any new query

## Git  
- Conventional commits: feat/fix/docs/refactor/test/chore
- Branch naming: `{type}/{ticket-id}-{short-description}`
- Squash merge to main, linear history enforced
