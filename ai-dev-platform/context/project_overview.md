# E-Commerce Platform

Main product monorepo serving 2M+ active users across web and mobile.

## Tech Stack
- Backend: Python 3.11 / FastAPI / SQLAlchemy 2.0
- Frontend: React 18 / TypeScript / TailwindCSS / Vite
- Databases: PostgreSQL 15 (primary), Redis 7 (cache/sessions)  
- Infrastructure: Kubernetes on AWS EKS, Terraform IaC
- CI/CD: GitHub Actions → ECR → ArgoCD
- Monitoring: Datadog APM + CloudWatch + PagerDuty

## Key Business Context
- Payment processing is PCI-DSS compliant (Stripe handles card data)
- GDPR-compliant: EU user data stays in eu-west-1 region
- SLA: 99.9% uptime, p99 latency < 200ms for all endpoints
- Peak load: Black Friday ~50k req/sec sustained for 6 hours

## Team Structure
- 3 backend squads (Platform, Checkout, Discovery)
- 2 frontend squads (Web, Mobile)
- 1 Platform/Infra team
- ~60 engineers total, ~35 backend-focused
