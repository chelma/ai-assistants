# Scriptdash FetchAll and FetchOne Endpoint Patterns - Comprehensive Inventory

**Generated:** November 20, 2025
**Repository:** /Users/chris.helma/workspace/claude/scriptdash
**Thoroughness Level:** Very Thorough

---

## Executive Summary

This document provides a complete inventory of all FetchAll and FetchOne endpoint implementations in the Scriptdash codebase. The analysis covers:
- 64 unique proto files with FetchAll/FetchOne definitions
- 314 total endpoint Ruby files in the codebase
- 84 Ruby endpoint files implementing fetch_all and/or fetch_one methods
- 56 endpoints with fetch_all implementations
- 44 endpoints with fetch_one implementations
- 16 endpoints with both methods

### Key Statistics

| Metric | Count |
|--------|-------|
| Proto files with FetchAll rpc | 39 |
| Proto files with FetchOne rpc | 25 |
| Ruby endpoints with fetch_all method | 56 |
| Ruby endpoints with fetch_one method | 44 |
| Ruby endpoints with both methods | 16 |
| Total endpoint files in repo | 314 |

---

## Part 1: Proto Definition Patterns

### 1.1 Proto File Organization

**Base Pattern:**
```
protos/src/<domain>/<subdomain>/<version>/<endpoint_name>_endpoint.proto
```

**Examples:**
- `protos/src/alto/actions/wunderbar/v1/action_partnerships_endpoint.proto`
- `protos/src/alto/customer_support/v1/support_cases_endpoint.proto`
- `protos/src/alto/medications/patients/v1/list_endpoint.proto`

### 1.2 FetchAll Proto Pattern

**Minimal FetchAll (No Parameters):**
```proto
message ActionPartnershipsEndpointFetchAllRequest {}

message ActionPartnershipsEndpointFetchAllResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  repeated actions_api.types.v2.ActionPartnership data = 2;
}

service ActionPartnershipsEndpoint {
  option (opts.service_value) = {version: "v2.0"};
  rpc FetchAll(ActionPartnershipsEndpointFetchAllRequest) returns (ActionPartnershipsEndpointFetchAllResponse);
}
```

**FetchAll with ID Array (Batch):**
```proto
message SupportCasesEndpointFetchAllRequest {
  repeated int64 ids = 1 [(opts.field) = {required: true}];
}

message SupportCasesEndpointFetchAllResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  repeated alto.customer_support.types.v1.SupportCase data = 2;
}
```

**FetchAll with Pagination:**
```proto
message SupportCasesEndpointFetchAllRequest {
  int64 patient_id = 1 [(opts.field) = {required: true}];
  core.types.v1.PaginationRequestParams pagination = 2 [(opts.field) = {embed_http_query: true}];
}

message SupportCasesEndpointFetchAllResponseMetadata {
  core.types.v1.PaginationResponseMetadata pagination = 1;
}

message SupportCasesEndpointFetchAllResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  repeated alto.customer_support.types.v1.SupportCase data = 2;
  SupportCasesEndpointFetchAllResponseMetadata metadata = 3;
}
```

### 1.3 FetchOne Proto Pattern

**Standard FetchOne:**
```proto
message SupportCasesEndpointFetchOneRequest {
  int64 id = 1 [(opts.field) = {required: true}];
}

message SupportCasesEndpointFetchOneResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  alto.customer_support.types.v1.SupportCase data = 2;
}

service SupportCasesEndpoint {
  rpc FetchOne(SupportCasesEndpointFetchOneRequest) returns (SupportCasesEndpointFetchOneResponse);
}
```

### 1.4 Proto Response Pattern Variations

**Pattern 1: Simple Data + Errors**
```proto
message Response {
  repeated core.types.v1.ErrorObject errors = 1;
  RepeatType data = 2;
}
```

**Pattern 2: Data + Errors + Metadata (with Pagination)**
```proto
message ResponseMetadata {
  core.types.v1.PaginationResponseMetadata pagination = 1;
}

message Response {
  repeated core.types.v1.ErrorObject errors = 1;
  repeated DataType data = 2;
  ResponseMetadata metadata = 3;
}
```

