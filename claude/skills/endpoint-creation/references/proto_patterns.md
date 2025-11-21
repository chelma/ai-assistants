# FetchAll + FetchOne Endpoint Patterns

**Scope**: Patterns for creating read-only endpoints (FetchAll, FetchOne) in Scriptdash and Rails Engines
**Source**: PRs #48986 (Scriptdash), #535 (Actions Engine), Actions Engine codebase analysis
**Philosophy**: Prescriptive guidance based on current best practices
**Last Updated**: 2025-11-20

---

## Table of Contents

- [Layer 1: Proto System](#layer-1-proto-system)
- [Layer 2: Code Generation](#layer-2-code-generation) (TBD)
- [Layer 3: Implementation - Engine Endpoints](#layer-3-implementation---engine-endpoints)
- [Layer 4: Controllers](#layer-4-controllers) (TBD)
- [Layer 5: Routes](#layer-5-routes) (TBD)
- [Layer 6: Core API Integration](#layer-6-core-api-integration) (TBD)
- [Layer 7: Permissions](#layer-7-permissions) (TBD)
- [Layer 8: Testing](#layer-8-testing) (TBD)
- [Common Errors & Fixes](#common-errors--fixes) (TBD)

---

## Layer 1: Proto System

Protocol Buffers (proto3) serve as the source of truth for all API contracts. Every endpoint starts with proto definitions.

### Pattern 1.1: Proto-First Design [CRITICAL]

**Priority**: CRITICAL

**Purpose**: Establish API contract before implementation. Enables type-safe code generation for Ruby, TypeScript, and consistent structure across all endpoints.

**When to use**: Always. Every endpoint starts with proto definitions.

**Implementation**:

1. **Define the type first** (`types/v{version}/{resource}.proto`):

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

2. **Define the endpoint** (`v{version}/{resource}_endpoint.proto`):

```protobuf
syntax = "proto3";

package actions_api.v2;

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

3. **Generate code**:

```bash
cd engine-actions
bin/protos
git checkout actions_api/lib/actions_api.rb  # Important! Generator deletes this
```

**Trade-offs**:
- ✅ Type safety across Ruby and TypeScript
- ✅ Consistent API structure
- ✅ Self-documenting (proto files are the spec)
- ✅ Auto-generates controllers, routes, clients
- ❌ Requires learning proto syntax
- ❌ Changes require regeneration

**Common Error**: Forgetting to restore `actions_api.rb` after generation

```bash
# Error: LoadError: cannot load such file -- actions_api
# Fix:
git checkout actions_api/lib/actions_api.rb
```

---

### Pattern 1.2: Service V2.0 Annotation [CRITICAL]

**Priority**: CRITICAL

**Purpose**: Enables advanced code generation including controllers, routes, and clients. V2.0 is the modern standard.

**When to use**: Always. All new endpoints should use Service V2.0.

**Implementation**:

```protobuf
service ActionPartnershipsEndpoint {
  option (opts.service_value) = {version: "v2.0"};  // ← This is critical

  rpc FetchAll(ActionPartnershipsEndpointFetchAllRequest)
      returns (ActionPartnershipsEndpointFetchAllResponse);
}
```

**What V2.0 generates**:
- `interface.rb` - Request/Response types + Abstract endpoint class
- `controller.rb` - Rails controller actions
- `client.rb` - Ruby client for local/RPC calls
- `rpc_client.rb` - HTTP client for remote calls (Engine only)
- `routes.rb` - Rails route definitions

**Trade-offs**:
- ✅ Automatic controller/routes generation
- ✅ Standardized patterns enforced
- ✅ Less boilerplate code to write
- ❌ Must follow generated structure (less flexibility)

**Common Error**: Omitting the service_value option

```protobuf
// ❌ Wrong: No service version
service ActionPartnershipsEndpoint {
  rpc FetchAll(...) returns (...);
}

// ✅ Correct: V2.0 annotation
service ActionPartnershipsEndpoint {
  option (opts.service_value) = {version: "v2.0"};
  rpc FetchAll(...) returns (...);
}
```

---

### Pattern 1.3: Separate Type Definitions [CRITICAL]

**Priority**: CRITICAL

**Purpose**: Reusable types across multiple endpoints and services. Enables Scriptdash to import Engine types without duplication.

**When to use**: Always. Types go in `types/v{version}/`, endpoints go in `v{version}/`.

**Implementation**:

**File structure**:
```
protos/src/
├── actions_api/
│   ├── types/v2/
│   │   └── action_partnership.proto    ← Type definition
│   └── v2/
│       └── action_partnerships_endpoint.proto  ← Endpoint using the type
```

**Type file** (`types/v2/action_partnership.proto`):
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

**Endpoint file** (`v2/action_partnerships_endpoint.proto`):
```protobuf
syntax = "proto3";

package actions_api.v2;

import "actions_api/types/v2/action_partnership.proto";  // ← Import the type

message ActionPartnershipsEndpointFetchAllResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  repeated actions_api.types.v2.ActionPartnership data = 2;  // ← Use imported type
}
```

**Type reuse in Scriptdash** (`alto/actions/wunderbar/v1/action_partnerships_endpoint.proto`):
```protobuf
syntax = "proto3";

package alto.actions.wunderbar.v1;

import "actions_api/types/v2/action_partnership.proto";  // ← Reuse Engine type!

message ActionPartnershipsEndpointFetchAllResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  repeated actions_api.types.v2.ActionPartnership data = 2;  // ← Same type
}
```

**Trade-offs**:
- ✅ Single source of truth for types
- ✅ Scriptdash and Engine share types
- ✅ Changes propagate automatically
- ✅ Prevents drift between services
- ❌ Tighter coupling (type changes affect multiple services)

---

### Pattern 1.4: Request/Response Naming Convention [CRITICAL]

**Priority**: CRITICAL

**Purpose**: Consistent, predictable naming makes generated code discoverable and maintainable.

**When to use**: Always. Follow this exact pattern.

**Implementation**:

**Pattern**:
```
{ServiceName}{MethodName}Request
{ServiceName}{MethodName}Response
```

**FetchAll example**:
```protobuf
service ActionPartnershipsEndpoint {
  rpc FetchAll(ActionPartnershipsEndpointFetchAllRequest)  // ← Request
      returns (ActionPartnershipsEndpointFetchAllResponse);  // ← Response
}

message ActionPartnershipsEndpointFetchAllRequest {}

message ActionPartnershipsEndpointFetchAllResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  repeated actions_api.types.v2.ActionPartnership data = 2;
}
```

**FetchOne example**:
```protobuf
service ActionTypesEndpoint {
  rpc FetchOne(ActionTypesEndpointFetchOneRequest)  // ← Request
      returns (ActionTypesEndpointFetchOneResponse);  // ← Response
}

message ActionTypesEndpointFetchOneRequest {
  int64 id = 1 [(opts.field) = {required: true}];
}

message ActionTypesEndpointFetchOneResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  actions_api.types.v2.ActionType data = 2;
}
```

**Naming breakdown**:
- `ActionPartnershipsEndpoint` - Service name (singular or plural resource)
- `FetchAll` / `FetchOne` - Method name (Standard Resource Method)
- `Request` / `Response` - Message type

**Trade-offs**:
- ✅ Predictable names make code searchable
- ✅ Code generators expect this pattern
- ✅ Easy to understand relationships
- ❌ Verbose (but explicit is better than implicit)

**Common Error**: Inconsistent naming

```protobuf
// ❌ Wrong: Doesn't match pattern
message FetchAllActionPartnerships {}
message ActionPartnershipsResponse {}

// ✅ Correct: Follows pattern
message ActionPartnershipsEndpointFetchAllRequest {}
message ActionPartnershipsEndpointFetchAllResponse {}
```

---

### Pattern 1.5: Standard Response Structure [CRITICAL]

**Priority**: CRITICAL

**Purpose**: Uniform error handling and data structure across all endpoints. Clients can rely on consistent format.

**When to use**: Always. Every response follows this structure.

**Implementation**:

**Structure**:
```protobuf
message {Endpoint}{Method}Response {
  repeated core.types.v1.ErrorObject errors = 1;  // Field 1: Always errors array
  {Type} data = 2;                                  // Field 2: Data (single or repeated)
  {ResponseMetadata} metadata = 3;                  // Field 3: Optional metadata
}
```

**FetchOne response** (single record):
```protobuf
message ActionTypesEndpointFetchOneResponse {
  repeated core.types.v1.ErrorObject errors = 1;  // Errors (optional, can be empty)
  actions_api.types.v2.ActionType data = 2;        // Single record
}
```

**FetchAll response** (multiple records):
```protobuf
message ActionPartnershipsEndpointFetchAllResponse {
  repeated core.types.v1.ErrorObject errors = 1;           // Errors (optional)
  repeated actions_api.types.v2.ActionPartnership data = 2; // Array of records
}
```

**With metadata** (for pagination, etc.):
```protobuf
message ActionTypesEndpointSearchResponseMetadata {
  core.types.v1.PaginationResponseMetadata pagination = 1;
}

message ActionTypesEndpointSearchResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  repeated actions_api.types.v2.ActionType data = 2;
  ActionTypesEndpointSearchResponseMetadata metadata = 3;  // ← Optional field 3
}
```

**Field numbering rules**:
- Field 1: **Always** `errors` (repeated ErrorObject)
- Field 2: **Always** `data` (single entity or repeated)
- Field 3: **Optional** `metadata` (for pagination, counts, etc.)

**Trade-offs**:
- ✅ Consistent error handling
- ✅ Clients know where to find data
- ✅ Optional errors field (success = empty array)
- ✅ Extensible (can add metadata later)
- ❌ Slightly verbose (errors field even when never used)

**Common Error**: Wrong field numbers or names

```protobuf
// ❌ Wrong: Fields out of order
message BadResponse {
  actions_api.types.v2.ActionType data = 1;        // data should be field 2
  repeated core.types.v1.ErrorObject errors = 2;   // errors should be field 1
}

// ❌ Wrong: Wrong field name
message BadResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  repeated actions_api.types.v2.ActionType results = 2;  // Should be 'data'
}

// ✅ Correct: Errors field 1, data field 2
message GoodResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  repeated actions_api.types.v2.ActionType data = 2;
}
```

---

### Pattern 1.6: FetchAll Request Variations [PREFERRED]

**Priority**: PREFERRED

**Purpose**: Different use cases require different FetchAll request patterns. Choose based on your access pattern.

**When to use**: Choose the pattern that matches your use case.

**Variation A: Empty Request** (fetch all records in system)

```protobuf
message ActionPartnershipsEndpointFetchAllRequest {}

message ActionPartnershipsEndpointFetchAllResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  repeated actions_api.types.v2.ActionPartnership data = 2;
}
```

**When to use**: Small datasets (< 1000 records), dropdowns, reference data
**HTTP URL**: `GET /v2/action_partnerships/fetch_all`
**Implementation**: `Model.all.map { |m| to_struct(m) }`

---

**Variation B: Required IDs Parameter** (fetch specific records)

```protobuf
message ActionTypesEndpointFetchAllRequest {
  repeated int64 ids = 1;  // No [(opts.field) = {required: true}] in proto3
}

message ActionTypesEndpointFetchAllResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  repeated actions_api.types.v2.ActionType data = 2;
}
```

**When to use**: Client knows which IDs they need (e.g., from a previous query)
**HTTP URL**: `GET /v2/action_types/fetch_all?ids=1&ids=2&ids=3`
**Implementation**: `Model.where(id: ids).map { |m| to_struct(m) }`

**Note**: proto3 doesn't have a true "required" keyword for fields. Use `[(opts.field) = {required: true}]` annotation for validation.

---

**Variation C: Optional IDs Parameter** (fetch all or filter by IDs)

```protobuf
message TaskThresholdsEndpointFetchAllRequest {
  repeated int64 ids = 1;  // Optional - field can be empty/missing
}

message TaskThresholdsEndpointFetchAllResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  repeated actions_api.types.v2.TaskThreshold data = 2;
}
```

**When to use**: Flexible access - sometimes fetch all, sometimes filter
**HTTP URLs**:
- `GET /v1/task_thresholds/fetch_all` (no IDs = all records)
- `GET /v1/task_thresholds/fetch_all?ids=1&ids=2` (with IDs = filtered)

**Implementation**:
```ruby
def fetch_all(ids: nil)
  relation = ids.present? ? TaskThreshold.where(id: ids) : TaskThreshold.all
  relation.map { |t| to_struct(t) }
end
```

---

**Trade-offs**:
- **Empty Request**: ✅ Simplest, ❌ Not scalable for large datasets
- **Required IDs**: ✅ Explicit intent, ❌ Can't fetch "all"
- **Optional IDs**: ✅ Most flexible, ❌ Ambiguous behavior (document clearly!)

**Recommendation**: Use Empty Request for small reference data, Required IDs for most use cases.

---

### Pattern 1.7: FetchOne Request Pattern [CRITICAL]

**Priority**: CRITICAL

**Purpose**: Retrieve a single record by ID. Standard pattern across all resources.

**When to use**: When you need to fetch one specific record.

**Implementation**:

```protobuf
message ActionTypesEndpointFetchOneRequest {
  int64 id = 1 [(opts.field) = {required: true}];  // Single ID, required
}

message ActionTypesEndpointFetchOneResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  actions_api.types.v2.ActionType data = 2;  // Single record (not repeated)
}

service ActionTypesEndpoint {
  option (opts.service_value) = {version: "v2.0"};

  rpc FetchOne(ActionTypesEndpointFetchOneRequest)
      returns (ActionTypesEndpointFetchOneResponse);
}
```

**Key differences from FetchAll**:
- Request: `int64 id` (singular, not `repeated int64 ids`)
- Response data: `ActionType data` (not `repeated ActionType data`)
- Required: ID is always required

**HTTP mapping**: `GET /v2/action_types/:id`

**Trade-offs**:
- ✅ Simple, unambiguous
- ✅ Maps to RESTful `GET /resource/:id`
- ✅ Standard pattern everyone understands
- ❌ Can only fetch one record per request (use FetchAll for bulk)

---

### Pattern 1.8: Package Naming Convention [CRITICAL]

**Priority**: CRITICAL

**Purpose**: Package names map directly to Ruby module hierarchy. Determines code organization.

**When to use**: Always. Choose package name carefully - it affects all generated code.

**Implementation**:

**Engine packages**:
```protobuf
package actions_api.types.v2;     // → ActionsAPI::Types::V2
package actions_api.v2;           // → ActionsAPI::V2
```

**Scriptdash packages**:
```protobuf
package alto.actions.wunderbar.v1;  // → Alto::Actions::Wunderbar::V1
```

**Naming rules**:
- **Engine**: `{domain}_api.{types.}v{version}`
- **Scriptdash**: `alto.{domain}.{application}.v{version}`
- Dots (`.`) become double colons (`::`) in Ruby
- Use lowercase with underscores (snake_case)
- Always include version (`v1`, `v2`, etc.)

**Examples**:

```protobuf
// Engine type
package actions_api.types.v2;
// Ruby: ActionsAPI::Types::V2::ActionPartnership

