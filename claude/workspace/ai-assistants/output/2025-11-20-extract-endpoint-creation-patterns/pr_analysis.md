# PR Analysis: FetchAll Action Partnerships Endpoint

**Purpose**: Document concrete implementation patterns from two parallel PRs implementing the same feature.

**PRs Analyzed**:
- **Scriptdash PR #48986**: FetchAll Action Partnerships endpoint (308 additions, 16 files)
- **Actions Engine PR #535**: FetchAll Action Partnerships endpoint (298 additions, 17 files)

**Feature**: Create FetchAll endpoints for Action Partnerships to populate dropdown menus in Wunderbar UI.

---

## Architecture Overview

### Service Relationship

```
┌─────────────────────────────────────┐
│   Frontend (Wunderbar UI)           │
│   Needs: Partnership dropdowns      │
└──────────────┬──────────────────────┘
               │ HTTP GET
               ▼
┌─────────────────────────────────────┐
│   Scriptdash                         │
│   Package: alto.actions.wunderbar.v1 │
│   Endpoint: ActionPartnershipsEndpoint│
│   Route: /actions/v1/action_partnerships│
│   - Adds permissions layer           │
│   - Wraps Actions Engine API         │
└──────────────┬──────────────────────┘
               │ Local call
               │ (Actions.action_partnerships.fetch_all)
               ▼
┌─────────────────────────────────────┐
│   Actions Engine                     │
│   Package: actions_api.v2            │
│   Endpoint: ActionPartnershipsEndpoint│
│   Route: /v2/action_partnerships/fetch_all│
│   - Business logic implementation    │
│   - Database access                  │
└─────────────────────────────────────┘
```

**Key Insight**: Two-layer pattern where Scriptdash provides frontend-facing API with permissions, delegating to Engine for business logic.

---

## File-by-File Comparison

### 1. Proto Definitions

**Actions Engine** (Core API - `actions_api.v2`):
```
protos/src/actions_api/types/v2/action_partnership.proto
protos/src/actions_api/v2/action_partnerships_endpoint.proto
```

**Scriptdash** (Frontend API - `alto.actions.wunderbar.v1`):
```
protos/src/alto/actions/wunderbar/v1/action_partnerships_endpoint.proto
```

**Pattern**:
- Engine defines the **type** and **core API** (`actions_api.v2`)
- Scriptdash defines **frontend-specific API** (`alto.actions.wunderbar.v1`)
- Scriptdash imports Engine's type: `import "actions_api/types/v2/action_partnership.proto"`
- Both use Service V2.0: `option (opts.service_value) = {version: "v2.0"}`

**Type Definition** (Actions Engine):
```protobuf
message ActionPartnership {
  int64 id = 1 [(opts.field) = {required: true}];
  string name = 2 [(opts.field) = {required: true}];
  string value = 3 [(opts.field) = {required: true}];
}
```

**Endpoint Definition** (Actions Engine):
```protobuf
service ActionPartnershipsEndpoint {
  option (opts.service_value) = {version: "v2.0"};

  rpc FetchAll(ActionPartnershipsEndpointFetchAllRequest)
      returns (ActionPartnershipsEndpointFetchAllResponse);
}

message ActionPartnershipsEndpointFetchAllRequest {}

message ActionPartnershipsEndpointFetchAllResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  repeated actions_api.types.v2.ActionPartnership data = 2;
}
```

**Endpoint Definition** (Scriptdash):
```protobuf
service ActionPartnershipsEndpoint {
  option (opts.service_value) = {version: "v2.0"};

  rpc FetchAll(ActionPartnershipsEndpointFetchAllRequest)
      returns (ActionPartnershipsEndpointFetchAllResponse);
}

message ActionPartnershipsEndpointFetchAllRequest {}

message ActionPartnershipsEndpointFetchAllResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  repeated actions_api.types.v2.ActionPartnership data = 2;  // Imports Engine type
}
```

---

### 2. Generated Code

Both PRs generate similar code structures in their respective `_api` gems:

