# Controller & Routes Patterns

**Scope**: HTTP layer integration for FetchAll/FetchOne endpoints
**Source**: PRs #48986 (Scriptdash), #535 (Actions Engine)
**Last Updated**: 2025-11-20

---

## Overview

After implementing your endpoint business logic, you need to wire it up to HTTP. This involves:
1. Creating a controller that includes generated mixins
2. Providing an endpoint accessor
3. Extending routes with generated routes module

The generated code (from Service V2.0) does most of the work. You just need to connect the pieces.

---

## Layer 4: Controllers

### Pattern 4.1: Engine Controller Structure [CRITICAL]

**Priority**: CRITICAL

**Purpose**: Minimal controller that delegates to your endpoint implementation. The generated mixin handles all HTTP concerns.

**When to use**: Always. Every Engine endpoint needs a controller.

**Implementation**:

```ruby
# typed: strict
# frozen_string_literal: true

module ActionsEngine
  module V2
    # @owners { team: unified-workflow, domain: actions }
    class ActionPartnershipsController < ApplicationController
      include ActionsAPI::V2::ActionPartnershipsEndpoint::Controller
      extend T::Sig

      sig { returns(ActionPartnerships::Endpoint) }
      def endpoint
        @endpoint ||= T.let(
          ActionPartnerships::Endpoint.new,
          T.nilable(ActionPartnerships::Endpoint),
        )
      end
    end
  end
end
```

**Key elements**:
1. **Inherit from ApplicationController** - Gets base Rails controller behavior
2. **Include generated Controller mixin** - `include ActionsAPI::V2::ActionPartnershipsEndpoint::Controller`
3. **Provide `endpoint` accessor** - Returns instance of your endpoint class
4. **Memoize with `||=`** - Create endpoint once per request
5. **Sorbet type annotation** - `T.let` for memoized instance variable

**What the generated mixin provides**:
- `#index` action for FetchAll (GET /resource)
- `#show` action for FetchOne (GET /resource/:id)
- Parameter extraction and validation
- Error handling
- JSON serialization

**Trade-offs**:
- ✅ Minimal code (5-10 lines)
- ✅ All HTTP logic in generated code
- ✅ Type-safe endpoint accessor
- ✅ Consistent across all endpoints
- ❌ Can't customize request/response handling easily
- ❌ Must follow generated structure

**Common Error**: Wrong endpoint class path

```ruby
# ❌ Wrong: Missing namespace
def endpoint
  @endpoint ||= Endpoint.new  # NameError!
end

# ✅ Correct: Full module path
def endpoint
  @endpoint ||= ActionPartnerships::Endpoint.new
end
```

---

### Pattern 4.2: Scriptdash Controller Structure [CRITICAL]

**Priority**: CRITICAL

**Purpose**: Similar to Engine, but inherits from WunderbarController and uses full namespace for endpoint.

**When to use**: When creating frontend-facing endpoints in Scriptdash.

**Implementation**:

```ruby
# typed: strict

module Wunderbar
  module Actions
    module V1
      # @owners { team: care, domain: actions, followers: [unified-workflow] }
      class ActionPartnershipsController < WunderbarController
        include Alto::Actions::Wunderbar::V1::ActionPartnershipsEndpoint::Controller
        extend T::Sig

        sig { returns(::Actions::Wunderbar::ActionPartnershipsEndpoint) }
        def endpoint
          @endpoint ||= T.let(
            ::Actions::Wunderbar::ActionPartnershipsEndpoint.new,
            T.nilable(::Actions::Wunderbar::ActionPartnershipsEndpoint),
          )
        end
      end
    end
  end
end
```

**Key differences from Engine**:
- Inherits from **WunderbarController** (not ApplicationController)
- Endpoint class uses **global namespace** (`::Actions::Wunderbar::...`)
- Generated mixin is under `Alto::` namespace

**Why global namespace (`::`)**: Avoids conflicts with local modules. From within `Wunderbar::Actions::V1`, `Actions` would resolve to the local module, not the top-level `Actions` module.

**Trade-offs**:
- ✅ Same minimal structure as Engine
- ✅ Inherits Wunderbar-specific behavior (auth, logging)
- ❌ Must remember `::` prefix for top-level modules

**Common Error**: Forgetting `::` prefix

```ruby
# ❌ Wrong: Resolves to Wunderbar::Actions::V1::Actions (doesn't exist)
def endpoint
  @endpoint ||= Actions::Wunderbar::ActionPartnershipsEndpoint.new
end

# ✅ Correct: :: forces top-level lookup
def endpoint
  @endpoint ||= ::Actions::Wunderbar::ActionPartnershipsEndpoint.new
end
```

---

