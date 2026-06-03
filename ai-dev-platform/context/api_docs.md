# API Documentation

## Authentication
All endpoints require `Authorization: Bearer <jwt-token>` header.
Tokens expire after 24h. Refresh via `POST /auth/refresh`.
Service-to-service calls use `X-Service-Token` header with rotating secrets.

## Versioning
- Current stable: **v2** at `/api/v2/`
- Legacy v1 at `/api/v1/` — deprecated, sunset 2026-06-01
- Breaking changes require a new version number

## Common Request Headers
| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | `Bearer <jwt>` |
| `X-Request-ID` | No | UUID for tracing (auto-generated if absent) |
| `X-Tenant-ID` | B2B only | Multi-tenant identifier |
| `Content-Type` | Yes (POST/PUT) | `application/json` |

## Rate Limits
- Standard: 1000 req/min per API key
- Burst: 100 req/sec for up to 10 seconds
- Payment endpoints: 60 req/min (fraud prevention)
- Response headers: `X-RateLimit-Remaining`, `X-RateLimit-Reset`

## Standard Error Format
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "User with ID 123 not found",
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "details": {}
  }
}
```

## Key Endpoints
- `GET  /api/v2/users/{id}` — User profile
- `POST /api/v2/orders` — Create order (idempotency-key header required)
- `GET  /api/v2/products?q=&category=&page=&limit=` — Product search
- `POST /api/v2/auth/login` — Get access + refresh tokens
- `POST /api/v2/auth/refresh` — Rotate tokens