**Generated Files** (Pattern applies to both):
```
<domain>_api/lib/<domain>_api/v<version>/<resource>_endpoint/
├── client.rb           # Local client for Core::API
├── controller.rb       # Generated controller mixin
├── interface.rb        # Request/Response types + abstract endpoint
├── routes.rb           # Generated routes module
└── rpc_client.rb       # Remote RPC client (Engine only)
```

**Key Difference - RPC Client**:
- **Actions Engine**: Generates `rpc_client.rb` for remote invocation
  - Uses `ENV['ACTIONS_API_BASE_URL']` for base URL
  - Makes HTTP GET to `/v2/action_partnerships/fetch_all`
- **Scriptdash**: No RPC client generated (frontend-facing, not consumed remotely)

**Client Pattern** (Actions Engine):
```ruby
module ActionsAPI::V2::ActionPartnershipsEndpoint::Client
  def action_partnerships_endpoint
    if @action_partnerships_endpoint.blank? || Core::API::RPCClient.use_rpc?(service: 'actions_api')
      RPCClient.new  # Use RPC if not configured or explicitly enabled
    else
      @action_partnerships_endpoint.new  # Use local endpoint
    end
  end

  def fetch_all
    action_partnerships_endpoint.fetch_all
  end
end
```

**Client Pattern** (Scriptdash):
```ruby
module Alto::Actions::Wunderbar::V1::ActionPartnershipsEndpoint::Client
  def action_partnerships_endpoint
    T.must(@action_partnerships_endpoint).new  # Always local
  end

  def fetch_all
    action_partnerships_endpoint.fetch_all
  end
end
```

---

### 3. Endpoint Implementation

**Actions Engine** (Business Logic):
```ruby
# app/services/actions_engine/action_partnerships/endpoint.rb
module ActionsEngine
  module ActionPartnerships
    class Endpoint < ActionsAPI::V2::ActionPartnershipsEndpoint::Interface::AbstractActionPartnershipsEndpoint
      extend T::Sig

      sig { override.returns(T::Array[ActionsAPI::Types::V2::ActionPartnership]) }
      def fetch_all
        # Access database directly
        ActionPartnership.all.map do |action_partnership|
          ActionsAPI::Types::V2::ActionPartnership.new(
            id: action_partnership.id,
            name: action_partnership.name,
            value: action_partnership.value,
          )
        end
      end
    end
  end
end
```

**Scriptdash** (Permissions + Delegation):
```ruby
# app/services/actions/wunderbar/action_partnerships_endpoint.rb
module Actions
  module Wunderbar
    class ActionPartnershipsEndpoint <
        Alto::Actions::Wunderbar::V1::ActionPartnershipsEndpoint::Interface::AbstractActionPartnershipsEndpoint
      extend T::Sig
      include Auth::CurrentAbility  # Adds permissions
      include Alto::Actions::Wunderbar::V1::ActionPartnershipsEndpoint::Interface

      sig { override.returns(T::Array[ActionsAPI::Types::V2::ActionPartnership]) }
      def fetch_all
        # Check permissions first
        current_ability.authorize! :read, ActionsAPI::Types::V2::ActionPartnership

        # Delegate to Engine API
        Actions.action_partnerships.fetch_all
      end
    end
  end
end
```

**Pattern**:
- Engine implements business logic (database access, mapping to types)
- Scriptdash adds permissions layer, delegates to Engine
- Both extend abstract interface generated from proto
- Both use Sorbet strict typing with `override` signatures

---

### 4. Core API Wiring (Scriptdash Only)

```ruby
# app/services/actions/action_partnerships.rb
module Actions
  module ActionPartnerships
    extend T::Sig
    include Core::API

    # Wire up the Core API client
    add_api ActionsAPI::V2::ActionPartnershipsEndpoint::Client

    # Configure local endpoint (Engine is mounted in Scriptdash)
    self.action_partnerships_endpoint = ActionsEngine::ActionPartnerships::Endpoint
  end
end
```

```ruby
# app/services/actions.rb
module Actions
  # Expose submodule via dotted accessor
  sig { returns(T.class_of(ActionPartnerships)) }
  def self.action_partnerships
    ActionPartnerships
  end
end
```

