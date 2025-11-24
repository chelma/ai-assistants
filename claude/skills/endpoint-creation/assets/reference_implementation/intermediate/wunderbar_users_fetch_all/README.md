# Intermediate Pattern: Proto in Engine, Implementation in Scriptdash

## When to Use This Pattern

Use this pattern when:
- **Models are deeply coupled to Scriptdash** - The underlying model has many associations to other Scriptdash models that would be difficult to move
- **Authentication dependencies** - Model uses Devise or other Scriptdash-specific auth systems
- **You want proto benefits without refactoring** - Get type safety, generated clients, and API contracts without massive model migration
- **Internal operations endpoints** - Where Scriptdash is the natural authority for the data

**This is NOT a migration guide** - this is a valid long-term pattern. Many engines remain mounted in Scriptdash indefinitely.

## Why Models Stay in Scriptdash

**Real-world example**: WunderbarUser model has:
- `belongs_to :patient` (Scriptdash model)
- `has_many :attachments` (Scriptdash model)
- Dozens of other associations to Scriptdash models
- Uses Devise for authentication (Scriptdash gem)

**Moving to engine would require**:
- Moving Patient model (and all ITS associations)
- Moving Attachment model (and all ITS associations)
- Reimplementing authentication system
- Cascade effect touching hundreds of files

**This pattern solves it**:
- ✅ Model stays in Scriptdash (no cascade refactoring)
- ✅ Proto establishes API contract (better than direct model access)
- ✅ Generated clients/routes (infrastructure benefits)
- ✅ Can remain this way indefinitely (not temporary!)

**TLDR**: Implementation lives in Scriptdash when the underlying model can't or hasn't yet been moved due to coupling.

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
