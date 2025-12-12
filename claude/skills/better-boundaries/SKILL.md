---
name: better-boundaries
description: Understand and apply Better Boundaries architecture through hands-on endpoint creation. Covers proto-first API development, Module→Engine→Boxcar migration path, Core::API patterns, and alto-workspace tooling. Primary use case is building production-ready FetchAll/FetchOne endpoints for Scriptdash and Rails Engines.
---

# Better Boundaries

## Overview

**Better Boundaries** is an architectural philosophy for building scalable Rails applications through progressive service extraction. This skill teaches Better Boundaries principles through the practical lens of **building production-ready API endpoints** using proto-first architecture.

**The Better Boundaries journey**:
1. **Module** - Organize monolith code with public APIs (Core::API pattern)
2. **Engine** - Extract to Rails Engine with proto-defined contracts
3. **Boxcar** - Deploy as independent service with autonomous scaling

**Core architectural principles**:
- **Proto-first design**: Protocol Buffers as source of truth, generating Ruby types, interfaces, controllers, routes, and TypeScript definitions
- **Two-layer pattern**: Engine provides business logic, Scriptdash adds permissions/frontend integration
- **Seamless migration**: Local method calls evolve to RPC calls via environment configuration
- **Type safety**: Sorbet types throughout, enforced contracts across Ruby and TypeScript

**What this skill provides**:
- Step-by-step workflow for creating FetchAll and FetchOne endpoints (v1.0)
- Complete reference implementations with copy-paste ready code
- Comprehensive pattern documentation by architectural layer
- alto-workspace tooling integration (CLI, proto generation, dependency management)
- Foundation for understanding broader Better Boundaries concepts

## When to Use This Skill

Invoke this skill when:
- **Creating new or modifying existing API endpoints** in Scriptdash or Rails Engines (primary use case)
- Understanding the **Better Boundaries philosophy and methodology**
- Working with **alto-workspace tooling** (engine creation, dependency management, proto generation)

**Currently covers**: Read operations (FetchAll - multiple records, FetchOne - single record)
**Future versions**: Write operations (Create, Update, Delete, FetchBy, Search)

## Proto-First Architecture

Better Boundaries implementation relies on **proto-first architecture**:

**Module → Engine → Boxcar migration path**:
1. **Module**: Organize with public APIs (Core::API)
2. **Engine**: Extract to Rails Engine with proto-defined APIs
3. **Boxcar**: Deploy separately with independent scaling

**Foundation**: alto-workspace manages the entire infrastructure (repositories, dependencies, proto generation, deployment configs). See `references/alto-workspace-infrastructure.md` for complete context.

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

## Initial Assessment

**Before starting endpoint creation**, ask these questions to avoid unnecessary work:

### 1. Which repositories?
Ask: **"Which repositories are you working with?"** (`scriptdash`, `engine-partnerships`, etc)

Remember the list - we'll need to initialize each one.

### 2. Is workspace ready?
Ask: **"Is your Alto workspace set up for `<list of repository names>`?"**