**Pattern**:
- Create module for resource with `Core::API` included
- Use `add_api` to wire generated client
- Set endpoint to Engine implementation (local invocation)
- Expose via parent module with dotted accessor

**Usage**:
```ruby
# From anywhere in Scriptdash
Actions.action_partnerships.fetch_all
```

---

### 5. Controllers

**Actions Engine**:
```ruby
# app/controllers/actions_engine/v2/action_partnerships_controller.rb
module ActionsEngine
  module V2
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

**Scriptdash**:
```ruby
# app/controllers/wunderbar/actions/v1/action_partnerships_controller.rb
module Wunderbar
  module Actions
    module V1
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

**Pattern**:
- Include generated controller mixin
- Provide `endpoint` accessor returning endpoint instance
- Use Sorbet for type safety with memoization
- Inherit from appropriate base controller

---

### 6. Routes

**Actions Engine**:
```ruby
# config/routes.rb
ActionsEngine::Engine.routes.draw do
  extend ActionsAPI::V2::ActionPartnershipsEndpoint::Routes
  # Other routes...
end
```

**Generated Routes** (Actions Engine):
```ruby
# actions_api/lib/actions_api/v2/action_partnerships_endpoint/routes.rb
namespace :v2 do
  scope :action_partnerships do
    get 'fetch_all', action: :index, as: :action_partnerships_index,
        controller: 'action_partnerships'
  end
end
```

**Scriptdash**:
```ruby
# config/routes.rb (inside wunderbar subdomain constraint)
extend Alto::Actions::Wunderbar::V1::ActionPartnershipsEndpoint::Routes
```

**Generated Routes** (Scriptdash):
```ruby
# app/types/alto/actions/wunderbar/v1/action_partnerships_endpoint/routes.rb
namespace :actions do
  namespace :v1 do
    resources :action_partnerships, only: [:index], controller: 'action_partnerships'
  end
end
```

**Pattern**:
- Extend generated routes module in `config/routes.rb`
- Routes module uses `namespace` and `resources` to define routes
- FetchAll maps to `:index` action
- Controller name derived from resource name

**Resulting Routes**:
- Actions Engine: `GET /v2/action_partnerships/fetch_all`
- Scriptdash: `GET /actions/v1/action_partnerships`

---

### 7. Permissions (Scriptdash Only)

```ruby
# app/models/abilities/ability.rb (multiple roles)
def ops(wunderbar_user = nil)
  can :read, ActionsAPI::Types::V2::ActionPartnership
end

def manager(wunderbar_user = nil)
  can :read, ActionsAPI::Types::V2::ActionPartnership
end

def engineer(_wunderbar_user = nil)
  can :read, ActionsAPI::Types::V2::ActionPartnership
end
```

```ruby
# app/models/abilities/wunderbar_ability.rb (role-specific)
def grant_abilities_for_role(role)
  case role
  when :engineer, :manager, :ops
    can :read, ActionsAPI::Types::V2::ActionPartnership
  end
end
```

**Pattern**:
- Add permissions for **generated type** (not model)
- Update both `Ability` and `WunderbarAbility` classes
- Specify per-role permissions (`:read`, `:create`, `:update`, `:destroy`, `:manage`)
- Use CanCanCan syntax: `can <action>, <Type>`

**Note**: Engines typically don't implement permissions; handled at Scriptdash layer.

---

### 8. TypeScript Code Generation

Both PRs generate TypeScript types and client functions:

**Actions Engine**:
```typescript
// protos/gen/typescript/lib/actions_api/types/v2/action_partnership.ts
export interface ActionPartnership {
  id: number;
  name: string;
  value: string;
}

// protos/gen/typescript/lib/actions_api/v2/action_partnerships_endpoint.ts
export const ActionPartnershipsEndpoint = <Options extends Record<string, unknown>>(
  makeRequest: (method: string, endpoint: string, params: {}, options?: Options) => Promise<any>,
) => {
  return {
    fetchAll(
      params: ActionPartnershipsEndpointFetchAllRequest,
      options?: Options,
    ): Promise<ActionPartnershipsEndpointFetchAllResponse> {
      return makeRequest('GET', '/v2/action_partnerships/fetch_all', params, options);
    },
  };
};
```

