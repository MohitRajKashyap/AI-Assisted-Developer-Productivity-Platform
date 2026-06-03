# Team Guidelines & Conventions

## PR Process
- Minimum 2 approvals required (1 must be senior engineer)
- CI must be green: tests, lint, type-check, security scan (Snyk)
- No direct pushes to `main` or `release/*` branches ever
- PRs > 500 lines of diff require async architecture discussion first
- Link Jira ticket in PR description: "Closes PLAT-1234"

## Deployment
- Production deploys: Tuesdays and Thursdays only (unless P0 emergency)
- All deploys require a runbook link in deploy PR
- Feature flags via LaunchDarkly for gradual rollouts (10% → 50% → 100%)
- Auto-rollback: error rate > 1% within 10min of deploy triggers automatic revert
- Database migrations run separately before code deploy (backward-compatible only)

## On-Call
- PagerDuty 6-person rotation, 1 week per person
- P0 (site down / data loss): 5min acknowledge, 15min resolve or escalate to manager
- P1 (major feature broken): 30min acknowledge, 2h resolve target
- P2 (degraded): next business day
- Postmortem required for ALL P0 and P1 incidents within 24h

## Engineering Conventions
- No TODO comments in production code — create a Jira ticket instead
- No magic numbers — use named constants with comments explaining why
- Log at DEBUG for tracing, INFO for business events, WARN for recoverable errors, ERROR for failures
- All new services need: health endpoint, metrics endpoint, OpenAPI spec, README with local dev setup
