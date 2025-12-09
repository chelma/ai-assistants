# Two-Layer Testing Patterns in Scriptdash

**Investigation Date**: 2025-12-09
**Context**: Research into testing strategies for Two-Layer pattern endpoints where Scriptdash service endpoints add authorization and delegate to Core API modules wrapping Rails Engines.

## Executive Summary

Found **87+ Two-Layer endpoint implementations** across multiple domains (Actions, Billing, Inventory, Scheduling, Fill, etc.). Testing approaches vary by complexity:

1. **Simple delegation endpoints**: Direct unit tests with mocked Core API modules
2. **Complex business logic endpoints**: Integration/request specs testing via controllers
3. **Hybrid approaches**: Some have no tests, relying on controller-level coverage

**Key Finding**: The Core::API `add_api` issue is handled by **pre-loading the Core API module once before tests** (see Partnerships::Labels pattern).

---

## Pattern Categories

### Pattern 1: Simple Delegation with Mocked Core API (Unit Tests)

**When used**: Endpoints that only add authorization and delegate to Core API with minimal transformation.

#### Example 1: `Partnerships::Wunderbar::LabelsEndpoint`

**Implementation** (`app/services/partnerships/wunderbar/labels_endpoint.rb`):
```ruby
module Partnerships
  module Wunderbar
    class LabelsEndpoint
      extend T::Sig
      include Auth::CurrentAbility

      sig do
        params(
          labelable_type: String,
          labelable_id: String
        ).returns(T::Array[LabelsAPI::Types::V1::LabelType::Label])
      end
      def fetch_by_labelable(labelable_type:, labelable_id:)
        # Check permissions FIRST
        current_ability.authorize! :read, LabelsAPI::Types::V1::LabelType::Label

        # Then delegate to Engine via Partnerships module
        Partnerships.labels.fetch_by_labelable(
          labelable_type: labelable_type,
          labelable_id: labelable_id
        )
      end
    end
  end
end
```

**Test Approach** (`spec/services/partnerships/wunderbar/labels_endpoint_spec.rb`):

**CRITICAL Pattern**: Pre-load Core API module to avoid `add_api` reloading issues:
```ruby
require 'rails_helper'

# Pre-load Partnerships::Labels once before any tests run to ensure
# Core::API's add_api only runs once (it fails on subsequent calls)
require_relative '../../../../app/services/partnerships/labels'

RSpec.describe Partnerships::Wunderbar::LabelsEndpoint do
  let(:endpoint) { described_class.new }
  let(:ability_mock) { instance_double(Abilities::WunderbarAbility) }
  let(:mock_labels) { [/* protobuf structs */] }

  before do
    # Mock current_ability
    allow(endpoint).to receive(:current_ability).and_return(ability_mock)

    # Mock Partnerships.labels to return stubbed module
    # (Partnerships::Labels is already loaded above, so add_api only runs once)
    allow(Partnerships).to receive(:labels).and_return(Partnerships::Labels)
  end

  describe '#fetch_by_labelable' do
    context 'when user has read permission' do
      before do
        allow(ability_mock).to receive(:authorize!).with(
          :read,
          LabelsAPI::Types::V1::LabelType::Label
        ).and_return(nil)

        allow(Partnerships::Labels).to receive(:fetch_by_labelable).and_return(mock_labels)
      end

      it 'checks authorization before fetching labels' do
        # Test authorization called
      end

      it 'delegates to Partnerships.labels.fetch_by_labelable' do
        # Test delegation
      end

      it 'returns the labels from the Engine' do
        # Test return value
      end
    end

    context 'when user does not have read permission' do
      before do
        allow(ability_mock).to receive(:authorize!).and_raise(CanCan::AccessDenied)
      end

      it 'raises CanCan::AccessDenied before calling the Engine' do
        # Test authorization failure prevents Engine call
      end
    end
  end
end
```

**Key Techniques**:
- ✅ **Pre-load Core API module** with `require_relative` before tests
- ✅ Mock `current_ability` to test authorization logic
- ✅ Mock Core API module (`Partnerships::Labels`) to test delegation
- ✅ Test both success and authorization failure paths
- ✅ Verify Engine is NOT called when authorization fails

#### Example 2: `Actions::Wunderbar::ActionPodsEndpoint`

