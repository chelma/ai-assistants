# Plan: 2025-12-08-partnerships-labels-integration

**Workspace**: alto
**Project Root**: /Users/chris.helma/workspace/alto
**Status**: draft
**GitHub Issue**: N/A
**Created**: 2025-12-08

## Problem Statement

Care team engineers currently cannot query labels for resources like deliveries from the partnerships engine, limiting their ability to track and manage partnership-related workflows.

## Acceptance Criteria

- [ ] Care team can query labels for a delivery (or other resource) from partnerships engine
- [ ] Labels are fetched from labels_engine via Core::API integration
- [ ] Scriptdash provides a permission-protected wrapper for frontend access
- [ ] Tests verify the integration works end-to-end

---

## Current State Analysis

### Labels Engine (Existing Infrastructure)
**Location**: `engine-labels/`

The labels engine is fully implemented with:
- **Model**: `engine-labels/app/models/labels_engine/label.rb`
  - Polymorphic association (`labelable_type`, `labelable_id`)
  - Fields: `id`, `name`, `labelable_type`, `labelable_id`, `source`, `created_at`, `updated_at`
  - Unique constraint: `(labelable_type, labelable_id, name)`
  - Kafka event emission on create/destroy

- **API Endpoint**: `engine-labels/app/services/labels_engine/v1/labels_endpoint.rb`
  - **Already implements `fetch_by_labelable(labelable_type:, labelable_id:)`** ✅
  - Returns array of `LabelsAPI::Types::V1::LabelType::Label` structs
  - Also provides: `fetch_one`, `fetch_all`, `add_label`, `remove_label`, `has_label`

- **Generated Client**: `engine-labels/labels_api/lib/labels_api/v1/labels_endpoint/client.rb`
  - Core::API-compatible client with RPC/local switching
  - Method signatures with Sorbet types

**Key finding**: The labels endpoint we need (`fetch_by_labelable`) is already fully implemented! This significantly reduces implementation effort.

### Partnerships Engine (Target Integration Point)
**Location**: `engine-partnerships/`

Current state:
- **Models**: Hub referrals, ASPN, Harrow partnerships
- **Existing Core::API patterns**: Uses Core::API to call other engines
  - Example: `engine-partnerships/app/services/partnerships_engine/patients/addresses.rb`
    ```ruby
    module PartnershipsEngine
      module Patients
        module Addresses
          include Core::API
          add_api PatientsAPI::V1::AddressesEndpoint::Client
        end
      end
    end
    ```
- **Dependencies**: Currently includes `patients_api`, `billing_api`, `comms_api` - but NOT `labels_api` or `labels_engine`

**Gap**: Partnerships engine does not yet have labels_engine/labels_api dependencies configured.

### Scriptdash Integration Pattern
**Location**: `scriptdash/`

Standard pattern for wrapping engine APIs:
1. **Service module with Core::API**: `scriptdash/app/services/{domain}/{resource}.rb`
   - Includes `Core::API`
   - Calls `add_api(ClientClass)` to expose methods
   - Sets endpoint: `self.resource_endpoint = EngineClass`

2. **Example**: `scriptdash/app/services/actions/task_qualifications.rb`
   ```ruby
   module Actions
     module TaskQualifications
       extend T::Sig
       include Core::API

       module V1
         include Core::API
         extend T::Sig

         add_api ActionsAPI::V1::TaskQualificationsEndpoint::Client
         self.task_qualifications_endpoint = ActionsEngine::TaskQualifications::Endpoint
       end

       sig { returns(T.class_of(V1)) }
       def self.v1
         V1
       end
     end
   end
   ```

3. **Permissions**: Handled via `APIController` which:
   - Authenticates via JWT tokens
   - Sets `Core::Request::Context.current_user`
   - Uses CanCan abilities for authorization

4. **Initializer wiring**: `scriptdash/config/initializers/{engine}_engine.rb`
   - Sets `base_controller = APIController`
   - Configures endpoint assignments

### Dependency Management (alto-workspace)
**Location**: `alto-workspace/`

Dependencies are managed via alto-workspace configuration:
- Repository configs: `alto-workspace/config/repositories/`
- Use `alto bump scriptdash partnerships` to update dependencies
- Generate Sorbet types: `bin/tapioca gem labels_api labels_engine`