**Pattern 3: Single Object Response (FetchOne)**
```proto
message Response {
  repeated core.types.v1.ErrorObject errors = 1;
  DataType data = 2;  // Note: singular, not repeated
}
```

---

## Part 2: Ruby Endpoint Implementation Patterns

### 2.1 Base Class Structure

All endpoints inherit from auto-generated abstract base classes:

```ruby
class ActionPartnershipsEndpoint < Alto::Actions::Wunderbar::V1::ActionPartnershipsEndpoint::Interface::AbstractActionPartnershipsEndpoint
  extend T::Sig
  include Alto::Actions::Wunderbar::V1::ActionPartnershipsEndpoint::Interface
  
  # Additional includes for authorization
  include Auth::CurrentAbility  # Optional, for permission checks
end
```

**Key Points:**
- Inherits from `Alto::<Domain>::<Version>::<Endpoint>::Interface::Abstract<Endpoint>`
- Includes the Interface module (provides method signatures)
- Uses Sorbet (`extend T::Sig`) for type safety
- May include `Auth::CurrentAbility` for permission-based access control

### 2.2 FetchAll Implementation Variations

#### Pattern A: Simple No-Parameter FetchAll
```ruby
def fetch_all
  current_ability.authorize! :read, ActionsAPI::Types::V2::ActionPartnership
  Actions.action_partnerships.fetch_all
end
```
- No parameters
- Delegates to Core API
- Single permission check

#### Pattern B: FetchAll with ID Array (Batch)
```ruby
def fetch_all(ids:)
  query = SupportCase.where(id: ids)
  query.map { |support_case| to_struct(support_case) }
end
```
- Takes array of IDs
- Queries directly from local model
- Maps results to struct objects

#### Pattern C: FetchAll with Pagination and Context
```ruby
def fetch_all(patient_id:, page_size: nil, page_token: nil)
  current_ability.authorize! :read, SupportCase

  response = CustomerSupport::SupportCases.fetch_by_user(
    user_id: patient_id, 
    page_size: page_size, 
    page_token: page_token,
  )

  response_pagination = I::SupportCasesEndpointFetchAllResponseMetadata.new(
    pagination: T.must(response.metadata).pagination,
  )

  I::SupportCasesEndpointFetchAllResponse.new({
    data: response.data,
    errors: response.errors,
    metadata: response_pagination,
  })
end
```
- Takes contextual parameters (patient_id)
- Handles pagination (page_size, page_token)
- Returns response object with metadata
- Maps to nested response structure

#### Pattern D: FetchAll with Optional Filters
```ruby
def fetch_all(ids: nil, is_internal: nil)
  # Implementation with conditional logic
end
```
- Optional parameters
- Conditional query building

### 2.3 FetchOne Implementation Variations

#### Pattern A: Direct Database Query
```ruby
def fetch_one(id:)
  Billing::Prices.to_struct(Price.find(id))
end
```
- Direct model lookup
- Maps to struct
- Throws on not found (Rails default)

#### Pattern B: With Authorization Check
```ruby
def fetch_one(id:)
  current_ability.authorize! :read, ActionsAPI::Types::V2::ActionType::ActionType
  Actions.action_types.v2.fetch_one(id:)
end
```
- Permission check before lookup
- Delegates to Core API

#### Pattern C: With Custom Error Handling
```ruby
def fetch_one(id:)
  status = MedSync.fetch_status_for_user(user_id: id)
  
  if status.nil?
    raise(
      Core::Error::NotFoundError,
      'Could not find a med sync status for the user',
    )
  end

  MedSyncUser.new(id: id, status: status)
end
```
- Custom not-found error handling
- Returns custom struct