**If YES** (experienced engineer):
- Offer quick verification for each repo: `scripts/verify_repo.sh <repo-name> --sorbet`
- If all pass → Proceed to [Endpoint Creation Workflow](#endpoint-creation-workflow)
- If any fail → Run setup below

**If NO or UNSURE**:

First-time workspace setup - ask: **"Do you want to sync all repositories to latest versions?"**

- **Recommended for new setups**: Runs `alto up` to sync all 50+ repos to origin/master. Side effect: rebases any local branches behind master. If you don't have local feature branches checked out, this is safe and gets you fully up-to-date.

- **If YES**: `scripts/init_workspace.sh --sync`
- **If NO**: `scripts/init_workspace.sh` (just verifies, no sync)

Then initialize each target repository:
```bash
scripts/init_repo.sh <repo-name>              # Install deps, generate protos, setup DB
scripts/verify_repo.sh <repo-name> --sorbet   # Quick type check
# Repeat for each repository
```

**On script failures**: See `references/workspace-setup.md` for troubleshooting.

### 3. Create feature branch

**Before making any changes**, ask: **"Would you like me to create a new feature branch off of mainline for this work?"**

**If YES**:
- Ask for branch name: **"What would you like to name your feature branch?"** (e.g., `add-partnerships-fetch-all`, `feature/partnerships-api`)
- For each repository, create and checkout the branch:
  ```bash
  cd $ALTO_WORKSPACE_REPO_ROOT/<repo-name>
  git checkout main  # or master
  git pull origin main
  git checkout -b <branch-name>
  ```

**If NO**: Proceed (they're already on a feature branch or will handle it themselves)

Then proceed to [Endpoint Creation Workflow](#endpoint-creation-workflow).

## Endpoint Creation Workflow

Follow this workflow for autonomous endpoint creation. Reference implementations demonstrate each step.

**Prerequisites**:

Complete [Initial Assessment](#initial-assessment) to verify workspace setup.

**Additional requirements**:
- Rails Engine exists (or use `alto generate engine <name>` - see `references/alto-workspace-infrastructure.md`)
- Database tables and models created
- alto-workspace configured for your engine (see `references/alto-workspace-quick-reference.md` for config examples)

### Step 0: Understand Deployment Topology

**Before writing any code**, understand how the engines relate to each other and to Scriptdash.

Ask: **"Which engines are involved in this feature?"** (e.g., PartnershipsEngine calls LabelsEngine, Scriptdash calls ActionsEngine)

For each engine, determine deployment model:

**Check scriptdash/config/routes.rb** to see what's mounted:
```bash
cd $ALTO_WORKSPACE_REPO_ROOT/scriptdash
grep -A2 "mount.*Engine" config/routes.rb
```

**Deployment models**:
- **Mounted in Scriptdash**: Engine runs in same process as Scriptdash (e.g., `mount LabelsEngine::Engine, at: '/labels'`)
- **Boxcar**: Engine deployed separately (not in routes.rb, has own `.deploy/` directory)

**Integration patterns based on topology**:

1. **Consuming Engine is Boxcar, Target Engine mounted in Scriptdash**:
   - Consuming Engine: Use RPC client only (via `*_API_BASE_URL` env var)
   - Scriptdash: Can call target engine directly (already mounted, local access)
   - Example: PartnershipsEngine (Boxcar) → LabelsEngine (mounted in Scriptdash)

2. **Both engines are Boxcar**:
   - Always use RPC client with env vars

3. **Consuming Engine mounted in Scriptdash, Target Engine mounted in Scriptdash**:
   - Direct local calls, no RPC needed

**Key insight**: If target engine is already mounted in Scriptdash with HTTP endpoints, **Scriptdash doesn't need a wrapper** - it can access those endpoints directly. Only Boxcar engines need RPC integration.

**This topology determines**:
- Whether to add dependencies (RPC-only vs local gem)
- Whether to create Scriptdash wrapper (usually not needed if target is mounted)
- Which environment variables to configure

**Example decision** (from PartnershipsEngine + LabelsEngine integration):
- LabelsEngine mounted at `/labels` in Scriptdash → Scriptdash uses existing endpoints
- PartnershipsEngine is Boxcar → Needs RPC client + `LABELS_API_BASE_URL` config
- No Scriptdash wrapper needed (would be redundant)

**Note**: This section will expand as more deployment patterns are discovered. When in doubt, ask an experienced engineer about the deployment model before proceeding.

**Choose your deployment pattern**:

If not clear from context, ask the user which pattern to use:

1. **Engine-only** - Proto and implementation both in engine
   - Use when: Independent backend API, no Scriptdash integration needed
   - Example: `assets/reference_implementation/engine/action_partnerships_fetch_all/`
   - Models: In engine
   - Routes: Engine routes (`/v2/resource`)

2. **Proto in Engine, Implementation in Scriptdash** - Contract in engine, logic in Scriptdash
   - Use when: Models deeply coupled to Scriptdash (associations, Devise auth) and can't be easily moved
   - Example: `assets/reference_implementation/intermediate/wunderbar_users_fetch_all/`
   - Models: In Scriptdash (stays due to coupling)
   - Routes: Engine routes (`/v1/resource`), implementation via initializer hookup
   - Common for: Operations endpoints, internal tools, auth-dependent models

3. **Two-Layer (Scriptdash + Engine)** - Scriptdash wraps Engine API with permissions
   - Use when: Frontend needs authorization, Engine provides business logic
   - Example: `assets/reference_implementation/scriptdash/action_partnerships_fetch_all/`
   - Models: In engine
   - Routes: Both Scriptdash (`/actions/v1/resource`) and Engine (`/v2/resource`)

**When to use each**:
- **Engine-only**: Building new backend-only service from scratch
- **Intermediate**: Models coupled to Scriptdash (associations, Devise) - can't easily move to engine
- **Two-layer**: Frontend-facing API needing permissions, Engine has independent business logic

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

**For alto-workspace integration**: `references/alto-workspace-infrastructure.md` (Proto Generation Pipeline section)

**Command**:
```bash
cd engine-{domain}
bin/protos
git checkout {domain}_api/lib/{domain}_api.rb  # CRITICAL: Restore after generation
```

**Note**: Proto generation uses configurations from alto-workspace (see `references/alto-workspace-quick-reference.md` for proto config syntax).

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

**For dependency management**: `references/alto-workspace-quick-reference.md` (Dependency Management section)

For Scriptdash wrapper with permissions:

1. **Update dependencies** (if new engine version)
   ```bash
   cd alto-workspace
   alto bump scriptdash {domain}  # Updates to latest engine version
   cd ../scriptdash
   bundle install
   bin/tapioca gem {domain}_api {domain}_engine
   ```
2. **Define Scriptdash proto** (imports Engine type)
3. **Core API wiring** (`app/services/{domain}/action_partnerships.rb`)
   - Include `Core::API`
   - Add Engine client
   - Configure local endpoint
4. **Dotted accessor** (`app/services/{domain}.rb`)
   - Expose module via class method
5. **Implement endpoint with permissions** (`app/services/{domain}/wunderbar/{resource}_endpoint.rb`)
   - Check `current_ability.authorize!`
   - Delegate to Engine via `Actions.resource.fetch_all`
6. **Add permissions** (`app/models/abilities/ability.rb`)
   - Define who can `:read` the Engine type
7. **Create controller** (same pattern as Engine)
8. **Write tests** (mock Engine API, test permissions)

### Step 9: Configure Deployment Environments

**If your Engine makes RPC calls to other Engines**, add environment variables to deployment configs:

**Files to update**:
- `.env.development` - Local development (e.g., `http://wunderbar.alto.local.alto.com:3000/<route>`)
- `.deploy/<engine-name>/sandbox.yaml` - Sandbox (DevEnv) environment
- `.deploy/<engine-name>/stg.yaml` - Staging environment
- `.deploy/<engine-name>/prod.yaml` - Production environment

**Pattern for sandbox/staging/production**:
```yaml
env:
  <DOMAIN>_API_BASE_URL: internal-api-gateway.alto-deploy-api-gateway.svc.cluster.local/<route>
```

**Example** (PartnershipsEngine calling LabelsEngine):
```yaml
env:
  LABELS_API_BASE_URL: internal-api-gateway.alto-deploy-api-gateway.svc.cluster.local/labels
```

**Where to find the route**: Check how the Engine is mounted in Scriptdash `config/routes.rb` (e.g., `mount LabelsEngine::Engine, at: '/labels'`)

### Step 10: Verify and Complete

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
- Verify alto-workspace proto config (see `references/alto-workspace-quick-reference.md`)

**Dependency errors**:
- Run `alto bump scriptdash {domain}` to update dependencies
- Check `alto-workspace/config/repositories/` for version constraints
- See `references/alto-workspace-infrastructure.md` for dependency resolution

**Sorbet type errors**:
- First check for pending migrations: `bundle exec rails db:migrate:status`
- If migrations pending: `bundle exec rails db:create db:migrate` then regenerate RBIs
- Run `bin/tapioca gem` and `bin/tapioca dsl` to regenerate RBI files
- Check `override` signatures match AbstractEndpoint
- Avoid manually creating RBI files - fix the root cause (migrations, dependencies) instead

**Tapioca hangs in Scriptdash**:
- First time setup: Install Auth0/S3 configs per `<scriptdash_root>/config/local/README.md`
- If still hanging: Run `spring stop` then retry (clears stale Rails preloader)

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

### Alto Workspace Reference

**references/** - Infrastructure and tooling documentation:

- `alto-workspace-quick-reference.md` (~1k tokens) - Quick lookups for CLI commands, config syntax, and common patterns
  - **When to use**: Fast answers during implementation (command syntax, YAML fields, type mappings)
  - **Contains**: CLI command reference, configuration schemas, SQL→Proto mappings, standard RPC methods

- `alto-workspace-infrastructure.md` (~5-6k tokens) - Complete architectural reference for alto-workspace
  - **When to use**: Understanding the workspace system, creating engines, configuring dependencies, proto generation pipeline
  - **Contains**: Repository structure, CLI implementation details, configuration system, proto generation, dependency management, integration patterns

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

## Beyond Endpoints

While endpoint creation is the primary entry point to Better Boundaries, the architecture encompasses broader concepts:

### Core::API Design Pattern

The Core::API pattern establishes public APIs within a monolith before extraction:
- Clean boundaries between domains
- Explicit API contracts via module interfaces
- Foundation for Engine extraction

**Deep dive**: See `references/better_boundaries_reference.md` for Core::API internals and configuration patterns.

### Creating New Engines

Rails Engines are the second step in the Better Boundaries journey:
- Extract domain logic from monolith
- Define proto-based contracts
- Independent versioning and testing

**Tooling**: Use `alto generate engine <name>` - see `references/alto-workspace-infrastructure.md` for complete engine creation workflow.

### Migration Strategies

Progressive migration from monolith to services:
- Start with Module (Core::API boundaries)
- Extract to Engine (proto contracts, local calls)
- Deploy as Boxcar (RPC calls, independent scaling)

**Guidance**: `references/better_boundaries_reference.md` documents migration paths and decision points.

### Future Expansion

As this skill evolves, expect coverage of:
- **v2.0**: Write operations (Create, Update, Delete patterns)
- **v3.0**: Advanced queries (FetchBy, Search, custom RPC methods)
- **Beyond**: Boxcar deployment, service orchestration, event-driven patterns

The proto-first foundation makes these additions straightforward - define in proto, regenerate, implement.

## Additional Notes

**Sorbet typing**: All generated code includes Sorbet type hints. Use `override` in implementations to ensure signatures match.

**CODEOWNERS**: Add `# @owners { team: ..., domain: ... }` annotations to endpoints and controllers.

**Semantic release**: Commit messages starting with `feat:`, `fix:`, or other semantic release prefixes trigger automated version bumps.

**Token efficiency**: Reference implementations use TODO comments for non-essential code. AI assistants can infer boilerplate from context.

**Resumability**: All patterns include "why" and "when" context to enable autonomous decision-making across sessions.