### Pattern 4.3: Controller File Location Convention [PREFERRED]

**Priority**: PREFERRED

**Purpose**: Consistent file structure makes controllers easy to find.

**When to use**: Always. Follow this convention.

**Convention**:

**Engine**:
```
app/controllers/{domain}_engine/v{version}/{resource}_controller.rb
```

Examples:
- `app/controllers/actions_engine/v2/action_partnerships_controller.rb`
- `app/controllers/actions_engine/v2/action_types_controller.rb`
- `app/controllers/actions_engine/v1/action_types_controller.rb`

**Scriptdash**:
```
app/controllers/{subdomain}/{domain}/v{version}/{resource}_controller.rb
```

Examples:
- `app/controllers/wunderbar/actions/v1/action_partnerships_controller.rb`
- `app/controllers/wunderbar/billing/v1/invoices_controller.rb`

**Naming rules**:
- Controller file name is plural: `action_partnerships_controller.rb`
- Class name matches file: `ActionPartnershipsController`
- Version in path matches proto package: `v2` directory for `actions_api.v2` package

**Trade-offs**:
- ✅ Predictable file locations
- ✅ Easy to find related files
- ✅ Auto-loading works correctly
- ❌ Deep nesting (but organized)

---

### Pattern 4.4: Endpoint Memoization Pattern [PREFERRED]

**Priority**: PREFERRED

**Purpose**: Create endpoint instance once per request, reuse for all method calls within that request.

**When to use**: Always. Use this exact pattern.

**Implementation**:

```ruby
sig { returns(ActionPartnerships::Endpoint) }
def endpoint
  @endpoint ||= T.let(
    ActionPartnerships::Endpoint.new,
    T.nilable(ActionPartnerships::Endpoint),
  )
end
```

**Why memoize**:
- Endpoint instance might cache data or state during request
- Avoid creating multiple instances unnecessarily
- Standard Ruby pattern for lazy initialization

**Sorbet pattern breakdown**:
- `@endpoint ||=` - Memoization (create once, reuse)
- `T.let(...)` - Tell Sorbet the type of the memoized value
- `T.nilable(...)` - Instance variable can be nil before first access
- Return type `returns(Endpoint)` - After memoization, never nil

**Alternative (without Sorbet)**:
```ruby
def endpoint
  @endpoint ||= ActionPartnerships::Endpoint.new
end
```

**Trade-offs**:
- ✅ Efficient (create once)
- ✅ Standard Rails pattern
- ✅ Type-safe with Sorbet
- ❌ Verbose Sorbet annotations
- ❌ Can't easily test with different endpoints (but shouldn't need to)

---

## Layer 5: Routes

### Pattern 5.1: Routes Extension Pattern [CRITICAL]

**Priority**: CRITICAL

**Purpose**: Use generated routes module instead of manually defining routes. Ensures URLs match proto definitions.

**When to use**: Always. Never manually define routes for generated endpoints.

**Implementation**:

**Engine** (`config/routes.rb`):
```ruby
# frozen_string_literal: true

ActionsEngine::Engine.routes.draw do
  extend ActionsAPI::V2::ActionsEndpoint::Routes
  extend ActionsAPI::V2::ActionTypesEndpoint::Routes
  extend ActionsAPI::V2::ActionPodsEndpoint::Routes
  extend ActionsAPI::V2::ActionPartnershipsEndpoint::Routes
  extend ActionsAPI::V1::ActionTypesEndpoint::Routes
  extend ActionsAPI::V1::AspectRolesEndpoint::Routes
  # ... more endpoints
end
```

**Scriptdash** (`config/routes.rb` - within subdomain constraint):
```ruby
constraints subdomain: 'wunderbar' do
  scope module: :wunderbar do
    extend Alto::Actions::Wunderbar::V1::ActionPartnershipsEndpoint::Routes
    # ... more endpoints
  end
end
```

**What `extend` does**:
- Includes routes defined in generated Routes module
- Each endpoint's Routes module knows how to wire its own URLs
- Maps RPC methods to Rails controller actions

**Pattern**: One `extend` line per endpoint

**Trade-offs**:
- ✅ Generated routes match proto definitions
- ✅ No manual URL configuration
- ✅ Consistent across all endpoints
- ✅ URL changes when proto changes
- ❌ Can't easily customize URLs
- ❌ Must regenerate if proto changes

**Common Error**: Forgetting to extend routes after adding new endpoint