## Proposed Solution

**High-level approach**: Use the existing `labels_engine` infrastructure and integrate it into `partnerships_engine` using the Core::API pattern, then expose it to Scriptdash with permissions.

### Architecture Flow
```
Care Team (Frontend)
    ↓ HTTP + JWT
Scriptdash Wrapper (app/services/partnerships/labels.rb)
    ↓ Authorization check (CanCan)
PartnershipsEngine Labels Module (app/services/partnerships_engine/labels.rb)
    ↓ Core::API delegation (local or RPC)
LabelsEngine Endpoint (fetch_by_labelable)
    ↓ ActiveRecord query
Labels Table (polymorphic)
```

### Key Design Decisions

1. **Use existing `fetch_by_labelable` endpoint**: No need to create new proto or endpoint - labels_engine already has exactly what we need

2. **Core::API integration at partnerships level**: Create a labels module in partnerships_engine that delegates to labels_engine, following the same pattern as `patients/addresses.rb`

3. **Scriptdash wrapper pattern**: Follow the standard two-layer pattern (Scriptdash → Engine) for permission enforcement

4. **Dependency via alto-workspace**: Add labels dependencies to partnerships_engine through alto-workspace config (not direct gemspec edits)

## Implementation Steps

### Phase 1: Add Dependencies to Partnerships Engine

**Reference**: `references/alto-workspace-quick-reference.md` - Dependency Management section

1. **Update alto-workspace configuration**
   - File: `alto-workspace/config/repositories/engine-partnerships.yml`
   - Add to `alto_ruby_deps` section:
     ```yaml
     - name: labels
       version: '~> 1.0'
       gems:
         - labels_api
         - labels_engine
     ```
   - Commit change to alto-workspace

2. **Regenerate dependency files and install**
   - Command: `cd alto-workspace && alto generate deps engine-partnerships`
   - Then: `cd engine-partnerships && bundle install`
   - Generate Sorbet types: `bin/tapioca gem labels_api labels_engine`

3. **Verify Sorbet type checking**
   - Command: `cd engine-partnerships && bundle exec srb tc`
   - Should show: "No errors! Great job."

### Phase 2: Create Core::API Module in Partnerships Engine

**Reference**: `references/scriptdash_patterns.md` - Pattern 6.1 (Core API Module Structure)

4. **Create labels module with Core::API integration**
   - File: `engine-partnerships/app/services/partnerships_engine/labels.rb`
   - **Pattern 6.1**: Core API Module Structure [CRITICAL]
   - Implementation:
     ```ruby
     # typed: strict

     module PartnershipsEngine
       # @owners { team: care, domain: partnerships }
       module Labels
         extend T::Sig
         include Core::API

         # Add labels_api client with local/RPC switching
         add_api LabelsAPI::V1::LabelsEndpoint::Client

         # Configure to use labels_engine endpoint locally
         self.labels_endpoint = LabelsEngine::V1::LabelsEndpoint
       end
     end
     ```

5. **Add dotted accessor to PartnershipsEngine**
   - File: `engine-partnerships/lib/partnerships_engine.rb`
   - **Pattern 6.2**: Dotted Accessor Pattern [CRITICAL]
   - Add method:
     ```ruby
     sig { returns(T.class_of(Labels)) }
     def self.labels
       Labels
     end
     ```
   - Enables: `PartnershipsEngine.labels.fetch_by_labelable(...)`

### Phase 3: Set Up Scriptdash Wrapper with Permissions

**Reference**: `references/scriptdash_patterns.md` - Patterns 6.6, 7.1, 7.2

6. **Decide on proto approach**
   - **Option A** (Recommended): Skip Scriptdash proto, use `LabelsAPI` types directly
   - **Option B**: Create Scriptdash proto that imports labels types (Pattern 6.6)
   - **Recommendation**: Use Option A - no need for duplicate proto when labels_api already defines types

