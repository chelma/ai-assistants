---
name: endpoint-creation
description: Create FetchAll and FetchOne endpoints across Scriptdash and Rails Engines using proto-first architecture. Currently covers read operations (v1.0); will expand to Create/Update/Delete operations in future versions. Provides complete reference implementations and step-by-step workflow for autonomous endpoint creation.
---

# Endpoint Creation

## Overview

Build production-ready API endpoints for Scriptdash and Rails Engines using **proto-first architecture**. This skill provides copy-paste ready code examples and comprehensive guidance for creating FetchAll and FetchOne endpoints with:

- **Proto-first design**: Protocol Buffers drive code generation (Ruby, TypeScript)
- **Service V2.0**: Automated controller, routes, and client generation
- **Two-layer pattern**: Engine (business logic) + Scriptdash (permissions/frontend)
- **Seamless upgrade path**: Local method calls → RPC calls via environment configuration

**Current version**: v1.0 (FetchAll + FetchOne read operations)

**When to use this skill**:
- Creating new API endpoints in Scriptdash or Rails Engines
- Currently: Read operations (FetchAll - fetch multiple records, FetchOne - fetch single record)
- Future: Write operations (Create, Update, Delete, FetchBy, Search)

## Core Philosophy: Proto-First Architecture

The endpoint creation workflow follows **Better Boundaries** architectural principles:

**Module → Engine → Boxcar migration path**:
1. **Module**: Organize with public APIs (Core::API)
2. **Engine**: Extract to Rails Engine with proto-defined APIs
3. **Boxcar**: Deploy separately with independent scaling

**Proto as source of truth**: Every endpoint starts with `.proto` files that generate:
- Ruby types (T::Struct with Sorbet)
- Interface modules (abstract endpoints to implement)
- Controller mixins (HTTP handling)
- Route definitions (URL mapping)
- RPC clients (for remote calls)
- TypeScript types (for frontend)

**Why proto-first**:
- Type safety across Ruby and TypeScript
- Consistent API structure enforced
- Self-documenting (proto files are the spec)
- Automatic code generation reduces boilerplate

**Trade-off**: Requires learning proto syntax, changes require regeneration. The upfront investment pays dividends in reliability, maintainability, and multi-language support.

## Endpoint Creation Workflow

Follow this workflow for autonomous endpoint creation. Reference implementations demonstrate each step.

**Choose your deployment pattern**:

If not clear from context, ask the user which pattern to use:

1. **Engine-only** - Proto and implementation both in engine
   - Use when: Independent backend API, no Scriptdash integration needed
   - Example: `assets/reference_implementation/engine/action_partnerships_fetch_all/`
   - Models: In engine
   - Routes: Engine routes (`/v2/resource`)

2. **Proto in Engine, Implementation in Scriptdash** - Contract in engine, logic in Scriptdash
   - Use when: Want proto contract but models/logic stay in Scriptdash (common for gradual migration)
   - Example: `assets/reference_implementation/intermediate/wunderbar_users_fetch_all/`
   - Models: In Scriptdash
   - Routes: Engine routes (`/v1/resource`), implementation via initializer hookup

3. **Two-Layer (Scriptdash + Engine)** - Scriptdash wraps Engine API with permissions
   - Use when: Frontend needs authorization, Engine provides business logic
   - Example: `assets/reference_implementation/scriptdash/action_partnerships_fetch_all/`
   - Models: In engine
   - Routes: Both Scriptdash (`/actions/v1/resource`) and Engine (`/v2/resource`)

**When to use each**:
- **Engine-only**: Building new backend-only service
- **Intermediate**: Migrating existing Scriptdash code to proto contracts
- **Two-layer**: Frontend-facing API with separate business logic layer

### Step 1: Define Proto Type

**See**: `assets/reference_implementation/engine/action_partnerships_fetch_all/protos/types/v2/action_partnership.proto`

**For patterns**: `references/proto_patterns.md` (Pattern 1.3: Separate Type Definitions)

Define your resource structure in a `.proto` file:
- Location: `protos/src/{domain}_api/types/v{version}/{resource}.proto`
- Use `syntax = "proto3"`
- Mark required fields: `[(opts.field) = {required: true}]`
- Field numbers are permanent (never reuse)

```protobuf
message YourResource {
  int64 id = 1 [(opts.field) = {required: true}];
  string name = 2 [(opts.field) = {required: true}];
  // ... your fields
}
```

### Step 2: Define Proto Endpoint

**See**: `assets/reference_implementation/engine/action_partnerships_fetch_all/protos/v2/action_partnerships_endpoint.proto`

**For patterns**: `references/proto_patterns.md` (Patterns 1.2, 1.4, 1.5, 1.6)

