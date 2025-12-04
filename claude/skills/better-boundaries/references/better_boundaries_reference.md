# Better Boundaries Architecture Reference

**When to load this file**: Use this comprehensive reference when encountering complex issues not covered by the main workflow or pattern documents. This contains deep architectural context from Alto's Better Boundaries initiative and Notion documentation.

**What this provides**:
- Complete Better Boundaries migration path (Module → Engine → Boxcar)
- Detailed proto-first architecture explanation
- Standard Resource Methods reference (FetchAll, FetchOne, Create, Update, Delete, FetchBy, Search)
- Multi-layer endpoint stack visualization
- Core API pattern internals
- Rails Engine creation and deployment
- Service coordination patterns (local vs RPC)
- TypeScript code generation
- Complete workflow examples
- Troubleshooting deep-dives

**Token budget**: ~19k tokens - only load when needed for complex scenarios.

**Primary use cases**:
- Understanding the "why" behind architectural decisions
- Troubleshooting deployment or RPC configuration issues
- Understanding Core::API internals and local/RPC switching
- Creating engines from scratch
- Deploying to Boxcar
- Understanding Standard Resource Methods beyond FetchAll/FetchOne

**Don't load this for**: Basic endpoint creation - use the main SKILL.md workflow and pattern documents instead.

---


**Purpose**: Comprehensive architectural reference for creating endpoints across Scriptdash and Rails Engines. Enables AI-autonomous implementation and serves as team documentation.

**Token Budget**: 20k tokens (expanded from 4k for detailed guidance)

**Source**: Alto Notion workspace - Better Boundaries initiative documentation + PR analysis

**Last Updated**: 2025-11-20

---

## Table of Contents