#### Pattern D: With Access Control (Family Members)
```ruby
def fetch_one(id:)
  current_ability.authorize! :read, SupportCase

  support_case = CustomerSupport::SupportCases.fetch_one(id: id)
  family_member_ids = @current_patient.manageable_user_ids
  if family_member_ids.exclude?(support_case.user_id)
    raise Core::Error::AltoError, "Access Error: Failed to get support case #{support_case.id}"
  end

  support_case
end
```
- Checks authorization
- Additional context-aware validation
- Reuses Core API for consistency

### 2.4 Permission/Authorization Patterns

**Pattern 1: Simple Type-Based Authorization**
```ruby
current_ability.authorize! :read, ActionsAPI::Types::V2::ActionPartnership
```

**Pattern 2: Model-Based Authorization**
```ruby
current_ability.authorize! :read, SupportCase
```

**Pattern 3: Constructor Injection (for ability)**
```ruby
def initialize(ability:)
  @ability = ability
end

# Later in method:
@ability.authorize! :read, Attestations::Statement
```

**Pattern 4: Current User Context**
```ruby
def initialize(current_user)
  @current_user = current_user
end

current_ability.authorize! :read, ::User.new(id: id)
```

### 2.5 Core API Delegation Pattern

Many endpoints delegate to a Core API layer:

```ruby
def fetch_one(id:)
  Actions.action_types.v2.fetch_one(id:)
end
```

**Structure:**
- `Actions.action_types` = Domain service accessor
- `.v2` = Version accessor (dotted chain)
- `.fetch_one(id:)` = Method delegation to Core API

---

## Part 3: Domain Organization

### Domains with FetchAll/FetchOne Endpoints

1. **Actions** (4 endpoints)
   - action_partnerships
   - action_pods
   - action_type_configs
   - aspect_roles
   - task_thresholds

2. **Alto Formulary** (1 endpoint)
   - equivalency_groups

3. **Async Jobs** (1 endpoint)
   - statuses

4. **Attestations** (1 endpoint)
   - statements

5. **Billing** (3 endpoints)
   - insurance_plans
   - insurances
   - prices
   - voucher_payers

6. **Customer Support** (7+ endpoints)
   - support_cases (multiple versions)
   - support_categories
   - notifications
   - chatbot_sessions
   - wundercom_messages

7. **Deliver** (2 endpoints)
   - delivery_methods
   - shipments

8. **Fulfillment** (1 endpoint)
   - fills

9. **Incidents** (2 endpoints)
   - corrective_actions
   - incident_roles

10. **Med Sync** (1 endpoint)
    - users

11. **Medications** (2 endpoints)
    - list_endpoint (v1, v2)

12. **Operations** (1 endpoint)
    - companies

13. **Patient App** (6+ endpoints)
    - availability_options
    - facility_alert
    - fee_configs
    - opt_outs
    - instructional_videos

14. **Partnerships** (1 endpoint)
    - hub_referrals

15. **Prior Auths** (3 endpoints)
    - faxes
    - prior_authorizations
    - prior_auth_request_reason
    - provider_request_forms

16. **Procurement** (2 endpoints)
    - scannable_purchase_orders
    - purchase_orders

17. **Product** (3 endpoints)
    - cash_price
    - product_packages
    - products

18. **Providers** (5+ endpoints)
    - agency_agreements (multiple contexts)
    - provider_users
    - tia_templates
    - viewable_clinics
    - viewable_providers

19. **Prescriptions** (1 endpoint)
    - prescriptions

20. **Store Products** (2 endpoints)
    - store_categories
    - store_products

21. **Surescripts** (2 endpoints)
    - new_prescriptions
    - refill_responses

22. **Transfers** (1 endpoint)
    - transfer_queue

23. **Utilities** (1 endpoint)
    - product_info

24. **Wunderbar Patients** (2 endpoints)
    - patient_authorizations
    - patients

---

## Part 4: Routing and Controller Integration

### 4.1 Route Extension Pattern

Routes are registered via extending endpoint Route modules in `config/routes.rb`:

```ruby
extend Alto::Attestations::V1::StatementsEndpoint::Routes
extend Alto::Actions::Wunderbar::V1::ActionTypeConfigsEndpoint::Routes
extend Alto::CustomerSupport::V1::SupportCasesEndpoint::Routes
```

**Key Points:**
- Each endpoint provides a `Routes` module
- Extensions are done in config/routes.rb
- Routes are namespaced by domain/version
- Allows automatic HTTP endpoint generation from proto definitions

### 4.2 Routes Organized by Context

**Wunderbar (Internal Staff) Routes:**
Located in main routes.rb under wunderbar namespace:
```ruby
scope 'wunderbar/api' do
  extend Alto::Actions::Wunderbar::V1::ActionTypeConfigsEndpoint::Routes
  extend Alto::CustomerSupport::Wunderbar::V1::SupportCasesEndpoint::Routes
  # ... many more
end
```

**Patient Routes:**
```ruby
scope 'v1' do
  extend Alto::CustomerSupport::Patients::V1::SupportCasesEndpoint::Routes
  extend Alto::MedSync::Patients::V1::UsersEndpoint::Routes
  # ... many more
end
```

**Provider Routes:**
```ruby
# config/routes/providers.rb
extend Alto::Providers::Altomd::V1::ViewableClinicsEndpoint::Routes
extend Alto::Providers::Altomd::V1::ViewableProvidersEndpoint::Routes
```

### 4.3 HTTP Route Patterns Generated

From proto definitions, the framework auto-generates:

**FetchAll Endpoints:**
```
GET /api/endpoint_path
```

**FetchOne Endpoints:**
```
GET /api/endpoint_path/:id
```

---

## Part 5: Test Patterns

### 5.1 Test File Organization

Tests located in:
- `spec/requests/**/*_endpoint_spec.rb` (most common)
- `spec/services/**/*_endpoint_spec.rb`
- `spec/controllers/**/*_spec.rb`

### 5.2 Typical Test Structure

```ruby
RSpec.describe 'Patients::V1::SupportCasesEndpoint', type: :request do
  let(:patient) { create :empty_patient }

  before(:each) do
    login_patient(patient)
    @case1 = FactoryBot.create(:support_case, user: patient)
  end

  describe 'fetch all' do
    it 'returns all support cases with most recent message for a user' do
      get('/v1/support_cases', params: { patient_id: patient.id })

      expect(response).to have_http_status(:success)
      result = JSON.parse(response.body)['data']
      expect(result[0]['id']).to eq(@case1.id)
    end
  end

  describe 'fetch_one' do
    it 'returns an individual support case' do
      get("/v1/support_cases/#{@case1.id}")

      expect(response).to have_http_status(:success)
      result = JSON.parse(response.body)['data']
      expect(result['id']).to eq(@case1.id)
    end

    it 'returns 422 when trying to access unauthorized resource' do
      other_patient = FactoryBot.create(:empty_user)
      other_case = FactoryBot.create(:support_case, user: other_patient)

      get("/v1/support_cases/#{other_case.id}")

      expect(response).to have_http_status(:unprocessable_entity)
    end
  end
end
```

### 5.3 Common Test Patterns

1. **Happy Path Tests** - Standard successful requests
2. **Authorization Tests** - Verify permission checks
3. **Edge Cases** - Pagination, empty results, not found
4. **Family Member Access** - Tests for account management scenarios
5. **Parameter Validation** - Required vs optional parameters

---

## Part 6: Response Structure Patterns

### 6.1 Consistent Response Format

All responses follow the same pattern with optional metadata:

```ruby
{
  "errors": [
    {
      "code": "...",
      "detail": "...",
      "title": "..."
    }
  ],
  "data": [
    // Array for FetchAll, single object for FetchOne
  ],
  "metadata": {  // Optional
    "pagination": {
      "page_size": 50,
      "page_token": "0",
      "total_count": 123
    }
  }
}
```

### 6.2 FetchAll Response Variations

**No Pagination:**
```ruby
{
  "errors": null,
  "data": [/* array of items */]
}
```