```ruby
# After creating new endpoint and controller...

# ❌ Wrong: Routes not added
ActionsEngine::Engine.routes.draw do
  extend ActionsAPI::V2::ActionPartnershipsEndpoint::Routes
  # Missing: extend ActionsAPI::V2::NewEndpoint::Routes
end

# Result: 404 errors, endpoint not accessible

# ✅ Correct: Add extend for new endpoint
ActionsEngine::Engine.routes.draw do
  extend ActionsAPI::V2::ActionPartnershipsEndpoint::Routes
  extend ActionsAPI::V2::NewEndpoint::Routes  # ← Added
end
```

---

### Pattern 5.2: HTTP Verb Mapping [CRITICAL]

**Priority**: CRITICAL

**Purpose**: Understand how RPC methods map to RESTful HTTP verbs and Rails actions.

**When to use**: Always good to understand this mapping.

**Standard Mappings**:

| RPC Method | HTTP Verb | URL Pattern | Rails Action | Use Case |
|------------|-----------|-------------|--------------|----------|
| **FetchOne** | GET | `/:id` | `show` | Get single record |
| **FetchAll** | GET | `/` or `/fetch_all` | `index` | Get multiple records |
| **Create** | POST | `/` | `create` | Create new record |
| **Update** | PUT | `/:id` | `update` | Update existing record |
| **Delete** | DELETE | `/:id` | `destroy` | Delete record |
| **Search** | GET | `/search` | `search` | Search/filter records |
| **Custom** | GET/POST | `/method_name` | `method_name` | Custom operations |

**FetchAll variations**:
- Empty request: `GET /v2/action_partnerships` (no IDs)
- With IDs: `GET /v2/action_types?ids[]=1&ids[]=2`
- Named route: `GET /v2/action_partnerships/fetch_all` (explicit)

**FetchOne**:
- Standard: `GET /v2/action_types/:id` → `GET /v2/action_types/123`

**What the generated mixin provides**:

```ruby
# Generated controller mixin (simplified)
module ActionsAPI::V2::ActionPartnershipsEndpoint::Controller
  # FetchAll maps to #index
  def index
    data = endpoint.fetch_all
    response = ActionPartnershipsEndpointFetchAllResponse.new(data: data)
    render(json: response.serialize, status: :ok)
  end

  # FetchOne maps to #show
  def show
    id = params[:id].to_i
    data = endpoint.fetch_one(id: id)
    response = ActionPartnershipsEndpointFetchOneResponse.new(data: data)
    render(json: response.serialize, status: :ok)
  end
end
```

**Trade-offs**:
- ✅ RESTful conventions
- ✅ Standard Rails action names
- ✅ Predictable URLs
- ❌ RPC method names don't always map cleanly to REST
- ❌ Multiple "fetch" methods can be confusing

---

### Pattern 5.3: URL Structure Convention [PREFERRED]

**Priority**: PREFERRED

**Purpose**: Consistent, predictable URLs across all endpoints.

**When to use**: Understanding URL patterns helps with debugging and API documentation.

**URL Patterns**:

**Engine (Backend API)**:
```
/v{version}/{resources}/{method}
```

Examples:
- `GET /v2/action_partnerships/fetch_all`
- `GET /v2/action_partnerships` (RESTful variant)
- `GET /v2/action_types/:id`
- `GET /v2/action_types?ids[]=1&ids[]=2`
- `POST /v2/actions`
- `GET /v2/actions/search?tags[]=urgent`

**Scriptdash (Frontend API)**:
```
/{domain}/v{version}/{resources}
```

Examples:
- `GET /actions/v1/action_partnerships`
- `GET /billing/v1/invoices/:id`
- `POST /patients/v1/patients`

**Subdomain routing** (Wunderbar):
```
https://wunderbar.example.com/actions/v1/action_partnerships
```

**Version in URL**:
- Always include version (`/v1/`, `/v2/`)
- Enables API evolution without breaking clients
- Version in URL matches proto package version

**Trade-offs**:
- ✅ Predictable structure
- ✅ Versioned (non-breaking changes)
- ✅ Self-documenting (resource name in URL)
- ❌ Long URLs for nested resources
- ❌ Version proliferation over time

---

## Pattern Summary

**Layers 4-5 extracted**: 6 patterns (5 CRITICAL, 1 PREFERRED)

**Key takeaways**:
1. Controllers are minimal - just include mixin + provide endpoint
2. Routes use generated modules - one `extend` per endpoint
3. HTTP verbs map to Rails actions (GET → index/show, POST → create, etc.)
4. URL structure is consistent and versioned
5. Memoize endpoint accessor for efficiency
6. Sorbet annotations for type safety

**Common mistakes**:
- Forgetting `::` prefix in Scriptdash endpoints
- Not extending routes after adding new endpoint
- Wrong Sorbet type annotations for memoized variables
- Missing version in URL or file path

**Next**: Testing patterns (how to test these controllers)
