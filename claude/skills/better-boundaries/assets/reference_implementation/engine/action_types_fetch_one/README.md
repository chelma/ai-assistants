# Engine FetchOne Example: Action Types

**Pattern**: FetchOne with Required ID Parameter

## What This Demonstrates

- [CRITICAL] FetchOne request with required `id` parameter
- [CRITICAL] Response with single record (not `repeated`)
- [CRITICAL] Model.find(id) pattern
- [PREFERRED] Adapter pattern for complex model → struct mapping

## Key Differences from FetchAll

| Aspect | FetchAll | FetchOne |
|--------|----------|----------|
| **Request** | Empty or `repeated int64 ids` | `int64 id` (singular, required) |
| **Response data** | `repeated ActionType data` | `ActionType data` (singular) |
| **HTTP** | `GET /v2/action_types/fetch_all` | `GET /v2/action_types/:id` |
| **Implementation** | `Model.all` or `Model.where(id: ids)` | `Model.find(id)` |

## When to Use This Pattern

Use FetchOne when:
- Fetching specific record by primary key
- Detail pages (show one resource)
- Following RESTful conventions

## Complete Workflow

Same as FetchAll example, but:
1. Proto request has `int64 id` field (required)
2. Proto response data is singular (not repeated)
3. Endpoint implements `def fetch_one(id:)`
4. Controller gets `show` action (not `index`)
5. Routes include `get ':id'` (not `get 'fetch_all'`)