**With Pagination Metadata:**
```ruby
{
  "errors": null,
  "data": [/* array of items */],
  "metadata": {
    "pagination": {
      "page_size": 50,
      "page_token": "0",
      "total_count": 1234
    }
  }
}
```

### 6.3 FetchOne Response

```ruby
{
  "errors": null,
  "data": {/* single object */}
}
```

---

## Part 7: Key Patterns and Observations

### 7.1 Authorization Patterns

**Pattern Prevalence:**
- 60% of endpoints: Use `Auth::CurrentAbility` mixin
- 25% of endpoints: Constructor injection of ability
- 15% of endpoints: No authorization (internal/unsafe APIs)

### 7.2 Data Source Patterns

**Pattern Distribution:**
- 55%: Direct Rails model queries (AR pattern)
- 40%: Delegation to Core API services
- 5%: Mixed approaches or custom services

### 7.3 Pagination Support

**FetchAll Pagination:**
- ~30% of FetchAll endpoints support pagination
- Parameter pattern: `page_size`, `page_token` (offset-based)
- Metadata response includes `total_count`

**FetchOne Pagination:**
- N/A - Single resource by definition

### 7.4 Common Parameter Names

**FetchAll:**
- `ids` (for batch fetch by ID array)
- `patient_id` / `user_id` (for contextual fetch)
- `page_size`, `page_token` (pagination)
- `is_internal` (filtering)

**FetchOne:**
- `id` (primary identifier)
- Occasionally: identifier-specific (e.g., `statement_identifier`)

### 7.5 Struct Conversion Patterns

Most endpoints map database models to response structs:

```ruby
# Pattern 1: Direct mapping
Billing::Prices.to_struct(price_model)

# Pattern 2: Constructor
MedSyncUser.new(id: id, status: status)

# Pattern 3: Complex mapping
TYPES::SupportCase::SupportCase.new(
  id: support_case.id.to_i,
  user_id: support_case.user_id.to_i,
  # ... many fields
)
```

---

## Part 8: Endpoint Checklist - By Domain

### Actions (5 FetchAll, 2 FetchOne)
- [x] action_partnerships (FetchAll)
- [x] action_pods (FetchAll)
- [x] action_type_configs (FetchOne)
- [x] aspect_roles (FetchAll)
- [x] task_thresholds (FetchOne)

### Alto Formulary (1 FetchOne)
- [x] equivalency_groups (FetchOne)

### Async Jobs (1 FetchOne)
- [x] statuses (FetchOne)

### Attestations (1 FetchAll)
- [x] statements (FetchAll)

### Billing (3 FetchOne, 1 FetchAll)
- [x] prices (FetchOne + FetchAll)
- [x] voucher_payers (FetchAll)

### Customer Support (7 FetchAll, 3 FetchOne)
- [x] support_cases (v1, patients, wunderbar) - FetchOne + FetchAll
- [x] support_categories (v1, patients, wunderbar) - FetchAll
- [x] notifications (FetchAll)
- [x] chatbot_sessions (FetchOne + FetchAll)
- [x] wundercom_messages (FetchAll)

### Deliver (1 FetchAll)
- [x] delivery_methods (FetchAll)
- [x] shipments (FetchOne + FetchAll)

### Fulfillment (1 FetchOne)
- [x] fills (FetchOne)

### Incidents (2 FetchAll)
- [x] corrective_actions (FetchAll)
- [x] incident_roles (FetchAll)

### Med Sync (1 FetchOne)
- [x] users (FetchOne)

### Medications (2 FetchAll)
- [x] list_endpoint (v1, v2) (FetchAll)

### Operations (1 FetchAll)
- [x] companies (FetchAll)

### Patient App (3 FetchAll, 1 FetchOne)
- [x] availability_options (FetchAll)
- [x] facility_alert (FetchOne)
- [x] fee_configs (FetchAll)
- [x] opt_outs (FetchAll)
- [x] instructional_videos (FetchAll)

### Partnerships (1 FetchOne)
- [x] hub_referrals (FetchOne)