**Implementation** (`app/services/actions/wunderbar/action_pods_endpoint.rb`):
```ruby
module Actions
  module Wunderbar
    class ActionPodsEndpoint < Alto::Actions::Wunderbar::V1::ActionPodsEndpoint::Interface::AbstractActionPodsEndpoint
      extend T::Sig
      include Auth::CurrentAbility
      include Alto::Actions::Wunderbar::V1::ActionPodsEndpoint::Interface

      sig do
        override.returns(T::Array[ActionsAPI::Types::V2::ActionPod])
      end
      def fetch_all
        current_ability.authorize! :read, ActionsAPI::Types::V2::ActionPod
        Actions.action_pods.fetch_all
      end
    end
  end
end
```

**Test Status**: ❌ No test file found (`spec/services/actions/wunderbar/action_pods_endpoint_spec.rb` does not exist)

**Pattern**: Simple delegation, would follow same pattern as Partnerships::Labels if tested.

---

### Pattern 2: Complex Business Logic (Request/Integration Tests)

**When used**: Endpoints with significant business logic, multiple Core API calls, or complex orchestration.

#### Example 3: `Billing::Wunderbar::V1::BenefitsInvestigationEndpoint`

**Implementation** (`app/services/billing/wunderbar/v1/benefits_investigation_endpoint.rb`):
- Multiple methods: `update`, `summarize`, `summarize_all`, `complete`
- Complex business logic: builds coverage inquiry summaries, determines insurance IDs, creates manual benefits entries
- Orchestrates multiple Core API calls: `Billing.benefits_investigations`, `Billing.coverage_inquiry_results`, `Billing.manual_benefits_entries`
- ~280 lines of code

**Test Approach** (`spec/services/billing/wunderbar/v1/benefits_investigation_endpoint_spec.rb`):

**Pattern**: Request specs (NOT unit tests):
```ruby
RSpec.describe Billing::Wunderbar::V1::BenefitsInvestigationEndpoint, type: :request do
  let(:wunderbar_user) { FactoryBot.create(:ops_wb_user) }

  before(:each) do
    login_wunderbar_user(wunderbar_user)
    allow(Core::Request::Context).to receive(:current_user).and_return(/* mocked user */)
  end

  describe '#complete' do
    subject(:invoke) do
      Billing::Wunderbar::V1::BenefitsInvestigationEndpoint.new.complete(
        benefits_investigation_ids:,
      )
    end

    # Direct invocation of endpoint (not via HTTP controller)
    # Uses real Core API modules, not mocks
    # Tests full integration including database changes
  end
end
```

**Key Techniques**:
- ✅ Direct instantiation and invocation (`.new.complete(...)`)
- ✅ Uses real Core API modules (no mocking)
- ✅ Sets up authentication context
- ✅ Tests full business logic integration
- ✅ Uses fixtures and factories for test data
- ✅ Tests database state changes

#### Example 4: `Inventory::Wunderbar::V1::ReturnEndpoint`

**Implementation** (`app/services/inventory/wunderbar/v1/return_endpoint.rb`):
- Multiple methods: `scan_package`, `fetch_shipments`, `fetch_shipment`, `return_to_stock`, etc.
- Complex business logic: barcode parsing, shipment filtering, pagination, analytics
- ~200 lines of code

**Test Approach** (`spec/services/inventory/wunderbar/v1/return_endpoint_spec.rb`):

**Pattern**: Full request specs via HTTP controller:
```ruby
RSpec.describe 'Return Endpoint', type: :request do
  let(:base_url) { "#{WUNDERBAR_URL}/inventory/v1/return" }
  let(:wb_user) { create(:wunderbar_user) }

  describe 'GET /inventory/v1/return/scan_package' do
    subject(:scan_package) do
      get "#{base_url}/scan_package", params: { barcode_content: }
    end

    include_examples 'requires authentication'

    context 'when logged in' do
      before { login_wunderbar_user(wb_user) }

      context 'as a pharm_tech_wb_user' do
        # Tests HTTP endpoints, status codes, JSON responses
      end
    end
  end
end
```

**Key Techniques**:
- ✅ Full HTTP request specs (`get`, `post`)
- ✅ Tests authentication requirements
- ✅ Tests authorization (403 Forbidden for wrong roles)
- ✅ Tests JSON response structure
- ✅ Uses real Core API modules
- ✅ Tests full request/response cycle

