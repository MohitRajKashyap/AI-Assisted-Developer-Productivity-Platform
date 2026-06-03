# System Architecture

## Service Topology
```
Client → CloudFront CDN → API Gateway (Kong) → Microservices
                                               ├── user-service      :8001
                                               ├── product-service   :8002
                                               ├── order-service     :8003
                                               ├── payment-service   :8004
                                               └── notification-svc  :8005
```

## Data Architecture
- Each service owns its PostgreSQL database (bounded context DDD)
- Event-driven communication via Kafka (MSK) for async flows
- Outbox pattern for guaranteed at-least-once message delivery
- CQRS for order/product (separate read/write models)
- Elasticsearch for product search (1B+ indexed items)

## Caching Strategy
- L1: In-process LRU (product catalog, 5min TTL, 10k items)
- L2: Redis cluster (sessions, cart, user prefs, 24h TTL)
- L3: CloudFront (static assets, API responses with Cache-Control)

## Security
- JWT (RS256) for auth, 24h expiry, refresh token rotation
- All inter-service calls use mTLS
- Secrets in AWS Secrets Manager, rotated automatically
- WAF rules for OWASP Top 10
