"""
Developer Context Management System
Loads project context files (CLAUDE.md-inspired) to inject into AI prompts.
"""
import os
from pathlib import Path
from typing import Dict, Optional
from backend.database.db import get_db, rows_to_list


CONTEXT_DIR = Path(__file__).parent.parent.parent / "context"

DEFAULT_CONTEXT_FILES = {
    "project_overview.md": """# E-Commerce Platform
Main product monorepo serving 2M+ active users across web and mobile.

## Tech Stack
- Backend: Python 3.11 / FastAPI / SQLAlchemy
- Frontend: React 18 / TypeScript / TailwindCSS
- Databases: PostgreSQL 15 (primary), Redis 7 (cache/sessions)
- Infrastructure: Kubernetes on AWS EKS, Terraform IaC
- CI/CD: GitHub Actions → ECR → ArgoCD

## Key Business Context
- Payment processing is PCI-DSS compliant (no card data in our systems)
- GDPR-compliant: EU user data stays in eu-west-1
- SLA: 99.9% uptime, p99 latency < 200ms for all endpoints
""",
    "architecture.md": """# System Architecture

## Service Topology
```
Client → CloudFront CDN → API Gateway (Kong) → Services
                                               ├── user-service (port 8001)
                                               ├── product-service (port 8002)
                                               ├── order-service (port 8003)
                                               └── payment-service (port 8004)
```

## Data Architecture
- Each service owns its database (bounded context)
- Event-driven communication via Kafka (MSK)
- Outbox pattern for guaranteed message delivery
- CQRS for order/product read-heavy flows

## Caching Strategy
- L1: In-process LRU (product catalog, 5min TTL)
- L2: Redis cluster (sessions, cart, user prefs)
- L3: CloudFront (static assets, API responses with Cache-Control)
""",
    "coding_standards.md": """# Coding Standards

## Python
- PEP 8 enforced via Black (line length 100) + isort
- Type hints mandatory on ALL public functions and class attributes
- Docstrings required for all public classes and methods (Google style)
- No bare `except:` — always catch specific exceptions
- Logging over print — use `logger = logging.getLogger(__name__)`
- Async by default for I/O operations (aiohttp, asyncpg, aioredis)
- Maximum function length: 50 lines; extract helpers if exceeded
- Test coverage minimum: 80% per module, 90% for payment/auth modules

## TypeScript/React
- Strict mode enabled in tsconfig
- No `any` types — use proper generics or `unknown`
- Hooks must start with `use`, custom hooks in `src/hooks/`
- Components: functional only, no class components
- State management: Zustand for global, useState/useReducer for local

## Git
- Conventional commits: feat/fix/docs/refactor/test/chore
- Branch naming: {type}/{ticket-id}-{short-description}
- Squash merge to main, linear history required
""",
    "api_docs.md": """# API Documentation

## Authentication
All endpoints require `Authorization: Bearer <jwt-token>` header.
Tokens expire after 24h. Refresh via `POST /auth/refresh`.

## Versioning
Current: v2 at `/api/v2/`
Legacy v1 deprecated, sunset date: 2026-06-01

## Common Headers
- `X-Request-ID`: UUID for distributed tracing (auto-generated if absent)
- `X-Tenant-ID`: For multi-tenant B2B clients

## Rate Limits
- Standard: 1000 req/min per API key
- Burst: 100 req/sec for up to 10 seconds
- Payment endpoints: 60 req/min (fraud prevention)

## Error Format
```json
{"error": {"code": "RESOURCE_NOT_FOUND", "message": "...", "request_id": "uuid"}}
```

## Key Endpoints
- `GET /api/v2/users/{id}` — Get user profile
- `POST /api/v2/orders` — Create order (idempotency key required)
- `GET /api/v2/products?q=&page=&limit=` — Search products
""",
    "team_guidelines.md": """# Team Guidelines & Conventions

## PR Process
- Minimum 2 approvals required to merge
- CI must be green (tests, lint, type-check, security scan)
- No direct pushes to `main` or `release/*` branches
- PRs > 500 lines of diff require architecture discussion first

## Deployment
- Deploys on Tuesdays and Thursdays only (unless emergency)
- All deploys require a runbook update in Confluence
- Feature flags via LaunchDarkly for gradual rollouts
- Auto-rollback triggers if error rate > 1% within 10min of deploy

## On-Call
- PagerDuty rotation, 1 week each, 6-person rotation
- P0 (site down): 5min response, 15min resolve or escalate
- P1 (major feature): 30min response
- Postmortem required for all P0 and P1 incidents within 24h

## Documentation
- ADRs (Architecture Decision Records) in `/docs/adr/`
- Runbooks in Confluence under Engineering > Runbooks
- OpenAPI specs auto-generated and published to internal portal
""",
}


def load_context_files(project_id: Optional[str] = None) -> Dict[str, str]:
    """Load context files for a project from DB, falling back to defaults."""
    context = {}

    # Try DB first
    if project_id:
        try:
            with get_db() as conn:
                rows = conn.execute(
                    "SELECT filename, content FROM context_files WHERE project_id = ?",
                    (project_id,)
                ).fetchall()
            for row in rows:
                context[row[0]] = row[1]
        except Exception:
            pass

    # Fall back to filesystem defaults
    if not context:
        if CONTEXT_DIR.exists():
            for fname in DEFAULT_CONTEXT_FILES:
                fpath = CONTEXT_DIR / fname
                if fpath.exists():
                    context[fname] = fpath.read_text()
        if not context:
            context = dict(DEFAULT_CONTEXT_FILES)

    return context


def build_context_string(project_id: Optional[str] = None) -> str:
    """Build a consolidated context string for injection into prompts."""
    files = load_context_files(project_id)
    parts = []
    for fname, content in files.items():
        section = fname.replace(".md", "").replace("_", " ").upper()
        parts.append(f"### {section}\n{content.strip()}")
    return "\n\n---\n\n".join(parts)


def get_coding_standards(project_id: Optional[str] = None) -> str:
    files = load_context_files(project_id)
    return files.get("coding_standards.md", "Follow language best practices.")


def get_architecture_notes(project_id: Optional[str] = None) -> str:
    files = load_context_files(project_id)
    return files.get("architecture.md", "Standard microservices architecture.")


def ensure_context_files_on_disk():
    """Write default context files to disk if they don't exist."""
    CONTEXT_DIR.mkdir(exist_ok=True)
    for fname, content in DEFAULT_CONTEXT_FILES.items():
        fpath = CONTEXT_DIR / fname
        if not fpath.exists():
            fpath.write_text(content)