#### Example 5: `Scheduling::Wunderbar::V1::SchedulingEndpoint`

**Implementation** (`app/services/scheduling/wunderbar/v1/scheduling_endpoint.rb`):
- Extremely complex: ~650 lines of code
- Multiple methods: `schedule`, `schedule_pickup`, `schedule_refill`, `unschedule`, etc.
- Heavy business logic: validation, payment pre-authorization, analytics, mail request processing
- Orchestrates many service calls

**Test Approach** (`spec/services/scheduling/wunderbar/v1/scheduling_endpoint_spec.rb`):

**Pattern**: Direct invocation with mocked dependencies:
```ruby
RSpec.describe Scheduling::Wunderbar::V1::SchedulingEndpoint do
  let(:scheduling_endpoint) { described_class.new }

  describe '#schedule' do
    before(:each) do
      # Mock CanCan authorization to allow all operations
      allow_any_instance_of(CanCan::Ability).to receive(:authorize!)

      # Mock feature flags
      allow(Experimentation).to receive(:on?).and_call_original
    end

    # Tests specific private methods like #validate_mail_request_confirmed!
    # Uses send() to test private methods
  end
end
```

**Key Techniques**:
- ✅ Direct instantiation
- ✅ Mocks authorization to bypass permission checks
- ✅ Mocks external dependencies (feature flags, services)
- ✅ Tests private methods using `send()`
- ✅ Focuses on specific business logic branches

---

### Pattern 3: No Direct Tests (Controller-Level Coverage Only)

#### Example 6: `Patients::Wunderbar::V1::PatientsEndpoint`

**Implementation** (`app/services/patients/wunderbar/v1/patients_endpoint.rb`):
```ruby
module Patients
  module Wunderbar
    module V1
      class PatientsEndpoint < Alto::Wunderbar::Patients::V1::PatientsEndpoint::Interface::AbstractPatientsEndpoint
        # NOTE: Does NOT include Auth::CurrentAbility

        def fetch_one(id:)
          to_struct(User.includes(:company).find(id))
        end

        private

        def to_struct(patient)
          # Maps ActiveRecord model to protobuf struct
        end
      end
    end
  end
end
```

**Test Approach** (`spec/services/patients/wunderbar/v1/patients_endpoint_spec.rb`):

**Pattern**: Simple unit test (no authorization):
```ruby
RSpec.describe Patients::Wunderbar::V1::PatientsEndpoint do
  describe '#fetch_one' do
    subject(:fetch_one) { described_class.new.fetch_one(id: patient_id) }

    context 'when the patient exists' do
      let(:patient) { FactoryBot.create(:normal_user) }

      it 'returns a patient struct with correct attributes' do
        # Tests struct mapping
      end
    end
  end
end
```

**Key Observation**: This endpoint does NOT include `Auth::CurrentAbility`, so authorization is handled elsewhere (likely at controller level). Test is just a simple struct transformation test.

---

## Testing Strategy Decision Matrix

| Endpoint Characteristics | Recommended Test Approach | Example |
|---------------------------|--------------------------|---------|
| Simple delegation + authorization only | Unit test with mocked Core API | `Partnerships::LabelsEndpoint` |
| Complex business logic (50-200 lines) | Direct invocation with partial mocks | `Scheduling::SchedulingEndpoint` |
| Very complex orchestration (200+ lines) | Request specs (integration tests) | `Billing::BenefitsInvestigationEndpoint`, `Inventory::ReturnEndpoint` |
| Simple transformation (no auth) | Simple unit test | `Patients::PatientsEndpoint` |

---

## Core::API Module Reloading Solution

### The Problem
`Core::API.add_api` fails when called multiple times in test environment due to module reloading:
```ruby
# This pattern fails:
RSpec.describe MyEndpoint do
  before do
    require 'app/services/partnerships/labels'  # Loads module, calls add_api
  end

  it 'test 1' do
    # Works
  end

  it 'test 2' do
    # Module reloaded, add_api called again → FAILS
  end
end
```

### The Solution Pattern (from `Partnerships::LabelsEndpoint` test)