7. **Create Scriptdash service module**
   - File: `scriptdash/app/services/partnerships/labels.rb`
   - **Pattern 6.1**: Core API Module Structure [CRITICAL]
   - Implementation:
     ```ruby
     # typed: strict

     module Partnerships
       # @owners { team: care, domain: partnerships }
       module Labels
         extend T::Sig
         include Core::API

         # Delegate to PartnershipsEngine's labels API
         add_api LabelsAPI::V1::LabelsEndpoint::Client
         self.labels_endpoint = PartnershipsEngine::Labels
       end
     end
     ```

8. **Add dotted accessor to Partnerships module**
   - File: `scriptdash/app/services/partnerships.rb`
   - **Pattern 6.2**: Dotted Accessor Pattern [CRITICAL]
   - Add or update:
     ```ruby
     module Partnerships
       extend T::Sig
       include Core::API

       sig { returns(T.class_of(Labels)) }
       def self.labels
         Labels
       end
     end
     ```

9. **Create Scriptdash endpoint with authorization**
   - File: `scriptdash/app/services/partnerships/wunderbar/labels_endpoint.rb`
   - **Pattern 7.1**: Scriptdash Endpoint with Authorization [CRITICAL]
   - Implementation:
     ```ruby
     # typed: strict

     module Partnerships
       module Wunderbar
         # @owners { team: care, domain: partnerships }
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

10. **Add permissions in ability classes**
    - Files:
      - `scriptdash/app/models/abilities/ability.rb`
      - `scriptdash/app/models/abilities/wunderbar_ability.rb`
    - **Pattern 7.2**: Ability Class Permission Definitions [CRITICAL]
    - In `ability.rb`:
      ```ruby
      def ops(_wunderbar_user = nil)
        can :read, LabelsAPI::Types::V1::LabelType::Label
        # ... existing permissions
      end

      def manager(_wunderbar_user = nil)
        can :read, LabelsAPI::Types::V1::LabelType::Label
        # ... existing permissions
      end

      def engineer(_wunderbar_user = nil)
        can :read, LabelsAPI::Types::V1::LabelType::Label
        # ... existing permissions
      end
      ```
    - In `wunderbar_ability.rb`:
      ```ruby
      def grant_abilities_for_role(role)
        case role
        when :engineer, :manager, :ops
          can :read, LabelsAPI::Types::V1::LabelType::Label
          # ... existing permissions
        end
      end
      ```

11. **Create Wunderbar controller (if HTTP endpoint needed)**
    - File: `scriptdash/app/controllers/wunderbar/partnerships/v1/labels_controller.rb`
    - **Pattern 4.2**: Scriptdash Controller Structure [CRITICAL]
    - Implementation:
      ```ruby
      # typed: strict

      module Wunderbar
        module Partnerships
          module V1
            # @owners { team: care, domain: partnerships }
            class LabelsController < WunderbarController
              extend T::Sig

              sig { returns(::Partnerships::Wunderbar::LabelsEndpoint) }
              def endpoint
                @endpoint ||= T.let(
                  ::Partnerships::Wunderbar::LabelsEndpoint.new,
                  T.nilable(::Partnerships::Wunderbar::LabelsEndpoint)
                )
              end

              # GET /partnerships/v1/labels/by_resource?labelable_type=Delivery&labelable_id=123
              def by_resource
                result = endpoint.fetch_by_labelable(
                  labelable_type: params[:labelable_type],
                  labelable_id: params[:labelable_id]
                )
                render json: { data: result.map(&:serialize) }, status: :ok
              end
            end
          end
        end
      end
      ```

12. **Add routes for controller**
    - File: `scriptdash/config/routes.rb`
    - Add within Wunderbar constraints:
      ```ruby
      constraints subdomain: 'wunderbar' do
        scope module: :wunderbar do
          namespace :partnerships do
            namespace :v1 do
              get 'labels/by_resource', to: 'labels#by_resource'
            end
          end
        end
      end
      ```

### Phase 4: Testing

**Reference**: `references/testing_patterns.md` - Patterns 8.1, 8.4, 8.5

13. **Write unit tests for partnerships labels module**
    - File: `engine-partnerships/spec/services/partnerships_engine/labels_spec.rb`
    - Test Core::API delegation:
      ```ruby
      require 'rails_helper'

      RSpec.describe PartnershipsEngine::Labels do
        describe '.fetch_by_labelable' do
          it 'delegates to labels_engine' do
            expect(LabelsEngine::V1::LabelsEndpoint).to receive_message_chain(:new, :fetch_by_labelable)
              .with(labelable_type: 'Delivery', labelable_id: '123')
              .and_return([])

            PartnershipsEngine.labels.fetch_by_labelable(
              labelable_type: 'Delivery',
              labelable_id: '123'
            )
          end
        end
      end
      ```

14. **Write Scriptdash controller tests**
    - File: `scriptdash/spec/controllers/wunderbar/partnerships/v1/labels_controller_spec.rb`
    - **Pattern 8.4**: Scriptdash Controller Spec Structure [CRITICAL]
    - **Pattern 8.5**: Permission Testing Pattern [PREFERRED]
    - Implementation:
      ```ruby
      require 'rails_helper'

      RSpec.describe Wunderbar::Partnerships::V1::LabelsController, type: :controller do
        describe 'GET #by_resource' do
          context 'with read permission (manager)' do
            before(:each) do
              @wunderbar_user = FactoryBot.create(:manager_wb_user)
              login_wunderbar_user(@wunderbar_user)
            end

            it 'returns labels for resource' do
              # Mock the labels API response
              mock_labels = [
                LabelsAPI::Types::V1::LabelType::Label.new(
                  id: '1',
                  labelable_type: 'Delivery',
                  labelable_id: '123',
                  name: 'urgent',
                  source: 'system',
                  created_at: Time.now.iso8601,
                  updated_at: Time.now.iso8601
                )
              ]
              allow(Partnerships.labels).to receive(:fetch_by_labelable)
                .with(labelable_type: 'Delivery', labelable_id: '123')
                .and_return(mock_labels)

              get :by_resource, params: { labelable_type: 'Delivery', labelable_id: '123' }

              expect(response).to have_http_status(200)
              body = JSON.parse(response.body)
              expect(body['data']).to be_an(Array)
              expect(body['data'].length).to eq(1)
              expect(body['data'].first['name']).to eq('urgent')
            end
          end

          context 'without permission (basic user)' do
            before(:each) do
              @wunderbar_user = FactoryBot.create(:basic_wb_user)
              login_wunderbar_user(@wunderbar_user)
            end

            it 'denies access' do
              expect {
                get :by_resource, params: { labelable_type: 'Delivery', labelable_id: '123' }
              }.to raise_error(CanCan::AccessDenied)
            end
          end
        end
      end
      ```

15. **Integration test with real labels_engine**
    - File: `scriptdash/spec/integration/partnerships/labels_integration_spec.rb`
    - Test end-to-end with real database:
      ```ruby
      require 'rails_helper'

      RSpec.describe 'Partnerships Labels Integration' do
        it 'fetches labels for delivery through partnerships' do
          # Create a label in labels_engine
          label = LabelsEngine::Label.create!(
            labelable_type: 'Delivery',
            labelable_id: 123,
            name: 'urgent',
            source: 'system'
          )

          # Fetch via partnerships API
          result = PartnershipsEngine.labels.fetch_by_labelable(
            labelable_type: 'Delivery',
            labelable_id: '123'
          )

          expect(result).to be_an(Array)
          expect(result.length).to eq(1)
          expect(result.first.name).to eq('urgent')
          expect(result.first.labelable_type).to eq('Delivery')
        end
      end
      ```

16. **Manual testing checklist**
    - [ ] Create test delivery with labels via Rails console
    - [ ] Query via Scriptdash API as manager user (should succeed)
    - [ ] Query via Scriptdash API as basic user (should fail with 403)
    - [ ] Verify response format matches `LabelsAPI::Types::V1::LabelType::Label`
    - [ ] Test with multiple labels on same resource
    - [ ] Test with no labels (should return empty array)

## Risks and Considerations

### Dependency Management
- **Risk**: Alto-workspace dependency updates can be complex across 55+ repos
- **Mitigation**: Follow alto-workspace patterns documented in `references/alto-workspace-quick-reference.md`
  - Use `alto generate deps engine-partnerships` to regenerate dependency files
  - Use `alto bump` commands for version updates
  - Test in isolation first
- **Reference**: Pattern documented in alto-workspace-quick-reference.md

### RPC vs Local Mode Configuration
- **Risk**: Code works locally but fails in RPC mode (or vice versa)
- **Mitigation**: Core::API client handles switching automatically via ENV vars
  - **Local mode** (default): `ALTO_DISABLE_RPC_LABELS_API=true` or endpoint configured
  - **RPC mode**: Set `LABELS_API_BASE_URL=http://labels-service`
  - Test both modes if deploying separately