Define the service with Request/Response messages:
- Location: `protos/src/{domain}_api/v{version}/{resource}_endpoint.proto`
- Use Service V2.0: `option (opts.service_value) = {version: "v2.0"};`
- Standard response structure: `errors` (field 1), `data` (field 2)
- FetchAll: Empty or `repeated int64 ids` request, `repeated Resource data` response
- FetchOne: `int64 id` request, `Resource data` response (singular)

### Step 3: Generate Code

**See**: `assets/reference_implementation/engine/action_partnerships_fetch_all/generated/`

**Command**:
```bash
cd engine-{domain}
bin/protos
git checkout {domain}_api/lib/{domain}_api.rb  # CRITICAL: Restore after generation
```

**What gets generated**:
- `interface.rb` - Request/Response types + AbstractEndpoint
- `controller.rb` - Rails controller actions
- `client.rb` - Ruby client (local/RPC switching)
- `routes.rb` - Rails route definitions
- `rpc_client.rb` - HTTP client for remote calls

### Step 4: Implement Endpoint

**See**: `assets/reference_implementation/engine/action_partnerships_fetch_all/impl/endpoint.rb`

**For patterns**: `references/implementation_patterns.md` (Patterns 3.1, 3.2, 3.5)

Extend the generated AbstractEndpoint and implement business logic:
- Location: `app/services/{domain}_engine/{resource}/endpoint.rb`
- Extend: `AbstractEndpoint` from generated interface
- Use `override` in method signature
- Return proto structs (not ActiveRecord models)
- FetchAll: `Model.all.map { |m| to_struct(m) }`
- FetchOne: `to_struct(Model.find(id))`

### Step 5: Create Controller

**See**: `assets/reference_implementation/engine/action_partnerships_fetch_all/impl/controller.rb`

**For patterns**: `references/controller_routes_patterns.md` (Patterns 4.1, 4.3)

Include generated controller mixin and provide endpoint accessor:
- Location: `app/controllers/{domain}_engine/v{version}/{resource}_controller.rb`
- Include generated `Controller` module
- Provide memoized `#endpoint` accessor
- Minimal code (3-10 lines)

### Step 6: Mount Routes

**For patterns**: `references/controller_routes_patterns.md` (Pattern 4.5)

Extend generated routes module in `config/routes.rb`:

```ruby
ActionsEngine::Engine.routes.draw do
  extend ActionsAPI::V2::YourResourceEndpoint::Routes
end
```

### Step 7: Write Tests

**See**: `assets/reference_implementation/engine/action_partnerships_fetch_all/spec/action_partnerships_controller_spec.rb`

**For patterns**: `references/testing_patterns.md` (Patterns 7.1, 7.2, 7.3)

Test full stack using RPC client:
- Location: `spec/requests/{domain}_engine/v{version}/{resource}_controller_spec.rb`
- Use `:rpc_client_requests` helper
- Test via RPC client (not controller directly)
- Use factories for test data
- Verify response types and structure

### Step 8: Wire Up in Scriptdash (If Frontend-Facing)

**See**: `assets/reference_implementation/scriptdash/action_partnerships_fetch_all/`

**For patterns**: `references/scriptdash_patterns.md` (All patterns)

For Scriptdash wrapper with permissions:

1. **Define Scriptdash proto** (imports Engine type)
2. **Core API wiring** (`app/services/{domain}/action_partnerships.rb`)
   - Include `Core::API`
   - Add Engine client
   - Configure local endpoint
3. **Dotted accessor** (`app/services/{domain}.rb`)
   - Expose module via class method
4. **Implement endpoint with permissions** (`app/services/{domain}/wunderbar/{resource}_endpoint.rb`)
   - Check `current_ability.authorize!`
   - Delegate to Engine via `Actions.resource.fetch_all`
5. **Add permissions** (`app/models/abilities/ability.rb`)
   - Define who can `:read` the Engine type
6. **Create controller** (same pattern as Engine)
7. **Write tests** (mock Engine API, test permissions)

### Step 9: Verify and Complete

You've created a production-ready endpoint following Better Boundaries architecture! Run tests to verify everything works as expected.

## Common Patterns Quick Reference

Load detailed pattern docs from `references/` as needed. Here are the most critical patterns:

**Proto System** (see `references/proto_patterns.md`):
- [CRITICAL] Proto-First Design (Pattern 1.1): .proto → bin/protos → generated code → implementation
- [CRITICAL] Service V2.0 Annotation (Pattern 1.2): Enables controller/routes/client generation
- [CRITICAL] Standard Response Structure (Pattern 1.5): `errors` field 1, `data` field 2