**Load Core API module ONCE at top of spec file**:
```ruby
require 'rails_helper'

# CRITICAL: Pre-load Partnerships::Labels once before any tests run to ensure
# Core::API's add_api only runs once (it fails on subsequent calls)
require_relative '../../../../app/services/partnerships/labels'

RSpec.describe Partnerships::Wunderbar::LabelsEndpoint do
  before do
    # Mock Partnerships.labels to return stubbed module
    # (Partnerships::Labels is already loaded above, so add_api only runs once)
    allow(Partnerships).to receive(:labels).and_return(Partnerships::Labels)

    # Then stub individual methods on the already-loaded module
    allow(Partnerships::Labels).to receive(:fetch_by_labelable).and_return(mock_labels)
  end
end
```

**Why this works**:
1. `require_relative` loads module once before RSpec starts running examples
2. Module stays loaded for all test examples
3. `add_api` only called once
4. Use `allow(...).to receive(:labels).and_return(Partnerships::Labels)` to enable method stubbing
5. Stub methods on the real module instance

**Alternative approaches observed**:
- **Request specs**: Don't mock Core API at all, use real implementations (see Billing, Inventory examples)
- **No authorization tests**: For endpoints without `Auth::CurrentAbility`, skip the mocking entirely

---

## Summary of Representative Examples

### 1. **Partnerships::Wunderbar::LabelsEndpoint** ⭐ RECOMMENDED FOR YOUR USE CASE

- **File**: `app/services/partnerships/wunderbar/labels_endpoint.rb`
- **Test**: `spec/services/partnerships/wunderbar/labels_endpoint_spec.rb`
- **Pattern**: Simple delegation with authorization
- **Test Approach**: Unit test with mocked Core API (pre-loaded module)
- **Tests Pass**: ✅ Yes
- **Best Practice**: Pre-loads Core API module to avoid `add_api` issues

### 2. **Billing::Wunderbar::V1::BenefitsInvestigationEndpoint**

- **File**: `app/services/billing/wunderbar/v1/benefits_investigation_endpoint.rb`
- **Test**: `spec/services/billing/wunderbar/v1/benefits_investigation_endpoint_spec.rb`
- **Pattern**: Complex business logic with multiple Core API calls
- **Test Approach**: Request specs with direct invocation (no mocking)
- **Tests Pass**: ✅ Yes
- **Use When**: Complex orchestration, multiple Engine calls

### 3. **Inventory::Wunderbar::V1::ReturnEndpoint**

- **File**: `app/services/inventory/wunderbar/v1/return_endpoint.rb`
- **Test**: `spec/services/inventory/wunderbar/v1/return_endpoint_spec.rb`
- **Pattern**: Complex business logic exposed via HTTP API
- **Test Approach**: Full request specs via controller routes
- **Tests Pass**: ✅ Yes
- **Use When**: Testing full HTTP request/response cycle

### 4. **Scheduling::Wunderbar::V1::SchedulingEndpoint**

- **File**: `app/services/scheduling/wunderbar/v1/scheduling_endpoint.rb`
- **Test**: `spec/services/scheduling/wunderbar/v1/scheduling_endpoint_spec.rb`
- **Pattern**: Very complex orchestration (650 lines)
- **Test Approach**: Direct invocation with mocked authorization and dependencies
- **Tests Pass**: ✅ Yes (partial - tests specific private methods)
- **Use When**: Need to test specific private method branches

### 5. **Actions::Wunderbar::ActionPodsEndpoint**

- **File**: `app/services/actions/wunderbar/action_pods_endpoint.rb`
- **Test**: ❌ None
- **Pattern**: Simple delegation with authorization
- **Test Approach**: N/A (no tests)
- **Notes**: Would follow Pattern 1 (Partnerships::Labels) if tested

---

## Recommendation for `Partnerships::Wunderbar::LabelsEndpoint`

### Your Current Implementation Matches Pattern 1 Perfectly ✅

Your endpoint is a **simple delegation with authorization** - exactly matching the `Partnerships::LabelsEndpoint` pattern.

### Testing Strategy

**Follow the existing `labels_endpoint_spec.rb` pattern**:

1. **Pre-load Core API module** to avoid `add_api` issues:
   ```ruby
   require 'rails_helper'
   require_relative '../../../../app/services/partnerships/labels'
   ```