**Scriptdash**:
```typescript
// protos/gen/typescript/lib/alto/actions/wunderbar/v1/action_partnerships_endpoint.ts
export const ActionPartnershipsEndpoint = <Options extends Record<string, unknown>>(
  makeRequest: (method: string, endpoint: string, params: {}, options?: Options) => Promise<any>,
) => {
  return {
    fetchAll(
      params: ActionPartnershipsEndpointFetchAllRequest,
      options?: Options,
    ): Promise<ActionPartnershipsEndpointFetchAllResponse> {
      return makeRequest('GET', '/actions/v1/action_partnerships', params, options);
    },
  };
};
```

**Pattern**:
- Types generated from proto messages
- Client function generated with higher-order function pattern
- Uses `makeRequest` injected function for HTTP calls
- TypeScript mirrors Ruby request/response structure

---

### 9. Tests

**Actions Engine** (Request Spec):
```ruby
# spec/requests/actions_engine/v2/action_partnerships_controller_spec.rb
RSpec.describe ActionsEngine::V2::ActionPartnershipsController,
               :rpc_client_requests, type: :request do
  let(:client) { ActionsAPI::V2::ActionPartnershipsEndpoint::RPCClient.new }

  describe 'GET /v2/action_partnerships/fetch_all' do
    subject(:fetch_all) do
      client.fetch_all
    end

    it 'returns all action partnerships' do
      create(:action_partnership, name: 'Progyny', value: 'progyny', company_id: 1)
      create(:action_partnership, name: 'Carrot', value: 'carrot', company_id: 1)
      result = fetch_all

      expect(result.length).to eq(2)
      expect(result.first).to be_a(ActionsAPI::Types::V2::ActionPartnership)
    end
  end
end
```

**Scriptdash** (Controller Spec):
```ruby
# spec/requests/wunderbar/actions/v1/action_partnerships_controller_spec.rb
RSpec.describe Wunderbar::Actions::V1::ActionPartnershipsController,
               { type: :controller } do
  before(:each) do
    @wunderbar_user = FactoryBot.create(:manager_wb_user)
    login_wunderbar_user(@wunderbar_user)
  end

  describe 'GET /actions/v1/action_partnerships/fetch_all' do
    it 'returns all action partnerships successfully' do
      mock_action_partnerships = [
        ActionsAPI::Types::V2::ActionPartnership.new(
          id: 1, name: 'Progyny', value: 'progyny'
        ),
        # ... more mocks
      ]
      allow(Actions.action_partnerships).to receive(:fetch_all)
        .and_return(mock_action_partnerships)

      get :index

      expect(response).to have_http_status(200)
      body = JSON.parse(response.body)
      expect(body['data']).to be_an(Array)
      expect(body['data'].length).to eq(3)
    end
  end
end
```

**Pattern Differences**:
- **Engine**: Uses `:rpc_client_requests` helper, tests via RPC client, uses factories
- **Scriptdash**: Controller spec, mocks Engine API, tests permissions (login user)
- Engine tests full stack (database → response)
- Scriptdash tests delegation and permissions

---

### 10. Additional Files

**Actions Engine**:
```
CODEOWNERS  # Add ownership for new endpoint directory
```

**Scriptdash**:
```
sorbet/rbi/dsl/actions/action_partnerships.rbi  # Tapioca-generated type hints
```

**Pattern**:
- Update `CODEOWNERS` when adding new directories
- Run `bin/tapioca dsl` after adding Core API to generate type hints

---

## Layering Summary

### Actions Engine (Backend/API Layer)

1. **Proto Type**: `actions_api/types/v2/action_partnership.proto`
2. **Proto Endpoint**: `actions_api/v2/action_partnerships_endpoint.proto`
3. **Generated Type**: `actions_api/lib/actions_api/types/v2/action_partnership.rb`
4. **Generated API**: `actions_api/lib/actions_api/v2/action_partnerships_endpoint/`
   - Client (local/RPC switching)
   - Controller (mixin)
   - Interface (types + abstract endpoint)
   - Routes (URL mapping)
   - RPCClient (remote invocation)