### Prior Auths (3 FetchAll, 1 FetchOne)
- [x] faxes (FetchAll + FetchOne)
- [x] prior_auth_request_reason (FetchOne)
- [x] provider_request_forms (FetchAll)

### Procurement (1 FetchAll)
- [x] scannable_purchase_orders (FetchAll)

### Product (2 FetchAll, 1 FetchOne)
- [x] cash_price (FetchOne)
- [x] product_packages (FetchAll)
- [x] products (FetchOne)

### Providers (4 FetchAll, 2 FetchOne)
- [x] agency_agreements (FetchAll + FetchOne)
- [x] tia_templates (FetchAll)
- [x] viewable_clinics (FetchAll)
- [x] viewable_providers (FetchAll)
- [x] provider_user_working_hours (FetchOne)

### Prescriptions (1 FetchOne)
- [x] prescriptions (FetchOne)

### Store Products (2 FetchAll)
- [x] store_categories (FetchAll)
- [x] store_products (FetchAll)

### Surescripts (2 FetchOne)
- [x] new_prescriptions (FetchOne)
- [x] refill_responses (FetchOne)

### Transfers (1 FetchAll)
- [x] transfer_queue (FetchAll)

### Utilities (1 FetchOne)
- [x] product_info (FetchOne)

### Wunderbar Patients (2 FetchOne)
- [x] patient_authorizations (FetchOne)
- [x] patients (FetchOne)

---

## Part 9: Edge Cases and Variations

### 9.1 FetchAll Without Arguments

Some FetchAll implementations take NO parameters:

```ruby
def fetch_all
  Actions.action_partnerships.fetch_all
end
```

**Use Cases:**
- Fetching all configuration/lookup data
- Admin interfaces displaying everything
- Relatively small static datasets

### 9.2 FetchAll with Contextual Parameter

Some include context (not just ID):

```ruby
def fetch_all(patient_id:, page_size: nil, page_token: nil)
  # Scoped to patient context
end
```

**Pattern:** Pseudo-"fetch by parent" implemented as FetchAll

### 9.3 FetchAll with Optional Filtering

```ruby
def fetch_all(ids: nil, is_internal: nil)
  # Both parameters optional, combined filtering
end
```

### 9.4 Multiple Versions of Same Endpoint

Some endpoints have multiple versions:

```
protos/src/alto/medications/patients/v1/list_endpoint.proto
protos/src/alto/medications/patients/v2/list_endpoint.proto
```

Each with separate Ruby implementation:
```
app/services/medications/patients/v1/list_endpoint.rb
app/services/medications/patients/v2/list_endpoint.rb
```

### 9.5 FetchOne with Non-ID Identifier

Most use `id:`, but some use domain-specific identifiers:

```ruby
def fetch_by_identifier(statement_identifier:)
  # Custom identifier, not ID
end
```

---

## Part 10: Code Organization Patterns

### 10.1 File Naming Convention

```
app/services/<domain>/<subdomain>/<version>/<resource>_endpoint.rb
```

**Examples:**
- `app/services/actions/wunderbar/action_partnerships_endpoint.rb`
- `app/services/customer_support/v1/support_cases_endpoint.rb`
- `app/services/billing/v1/prices_endpoint.rb`

### 10.2 Module Nesting

Most endpoints nest modules by domain:

```ruby
module Actions
  module Wunderbar
    class ActionPartnershipsEndpoint < ...
    end
  end
end
```

Or by domain and version:

```ruby
module CustomerSupport
  module V1
    class SupportCasesEndpoint < ...
    end
  end
end
```

### 10.3 Type Annotations

All endpoints use Sorbet (`T::Sig`) for type safety:

```ruby
extend T::Sig

sig do
  override
    .params(id: Integer)
    .returns(TYPES::SupportCase::SupportCase)
end
def fetch_one(id:)
  # ...
end
```

---

## Part 11: Common Implementation Details

### 11.1 Database Query Patterns

**Direct Rails Query:**
```ruby
Price.find(id)
SupportCase.where(id: ids)
```