1. [Architectural Overview: Better Boundaries Initiative](#1-architectural-overview-better-boundaries-initiative)
2. [Proto-First Architecture](#2-proto-first-architecture)
3. [Standard Resource Methods](#3-standard-resource-methods)
4. [Multi-Layer Endpoint Stack](#4-multi-layer-endpoint-stack)
5. [Core API Pattern](#5-core-api-pattern)
6. [Rails Engines](#6-rails-engines)
7. [Service Coordination Patterns](#7-service-coordination-patterns)
8. [Testing Patterns](#8-testing-patterns)
9. [Complete Workflow: Creating a FetchAll Endpoint](#9-complete-workflow-creating-a-fetchall-endpoint)
10. [Two-Service Coordination Pattern](#10-two-service-coordination-pattern)
11. [Permissions and Authorization](#11-permissions-and-authorization)
12. [TypeScript Code Generation](#12-typescript-code-generation)
13. [Common Patterns and Conventions](#13-common-patterns-and-conventions)
14. [Troubleshooting and Gotchas](#14-troubleshooting-and-gotchas)
15. [References](#15-references)

---

## 1. Architectural Overview: Better Boundaries Initiative

### Vision

Decompose the Rails monolith (Scriptdash) into 10-20 smaller, independently deployable applications with:
- Small environments you feel like you own
- High standards under your control
- Dependable, focused codebases
- Separate deployment capabilities

### Three-Stage Migration Path

#### Stage 1: Module (Organize with Public APIs)

**What**: Define module boundaries with public APIs using Core::API

**Key Activities**:
- Organize service classes into domain modules
- Define public APIs using dotted accessor convention: `Actions.fetch_all`
- Implement Core APIs with built-in observability, metrics, logging
- Migrate consumers from direct model access to module APIs
- Track progress toward 100% encapsulation

**Tools**:
- **Core::API**: Framework for public APIs with standardized logs/metrics
- **Packwerk**: Track boundary violations (privacy violations)
- **Core::Prometheus::TableAccess**: Monitor read/write access to tables

**Example Module Structure**:
```ruby
# app/services/actions.rb
module Actions
  include Core::API

  module Commands
    extend T::Sig

    sig { params(params: T::Hash[Symbol, T.untyped]).returns(Action) }
    def create(params:)
      Action.create!(params)
    end
  end

  add_api Commands

  sig { returns(T.class_of(ActionTypes)) }
  def self.action_types
    ActionTypes
  end
end

# Usage anywhere in Scriptdash:
Actions.create(params: { name: 'New Action' })
Actions.action_types.fetch_all
```

**Success Criteria**:
- 100% of external model access goes through public APIs
- Packwerk shows no privacy violations
- Table access metrics show all reads/writes from within domain
- Alerts configured for boundary violations

**Notion Reference**: https://www.notion.so/alto/How-to-Define-a-Module-Boundary-in-Scriptdash-37cd3a9ec8cd493bbc5fd5b30cf49dd4

---

#### Stage 2: Engine (Extract to Rails Engine)

**What**: Move models and endpoints from Scriptdash to isolated Rails Engine

**Key Activities**:
- Create Rails Engine using `alto generate engine <name>`
- Migrate models to engine (with table_name overrides)
- Define APIs using Protocol Buffers (proto-first)
- Mount engine in Scriptdash for local invocation
- Run separate test suite with isolated dependencies

**Benefits**:
- Lightning-fast build and test cycles (isolated environment)
- High standards under your control (separate linting, conventions)
- Focused code documentation context
- Minimal interference from other teams

**Example Engine Structure**:
```
engine-actions/
├── actions_engine/          # Engine gem
│   ├── app/
│   │   ├── controllers/actions_engine/v2/
│   │   ├── models/actions_engine/
│   │   └── services/actions_engine/
│   ├── config/routes.rb
│   └── spec/
├── actions_api/             # API gem (generated code)
│   └── lib/actions_api/
├── protos/
│   └── src/actions_api/
└── Gemfile
```

**Success Criteria**:
- Engine mounts in Scriptdash successfully
- All APIs defined in Protocol Buffers
- Tests run independently in < 5 minutes
- Models moved with table access still at 100% encapsulation
- Documentation generated from proto definitions

**Notion Reference**: https://www.notion.so/alto/How-to-Create-an-Engine-5e90b8f26e6042d3956d16eadcaf95c4

---

#### Stage 3: App (Deploy Separately on Boxcar)

**What**: Deploy engine as independent application with separate database and compute

**Key Activities**:
- Migrate consumers away from direct database access (all via API)
- Create dedicated database for domain
- Deploy engine on Boxcar with independent scaling
- Shadow traffic to verify consistency
- Rollout with gradual traffic migration

**Benefits**:
- Flexibility to change data architecture behind stable API
- Independently scalable data (tune DB for domain needs)
- Independently scalable compute (scale based on traffic)
- Deploy without coordinating with monolith deployments

**Boxcar Configuration Example**:
```yaml
# config/apps/apps.yml in alto-workspace
applications:
  actions:
    boxcarVersion: v1.0.0
    deps:
      - name: actions
        tag: latest
    concourse:
      status_repo: actions
      trigger_deps:
        - actions
      pagerduty_team: care_pd_key
```

**Success Criteria**:
- Engine deployed on Boxcar with 0 errors
- Shadowing shows < 0.1% mismatches
- Dedicated database migrated with 0 data loss
- Traffic cutover completed with < 1% error rate increase
- Consumers updated to use RPC instead of local calls

**Notion Reference**: https://www.notion.so/alto/How-to-Set-Up-a-Boxcar-App-400b59ae46284dc4b110579bf6740e29

---

### Key Principle: Seamless Upgrade Path

The entire architecture is designed around Core::API enabling **seamless upgrades from local method calls → networked RPC calls**:

```ruby
# Module stage (local method calls)
Actions.fetch_one(id: 1)  # Calls method directly

# Engine stage (still local, but via Core API)
Actions.fetch_one(id: 1)  # Core::API routes to mounted engine

# App stage (RPC call via HTTP)
Actions.fetch_one(id: 1)  # Core::API routes to remote endpoint

# Same calling code, zero changes!
```

This is achieved through:
1. **Core::API abstraction**: Client handles local vs RPC routing
2. **Environment configuration**: `ACTIONS_API_BASE_URL` triggers RPC mode
3. **Generated clients**: Both local and RPC clients implement same interface

---

## 2. Proto-First Architecture

### Why Protocol Buffers?

Protocol Buffers serve as the **source of truth** for API contracts, enabling:
- **Implementation-agnostic** interface descriptions
- **Type-safe** code generation for Ruby, TypeScript, Python
- **Versioned** APIs with backward compatibility
- **Documentation** generated from proto definitions
- **Consistent** structure across all endpoints

### Repository Structure

**Primary Repo**: `alto-api` (https://github.com/scriptdash/alto-api)

**Proto Organization**:
```
alto-api/
└── proto/
    ├── core/                          # Shared core types
    │   └── types/v1/
    │       ├── error_object.proto
    │       ├── pagination.proto
    │       └── message_metadata.proto
    ├── actions_api/                   # Engine API (Core)
    │   ├── types/v2/
    │   │   └── action_partnership.proto
    │   └── v2/
    │       └── action_partnerships_endpoint.proto
    └── alto/                          # Scriptdash API (Frontend)
        └── actions/
            └── wunderbar/v1/
                └── action_partnerships_endpoint.proto
```

**Naming Conventions**:
- **Types**: `<domain>_api/types/v<version>/<resource>.proto`
- **Endpoints**: `<domain>_api/v<version>/<resource>_endpoint.proto`
- **Scriptdash**: `alto/<domain>/<application>/v<version>/<resource>_endpoint.proto`

---

### Proto Definition Anatomy

#### Type Definition

```protobuf
// protos/src/actions_api/types/v2/action_partnership.proto
syntax = "proto3";

package actions_api.types.v2;

import "opts/opts.proto";

message ActionPartnership {
  int64 id = 1 [(opts.field) = {required: true}];
  string name = 2 [(opts.field) = {required: true}];
  string value = 3 [(opts.field) = {required: true}];
}
```

**Key Elements**:
- `syntax = "proto3"`: Always use proto3
- `package`: Determines Ruby module hierarchy (`.` → `::`)
- `import "opts/opts.proto"`: Alto-specific annotations
- `(opts.field) = {required: true}`: Mark required fields
- Field numbers (1, 2, 3): Never change, used for serialization

---

#### Service Definition (Service V2.0)

```protobuf
// protos/src/actions_api/v2/action_partnerships_endpoint.proto
syntax = "proto3";

package actions_api.v2;

import "actions_api/types/v2/action_partnership.proto";
import "core/types/v1/error_object.proto";
import "google/api/annotations.proto";
import "opts/opts.proto";

message ActionPartnershipsEndpointFetchAllRequest {
  // Empty for FetchAll with no filters
}

message ActionPartnershipsEndpointFetchAllResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  repeated actions_api.types.v2.ActionPartnership data = 2;
}

service ActionPartnershipsEndpoint {
  // Service V2.0 enables advanced code generation
  option (opts.service_value) = {version: "v2.0"};

  rpc FetchAll(ActionPartnershipsEndpointFetchAllRequest)
      returns (ActionPartnershipsEndpointFetchAllResponse);
}
```

**Service V2.0 Features**:
- Generates Rails controllers automatically
- Generates routes configuration
- Generates both local and RPC clients
- Enforces standardized patterns
- Provides built-in validation

**Message Naming Convention**:
- Request: `<Service><Method>Request`
- Response: `<Service><Method>Response`
- Params (for Create/Update): `<Service><Method>Params`

**Response Structure** (always):
- Field 1: `repeated core.types.v1.ErrorObject errors` (optional)
- Field 2: `<Type> data` or `repeated <Type> data` (optional)
- Field 3: `<ResponseMetadata> metadata` (optional, for pagination/etc)

---

### Code Generation Workflow

#### 1. Write Proto Definitions

Create `.proto` files in `alto-api/proto/src/<domain>_api/`

#### 2. Generate Code

**In Engine**:
```bash
cd protos/src
make brew-install-buf  # First time only
make install-alto-api  # First time only
cd ../..
bin/protos  # Generates all code
```

**What Gets Generated**:

**Ruby** (`actions_api/lib/actions_api/v2/action_partnerships_endpoint/`):
```
├── client.rb           # Local client for Core::API
├── controller.rb       # Rails controller mixin
├── interface.rb        # Request/Response types + abstract endpoint
├── routes.rb           # Rails routes module
└── rpc_client.rb       # Remote RPC client (Engine only)
```

**TypeScript** (`protos/gen/typescript/lib/actions_api/v2/`):
```
├── action_partnerships_endpoint.ts  # Client function
└── action_partnership.ts            # Type definition
```

#### 3. Handle Generated Code

**CRITICAL**: The code generator deletes `<domain>_api/lib/<domain>_api.rb`, so:

```bash
bin/protos
git checkout <domain>_api/lib/<domain>_api.rb  # Restore after generation
```

**Commit Message**: Prefix with `feat:` to trigger semantic release:
```bash
git commit -m "feat: add action partnerships endpoint"
```

This triggers automated version bump and gem publication to Artifactory.

**Notion Reference**: https://www.notion.so/alto/How-to-Generate-an-Engine-API-223b48c9344d48abbf86b47cd2e9cd62

---

### Generated Code Deep Dive

#### Interface Module

```ruby
# actions_api/lib/actions_api/v2/action_partnerships_endpoint/interface.rb
# GENERATED CODE - DO NOT EDIT

module ActionsAPI::V2::ActionPartnershipsEndpoint::Interface
  # Request type (empty for FetchAll with no params)
  class ActionPartnershipsEndpointFetchAllRequest < T::Struct
  end

  # Response type
  class ActionPartnershipsEndpointFetchAllResponse < T::Struct
    prop :errors, T.nilable(T::Array[Core::Types::V1::ErrorObject])
    prop :data, T.nilable(T::Array[ActionsAPI::Types::V2::ActionPartnership])
  end

  # Abstract endpoint - you must implement this
  class AbstractActionPartnershipsEndpoint
    extend T::Sig
    extend T::Helpers
    abstract!

    sig { abstract.returns(T::Array[ActionsAPI::Types::V2::ActionPartnership]) }
    def fetch_all
    end
  end
end
```

#### Client Module

```ruby
# actions_api/lib/actions_api/v2/action_partnerships_endpoint/client.rb
# GENERATED CODE - DO NOT EDIT

module ActionsAPI::V2::ActionPartnershipsEndpoint::Client
  extend T::Sig
  include ActionsAPI::V2::ActionPartnershipsEndpoint::Interface

  sig { returns(AbstractActionPartnershipsEndpoint) }
  def action_partnerships_endpoint
    if @action_partnerships_endpoint.blank? || Core::API::RPCClient.use_rpc?(service: 'actions_api')
      RPCClient.new  # Use RPC if not configured or RPC enabled
    else
      @action_partnerships_endpoint.new  # Use local endpoint
    end
  end

  sig { params(action_partnerships_endpoint: T.class_of(AbstractActionPartnershipsEndpoint)).returns(...) }
  attr_writer :action_partnerships_endpoint

  sig { returns(T::Array[ActionsAPI::Types::V2::ActionPartnership]) }
  def fetch_all
    action_partnerships_endpoint.fetch_all
  end
end
```

**Key Features**:
- Automatically switches between local and RPC based on configuration
- Uses `Core::API::RPCClient.use_rpc?(service: 'actions_api')` to determine mode
- Provides clean calling interface: `client.fetch_all` instead of `client.endpoint.fetch_all`

#### Controller Module

```ruby
# actions_api/lib/actions_api/v2/action_partnerships_endpoint/controller.rb
# GENERATED CODE - DO NOT EDIT

module ActionsAPI::V2::ActionPartnershipsEndpoint::Controller
  include ActionsAPI::V2::ActionPartnershipsEndpoint::Interface

  # GET /v2/action_partnerships/fetch_all
  def index
    data = endpoint.fetch_all
    response = ActionPartnershipsEndpointFetchAllResponse.new(data: data)
    render(json: response.serialize, status: :ok)
  end
end
```

**Usage in Controller**:
```ruby
class ActionPartnershipsController < ApplicationController
  include ActionsAPI::V2::ActionPartnershipsEndpoint::Controller

  def endpoint
    @endpoint ||= ActionPartnerships::Endpoint.new
  end
end
```

#### Routes Module

```ruby
# actions_api/lib/actions_api/v2/action_partnerships_endpoint/routes.rb
# GENERATED CODE - DO NOT EDIT

module ActionsAPI::V2::ActionPartnershipsEndpoint::Routes
  def self.extended(router)
    router.instance_exec do
      namespace :v2 do
        scope :action_partnerships do
          get 'fetch_all', action: :index, as: :action_partnerships_index,
              controller: 'action_partnerships'
        end
      end
    end
  end
end
```

**Usage in Routes**:
```ruby
# config/routes.rb
ActionsEngine::Engine.routes.draw do
  extend ActionsAPI::V2::ActionPartnershipsEndpoint::Routes
end
```

---

## 3. Standard Resource Methods

### Resource-Oriented Design Principles

Alto follows Google Cloud API Design principles for resource-oriented APIs:
- Resources are **nouns** (clinics, patients, prescriptions)
- Methods are **standard verbs** (Create, Read, Update, Delete, List, Search)
- URLs follow predictable patterns
- Behavior is consistent across all resources

### Standard Methods Reference

| Method | Purpose | HTTP | URL Pattern | Request Fields | Response Data |
|--------|---------|------|-------------|----------------|---------------|
| **FetchOne** | Get single resource | GET | `/:id` | `id: int64` (required) | Single resource |
| **FetchAll** | Get multiple resources | GET | `/?ids[]=` | `ids: repeated int64` | Array of resources |
| **Create** | Create new resource | POST | `/` | `params: <CreateParams>` | Single resource |
| **Update** | Update existing resource | PUT | `/:id` | `id: int64`, `params: <UpdateParams>` | Single resource |
| **Delete** | Delete resource | DELETE | `/:id` | `id: int64` | Deleted resource |
| **FetchBy** | Query/filter resources | GET | `/fetch_by_<field>` | Custom filter fields | Array (or single if singular) |
| **Search** | Fuzzy search | GET | `/search_by_<field>` | Search terms | Array of resources |

---

### FetchOne - Read Single Resource

**Proto Definition**:
```protobuf
message ClinicsEndpointFetchOneRequest {
  int64 id = 1 [(opts.field) = {required: true}];
}

message ClinicsEndpointFetchOneResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  providers_api.types.v1.Clinic data = 2;
}

service ClinicsEndpoint {
  option (opts.service_value) = {version: "v2.0"};

  rpc FetchOne(ClinicsEndpointFetchOneRequest)
      returns (ClinicsEndpointFetchOneResponse);
}
```

**Implementation**:
```ruby
sig { override.params(id: Integer).returns(ProvidersAPI::Types::V1::Clinic) }
def fetch_one(id:)
  current_ability.authorize! :read, Clinic
  clinic = Clinic.find(id)
  to_struct(clinic)
end
```

**Generated Route**: `GET /v1/clinics/:id`

**Usage**:
```ruby
clinic = Providers.clinics.fetch_one(id: 1)
```

---

### FetchAll - Read Multiple Resources

**Proto Definition**:
```protobuf
message ClinicsEndpointFetchAllRequest {
  repeated int64 ids = 1 [(opts.field) = {required: true}];
}

message ClinicsEndpointFetchAllResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  repeated providers_api.types.v1.Clinic data = 2;
}

service ClinicsEndpoint {
  option (opts.service_value) = {version: "v2.0"};

  rpc FetchAll(ClinicsEndpointFetchAllRequest)
      returns (ClinicsEndpointFetchAllResponse);
}
```

**Implementation**:
```ruby
sig do
  override
    .params(ids: T::Array[Integer])
    .returns(T::Array[ProvidersAPI::Types::V1::Clinic])
end
def fetch_all(ids:)
  current_ability.authorize! :read, Clinic
  Clinic.where(id: ids).map { |c| to_struct(c) }
end
```

**Generated Route**: `GET /v1/clinics?ids[]=1&ids[]=2&ids[]=3`

**Usage**:
```ruby
clinics = Providers.clinics.fetch_all(ids: [1, 2, 3])
```

**Note**: If fetching all records (no filter), make `ids` optional and handle `nil`:
```ruby
def fetch_all(ids: nil)
  relation = ids.present? ? Clinic.where(id: ids) : Clinic.all
  relation.map { |c| to_struct(c) }
end
```

---

### Create - Create New Resource

**Proto Definition**:
```protobuf
message ClinicsEndpointCreateParams {
  string name = 1 [(opts.field) = {required: true}];
  string fax = 2;
  string phone = 3;
}

message ClinicsEndpointCreateRequest {
  ClinicsEndpointCreateParams params = 1 [(opts.field) = {required: true}];
}

message ClinicsEndpointCreateResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  providers_api.types.v1.Clinic data = 2;
}

service ClinicsEndpoint {
  option (opts.service_value) = {version: "v2.0"};

  rpc Create(ClinicsEndpointCreateRequest)
      returns (ClinicsEndpointCreateResponse);
}
```

**Implementation**:
```ruby
sig do
  override
    .params(params: I::ClinicsEndpointCreateParams)
    .returns(ProvidersAPI::Types::V1::Clinic)
end
def create(params:)
  current_ability.authorize! :create, Clinic
  clinic = Clinic.create!(params.serialize)
  to_struct(clinic)
end
```

**Generated Route**: `POST /v1/clinics`

**Usage**:
```ruby
clinic = Providers.clinics.create(
  params: { name: 'UCSF Medical Center', fax: '+14155551234' }
)
```

---

### Update - Update Existing Resource

**Proto Definition**:
```protobuf
message ClinicsEndpointUpdateParams {
  string name = 1;
  string fax = 2;
  string phone = 3;
}

message ClinicsEndpointUpdateRequest {
  int64 id = 1 [(opts.field) = {required: true}];
  ClinicsEndpointUpdateParams params = 2 [(opts.field) = {required: true}];
}

message ClinicsEndpointUpdateResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  providers_api.types.v1.Clinic data = 2;
}

service ClinicsEndpoint {
  option (opts.service_value) = {version: "v2.0"};

  rpc Update(ClinicsEndpointUpdateRequest)
      returns (ClinicsEndpointUpdateResponse);
}
```

**Implementation**:
```ruby
sig do
  override
    .params(id: Integer, params: I::ClinicsEndpointUpdateParams)
    .returns(ProvidersAPI::Types::V1::Clinic)
end
def update(id:, params:)
  current_ability.authorize! :update, Clinic
  clinic = Clinic.find(id)
  clinic.update!(params.serialize.symbolize_keys)
  to_struct(clinic)
end
```

**Generated Route**: `PUT /v1/clinics/:id`

**Usage**:
```ruby
clinic = Providers.clinics.update(
  id: 1,
  params: { name: 'UCSF Medical Center - Updated' }
)
```

---

### Delete - Delete Resource

**Proto Definition**:
```protobuf
message ClinicsEndpointDeleteRequest {
  int64 id = 1 [(opts.field) = {required: true}];
}

message ClinicsEndpointDeleteResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  providers_api.types.v1.Clinic data = 2;
}

service ClinicsEndpoint {
  option (opts.service_value) = {version: "v2.0"};

  rpc Delete(ClinicsEndpointDeleteRequest)
      returns (ClinicsEndpointDeleteResponse);
}
```

**Implementation**:
```ruby
sig { override.params(id: Integer).returns(ProvidersAPI::Types::V1::Clinic) }
def delete(id:)
  current_ability.authorize! :destroy, Clinic
  clinic = Clinic.find(id)
  clinic.delete  # Soft delete
  to_struct(clinic.reload)
end
```

**Generated Route**: `DELETE /v1/clinics/:id`

**Usage**:
```ruby
deleted_clinic = Providers.clinics.delete(id: 1)
```

---

### FetchBy - Query Resources

**Proto Definition**:
```protobuf
message ClinicsEndpointFetchByFaxRequest {
  string fax = 1 [(opts.field) = {required: true}];
  core.types.v1.PaginationRequestParams pagination = 2
      [(opts.field) = {embed_http_query: true}];
}

message ClinicsEndpointFetchByFaxResponseMetadata {
  core.types.v1.PaginationResponseMetadata pagination = 1;
}

message ClinicsEndpointFetchByFaxResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  repeated providers_api.types.v1.Clinic data = 2;
  ClinicsEndpointFetchByFaxResponseMetadata metadata = 3;
}

service ClinicsEndpoint {
  option (opts.service_value) = {version: "v2.0"};

  rpc FetchByFax(ClinicsEndpointFetchByFaxRequest)
      returns (ClinicsEndpointFetchByFaxResponse);
}
```

**Implementation**:
```ruby
sig do
  override
    .params(
      fax: String,
      pagination: T.nilable(Core::Types::V1::PaginationRequestParams)
    )
    .returns(ClinicsEndpointFetchByFaxResponse)
end
def fetch_by_fax(fax:, pagination: nil)
  current_ability.authorize! :read, Clinic

  response = Pagination::LimitAndOffset.new(
    pagination: pagination,
    relation: Clinic.where(fax: fax),
    default_page_size: 10,
  ).call

  ClinicsEndpointFetchByFaxResponse.new(
    data: response.relation.map { |c| to_struct(c) },
    metadata: ClinicsEndpointFetchByFaxResponseMetadata.new(
      pagination: response.pagination_response_metadata
    )
  )
end
```

**Generated Route**: `GET /v1/clinics/fetch_by_fax?fax=...&page=...&per_page=...`

**Usage**:
```ruby
response = Providers.clinics.fetch_by_fax(
  fax: '+14155551234',
  pagination: { page: 1, per_page: 20 }
)
clinics = response.data
total_pages = response.metadata.pagination.total_pages
```

**Naming Convention**: `FetchBy<Field>` or `FetchBy<Fields>` for clarity

---

### Search - Fuzzy Search

**Proto Definition**:
```protobuf
message ClinicsEndpointSearchByNameRequest {
  string name = 1 [(opts.field) = {required: true}];
  core.types.v1.PaginationRequestParams pagination = 2
      [(opts.field) = {embed_http_query: true}];
}

message ClinicsEndpointSearchByNameResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  repeated providers_api.types.v1.Clinic data = 2;
  ClinicsEndpointSearchByNameResponseMetadata metadata = 3;
}

service ClinicsEndpoint {
  option (opts.service_value) = {version: "v2.0"};

  rpc SearchByName(ClinicsEndpointSearchByNameRequest)
      returns (ClinicsEndpointSearchByNameResponse);
}
```

**Implementation**:
```ruby
sig do
  override
    .params(
      name: String,
      pagination: T.nilable(Core::Types::V1::PaginationRequestParams)
    )
    .returns(ClinicsEndpointSearchByNameResponse)
end
def search_by_name(name:, pagination: nil)
  current_ability.authorize! :read, Clinic

  response = Pagination::LimitAndOffset.new(
    pagination: pagination,
    default_page_size: 10,
  ).call

  clinics = Clinics.find_by_fuzzy_name(
    name,
    { limit: response.limit, offset: response.offset }
  )

  ClinicsEndpointSearchByNameResponse.new(
    data: clinics.map { |c| to_struct(c) },
    metadata: ClinicsEndpointSearchByNameResponseMetadata.new(
      pagination: response.pagination_response_metadata
    )
  )
end
```

**Generated Route**: `GET /v1/clinics/search_by_name?name=...&page=...`

**Usage**:
```ruby
response = Providers.clinics.search_by_name(
  name: 'UCSF',
  pagination: { page: 1, per_page: 20 }
)
clinics = response.data
```

**Fuzzy Search Implementation**: Use PostgreSQL trigram similarity (`pg_trgm` extension):
```sql
CREATE INDEX index_clinics_on_name_trigram ON clinics
  USING gin (name gin_trgm_ops);

SELECT * FROM clinics
WHERE name % 'search term'
ORDER BY similarity(name, 'search term') DESC;
```

**Notion Reference**: https://www.notion.so/alto/Standard-Resource-Methods-1717220d19d047f2bb827df0fdaca027

---

## 4. Multi-Layer Endpoint Stack

### Complete Stack Visualization

```
┌─────────────────────────────────────────────────┐
│ 1. Protocol Buffer Definition (.proto)         │  ← SOURCE OF TRUTH
│    - Service definition                         │
│    - Request/Response messages                  │
│    - Type definitions                           │
└──────────────────┬──────────────────────────────┘
                   │ bin/protos
                   ▼
┌─────────────────────────────────────────────────┐
│ 2. Generated Interface Module                   │  ← REQUEST/RESPONSE TYPES
│    - Request/Response T::Struct types           │
│    - AbstractEndpoint (to be implemented)       │
└──────────────────┬──────────────────────────────┘
                   │
                   ├────────────────────┬──────────────────────┐
                   ▼                    ▼                      ▼
┌──────────────────────────┐ ┌─────────────────┐  ┌──────────────────────┐
│ 3. Generated Client      │ │ 4. Generated    │  │ 5. Generated RPC     │
│    - Local invocation    │ │    Controller   │  │    Client            │
│    - Core::API           │ │    - Mixin      │  │    - Remote HTTP     │
│    - Auto-switch RPC     │ │    - #index etc │  │    - ENV-based URL   │
└──────────────────────────┘ └─────────────────┘  └──────────────────────┘
                   │                    │
                   ▼                    ▼
┌─────────────────────────────────────────────────┐
│ 6. Endpoint Implementation (YOU WRITE)          │  ← BUSINESS LOGIC
│    - Extends AbstractEndpoint                   │
│    - Implements abstract methods                │
│    - Database access, business rules            │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│ 7. Controller (YOU WRITE)                       │  ← HTTP LAYER
│    - Includes generated controller mixin        │
│    - Provides #endpoint accessor                │
│    - Inherits from ApplicationController        │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│ 8. Routes (YOU WIRE)                            │  ← URL MAPPING
│    - Extends generated routes module            │
│    - Mounts in config/routes.rb                 │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│ 9. Tests (YOU WRITE)                            │  ← VERIFICATION
│    - Request specs                              │
│    - Uses :rpc_client_requests helper           │
│    - Tests full stack                           │
└─────────────────────────────────────────────────┘
```

### Layer Details with File Locations

#### Layer 1: Protocol Buffer Definition

**Location**: `protos/src/<domain>_api/v<version>/<resource>_endpoint.proto`

**Example**: `protos/src/actions_api/v2/action_partnerships_endpoint.proto`

**Purpose**: Define the contract

**Contents**: See Section 2 for full examples

---

#### Layer 2: Generated Interface Module

**Location**: `<domain>_api/lib/<domain>_api/v<version>/<resource>_endpoint/interface.rb`

**Example**: `actions_api/lib/actions_api/v2/action_partnerships_endpoint/interface.rb`

**Generated Content**:
```ruby
# GENERATED CODE - DO NOT EDIT

module ActionsAPI::V2::ActionPartnershipsEndpoint::Interface
  # Request type
  class ActionPartnershipsEndpointFetchAllRequest < T::Struct
  end

  # Response type
  class ActionPartnershipsEndpointFetchAllResponse < T::Struct
    prop :errors, T.nilable(T::Array[Core::Types::V1::ErrorObject])
    prop :data, T.nilable(T::Array[ActionsAPI::Types::V2::ActionPartnership])
  end

  # Abstract interface - YOU IMPLEMENT THIS
  class AbstractActionPartnershipsEndpoint
    extend T::Sig
    extend T::Helpers
    abstract!

    sig { abstract.returns(T::Array[ActionsAPI::Types::V2::ActionPartnership]) }
    def fetch_all
    end
  end
end
```

---

#### Layer 3: Generated Client Module

**Location**: `<domain>_api/lib/<domain>_api/v<version>/<resource>_endpoint/client.rb`

**Purpose**: Provide clean API for Core::API, handle local/RPC switching

**Generated Content**:
```ruby
module ActionsAPI::V2::ActionPartnershipsEndpoint::Client
  extend T::Sig
  include ActionsAPI::V2::ActionPartnershipsEndpoint::Interface

  # Switches between local and RPC automatically
  sig { returns(AbstractActionPartnershipsEndpoint) }
  def action_partnerships_endpoint
    if @action_partnerships_endpoint.blank? ||
       Core::API::RPCClient.use_rpc?(service: 'actions_api')
      RPCClient.new  # Use RPC
    else
      @action_partnerships_endpoint.new  # Use local
    end
  end

  sig do
    params(action_partnerships_endpoint: T.class_of(AbstractActionPartnershipsEndpoint))
      .returns(T.nilable(T.class_of(AbstractActionPartnershipsEndpoint)))
  end
  attr_writer :action_partnerships_endpoint

  # Clean calling interface
  sig { returns(T::Array[ActionsAPI::Types::V2::ActionPartnership]) }
  def fetch_all
    action_partnerships_endpoint.fetch_all
  end
end
```

---

#### Layer 4: Generated Controller Module

**Location**: `<domain>_api/lib/<domain>_api/v<version>/<resource>_endpoint/controller.rb`

**Purpose**: Provide Rails controller actions

**Generated Content**:
```ruby
module ActionsAPI::V2::ActionPartnershipsEndpoint::Controller
  include ActionsAPI::V2::ActionPartnershipsEndpoint::Interface

  # Maps FetchAll to #index
  def index
    data = endpoint.fetch_all
    response = ActionPartnershipsEndpointFetchAllResponse.new(data: data)
    render(json: response.serialize, status: :ok)
  end
end
```

---

#### Layer 5: Generated RPC Client

**Location**: `<domain>_api/lib/<domain>_api/v<version>/<resource>_endpoint/rpc_client.rb`

**Purpose**: Make HTTP requests to remote endpoint

**Generated Content**:
```ruby
class ActionsAPI::V2::ActionPartnershipsEndpoint::RPCClient <
      ActionsAPI::V2::ActionPartnershipsEndpoint::Interface::AbstractActionPartnershipsEndpoint
  extend T::Sig
  include ActionsAPI::V2::ActionPartnershipsEndpoint::Interface

  sig { returns(String) }
  def base_url
    @base_url ||= ENV['ACTIONS_API_BASE_URL'] || 'http://localhost:3000'
  end

  sig { params(base_url: T.nilable(String)).returns(T.nilable(String)) }
  attr_writer :base_url

  sig { override.returns(T::Array[ActionsAPI::Types::V2::ActionPartnership]) }
  def fetch_all
    client = Core::API::RPCClient.new(base_url: base_url, shadow: false)
    headers = {}
    body = client.get(
      path: "/v2/action_partnerships/fetch_all",
      headers: headers
    ).body

    response = Core::Sorbet.unmarshal(
      ActionPartnershipsEndpointFetchAllResponse,
      body
    )
    T.must(response.data)
  end
end
```

---

#### Layer 6: Endpoint Implementation (YOU WRITE)

**Location**: `app/services/<domain>_engine/<resource>/endpoint.rb`

**Example**: `app/services/actions_engine/action_partnerships/endpoint.rb`

**Pattern**:
```ruby
# typed: strict

module ActionsEngine
  module ActionPartnerships
    # @owners { team: unified-workflow, domain: actions }
    class Endpoint < ActionsAPI::V2::ActionPartnershipsEndpoint::Interface::AbstractActionPartnershipsEndpoint
      extend T::Sig

      sig do
        override.returns(T::Array[ActionsAPI::Types::V2::ActionPartnership])
      end
      def fetch_all
        # Business logic goes here
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

**Key Points**:
- Extend `AbstractActionPartnershipsEndpoint`
- Use `override` on all method signatures
- Return typed structs, not ActiveRecord models
- Keep business logic here, not in controller

---

#### Layer 7: Controller (YOU WRITE)

**Location**: `app/controllers/<domain>_engine/v<version>/<resource>_controller.rb`

**Example**: `app/controllers/actions_engine/v2/action_partnerships_controller.rb`

**Pattern**:
```ruby
# typed: strict

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

**Key Points**:
- Include generated controller mixin
- Provide `#endpoint` accessor (memoized)
- Use Sorbet for type safety
- Inherit from appropriate base controller

---

#### Layer 8: Routes (YOU WIRE)

**Location**: `config/routes.rb`

**Pattern**:
```ruby
ActionsEngine::Engine.routes.draw do
  extend ActionsAPI::V2::ActionPartnershipsEndpoint::Routes
  # Other routes...
end
```

**What This Generates**:
- `GET /v2/action_partnerships/fetch_all` → `ActionsEngine::V2::ActionPartnershipsController#index`

---

#### Layer 9: Tests (YOU WRITE)

**Location**: `spec/requests/<domain>_engine/v<version>/<resource>_controller_spec.rb`

**Example**: `spec/requests/actions_engine/v2/action_partnerships_controller_spec.rb`

**Pattern**:
```ruby
require 'rails_helper'

RSpec.describe ActionsEngine::V2::ActionPartnershipsController,
               :rpc_client_requests, type: :request do
  let(:client) { ActionsAPI::V2::ActionPartnershipsEndpoint::RPCClient.new }

  describe 'GET /v2/action_partnerships/fetch_all' do
    subject(:fetch_all) { client.fetch_all }

    it 'returns all action partnerships' do
      create(:action_partnership, name: 'Progyny', value: 'progyny')
      create(:action_partnership, name: 'Carrot', value: 'carrot')

      result = fetch_all

      expect(result.length).to eq(2)
      expect(result.first).to be_a(ActionsAPI::Types::V2::ActionPartnership)
      expect(result.first.name).to eq('Progyny')
    end
  end
end
```

**Key Points**:
- Use `:rpc_client_requests` helper
- Test via RPC client (full stack test)
- Use factories for test data
- Verify response types and structure

---

## 5. Core API Pattern

### Purpose

Core::API provides a **seamless upgrade path** from local method calls to networked RPC calls without changing consumer code.

### Configuration Patterns

#### Pattern 1: Local Endpoint (Mounted in Same App)

```ruby
# app/services/actions/action_partnerships.rb
module Actions
  module ActionPartnerships
    extend T::Sig
    include Core::API

    # Wire up generated client
    add_api ActionsAPI::V2::ActionPartnershipsEndpoint::Client

    # Configure local endpoint
    self.action_partnerships_endpoint = ActionsEngine::ActionPartnerships::Endpoint
  end
end

# app/services/actions.rb
module Actions
  sig { returns(T.class_of(ActionPartnerships)) }
  def self.action_partnerships
    ActionPartnerships
  end
end

# .deploy/scriptdash/values.yaml (disable RPC)
env:
  - name: ALTO_DISABLE_RPC_ACTIONS_API
    value: "true"

# Usage (anywhere in Scriptdash):
Actions.action_partnerships.fetch_all
```

#### Pattern 2: Remote Endpoint (Different App)

```ruby
# app/services/actions/action_partnerships.rb
module Actions
  module ActionPartnerships
    extend T::Sig
    include Core::API

    # Wire up generated client
    add_api ActionsAPI::V2::ActionPartnershipsEndpoint::Client

    # No endpoint configuration - will use RPC
  end
end

# .deploy/scriptdash/values.yaml (enable RPC)
env:
  - name: ACTIONS_API_BASE_URL
    value: "https://actions.prod.alto.com"

# Usage (same code!):
Actions.action_partnerships.fetch_all  # Now makes HTTP call
```

#### Pattern 3: Conditional (Environment-Based)

```ruby
# config/initializers/actions.rb
Rails.application.reloader.to_prepare do
  if ActiveRecord::Base.configurations.find_db_config(:actions).present? &&
     !Core::API::RPCClient.use_rpc?(service: 'actions_api')
    # Local configuration
    Actions::ActionPartnerships.action_partnerships_endpoint =
      ActionsEngine::ActionPartnerships::Endpoint
  end
  # Otherwise uses RPC via ACTIONS_API_BASE_URL
end
```

### How RPC Detection Works

```ruby
# Core::API::RPCClient.use_rpc? logic:
def use_rpc?(service:)
  # Check if explicitly disabled
  return false if ENV["ALTO_DISABLE_RPC_#{service.upcase}"] == "true"

  # Check if base URL configured
  return true if ENV["#{service.upcase}_BASE_URL"].present?

  # Check if endpoint not configured
  return true if endpoint_not_configured?

  false
end
```

### Features Provided by Core::API

1. **Standardized Logging**:
```ruby
# Automatic logs for all API calls:
{
  "context": "core_api",
  "domain": "actions",
  "api_endpoint": "action_partnerships",
  "api_method": "fetch_all",
  "duration_ms": 45.2,
  "success": true
}
```

2. **Metrics**:
- `ruby_core_api_calls_total{domain, endpoint, method, status}`
- `ruby_core_api_duration_seconds{domain, endpoint, method}`

3. **Tracing**:
- Automatic trace spans for all API calls
- Integrates with Datadog APM

4. **Boundary Enforcement**:
```ruby
# In model:
class Action < ApplicationRecord
  include Core::API::WriteProtection
  write_protected domain: :actions
end

# Raises error if written from outside :actions domain
Action.create!(name: 'test')  # Error if called from :patients domain
```

**Notion Reference**: https://www.notion.so/alto/Core-APIs-5ce03b7443f94c57ba314561122fd1c6

---

## 6. Rails Engines

### What is a Rails Engine?

A Rails Engine is an **isolated Rails application** that can be:
- Developed independently with its own dependencies
- Tested in isolation with fast test cycles
- Mounted in another Rails app (Scriptdash)
- Deployed separately on Boxcar

Think of it as a "mini Rails app within a Rails app".

### Engine Structure

```
engine-actions/
├── actions_engine/              # Engine gem
│   ├── app/
│   │   ├── controllers/
│   │   │   └── actions_engine/
│   │   │       ├── application_controller.rb
│   │   │       └── v2/
│   │   │           └── action_partnerships_controller.rb
│   │   ├── models/
│   │   │   └── actions_engine/
│   │   │       ├── application_record.rb
│   │   │       └── action_partnership.rb
│   │   └── services/
│   │       └── actions_engine/
│   │           └── action_partnerships/
│   │               └── endpoint.rb
│   ├── config/
│   │   ├── routes.rb
│   │   └── database.yml
│   ├── lib/
│   │   ├── actions_engine.rb
│   │   ├── actions_engine/
│   │   │   ├── engine.rb
│   │   │   └── version.rb
│   │   └── tasks/
│   ├── spec/
│   │   ├── factories/
│   │   ├── requests/
│   │   └── rails_helper.rb
│   ├── actions_engine.gemspec
│   └── Gemfile
├── actions_api/                 # API gem (generated code)
│   ├── lib/
│   │   ├── actions_api.rb
│   │   ├── actions_api/
│   │   │   ├── types/v2/
│   │   │   └── v2/
│   │   │       └── action_partnerships_endpoint/
│   │   │           ├── client.rb
│   │   │           ├── controller.rb
│   │   │           ├── interface.rb
│   │   │           ├── routes.rb
│   │   │           └── rpc_client.rb
│   ├── actions_api.gemspec
│   └── Gemfile
├── protos/
│   ├── src/
│   │   └── actions_api/
│   │       ├── types/v2/
│   │       │   └── action_partnership.proto
│   │       └── v2/
│   │           └── action_partnerships_endpoint.proto
│   └── Makefile
├── .github/
│   └── workflows/
│       ├── build_and_test_ruby_engine.yml
│       └── publish_proto_package_typescript.yml
├── Gemfile
├── README.md
└── CODEOWNERS
```

### Creating an Engine

#### 1. Configure in alto-workspace

```yaml
# alto-workspace/config/repositories/engine-actions.yml
---
url: scriptdash/engine-actions
default_branch: main
gems:
  - actions_engine
  - actions_api
shared_ruby_deps:
  - core
  - rails_core
  - rails_app
  - sidekiq
alto_ruby_deps:
  - name: core
    version: '~> 1.0'
  - name: boxcar
    version: '~> 1.0'
github_actions:
  workflows:
    - build_and_test_ruby_engine
    - publish_proto_package_typescript
    - tapioca_gem
owner: care
domain: actions
reviewers:
  - scriptdash/unified-workflow
protos:
  name: actions_api
  targets:
    - type: typescript
    - type: ruby
      out: ./actions_api
  deps:
    - core
```

#### 2. Generate Engine

```bash
cd alto-workspace
alto generate engine actions
cd ../engine-actions
```

This creates the full engine structure with:
- Two gems: `actions_engine` and `actions_api`
- Proto generation setup
- GitHub Actions workflows
- Test setup with RSpec
- Sorbet configuration
- Gemfile and dependencies

#### 3. Push First Commit

```bash
# Create database
RAILS_ENV=test bin/rails db:create

# Fix any lints
bundle exec rubocop --auto-correct

# Check Sorbet
bundle exec srb tc

# Run tests
bin/rspec

# Commit
git add .
git commit -m 'feat: initial commit'
git push -u origin main
```

**Notion Reference**: https://www.notion.so/alto/How-to-Create-an-Engine-5e90b8f26e6042d3956d16eadcaf95c4

### Mounting Engine in Scriptdash

#### 1. Update alto-workspace Dependencies

```yaml
# alto-workspace/config/repositories/scriptdash.yml
alto_ruby_deps:
  - name: actions_engine
    version: '~> 1.0'
  - name: actions_api
    version: '~> 1.0'
```

```bash
cd alto-workspace
alto generate deps scriptdash
cd ../scriptdash
bundle install
bin/tapioca gem actions_engine actions_api
```

#### 2. Create Initializer

```ruby
# config/initializers/actions_engine.rb
Rails.application.reloader.to_prepare do
  ActionsEngine::Engine.base_controller = ApplicationController
end
```

#### 3. Mount Routes

```ruby
# config/routes.rb
mount ActionsEngine::Engine => '/actions'
```

Now engine routes are available at `/actions/*` in Scriptdash.

**Notion Reference**: https://www.notion.so/alto/How-to-Mount-an-Engine-API-in-Scriptdash-a8df82feba314b61b7d4a6c69d09f909

---

## 7. Service Coordination Patterns

### Deployment Scenarios

| Scenario | Engine Location | Scriptdash Location | Invocation | Configuration |
|----------|----------------|---------------------|------------|---------------|
| **Both in Scriptdash** | Mounted | N/A | Local | Set endpoint, disable RPC |
| **Engine on Boxcar** | Boxcar | N/A | RPC | Set API_BASE_URL |
| **Two-Layer** | Boxcar | Mounted wrapper | Local wrapper → RPC engine | Scriptdash: local, Engine: RPC |
| **Development** | Local | Local | Local | Set endpoint, disable RPC |
| **Staging** | Boxcar (stg) | Scriptdash (stg) | RPC | Set API_BASE_URL (stg) |
| **Production** | Boxcar (prod) | Scriptdash (prod) | RPC | Set API_BASE_URL (prod) |

### Pattern 1: Both in Scriptdash (Common during development)

```ruby
# Scriptdash mounts engine
mount ActionsEngine::Engine => '/actions'

# Scriptdash configures Core API to use local endpoint
Actions.action_partnerships.action_partnerships_endpoint =
  ActionsEngine::ActionPartnerships::Endpoint

# Disable RPC
ENV['ALTO_DISABLE_RPC_ACTIONS_API'] = 'true'

# Result: Local method calls, no HTTP
```

### Pattern 2: Engine on Boxcar, Scriptdash consumes via RPC

```ruby
# Scriptdash does NOT mount engine
# Does NOT set endpoint
# Configures RPC base URL
ENV['ACTIONS_API_BASE_URL'] = 'https://actions.prod.alto.com'

# Result: HTTP calls to Boxcar
```

### Pattern 3: Two-Layer (Scriptdash wraps Engine API)

This is the pattern seen in the PRs analyzed:

```
Frontend
   ↓
Scriptdash Endpoint (permissions + delegation)
   ↓ Local call
Scriptdash Core API Wrapper
   ↓ RPC call
Engine on Boxcar (business logic)
```

**Scriptdash**:
```ruby
# Wraps Engine API
module Actions
  module Wunderbar
    class ActionPartnershipsEndpoint < AbstractEndpoint
      def fetch_all
        # Check permissions
        current_ability.authorize! :read, ActionsAPI::Types::V2::ActionPartnership

        # Delegate to Engine via Core API
        Actions.action_partnerships.fetch_all
      end
    end
  end
end

# Configure Core API to use RPC
ENV['ACTIONS_API_BASE_URL'] = 'https://actions.prod.alto.com'
```

**Benefits**:
- Permissions enforced at gateway (Scriptdash)
- Business logic isolated in Engine
- Engine can serve multiple frontends
- Separate deployment cycles

---

## 8. Testing Patterns

### Engine Request Specs

**Pattern**: Test full stack using RPC client

```ruby
# spec/requests/actions_engine/v2/action_partnerships_controller_spec.rb
require 'rails_helper'

RSpec.describe ActionsEngine::V2::ActionPartnershipsController,
               :rpc_client_requests, type: :request do
  let(:client) { ActionsAPI::V2::ActionPartnershipsEndpoint::RPCClient.new }

  describe 'GET /v2/action_partnerships/fetch_all' do
    subject(:fetch_all) { client.fetch_all }

    context 'with action partnerships' do
      before do
        create(:action_partnership, name: 'Progyny', value: 'progyny', company_id: 1)
        create(:action_partnership, name: 'Carrot', value: 'carrot', company_id: 1)
      end

      it 'returns all action partnerships' do
        result = fetch_all

        expect(result).to be_an(Array)
        expect(result.length).to eq(2)
        expect(result.first).to be_a(ActionsAPI::Types::V2::ActionPartnership)
        expect(result.first.name).to eq('Progyny')
        expect(result.first.value).to eq('progyny')
      end
    end

    context 'with no action partnerships' do
      it 'returns empty array' do
        result = fetch_all
        expect(result).to eq([])
      end
    end
  end
end
```

**Key Elements**:
- `:rpc_client_requests` helper enables RPC testing
- Use `RPCClient.new` to make requests
- Test via RPC client (not controller directly)
- Use factories for test data
- Verify response types and values

### Scriptdash Controller Specs

**Pattern**: Test permissions and delegation, mock Engine API

```ruby
# spec/requests/wunderbar/actions/v1/action_partnerships_controller_spec.rb
require 'rails_helper'

RSpec.describe Wunderbar::Actions::V1::ActionPartnershipsController,
               type: :controller do
  before(:each) do
    @wunderbar_user = FactoryBot.create(:manager_wb_user)
    login_wunderbar_user(@wunderbar_user)
  end

  describe 'GET #index' do
    let(:mock_partnerships) do
      [
        ActionsAPI::Types::V2::ActionPartnership.new(
          id: 1, name: 'Progyny', value: 'progyny'
        ),
        ActionsAPI::Types::V2::ActionPartnership.new(
          id: 2, name: 'Carrot', value: 'carrot'
        ),
      ]
    end

    before do
      allow(Actions.action_partnerships).to receive(:fetch_all)
        .and_return(mock_partnerships)
    end

    it 'returns success' do
      get :index
      expect(response).to have_http_status(200)
    end

    it 'returns action partnerships' do
      get :index
      body = JSON.parse(response.body)
      expect(body['data']).to be_an(Array)
      expect(body['data'].length).to eq(2)
      expect(body['data'].first['name']).to eq('Progyny')
    end

    context 'without permission' do
      before do
        @wunderbar_user = FactoryBot.create(:basic_wb_user)
        login_wunderbar_user(@wunderbar_user)
      end

      it 'returns unauthorized' do
        expect { get :index }.to raise_error(CanCan::AccessDenied)
      end
    end
  end
end
```

**Key Elements**:
- Login user before each test
- Mock Engine API with `allow(...).to receive(...)`
- Test permissions (unauthorized scenarios)
- Test response format and values
- Don't test business logic (that's in Engine)

---

## 9. Complete Workflow: Creating a FetchAll Endpoint

### Prerequisites

- Rails Engine created and mounted in Scriptdash (or deployed on Boxcar)
- alto-workspace configured
- Database table exists with model

### Step-by-Step Guide

#### Step 1: Define Proto Type

```bash
cd engine-actions/protos/src
```

Create `actions_api/types/v2/action_partnership.proto`:
```protobuf
syntax = "proto3";

package actions_api.types.v2;

import "opts/opts.proto";

message ActionPartnership {
  int64 id = 1 [(opts.field) = {required: true}];
  string name = 2 [(opts.field) = {required: true}];
  string value = 3 [(opts.field) = {required: true}];
}
```

#### Step 2: Define Proto Endpoint

Create `actions_api/v2/action_partnerships_endpoint.proto`:
```protobuf
syntax = "proto3";

package actions_api.v2;

import "actions_api/types/v2/action_partnership.proto";
import "core/types/v1/error_object.proto";
import "google/api/annotations.proto";
import "opts/opts.proto";

message ActionPartnershipsEndpointFetchAllRequest {
}

message ActionPartnershipsEndpointFetchAllResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  repeated actions_api.types.v2.ActionPartnership data = 2;
}

service ActionPartnershipsEndpoint {
  option (opts.service_value) = {version: "v2.0"};

  rpc FetchAll(ActionPartnershipsEndpointFetchAllRequest)
      returns (ActionPartnershipsEndpointFetchAllResponse);
}
```

#### Step 3: Generate Code

```bash
cd ../..  # Back to engine root
bin/protos
git checkout actions_api/lib/actions_api.rb  # Restore deleted file
```

#### Step 4: Implement Endpoint

Create `app/services/actions_engine/action_partnerships/endpoint.rb`:
```ruby
# typed: strict

module ActionsEngine
  module ActionPartnerships
    # @owners { team: unified-workflow, domain: actions }
    class Endpoint < ActionsAPI::V2::ActionPartnershipsEndpoint::Interface::AbstractActionPartnershipsEndpoint
      extend T::Sig

      sig do
        override.returns(T::Array[ActionsAPI::Types::V2::ActionPartnership])
      end
      def fetch_all
        ActionPartnership.all.map do |partnership|
          ActionsAPI::Types::V2::ActionPartnership.new(
            id: partnership.id,
            name: partnership.name,
            value: partnership.value,
          )
        end
      end
    end
  end
end
```

#### Step 5: Create Controller

Create `app/controllers/actions_engine/v2/action_partnerships_controller.rb`:
```ruby
# typed: strict

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

#### Step 6: Mount Routes

Edit `config/routes.rb`:
```ruby
ActionsEngine::Engine.routes.draw do
  extend ActionsAPI::V2::ActionPartnershipsEndpoint::Routes
  # ... other routes
end
```

#### Step 7: Write Tests

Create `spec/requests/actions_engine/v2/action_partnerships_controller_spec.rb`:
```ruby
require 'rails_helper'

RSpec.describe ActionsEngine::V2::ActionPartnershipsController,
               :rpc_client_requests, type: :request do
  let(:client) { ActionsAPI::V2::ActionPartnershipsEndpoint::RPCClient.new }

  describe 'GET /v2/action_partnerships/fetch_all' do
    it 'returns all action partnerships' do
      create(:action_partnership, name: 'Progyny', value: 'progyny')
      create(:action_partnership, name: 'Carrot', value: 'carrot')

      result = client.fetch_all

      expect(result.length).to eq(2)
      expect(result.first).to be_a(ActionsAPI::Types::V2::ActionPartnership)
    end
  end
end
```

#### Step 8: Run Tests and Commit

```bash
bin/rspec spec/requests/actions_engine/v2/action_partnerships_controller_spec.rb
git add .
git commit -m "feat: add action partnerships fetch_all endpoint"
git push
```

#### Step 9: Wire Up in Scriptdash (If Frontend-Facing)

**Update alto-workspace deps** (if new engine version):
```bash
cd alto-workspace
alto bump scriptdash actions
cd ../scriptdash
bundle install
bin/tapioca gem actions_api actions_engine
```

**Create Core API wrapper** (`app/services/actions/action_partnerships.rb`):
```ruby
# typed: strict

module Actions
  # @owners { team: care, domain: actions }
  module ActionPartnerships
    extend T::Sig
    include Core::API

    add_api ActionsAPI::V2::ActionPartnershipsEndpoint::Client
    self.action_partnerships_endpoint = ActionsEngine::ActionPartnerships::Endpoint
  end
end
```

**Expose via parent module** (`app/services/actions.rb`):
```ruby
module Actions
  # ... existing code ...

  sig { returns(T.class_of(ActionPartnerships)) }
  def self.action_partnerships
    ActionPartnerships
  end
end
```

**Run tapioca** to generate type hints:
```bash
bin/tapioca dsl Actions::ActionPartnerships
```

**Usage**:
```ruby
partnerships = Actions.action_partnerships.fetch_all
```

#### Step 10: Add Frontend Endpoint with Permissions (Optional)

If you need a Scriptdash-specific endpoint with permissions:

**Define proto** (`protos/src/alto/actions/wunderbar/v1/action_partnerships_endpoint.proto`):
```protobuf
syntax = "proto3";

package alto.actions.wunderbar.v1;

import "actions_api/types/v2/action_partnership.proto";
import "core/types/v1/error_object.proto";
import "opts/opts.proto";

message ActionPartnershipsEndpointFetchAllRequest {}

message ActionPartnershipsEndpointFetchAllResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  repeated actions_api.types.v2.ActionPartnership data = 2;
}

service ActionPartnershipsEndpoint {
  option (opts.service_value) = {version: "v2.0"};

  rpc FetchAll(ActionPartnershipsEndpointFetchAllRequest)
      returns (ActionPartnershipsEndpointFetchAllResponse);
}
```

**Generate, implement endpoint with permissions**, create controller, mount routes, add permissions to Ability classes, write tests.

(See Section 10 for full two-service pattern details)

---

## 10. Two-Service Coordination Pattern

### When to Use

Use two-service pattern when:
- **Permissions needed**: Scriptdash enforces authorization, Engine doesn't
- **Multiple frontends**: Different UIs consume same Engine
- **UI-specific logic**: Scriptdash adds frontend-specific transformations
- **Gateway pattern**: Scriptdash acts as API gateway

### Architecture

```
┌──────────────────┐
│  Frontend (UI)   │
└────────┬─────────┘
         │ HTTP
         ▼
┌──────────────────────────────────┐
│  Scriptdash (Frontend Layer)     │
│  Route: /actions/v1/...           │
│  - Permissions (CanCanCan)        │
│  - UI-specific logic              │
│  - Delegates to Engine            │
└────────┬─────────────────────────┘
         │ Core::API (local or RPC)
         ▼
┌──────────────────────────────────┐
│  Engine (Backend Layer)           │
│  Route: /v2/...                   │
│  - Business logic                 │
│  - Database access                │
│  - Type mapping                   │
└──────────────────────────────────┘
```

### Implementation Pattern

#### Engine Side (Business Logic)

**Proto** (`actions_api/v2/action_partnerships_endpoint.proto`):
```protobuf
package actions_api.v2;

service ActionPartnershipsEndpoint {
  option (opts.service_value) = {version: "v2.0"};
  rpc FetchAll(...) returns (...);
}
```

**Endpoint** (`app/services/actions_engine/action_partnerships/endpoint.rb`):
```ruby
module ActionsEngine::ActionPartnerships
  class Endpoint < ActionsAPI::V2::ActionPartnershipsEndpoint::Interface::AbstractActionPartnershipsEndpoint
    def fetch_all
      # Business logic, database access
      ActionPartnership.all.map { |p| to_struct(p) }
    end
  end
end
```

**Controller** (`app/controllers/actions_engine/v2/action_partnerships_controller.rb`):
```ruby
module ActionsEngine::V2
  class ActionPartnershipsController < ApplicationController
    include ActionsAPI::V2::ActionPartnershipsEndpoint::Controller

    def endpoint
      @endpoint ||= ActionPartnerships::Endpoint.new
    end
  end
end
```

**Routes**: `GET /v2/action_partnerships/fetch_all`

---

#### Scriptdash Side (Frontend/Permissions)

**Proto** (`alto/actions/wunderbar/v1/action_partnerships_endpoint.proto`):
```protobuf
package alto.actions.wunderbar.v1;

import "actions_api/types/v2/action_partnership.proto";  // Reuse Engine type!

service ActionPartnershipsEndpoint {
  option (opts.service_value) = {version: "v2.0"};
  rpc FetchAll(...) returns (...);  // Returns Engine type
}
```

**Core API Wrapper** (`app/services/actions/action_partnerships.rb`):
```ruby
module Actions::ActionPartnerships
  include Core::API

  add_api ActionsAPI::V2::ActionPartnershipsEndpoint::Client
  self.action_partnerships_endpoint = ActionsEngine::ActionPartnerships::Endpoint
end
```

**Endpoint with Permissions** (`app/services/actions/wunderbar/action_partnerships_endpoint.rb`):
```ruby
module Actions::Wunderbar
  class ActionPartnershipsEndpoint < Alto::Actions::Wunderbar::V1::ActionPartnershipsEndpoint::Interface::AbstractActionPartnershipsEndpoint
    include Auth::CurrentAbility

    def fetch_all
      # 1. Check permissions
      current_ability.authorize! :read, ActionsAPI::Types::V2::ActionPartnership

      # 2. Delegate to Engine (via Core API)
      Actions.action_partnerships.fetch_all
    end
  end
end
```

**Controller** (`app/controllers/wunderbar/actions/v1/action_partnerships_controller.rb`):
```ruby
module Wunderbar::Actions::V1
  class ActionPartnershipsController < WunderbarController
    include Alto::Actions::Wunderbar::V1::ActionPartnershipsEndpoint::Controller

    def endpoint
      @endpoint ||= ::Actions::Wunderbar::ActionPartnershipsEndpoint.new
    end
  end
end
```

**Permissions** (`app/models/abilities/ability.rb`):
```ruby
def ops(wunderbar_user = nil)
  can :read, ActionsAPI::Types::V2::ActionPartnership
end

def manager(wunderbar_user = nil)
  can :read, ActionsAPI::Types::V2::ActionPartnership
end
```

**Routes**: `GET /actions/v1/action_partnerships`

---

### Key Benefits

1. **Separation of Concerns**:
   - Engine: Business logic, data access
   - Scriptdash: Permissions, UI concerns

2. **Reusability**:
   - Engine can serve multiple frontends (Wunderbar, mobile app, etc.)
   - Each frontend adds own permissions/transformations

3. **Independent Deployment**:
   - Update Engine business logic without touching Scriptdash
   - Update Scriptdash permissions without touching Engine

4. **Type Reuse**:
   - Scriptdash imports Engine types
   - No duplication, single source of truth

---

## 11. Permissions and Authorization

### Permissions in Scriptdash (Not Engines)

Engines typically **do not** implement permissions. Permissions are enforced at the **Scriptdash layer** using CanCanCan.

### Adding Permissions

#### 1. Update Ability Classes

**Base Abilities** (`app/models/abilities/ability.rb`):
```ruby
def ops(wunderbar_user = nil)
  can :read, ActionsAPI::Types::V2::ActionPartnership
  can :create, ActionsAPI::Types::V2::ActionPartnership
  can :update, ActionsAPI::Types::V2::ActionPartnership
end

def manager(wunderbar_user = nil)
  can :read, ActionsAPI::Types::V2::ActionPartnership
  can :update, ActionsAPI::Types::V2::ActionPartnership
end

def engineer(_wunderbar_user = nil)
  can :read, ActionsAPI::Types::V2::ActionPartnership
end
```

**Wunderbar Abilities** (`app/models/abilities/wunderbar_ability.rb`):
```ruby
def grant_abilities_for_role(role)
  case role
  when :engineer
    can :manage, ActionsAPI::Types::V2::ActionType::ActionType
    can :read, ActionsAPI::Types::V2::ActionPartnership  # Add this
  when :manager, :ops
    can :read, ActionsAPI::Types::V2::ActionPartnership  # Add this
  end
end
```

#### 2. Use in Endpoint

```ruby
module Actions::Wunderbar
  class ActionPartnershipsEndpoint < AbstractActionPartnershipsEndpoint
    include Auth::CurrentAbility

    def fetch_all
      current_ability.authorize! :read, ActionsAPI::Types::V2::ActionPartnership
      Actions.action_partnerships.fetch_all
    end

    def create(params:)
      current_ability.authorize! :create, ActionsAPI::Types::V2::ActionPartnership
      Actions.action_partnerships.create(params: params)
    end
  end
end
```

### Permission Actions

- `:read` - FetchOne, FetchAll, FetchBy, Search
- `:create` - Create
- `:update` - Update
- `:destroy` - Delete
- `:manage` - All actions

### Testing Permissions

```ruby
RSpec.describe Wunderbar::Actions::V1::ActionPartnershipsController do
  context 'with read permission' do
    before { @user = create(:manager_wb_user); login_wunderbar_user(@user) }

    it 'allows fetch_all' do
      get :index
      expect(response).to have_http_status(200)
    end
  end

  context 'without permission' do
    before { @user = create(:basic_wb_user); login_wunderbar_user(@user) }

    it 'denies fetch_all' do
      expect { get :index }.to raise_error(CanCan::AccessDenied)
    end
  end
end
```

---

## 12. TypeScript Code Generation

### Generated TypeScript

TypeScript types and client functions are automatically generated from proto definitions.

**Type** (`protos/gen/typescript/lib/actions_api/types/v2/action_partnership.ts`):
```typescript
// GENERATED CODE - DO NOT EDIT

export interface ActionPartnership {
  id: number;
  name: string;
  value: string;
}
```

**Client** (`protos/gen/typescript/lib/actions_api/v2/action_partnerships_endpoint.ts`):
```typescript
// GENERATED CODE - DO NOT EDIT
import { ActionPartnership } from '../types/v2/action_partnership';
import { ErrorObject } from '@alto/core/types/v1/error_object';

export interface ActionPartnershipsEndpointFetchAllRequest {}

export interface ActionPartnershipsEndpointFetchAllResponse {
  errors: ErrorObject[] | null | undefined;
  data: ActionPartnership[] | null | undefined;
}

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

### Frontend Usage

```typescript
import { ActionPartnershipsEndpoint } from '@alto/actions_api/v2/action_partnerships_endpoint';
import { ActionPartnership } from '@alto/actions_api/types/v2/action_partnership';

const client = ActionPartnershipsEndpoint(makeRequest);

const response = await client.fetchAll({});
const partnerships: ActionPartnership[] = response.data || [];

partnerships.forEach(p => {
  console.log(p.name); // Type-safe!
});
```

---

## 13. Common Patterns and Conventions

### Naming Conventions

| Concept | Pattern | Example |
|---------|---------|---------|
| **Proto Type** | `<Resource>` (singular, CamelCase) | `ActionPartnership` |
| **Proto Endpoint** | `<Resource>Endpoint` (singular) | `ActionPartnershipsEndpoint` |
| **Request Message** | `<Endpoint><Method>Request` | `ActionPartnershipsEndpointFetchAllRequest` |
| **Response Message** | `<Endpoint><Method>Response` | `ActionPartnershipsEndpointFetchAllResponse` |
| **Params Message** | `<Endpoint><Method>Params` | `ActionPartnershipsEndpointCreateParams` |
| **Ruby Module** | `<Domain>Engine` | `ActionsEngine` |
| **Ruby API** | `<Domain>API` | `ActionsAPI` |
| **Controller** | `<Resource>Controller` (plural) | `ActionPartnershipsController` |
| **Endpoint** | `<Resource>::Endpoint` | `ActionPartnerships::Endpoint` |
| **Routes Namespace** | `/v<version>/<resources>` | `/v2/action_partnerships` |

### File Locations

| File Type | Location |
|-----------|----------|
| **Proto Type** | `protos/src/<domain>_api/types/v<version>/<resource>.proto` |
| **Proto Endpoint** | `protos/src/<domain>_api/v<version>/<resource>_endpoint.proto` |
| **Generated Type** | `<domain>_api/lib/<domain>_api/types/v<version>/<resource>.rb` |
| **Generated API** | `<domain>_api/lib/<domain>_api/v<version>/<resource>_endpoint/` |
| **Endpoint Impl** | `app/services/<domain>_engine/<resource>/endpoint.rb` |
| **Controller** | `app/controllers/<domain>_engine/v<version>/<resource>_controller.rb` |
| **Routes** | `config/routes.rb` |
| **Request Spec** | `spec/requests/<domain>_engine/v<version>/<resource>_controller_spec.rb` |

### Response Structure

**Always follow this structure**:
```protobuf
message <Endpoint><Method>Response {
  repeated core.types.v1.ErrorObject errors = 1;  // Field 1, optional
  <Type> data = 2;                                 // Field 2, optional
  <Endpoint><Method>ResponseMetadata metadata = 3; // Field 3, optional
}
```

### Sorbet Patterns

**Endpoint Implementation**:
```ruby
# typed: strict

class Endpoint < AbstractEndpoint
  extend T::Sig

  sig { override.params(...).returns(...) }
  def method_name(...)
  end
end
```

**Controller**:
```ruby
# typed: strict

class Controller < ApplicationController
  extend T::Sig

  sig { returns(Endpoint) }
  def endpoint
    @endpoint ||= T.let(Endpoint.new, T.nilable(Endpoint))
  end
end
```

### Ownership Annotations

```ruby
# @owners { team: unified-workflow, domain: actions }
class Endpoint
end
```

### CODEOWNERS

Update when adding new directories:
```
/app/services/actions_engine/action_partnerships/*.rb @scriptdash/unified-workflow
```

---

## 14. Troubleshooting and Gotchas

### Proto Code Generation Issues

**Problem**: Generated code deletes `<domain>_api/lib/<domain>_api.rb`

**Solution**: Always restore after generation:
```bash
bin/protos
git checkout <domain>_api/lib/<domain>_api.rb
```

---

**Problem**: Sorbet errors after generating new code

**Solution**: Run tapioca:
```bash
bin/tapioca gem
bin/tapioca dsl
```

---

**Problem**: Routes not found after adding endpoint

**Solution**: Verify routes extended:
```ruby
# config/routes.rb should have:
extend ActionsAPI::V2::ActionPartnershipsEndpoint::Routes
```

---

### RPC vs Local Confusion

**Problem**: Calling local endpoint but making HTTP calls

**Solution**: Check environment configuration:
```ruby
# Should be set for local:
ENV['ALTO_DISABLE_RPC_ACTIONS_API'] = 'true'

# Should NOT be set for local:
ENV['ACTIONS_API_BASE_URL'] # should be nil or not set
```

---

**Problem**: RPC client returning 404

**Solution**: Verify endpoint deployed and base URL correct:
```bash
curl https://actions.prod.alto.com/v2/action_partnerships/fetch_all
```

---

### Testing Issues

**Problem**: `:rpc_client_requests` helper not working

**Solution**: Ensure in `spec/rails_helper.rb`:
```ruby
RSpec.configure do |config|
  config.include RPCClientRequestHelpers, type: :request, rpc_client_requests: true
end
```

---

**Problem**: Permissions tests failing

**Solution**: Ensure user logged in before test:
```ruby
before(:each) do
  @user = create(:manager_wb_user)
  login_wunderbar_user(@user)
end
```

---

### Database Issues

**Problem**: Table not found in engine

**Solution**: Override `table_name`:
```ruby
class ActionPartnership < ApplicationRecord
  self.table_name = :action_partnerships  # Not :actions_engine_action_partnerships
end
```

---

**Problem**: Database queries failing in tests

**Solution**: Ensure test database created:
```bash
RAILS_ENV=test bin/rails db:create
RAILS_ENV=test bin/rails db:migrate
```

---

### Build/Deploy Issues

**Problem**: Gem not published to Artifactory

**Solution**: Commit message must start with `feat:`, `fix:`, or other semantic release prefix:
```bash
git commit -m "feat: add action partnerships endpoint"
```

---

**Problem**: TypeScript types not found in frontend

**Solution**: Ensure TypeScript generation configured in `alto-workspace`:
```yaml
protos:
  targets:
    - type: typescript  # Must be present
```

---

## 15. References

### Primary Notion Documentation

- **Better Boundaries Overview**: https://www.notion.so/alto/Better-Boundaries-630ded036fde443db2a436369cf99da6
- **Protobuf Service Definitions**: https://www.notion.so/alto/Protobuf-Service-Definitions-81923cbea0a74a4bafd7c64e8c76a18f
- **Standard Resource Methods**: https://www.notion.so/alto/Standard-Resource-Methods-1717220d19d047f2bb827df0fdaca027
- **Core APIs**: https://www.notion.so/alto/Core-APIs-5ce03b7443f94c57ba314561122fd1c6
- **Module Boundaries**: https://www.notion.so/alto/Module-Boundaries-b6d6ce07dfe64920a5fc96f92325ccb8
- **Rails Engines**: https://www.notion.so/alto/Rails-Engines-14c28364d63c43969837a70f37c353d3
- **Boxcar Applications**: https://www.notion.so/alto/Boxcar-Applications-27ed421835444bd4aa41bb655dc44cd4

### How-To Guides

- **Create an Engine**: https://www.notion.so/alto/How-to-Create-an-Engine-5e90b8f26e6042d3956d16eadcaf95c4
- **Generate Engine API**: https://www.notion.so/alto/How-to-Generate-an-Engine-API-223b48c9344d48abbf86b47cd2e9cd62
- **Add to Engine API**: https://www.notion.so/alto/How-to-Add-to-an-Engine-API-11c6563641d980518891f644da8465d1
- **Connect Proto-Generated APIs**: https://www.notion.so/alto/How-to-Connect-Proto-Generated-APIs-57bdc11f836f4705ac32848ca8e00d89
- **Mount Engine in Scriptdash**: https://www.notion.so/alto/How-to-Mount-an-Engine-API-in-Scriptdash-a8df82feba314b61b7d4a6c69d09f909
- **Test Core APIs**: https://www.notion.so/alto/How-to-Test-Core-APIs-1a072c1eb9594f12a9cd76cc038aeea6
- **Set Up Boxcar App**: https://www.notion.so/alto/How-to-Set-Up-a-Boxcar-App-400b59ae46284dc4b110579bf6740e29

### Repositories

- **alto-api**: https://github.com/scriptdash/alto-api (Proto definitions)
- **scriptdash**: https://github.com/scriptdash/scriptdash (Monolith)
- **engine-actions**: https://github.com/scriptdash/engine-actions (Example engine)
- **alto-workspace**: https://github.com/scriptdash/alto-workspace (Meta-repo)
- **gem-core**: https://github.com/scriptdash/gem-core (Core::API implementation)

### Example PRs

- **Scriptdash**: https://github.com/scriptdash/scriptdash/pull/48986 (FetchAll Action Partnerships)
- **Actions Engine**: https://github.com/scriptdash/engine-actions/pull/535 (FetchAll Action Partnerships)

### Token Summary

This expanded reconnaissance summary: ~19k tokens
- Original summary: ~4k tokens
- Expansion factor: ~5x
- Coverage: Comprehensive architectural reference with code examples, patterns, troubleshooting

**Usage**: Load this single file instead of 40k Notion docs + 12k PR diffs for future sessions.