**Implementation** (see `references/implementation_patterns.md`):
- [CRITICAL] Endpoint Class Structure (Pattern 3.1): Extend AbstractEndpoint, use `override`
- [CRITICAL] FetchAll - Simple Implementation (Pattern 3.2): `Model.all.map { to_struct }`
- [CRITICAL] FetchOne Implementation (Pattern 3.5): `to_struct(Model.find(id))`

**Scriptdash Integration** (see `references/scriptdash_patterns.md`):
- [CRITICAL] Core API Module Structure (Pattern 6.1): Include Core::API, add_api, configure endpoint
- [CRITICAL] Dotted Accessor Pattern (Pattern 6.2): `Actions.resource.fetch_all`
- [CRITICAL] Endpoint with Authorization (Pattern 6.5): `current_ability.authorize!` then delegate

**Testing** (see `references/testing_patterns.md`):
- [CRITICAL] Engine Request Spec (Pattern 7.1): Use `:rpc_client_requests`, test via RPC client
- [CRITICAL] Scriptdash Controller Spec (Pattern 7.4): Mock Engine API, test permissions

## Troubleshooting Quick Start

For quick fixes, see `references/troubleshooting.md`. Common issues:

**Proto generation errors**:
- Run `git checkout {domain}_api/lib/{domain}_api.rb` after `bin/protos`
- Check proto syntax (required fields, imports, field numbers)

**Sorbet type errors**:
- Run `bin/tapioca gem` and `bin/tapioca dsl` after generating code
- Check `override` signatures match AbstractEndpoint

**Routes not found**:
- Verify `extend {Domain}API::V{X}::{Resource}Endpoint::Routes` in config/routes.rb

**RPC vs Local confusion**:
- Check ENV: `ALTO_DISABLE_RPC_{DOMAIN}_API` for local, `{DOMAIN}_API_BASE_URL` for RPC

**N+1 queries**:
- Add `.includes(:related_model)` before `.map`

**Permission errors**:
- Add `can :read, {Domain}API::Types::V{X}::{Resource}` to ability.rb

## Extension Roadmap

**v1.0 (current)**: FetchAll, FetchOne (read operations)
- Empty request FetchAll (fetch all records)
- Filtered FetchAll (with `ids` parameter)
- FetchOne (single record by ID)

**v2.0 (planned)**: Create, Update, Delete (write operations)
- Create with params validation
- Update with partial updates
- Delete (soft delete pattern)

**v3.0 (planned)**: FetchBy, Search, custom operations
- FetchBy with filtering and pagination
- Search with fuzzy matching
- Custom RPC methods

**Extensibility**: The proto-first approach makes adding new methods straightforward - add RPC to service definition, regenerate, implement.

## Resources

### Reference Implementations

**assets/reference_implementation/** - Complete, copy-paste ready code examples:

**Engine examples**:
- `engine/action_partnerships_fetch_all/` - Empty request FetchAll pattern
- `engine/action_types_fetch_one/` - FetchOne with ID parameter (lightweight reference)

**Scriptdash example**:
- `scriptdash/action_partnerships_fetch_all/` - Two-layer pattern with permissions

Each example includes:
- Proto definitions with full annotations
- Generated code (showing structure)
- Implementation (with pattern comments and TODOs)
- Tests (full-stack or mocked)
- README (when to use, key patterns)

### Pattern Documentation

**references/** - Detailed patterns by layer (load as needed):

- `proto_patterns.md` - 9 patterns for Protocol Buffer definitions
- `implementation_patterns.md` - 8 patterns for endpoint business logic
- `controller_routes_patterns.md` - 6 patterns for HTTP integration
- `testing_patterns.md` - 7 patterns for request specs
- `scriptdash_patterns.md` - 7 patterns for permissions and Core API
- `troubleshooting.md` - Common errors and fixes by layer

### Deep-Dive Reference

**references/better_boundaries_reference.md** - Comprehensive architectural context (~19k tokens):

**When to load**: Complex scenarios not covered by main workflow:
- Understanding Better Boundaries migration path
- Core::API internals and configuration
- Rails Engine creation from scratch
- Boxcar deployment
- Standard Resource Methods beyond FetchAll/FetchOne
- TypeScript code generation

**Don't load for**: Basic endpoint creation - use the main workflow above.

## Additional Notes

**Sorbet typing**: All generated code includes Sorbet type hints. Use `override` in implementations to ensure signatures match.

**CODEOWNERS**: Add `# @owners { team: ..., domain: ... }` annotations to endpoints and controllers.

**Semantic release**: Commit messages starting with `feat:`, `fix:`, or other semantic release prefixes trigger automated version bumps.

**Token efficiency**: Reference implementations use TODO comments for non-essential code. AI assistants can infer boilerplate from context.

**Resumability**: All patterns include "why" and "when" context to enable autonomous decision-making across sessions.
