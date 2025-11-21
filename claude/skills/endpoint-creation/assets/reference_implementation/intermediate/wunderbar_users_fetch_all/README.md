# Intermediate Pattern: Proto in Engine, Implementation in Scriptdash

## When to Use This Pattern

Use this pattern when:
- You want proto contract benefits (type safety, generated clients) but models/logic stay in Scriptdash
- Migrating existing Scriptdash code to Better Boundaries incrementally
- Not ready to move models to engine but want to establish API contract
- Common for internal operations endpoints where Scriptdash is the authority

**This is NOT a migration guide** - this is a valid standalone pattern. Many engines remain mounted in Scriptdash indefinitely.

## Pattern Overview

```
┌──────────────────────────────────────┐
│  engine-operations (Proto Contract)  │
│  - Proto definitions                 │
│  - Generated interface/routes        │
│  - Published as operations_api gem   │
└────────────────┬─────────────────────┘
                 │ depends on
                 ▼
┌──────────────────────────────────────┐
│  Scriptdash (Implementation)         │
│  - Mounts engine                     │
│  - Implements AbstractEndpoint       │
│  - Accesses Scriptdash models        │
│  - Hooks up via initializer          │
└──────────────────────────────────────┘
```

## Key Files

### Engine (operations_api gem)
- `protos/src/operations_api/types/v1/wunderbar_user.proto` - Type definition
- `protos/src/operations_api/v1/wunderbar_users_endpoint.proto` - Service definition
- Generated: `operations_api/lib/operations_api/v1/wunderbar_users_endpoint/interface.rb`

### Scriptdash
- `app/services/operations/v1/wunderbar_users_endpoint.rb` - Implementation
- `config/initializers/operations_engine.rb` - Hookup
- `spec/requests/operations/v1/wunderbar_users_endpoint_spec.rb` - Tests

## Routes

Engine provides routes: `GET /v1/wunderbar_users/:id` → Scriptdash implementation

## Differences from Other Patterns

| Aspect | Engine-Only | **This Pattern** | Two-Layer |
|--------|-------------|------------------|-----------|
| Proto location | Engine | Engine | Engine + Scriptdash |
| Implementation | Engine | **Scriptdash** | Scriptdash wraps Engine |
| Models | Engine | **Scriptdash** | Engine |
| Hookup | N/A | **Initializer** | Core::API |
| Routes | Engine | Engine | Both |

## Step-by-Step

See files in this directory for complete annotated examples:

1. **Define proto in engine** (`protos/`)
2. **Generate code** (`bin/protos` in engine)
3. **Publish gem** (operations_api)
4. **Add dependency** (Scriptdash Gemfile)
5. **Implement in Scriptdash** (`app/services/operations/v1/`)
6. **Hook up in initializer** (`config/initializers/operations_engine.rb`)
7. **Write tests** (`spec/requests/`)

## Migration Path (Optional)

If you later want to move implementation to engine:
1. Create models in engine (with table_name overrides)
2. Move endpoint implementation to engine
3. Remove Scriptdash implementation
4. Update initializer to use engine implementation
5. Models stay in Scriptdash DB (engine accesses via mounted connection)

But again: **this pattern is valid long-term**, not just a migration step.