- **Reference**: Pattern 6.4 in scriptdash_patterns.md (Endpoint Configuration)
- **Debugging tip**: Check which endpoint is being used:
  ```ruby
  puts PartnershipsEngine.labels.labels_endpoint.class
  # Local: LabelsEngine::V1::LabelsEndpoint
  # RPC: LabelsAPI::V1::LabelsEndpoint::RPCClient
  ```

### Permission Scope
- **Risk**: Too permissive (anyone can see labels) or too restrictive (care team blocked)
- **Mitigation**:
  - Define clear CanCan abilities in BOTH `ability.rb` and `wunderbar_ability.rb`
  - Test with different user types (manager, ops, engineer, basic user)
  - Follow **Pattern 7.2** (Ability Class Permission Definitions)
- **Common Error**: Forgetting to update WunderbarAbility (Pattern 7.2 warning)

### Polymorphic Association Complexity
- **Risk**: Labels can belong to ANY resource type - need to validate `labelable_type` values
- **Mitigation**:
  - Document supported resource types in partnerships context
  - Consider adding validation: only "Delivery", "HubReferral", etc. allowed
  - Labels engine already handles polymorphic associations correctly
  - Trust the unique constraint: `(labelable_type, labelable_id, name)`

### Authorization Check on Type vs Model
- **Risk**: Authorizing against wrong class (model instead of proto type)
- **Mitigation**:
  - **Always authorize against proto type**: `LabelsAPI::Types::V1::LabelType::Label`
  - **Never authorize against model**: `LabelsEngine::Label` (engine internal)