// Engine endpoint
package actions_api.v2;
// Ruby: ActionsAPI::V2::ActionPartnershipsEndpoint

// Scriptdash endpoint
package alto.actions.wunderbar.v1;
// Ruby: Alto::Actions::Wunderbar::V1::ActionPartnershipsEndpoint
```

**Trade-offs**:
- ✅ Clear namespace organization
- ✅ Predictable module structure
- ✅ Version isolation (v1 and v2 can coexist)
- ❌ Changing package name requires regenerating all code
- ❌ Deep nesting can be verbose

---

### Pattern 1.9: Field Annotations [PREFERRED]

**Priority**: PREFERRED

**Purpose**: Add validation rules and metadata to proto fields.

**When to use**: Mark fields as required, or add special behaviors.

**Implementation**:

**Required fields**:
```protobuf
import "opts/opts.proto";

message ActionPartnership {
  int64 id = 1 [(opts.field) = {required: true}];      // ← Required
  string name = 2 [(opts.field) = {required: true}];   // ← Required
  string value = 3 [(opts.field) = {required: true}];  // ← Required
}
```

**Embed HTTP query** (for pagination params):
```protobuf
import "core/types/v1/pagination_request_params.proto";
import "opts/opts.proto";

message ActionTypesEndpointSearchRequest {
  repeated string pods = 1;
  core.types.v1.PaginationRequestParams pagination = 2
      [(opts.field) = {embed_http_query: true}];  // ← Flattens into query params
}
```

**What `embed_http_query` does**:
- Flattens nested object into top-level query params
- `pagination.page` becomes `?page=1`
- `pagination.per_page` becomes `&per_page=20`

**Trade-offs**:
- ✅ Validation at API boundary
- ✅ Self-documenting (required fields are explicit)
- ✅ Generated code enforces rules
- ❌ Changing required → optional is a breaking change

---

## Iteration 1 Summary

**Patterns extracted**: 9 CRITICAL + PREFERRED patterns
**Files analyzed**:
- `engine-actions/protos/src/actions_api/v2/action_partnerships_endpoint.proto`
- `engine-actions/protos/src/actions_api/types/v2/action_partnership.proto`
- `engine-actions/protos/src/actions_api/v2/action_types_endpoint.proto`
- `scriptdash/protos/src/alto/actions/wunderbar/v1/action_partnerships_endpoint.proto`

**Next iteration**: Generated Code Patterns (interface, client, controller modules)

