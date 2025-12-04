# Scriptdash FetchAll Example: Action Partnerships (Two-Layer Pattern)

**Pattern**: Frontend/Gateway layer with permissions wrapping Engine API

## What This Demonstrates

- [CRITICAL] Two-layer architecture (Scriptdash → Engine)
- [CRITICAL] Core::API wiring for local/RPC switching
- [CRITICAL] Dotted accessor pattern (`Actions.action_partnerships.fetch_all`)
- [CRITICAL] Permission enforcement with CanCanCan
- [CRITICAL] Type reuse (imports Engine types)
- [PREFERRED] Testing with mocked Engine API

## When to Use This Pattern

Use Scriptdash wrapper when:
- Frontend needs permission enforcement
- Multiple frontends consume same Engine
- Gateway pattern (Scriptdash delegates to Engine)
- UI-specific logic needed

## Two-Layer Architecture

```
Frontend (Browser)
   ↓ HTTP
Scriptdash Endpoint (app/services/actions/wunderbar/action_partnerships_endpoint.rb)
   ├─ Check permissions (current_ability.authorize!)
   └─ Delegate to Engine via Core::API
        ↓ Core::API (local or RPC depending on ENV)
Engine Endpoint (ActionsEngine::ActionPartnerships::Endpoint)
   └─ Business logic + database access
```

## Key Differences from Engine-Only Pattern

| Aspect | Engine Only | Scriptdash + Engine |
|--------|-------------|---------------------|
| **Proto** | Engine types only | Scriptdash imports Engine types |
| **Endpoint** | Business logic | Permissions + delegation |
| **Testing** | RPC client (full stack) | Mock Engine API |
| **Deployment** | One service | Two services (can be separate) |

## Complete Workflow

### 1. Define Proto (`protos/alto/actions/wunderbar/v1/action_partnerships_endpoint.proto`)
- Import Engine type (type reuse!)
- Define Scriptdash service (same signature)

### 2. Core API Wiring (`app/services/actions/action_partnerships.rb`)
- Include Core::API
- Add Engine client
- Configure local endpoint

### 3. Dotted Accessor (`app/services/actions.rb`)
- Expose `Actions.action_partnerships` accessor

### 4. Implement Endpoint with Permissions (`app/services/actions/wunderbar/action_partnerships_endpoint.rb`)
- Check permissions first
- Delegate to `Actions.action_partnerships.fetch_all`

### 5. Add Permissions (`app/models/abilities/ability.rb`)
- Define who can `:read` ActionPartnership

### 6. Create Controller (`app/controllers/wunderbar/actions/v1/action_partnerships_controller.rb`)
- Same pattern as Engine controller

### 7. Write Tests (`spec/requests/wunderbar/actions/v1/action_partnerships_controller_spec.rb`)
- Mock Engine API (don't test Engine business logic)
- Test permissions (with/without access)

## Key Files

- **protos/** - Scriptdash service (imports Engine types)
- **core_api/** - Wiring for Actions.action_partnerships
- **impl/** - Endpoint (permissions) + Controller (HTTP)
- **permissions/** - Ability classes
- **spec/** - Tests (mock Engine, test permissions)