- **Reference**: Pattern 7.1 common error (scriptdash_patterns.md line 344-352)

### Backward Compatibility
- **Risk**: Breaking existing labels functionality in other contexts
- **Mitigation**:
  - We're only adding read access, not modifying existing endpoints
  - Labels engine already supports `fetch_by_labelable` method
  - No changes to labels_engine code needed
  - Integration is additive, not destructive

### N+1 Queries
- **Risk**: If fetching labels for multiple deliveries, could cause N+1 queries
- **Mitigation**:
  - Current use case: fetch labels for ONE resource at a time
  - If batch fetching becomes needed: labels_engine supports `fetch_all(ids: [...])`
  - Monitor query logs in development/staging
  - Consider eager loading if accessing labels in loops

### Missing Dotted Accessor
- **Risk**: Forgetting to add dotted accessor to parent module
- **Mitigation**:
  - Always add accessor method to expose submodule
  - Follow **Pattern 6.2** (Dotted Accessor Pattern)
- **Common Error**: Module exists but not accessible via dotted syntax (scriptdash_patterns.md line 150-154)

## Testing Strategy

**Reference**: `references/testing_patterns.md` - Patterns 8.1-8.7

### Testing Approach Overview

**Engine layer**: Test Core::API delegation (unit tests)
**Scriptdash layer**: Mock engine calls, test permissions (controller specs)
**Integration**: Test end-to-end with real database

### Unit Tests

**Partnerships labels module**:
- **Purpose**: Verify Core::API delegation to labels_engine
- **File**: `engine-partnerships/spec/services/partnerships_engine/labels_spec.rb`
- **What to test**:
  - Delegation to `LabelsEngine::V1::LabelsEndpoint`
  - Correct parameters passed through
  - Return type is array of Label structs
- **Pattern**: Mock the endpoint, verify delegation

**Scriptdash service module**:
- **Purpose**: Test authorization logic in isolation
- **Pattern 7.3**: Permission Testing in Endpoint (scriptdash_patterns.md)
- **What to test**:
  - Authorization check happens BEFORE delegation
  - CanCan::AccessDenied raised when unauthorized
  - Correct proto type used in authorization

### Controller Tests