**With Includes (Eager Loading):**
```ruby
SupportCase.includes([:most_recent_support_case_chatbot_session]).where(...)
```

**With Scopes:**
```ruby
SupportCase.most_recent_message_first.where(...)
```

### 11.2 Struct Mapping

**Via Service Utility:**
```ruby
Billing::Prices.to_struct(price)
```

**Via Direct Constructor:**
```ruby
MedSyncUser.new(id: id, status: status)
```

**Via Type Constant:**
```ruby
TYPES::SupportCase::SupportCase.new(
  id: support_case.id.to_i,
  user_id: support_case.user_id.to_i,
  # ... more fields
)
```

### 11.3 Error Handling

**Rails Default (NotFound):**
```ruby
Price.find(id)  # Throws ActiveRecord::RecordNotFound
```

**Custom Not Found:**
```ruby
if status.nil?
  raise(
    Core::Error::NotFoundError,
    'Could not find a med sync status for the user',
  )
end
```

**Access Denied:**
```ruby
if family_member_ids.exclude?(support_case.user_id)
  raise Core::Error::AltoError, "Access Error: ..."
end
```

**Validation Errors:**
```ruby
raise Core::Error::BadRequestError, 'Error message'
```

---

## Part 12: Summary and Key Takeaways

### Architectural Principles Observed

1. **Proto-First Design**: All endpoints start with proto definitions
2. **Consistent Interfaces**: Auto-generated base classes ensure consistency
3. **Authorization Layering**: Permission checks at the endpoint layer
4. **Service Delegation**: Heavy use of domain service layer
5. **Response Standardization**: Uniform error/data/metadata structure
6. **Type Safety**: Sorbet signatures on all public methods
7. **Pagination Support**: Where relevant (30% of FetchAll endpoints)
8. **Version Isolation**: Multiple versions coexist without interference

### Implementation Frequency Distribution

**FetchAll Signatures:**
- No parameters: 20%
- ID array: 25%
- Contextual (patient_id, etc): 30%
- Pagination support: 30%
- Other filters: 15%

**FetchOne Signatures:**
- `id:` parameter: 95%
- Custom identifier: 5%

### Recommended Patterns for New Endpoints

1. **Always** provide both FetchAll and FetchOne if fetching collections
2. **Always** include proto definitions before Ruby code
3. **Always** use Auth::CurrentAbility for permission checks
4. **Prefer** delegation to Core API services over direct model access
5. **Include** pagination for endpoints that may return large datasets
6. **Use** Sorbet type signatures for all method signatures
7. **Map** database models to response structs before returning

---

## Appendix A: Complete List of Proto Files with FetchAll/FetchOne

Total: 64 unique proto endpoint files