5. **Endpoint Implementation**: `app/services/actions_engine/action_partnerships/endpoint.rb`
6. **Controller**: `app/controllers/actions_engine/v2/action_partnerships_controller.rb`
7. **Routes**: Mount in `config/routes.rb`
8. **Tests**: Request spec using RPC client
9. **TypeScript**: Generated frontend types

### Scriptdash (Frontend/Permissions Layer)

1. **Proto Endpoint**: `alto/actions/wunderbar/v1/action_partnerships_endpoint.proto` (reuses Engine type)
2. **Generated API**: `app/types/alto/actions/wunderbar/v1/action_partnerships_endpoint/`
   - Client (local only)
   - Controller (mixin with auth annotation)
   - Interface (types + abstract endpoint)
   - Routes (URL mapping)
3. **Endpoint Implementation**: `app/services/actions/wunderbar/action_partnerships_endpoint.rb`
4. **Core API Wiring**: `app/services/actions/action_partnerships.rb`
5. **Module Accessor**: Add to `app/services/actions.rb`
6. **Controller**: `app/controllers/wunderbar/actions/v1/action_partnerships_controller.rb`
7. **Routes**: Mount in `config/routes.rb` (Wunderbar subdomain)
8. **Permissions**: Update `Ability` and `WunderbarAbility`
9. **Sorbet RBI**: Generated type hints for Core API
10. **Tests**: Controller spec with mocked Engine API
11. **TypeScript**: Generated frontend types

---

## Key Patterns Observed

### CRITICAL Patterns

1. **Proto-First Design**: Define contract in `.proto` → generate code
2. **Service V2.0 Standard**: `option (opts.service_value) = {version: "v2.0"}`
3. **Generated Code Artifacts**: Interface, Client, Controller, Routes, RPCClient
4. **Abstract Interface Extension**: Endpoint extends generated abstract class
5. **Controller Mixin Pattern**: Include generated controller, provide endpoint accessor
6. **Route Extension**: Extend generated routes module
7. **Core API Pattern**: `include Core::API`, `add_api Client`, set endpoint
8. **Dotted Accessor**: Expose via parent module (`Actions.action_partnerships`)
9. **Sorbet Typing**: Strict typing with `override` signatures
10. **Standard Resource Method**: FetchAll → `:index` action → `GET /resources`

### PREFERRED Patterns

1. **Request Specs**: Use `:rpc_client_requests` helper for integration testing
2. **Permissions at Scriptdash Layer**: Engines don't implement permissions
3. **Type Reuse**: Scriptdash imports Engine types rather than duplicating
4. **Memoized Endpoints**: `@endpoint ||= Endpoint.new`
5. **Factory Pattern**: Use factories for test data (Engine)
6. **Mocking Pattern**: Mock Core API calls in Scriptdash tests

### OBSERVED Patterns

1. **TypeScript Generation**: Automatic from proto, parallel structure to Ruby
2. **CODEOWNERS Updates**: Add new directories to CODEOWNERS
3. **Tapioca DSL**: Run `bin/tapioca dsl` to generate Sorbet type hints
4. **Namespace Alignment**: Proto package → Ruby module hierarchy
5. **Empty Request Messages**: FetchAll with no parameters still requires message
6. **Response Structure**: `errors` (field 1), `data` (field 2), optional `metadata` (field 3)

---

## Two-Service Coordination Pattern

**When to create in both Scriptdash and Engine:**
- Engine provides **backend API** (business logic, database access)
- Scriptdash provides **frontend API** (permissions, UI-specific transformations)
- Enables permission enforcement at gateway layer
- Allows Engine to be consumed by multiple frontends

**Alternative (Single Service)**:
- If only one consumer, implement directly in Engine
- If permissions not needed, skip Scriptdash layer
- If UI-specific logic needed, add to Scriptdash layer

---

## Token Efficiency Notes

This analysis represents ~5k tokens documenting patterns from both PRs. Future sessions can load this instead of re-analyzing PR diffs (~12k tokens of diff content).

**Files Referenced**:
- Scriptdash PR #48986: https://github.com/scriptdash/scriptdash/pull/48986
- Actions Engine PR #535: https://github.com/scriptdash/engine-actions/pull/535