**Scriptdash controller specs**:
- **File**: `scriptdash/spec/controllers/wunderbar/partnerships/v1/labels_controller_spec.rb`
- **Pattern 8.4**: Scriptdash Controller Spec Structure [CRITICAL]
- **Pattern 8.5**: Permission Testing Pattern [PREFERRED]
- **Key elements**:
  1. Login user before each test (`login_wunderbar_user`)
  2. Mock Core API calls (`allow(Partnerships.labels).to receive(...)`)
  3. Test with different user roles (manager, ops, basic)
  4. Verify HTTP response and JSON structure
- **What to test**:
  - Happy path with permission → 200 OK
  - Without permission → raises CanCan::AccessDenied
  - Not logged in → redirects to login
  - Correct delegation to service layer
  - JSON response format

### Integration Tests

**End-to-end with real database**:
- **File**: `scriptdash/spec/integration/partnerships/labels_integration_spec.rb`
- **Purpose**: Test full stack with real labels_engine
- **What to test**:
  - Create label in database
  - Fetch via `PartnershipsEngine.labels.fetch_by_labelable`
  - Verify correct data returned
  - No mocking - test real integration

### Test Data Setup

**Using FactoryBot**:
- **Pattern 8.3**: Factory Usage Pattern [PREFERRED]
- **What to create**:
  - `LabelsEngine::Label` with known `labelable_type` and `labelable_id`
  - WunderbarUser with different roles:
    - `:manager_wb_user` (has read permission)
    - `:ops_wb_user` (has read permission)
    - `:basic_wb_user` (no permission - control group)
  - Delivery or HubReferral if testing in partnerships context

### Test Scenarios

**Required test cases** (follow Pattern 8.5 - Permission Testing):

1. **Happy path (authorized)**:
   - User: Manager/Ops
   - Action: Fetch labels for delivery
   - Expected: 200 OK, array of labels returned

2. **Authorization denied**:
   - User: Basic user (no permissions)
   - Action: Fetch labels for delivery
   - Expected: CanCan::AccessDenied raised

3. **Not logged in**:
   - User: None
   - Action: Fetch labels for delivery
   - Expected: Redirect to login page

4. **Empty result**:
   - User: Manager
   - Resource: Delivery with no labels
   - Expected: 200 OK, empty array `[]`

5. **Multiple labels**:
   - User: Manager
   - Resource: Delivery with 3 labels
   - Expected: 200 OK, array with 3 label structs

6. **Polymorphic resources**:
   - Test with both Delivery and HubReferral
   - Verify `labelable_type` filtering works correctly

### Test File Locations

**Pattern 8.6**: Test File Location Convention [PREFERRED]

- **Partnerships specs**: `spec/services/partnerships_engine/labels_spec.rb`
- **Scriptdash controller specs**: `spec/controllers/wunderbar/partnerships/v1/labels_controller_spec.rb`
- **Integration specs**: `spec/integration/partnerships/labels_integration_spec.rb`

### Verification Checklist

**Before committing**:
- [ ] Sorbet type checking passes: `bundle exec srb tc` (all repos)
- [ ] RSpec tests pass in partnerships engine: `bundle exec rspec spec/services/partnerships_engine/labels_spec.rb`
- [ ] RSpec tests pass in scriptdash: `bundle exec rspec spec/controllers/wunderbar/partnerships/v1/`
- [ ] Integration test passes: `bundle exec rspec spec/integration/partnerships/labels_integration_spec.rb`
- [ ] No N+1 queries (check `log/test.log` for excessive SELECT queries)

**Manual testing**:
- [ ] Manual API call returns expected label data
- [ ] Permissions enforce care team access (manager/ops can access)
- [ ] Permissions block unauthorized users (basic user gets 403)
- [ ] Response format matches `LabelsAPI::Types::V1::LabelType::Label` schema
- [ ] Multiple labels returned correctly
- [ ] Empty array for resources with no labels

**Test description convention** (Pattern 8.7):
- Use `describe 'HTTP_VERB /url/path'` for endpoint tests
- Use `context 'when condition'` for scenarios
- Use `it 'does something'` for expectations
- Example:
  ```ruby
  describe 'GET /partnerships/v1/labels/by_resource' do
    context 'with read permission' do
      it 'returns labels for resource' do
        # ...
      end
    end
  end
  ```