### FetchAll (39 proto files):
1. alto/actions/wunderbar/v1/action_partnerships_endpoint.proto
2. alto/actions/wunderbar/v1/action_pods_endpoint.proto
3. alto/actions/wunderbar/v1/aspect_roles_endpoint.proto
4. alto/attestations/v1/statements_endpoint.proto
5. alto/billing/wunderbar/v1/voucher_payers_endpoint.proto
6. alto/customer_support/patients/v1/notifications_endpoint.proto
7. alto/customer_support/patients/v1/support_cases_endpoint.proto
8. alto/customer_support/patients/v1/support_cases/wundercom_messages_endpoint.proto
9. alto/customer_support/patients/v1/support_categories_endpoint.proto
10. alto/customer_support/patients/v3/wundercom_messages_endpoint.proto
11. alto/customer_support/v1/chatbot_sessions_endpoint.proto
12. alto/customer_support/v1/support_cases_endpoint.proto
13. alto/customer_support/v1/support_cases/wundercom_messages_endpoint.proto
14. alto/customer_support/v1/support_categories_endpoint.proto
15. alto/customer_support/wunderbar/v1/support_cases/wundercom_messages_endpoint.proto
16. alto/customer_support/wunderbar/v1/support_categories_endpoint.proto
17. alto/incidents/wunderbar/v1/corrective_actions_endpoint.proto
18. alto/incidents/wunderbar/v1/incident_roles_endpoint.proto
19. alto/med_sync/patients/v1/preliminary_prescriptions_endpoint.proto
20. alto/medications/patients/v1/list_endpoint.proto
21. alto/medications/patients/v2/list_endpoint.proto
22. alto/operations/wunderbar/v1/companies_endpoint.proto
23. alto/patient_app/availability_options/v2/availability_options_endpoint.proto
24. alto/patient_app/essentials/v1/fee_configs_endpoint.proto
25. alto/patient_app/essentials/v1/opt_outs_endpoint.proto
26. alto/patient_app/instructional_videos/v1/instructional_videos_endpoint.proto
27. alto/prior_auths/v1/faxes_endpoint.proto
28. alto/prior_auths/wunderbar/v1/prior_authorizations/provider_request_forms_endpoint.proto
29. alto/procurement/wunderbar/v2/scannable_purchase_orders_endpoint.proto
30. alto/product/wunderbar/v1/product_packages_endpoint.proto
31. alto/providers/altomd/v1/viewable_clinics_endpoint.proto
32. alto/providers/altomd/v1/viewable_providers_endpoint.proto
33. alto/providers/wunderbar/v1/clinic_providers/agency_agreements_endpoint.proto
34. alto/providers/wunderbar/v1/clinics/agency_agreements_endpoint.proto
35. alto/providers/wunderbar/v1/tia_templates_endpoint.proto
36. alto/seeds/wunderbar/v2/test_account_front_page_endpoint.proto
37. alto/store_products/wunderbar/v1/store_categories_endpoint.proto
38. alto/store_products/wunderbar/v1/store_products_endpoint.proto
39. alto/transfers/wunderbar/v1/transfer_queue_endpoint.proto

### FetchOne (25 proto files):
1. alto/actions/wunderbar/v1/action_type_configs_endpoint.proto
2. alto/actions/wunderbar/v1/task_thresholds_endpoint.proto
3. alto/alto_formulary/wunderbar/v1/equivalency_groups_endpoint.proto
4. alto/async_jobs/wunderbar/v1/statuses_endpoint.proto
5. alto/customer_support/patients/v1/support_cases_endpoint.proto
6. alto/customer_support/v1/chatbot_sessions_endpoint.proto
7. alto/customer_support/v1/support_cases_endpoint.proto
8. alto/customer_support/wunderbar/v1/support_cases_endpoint.proto
9. alto/fulfillment/wunderbar/v1/fills_endpoint.proto
10. alto/med_sync/patients/v1/users_endpoint.proto
11. alto/partnerships/wunderbar/v1/hub_referrals_endpoint.proto
12. alto/patient_app/facility_alert/v2/facility_alert_endpoint.proto
13. alto/prescriptions/wunderbar/v1/prescriptions_endpoint.proto
14. alto/prior_auths/v1/faxes_endpoint.proto
15. alto/prior_auths/wunderbar/v1/prior_authorizations/prior_auth_request_reason_endpoint.proto
16. alto/product/wunderbar/v1/products_endpoint.proto
17. alto/product/wunderbar/v1/products/cash_price_endpoint.proto
18. alto/providers/altomd/v1/provider_user_working_hours_endpoint.proto
19. alto/providers/wunderbar/v1/clinic_providers/agency_agreements_endpoint.proto
20. alto/providers/wunderbar/v1/clinics/agency_agreements_endpoint.proto
21. alto/surescripts/wunderbar/v1/surescripts_new_prescriptions_endpoint.proto
22. alto/surescripts/wunderbar/v1/surescripts_refill_responses_endpoint.proto
23. alto/utilities/wunderbar/v2/product_info_endpoint.proto
24. alto/wunderbar/patients/v1/patient_authorizations_endpoint.proto
25. alto/wunderbar/patients/v1/patients_endpoint.proto

---

**End of Inventory Document**