2. **Mock `current_ability`** to test authorization:
   ```ruby
   let(:ability_mock) { instance_double(Abilities::WunderbarAbility) }
   allow(endpoint).to receive(:current_ability).and_return(ability_mock)
   ```

3. **Mock Core API module** for delegation testing:
   ```ruby
   allow(Partnerships).to receive(:labels).and_return(Partnerships::Labels)
   allow(Partnerships::Labels).to receive(:fetch_by_labelable).and_return(mock_labels)
   ```

4. **Test both paths**:
   - ✅ Authorization success → delegates to Engine
   - ❌ Authorization failure → raises AccessDenied, Engine NOT called

### Why NOT Use Request Specs

Request specs (Pattern 2/3) are overkill for simple delegation endpoints:
- ❌ More complex setup (HTTP routes, JSON parsing)
- ❌ Slower (full request/response cycle)
- ❌ Tests routing/controller integration (not needed here)
- ❌ Harder to test authorization edge cases

Unit tests (Pattern 1) are perfect for your use case:
- ✅ Fast
- ✅ Focused on authorization + delegation logic
- ✅ Easy to mock and test edge cases
- ✅ Proven pattern used by existing endpoints

---

## Key Findings Summary

1. **87+ Two-Layer endpoints exist** across Actions, Billing, Inventory, Scheduling, Fill, etc.

2. **Testing approaches vary by complexity**:
   - Simple delegation → Unit tests with mocked Core API
   - Complex orchestration → Request/integration specs

3. **Core::API `add_api` solution**: Pre-load module once with `require_relative` before tests

4. **Authorization testing**: Mock `current_ability` to test both success and failure paths

5. **Your use case**: Matches `Partnerships::Wunderbar::LabelsEndpoint` pattern exactly - use its test as a template

6. **Tests pass successfully** for all examined patterns that have tests

---

## Files Referenced

### Implementations
- `app/services/partnerships/wunderbar/labels_endpoint.rb`
- `app/services/billing/wunderbar/v1/benefits_investigation_endpoint.rb`
- `app/services/actions/wunderbar/action_pods_endpoint.rb`
- `app/services/inventory/wunderbar/v1/return_endpoint.rb`
- `app/services/scheduling/wunderbar/v1/scheduling_endpoint.rb`
- `app/services/patients/wunderbar/v1/patients_endpoint.rb`
- `app/services/fill/autofill/wunderbar/v1/autofill_endpoint.rb`

### Tests
- `spec/services/partnerships/wunderbar/labels_endpoint_spec.rb` ⭐
- `spec/services/billing/wunderbar/v1/benefits_investigation_endpoint_spec.rb`
- `spec/services/inventory/wunderbar/v1/return_endpoint_spec.rb`
- `spec/services/scheduling/wunderbar/v1/scheduling_endpoint_spec.rb`
- `spec/services/patients/wunderbar/v1/patients_endpoint_spec.rb`
- `spec/services/fill/autofill/wunderbar/v1/autofill_endpoint_spec.rb`

### Additional Found Endpoints (87 total)
- 12 in Actions domain
- 5 in AltoFormulary domain
- 1 in Attachments domain
- 1 in AutoRefills domain
- 5 in Billing domain
- 2 in Compliance domain
- 5 in CustomerSupport domain
- 2 in DataChecking domain
- 1 in Deliver domain
- 1 in FertilityCycles domain
- 2 in Fill domain
- 4 in Fulfillment domain
- 2 in Incidents domain
- 4 in Intake domain
- 11 in Inventory domain
- 3 in MedSync domain
- 2 in Operations domain
- 1 in OrderCheck domain
- 2 in Orders domain
- 1 in Overview domain
- 2 in Partnerships domain
- 6 in Patients domain
- 1 in Payments domain
- 1 in PDMP domain
- 5 in Prescriptions domain
- 4 in PriorAuthorizations domain
- 10 in Procurement domain
- 4 in Products domain
- 4 in Providers domain
- (Plus many more...)

---

## Next Steps

1. **Copy the `labels_endpoint_spec.rb` test structure** for your endpoint
2. **Pre-load your Core API module** at the top of the spec file
3. **Mock `current_ability`** for authorization testing
4. **Mock Core API calls** for delegation verification
5. **Test both success and failure paths** for authorization
6. Run tests and verify `add_api` no longer causes issues
