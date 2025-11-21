# Testing Patterns

**Scope**: Testing FetchAll/FetchOne endpoints in Engine and Scriptdash
**Source**: PRs #48986 (Scriptdash), #535 (Actions Engine)
**Last Updated**: 2025-11-20

---

## Overview

Testing patterns differ between Engine and Scriptdash:

**Engine tests**:
- Use `:rpc_client_requests` helper
- Test via RPC client (full stack)
- Use factories for test data
- Focus on business logic and data transformations

**Scriptdash tests**:
- Controller specs (not request specs usually)
- Mock Core API calls
- Test permissions and delegation
- Focus on authorization, not business logic

---

## Layer 8: Testing

### Pattern 8.1: Engine Request Spec Structure [CRITICAL]

**Priority**: CRITICAL

**Purpose**: Test Engine endpoints through the RPC client to verify full stack behavior.

**When to use**: Always. Every Engine endpoint needs request specs.

**Implementation**:

```ruby
require 'rails_helper'

RSpec.describe ActionsEngine::V2::ActionPartnershipsController, :rpc_client_requests, type: :request do
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
      expect(result.first.name).to eq('Progyny')
    end
  end
end
```

**Key elements**:

1. **`:rpc_client_requests` helper** - Enables RPC testing
   ```ruby
   RSpec.describe SomeController, :rpc_client_requests, type: :request do
   ```

2. **Use RPC client** - Test through the client, not controller directly
   ```ruby
   let(:client) { ActionsAPI::V2::ActionPartnershipsEndpoint::RPCClient.new }
   ```

3. **Create test data with factories** - Use FactoryBot
   ```ruby
   create(:action_partnership, name: 'Progyny', value: 'progyny')
   ```

4. **Call client methods** - Test like a real client would
   ```ruby
   result = client.fetch_all
   ```

5. **Verify response types** - Check struct types
   ```ruby
   expect(result.first).to be_a(ActionsAPI::Types::V2::ActionPartnership)
   ```

**What `:rpc_client_requests` does**:
- Configures RPC client to hit test server (not real endpoint)
- Handles request/response serialization
- Enables full HTTP stack testing

**Trade-offs**:
- ✅ Tests full stack (controller → endpoint → database)
- ✅ Tests like real client usage
- ✅ Catches serialization issues
- ✅ Tests HTTP layer
- ❌ Slower than unit tests (full stack)
- ❌ Doesn't test error cases as easily

**Common Error**: Forgetting `:rpc_client_requests` helper

```ruby
# ❌ Wrong: Missing helper, client won't connect properly
RSpec.describe ActionsEngine::V2::ActionPartnershipsController, type: :request do
  let(:client) { ActionsAPI::V2::ActionPartnershipsEndpoint::RPCClient.new }
  # Tests will fail with connection errors
end

# ✅ Correct: Include helper
RSpec.describe ActionsEngine::V2::ActionPartnershipsController, :rpc_client_requests, type: :request do
  let(:client) { ActionsAPI::V2::ActionPartnershipsEndpoint::RPCClient.new }
end
```

---

### Pattern 8.2: Engine FetchOne Test Pattern [CRITICAL]

**Priority**: CRITICAL

**Purpose**: Test single-record fetching with error cases.

**When to use**: When testing FetchOne endpoints.

**Implementation**:

```ruby
require 'rails_helper'

RSpec.describe ActionsEngine::V2::ActionTypesController, :rpc_client_requests, type: :request do
  let(:client) { ActionsAPI::V2::ActionTypesEndpoint::RPCClient.new }

  describe 'GET /v2/action_types/:id' do
    subject(:fetch_one) { client.fetch_one(id: action_type.id) }

    context 'when action type exists' do
      let(:action_type) { create(:action_type, name: 'Urgent Task') }

      it 'returns the action type' do
        result = fetch_one

        expect(result).to be_a(ActionsAPI::Types::V2::ActionType)
        expect(result.id).to eq(action_type.id)
        expect(result.name).to eq('Urgent Task')
      end
    end

    context 'when action type does not exist' do
      it 'raises RecordNotFound' do
        expect {
          client.fetch_one(id: 999999)
        }.to raise_error(ActiveRecord::RecordNotFound)
      end
    end
  end
end
```

**Key testing patterns**:

1. **Test successful case** - Record exists
2. **Test error case** - Record not found
3. **Use contexts** - Organize test cases
4. **Verify type and data** - Check struct type and fields

**Trade-offs**:
- ✅ Tests both happy path and errors
- ✅ Verifies RecordNotFound behavior
- ✅ Clear test organization with contexts
- ❌ More verbose than minimal tests

---

### Pattern 8.3: Factory Usage Pattern [PREFERRED]

**Priority**: PREFERRED

**Purpose**: Use FactoryBot to create test data cleanly.

**When to use**: Always. Factories are cleaner than raw model creation.

**Implementation**:

**In test**:
```ruby
it 'returns all action partnerships' do
  create(:action_partnership, name: 'Progyny', value: 'progyny', company_id: 1)
  create(:action_partnership, name: 'Carrot', value: 'carrot', company_id: 1)

  result = client.fetch_all

  expect(result.length).to eq(2)
end
```

**Factory definition** (for reference):
```ruby
# spec/factories/action_partnerships.rb
FactoryBot.define do
  factory :action_partnership, class: 'ActionPartnership' do
    sequence(:name) { |n| "Partnership #{n}" }
    sequence(:value) { |n| "partnership_#{n}" }
    company_id { 1 }
  end
end
```

**Factory patterns**:
- Use `create` for persisted records
- Use `build` for unsaved objects (unit tests)
- Use `build_stubbed` for fast fake objects
- Override attributes as needed

**Trade-offs**:
- ✅ DRY test data creation
- ✅ Centralized defaults
- ✅ Easy to override specific attributes
- ❌ Factories must be maintained
- ❌ Slight magic (defaults not obvious in test)

---

### Pattern 8.4: Scriptdash Controller Spec Structure [CRITICAL]

**Priority**: CRITICAL

**Purpose**: Test Scriptdash controllers by mocking the Engine API and verifying permissions/delegation.

**When to use**: Always. Scriptdash controller tests are different from Engine tests.

**Implementation**:

```ruby
require 'rails_helper'

RSpec.describe Wunderbar::Actions::V1::ActionPartnershipsController, { type: :controller } do
  before(:each) do
    @wunderbar_user = FactoryBot.create(:manager_wb_user)
    login_wunderbar_user(@wunderbar_user)
  end

  describe 'GET /actions/v1/action_partnerships/fetch_all' do
    it 'returns all action partnerships successfully' do
      # Mock the Engine API response
      mock_action_partnerships = [
        ActionsAPI::Types::V2::ActionPartnership.new(
          id: 1,
          name: 'Progyny',
          value: 'progyny',
        ),
        ActionsAPI::Types::V2::ActionPartnership.new(
          id: 2,
          name: 'Carrot',
          value: 'carrot',
        ),
        ActionsAPI::Types::V2::ActionPartnership.new(
          id: 3,
          name: 'Iterum',
          value: 'iterum',
        ),
      ]
      allow(Actions.action_partnerships).to receive(:fetch_all).and_return(mock_action_partnerships)

      get :index

      expect(response).to have_http_status(200)
      body = JSON.parse(response.body)
      expect(body['data']).to be_an(Array)
      expect(body['data'].length).to eq(3)
      expect(body['data'].first['name']).to eq('Progyny')
      expect(body['data'].first['value']).to eq('progyny')
    end
  end
end
```

**Key elements**:

1. **Login user before each test** - Wunderbar requires auth
   ```ruby
   before(:each) do
     @wunderbar_user = FactoryBot.create(:manager_wb_user)
     login_wunderbar_user(@wunderbar_user)
   end
   ```

2. **Mock Core API calls** - Don't hit real Engine
   ```ruby
   allow(Actions.action_partnerships).to receive(:fetch_all).and_return(mock_data)
   ```

3. **Test controller action directly** - Use `get :index`, not HTTP client
   ```ruby
   get :index
   ```

4. **Verify HTTP response** - Check status and JSON body
   ```ruby
   expect(response).to have_http_status(200)
   body = JSON.parse(response.body)
   expect(body['data'].length).to eq(3)
   ```

**Why mock**:
- Tests run faster (no Engine calls)
- Tests Scriptdash layer in isolation
- Don't need Engine running
- Focus on permissions/delegation, not business logic

**Trade-offs**:
- ✅ Fast tests (mocked)
- ✅ Tests Scriptdash-specific logic
- ✅ No Engine dependency
- ❌ Doesn't test integration with real Engine
- ❌ Mocks can drift from reality

---

### Pattern 8.5: Permission Testing Pattern [PREFERRED]

**Priority**: PREFERRED

**Purpose**: Verify authorization checks work correctly.

**When to use**: Always test permissions for Scriptdash endpoints.

**Implementation**:

```ruby
require 'rails_helper'

RSpec.describe Wunderbar::Actions::V1::ActionPartnershipsController, { type: :controller } do
  describe 'GET /actions/v1/action_partnerships/fetch_all' do
    context 'with read permission (manager)' do
      before(:each) do
        @wunderbar_user = FactoryBot.create(:manager_wb_user)
        login_wunderbar_user(@wunderbar_user)
      end

      it 'allows access' do
        allow(Actions.action_partnerships).to receive(:fetch_all).and_return([])

        get :index

        expect(response).to have_http_status(200)
      end
    end

    context 'without permission (basic user)' do
      before(:each) do
        @wunderbar_user = FactoryBot.create(:basic_wb_user)  # No permissions
        login_wunderbar_user(@wunderbar_user)
      end

      it 'denies access' do
        expect {
          get :index
        }.to raise_error(CanCan::AccessDenied)
      end
    end

    context 'without login' do
      it 'redirects to login' do
        get :index

        expect(response).to redirect_to(login_path)
      end
    end
  end
end
```

**Test scenarios**:
1. **With permission** - User has required role, request succeeds
2. **Without permission** - User lacks role, raises `CanCan::AccessDenied`
3. **Not logged in** - Redirects to login page

**Common permission levels**:
- `:manager_wb_user` - Manager permissions (read most things)
- `:ops_wb_user` - Ops permissions (read + write many things)
- `:engineer_wb_user` - Engineer permissions (manage dev resources)
- `:basic_wb_user` - Minimal permissions (control group)

**Trade-offs**:
- ✅ Verifies authorization works
- ✅ Tests different user roles
- ✅ Prevents unauthorized access bugs
- ❌ More test cases to maintain
- ❌ Requires understanding permission system

**Common Error**: Not testing unauthorized case

```ruby
# ❌ Wrong: Only tests happy path
it 'returns action partnerships' do
  login_wunderbar_user(create(:manager_wb_user))
  get :index
  expect(response).to have_http_status(200)
end

# ✅ Correct: Test both authorized and unauthorized
context 'with permission' do
  it 'allows access' { ... }
end

context 'without permission' do
  it 'denies access' { ... }
end
```

---

### Pattern 8.6: Test File Location Convention [PREFERRED]

**Priority**: PREFERRED

**Purpose**: Consistent file structure for tests mirrors controller structure.

**When to use**: Always.

**Convention**:

**Engine Request Specs**:
```
spec/requests/{domain}_engine/v{version}/{resource}_controller_spec.rb
```

Examples:
- `spec/requests/actions_engine/v2/action_partnerships_controller_spec.rb`
- `spec/requests/actions_engine/v2/action_types_controller_spec.rb`

**Scriptdash Controller Specs**:
```
spec/requests/{subdomain}/{domain}/v{version}/{resource}_controller_spec.rb
```

OR (older convention):
```
spec/controllers/{subdomain}/{domain}/v{version}/{resource}_controller_spec.rb
```

Examples:
- `spec/requests/wunderbar/actions/v1/action_partnerships_controller_spec.rb`
- `spec/controllers/wunderbar/billing/v1/invoices_controller_spec.rb`

**Naming rules**:
- Spec file mirrors controller file path
- Use `_spec.rb` suffix
- Include version in path

**Trade-offs**:
- ✅ Easy to find test for any controller
- ✅ Matches Rails conventions
- ✅ Auto-loading works
- ❌ Deep nesting

---

### Pattern 8.7: Test Description Convention [PREFERRED]

**Priority**: PREFERRED

**Purpose**: Clear test descriptions make failures easy to understand.

**When to use**: Always.

**Convention**:

```ruby
RSpec.describe SomeController do
  describe 'HTTP_VERB /url/path' do  # ← HTTP verb + URL
    context 'when condition' do      # ← Test scenario
      it 'does something' do          # ← Expected behavior
        # Test code
      end
    end
  end
end
```

**Example**:

```ruby
RSpec.describe ActionsEngine::V2::ActionPartnershipsController do
  describe 'GET /v2/action_partnerships/fetch_all' do
    context 'when partnerships exist' do
      it 'returns all partnerships' do
        # ...
      end
    end

    context 'when no partnerships exist' do
      it 'returns empty array' do
        # ...
      end
    end
  end
end
```

**Benefits**:
- Clear what's being tested (HTTP verb + URL)
- Clear test scenarios (contexts)
- Clear expectations (it statements)
- Readable test output

**Trade-offs**:
- ✅ Self-documenting tests
- ✅ Clear failure messages
- ✅ Organized by endpoint
- ❌ Verbose (but worth it)

---

## Testing Checklist

**Engine endpoint tests should**:
- ✅ Use `:rpc_client_requests` helper
- ✅ Test via RPC client
- ✅ Use factories for test data
- ✅ Verify response types
- ✅ Test happy path and error cases
- ✅ Check database queries work
- ✅ Verify data transformations

**Scriptdash endpoint tests should**:
- ✅ Login user before each test
- ✅ Mock Core API calls
- ✅ Test with different user roles
- ✅ Verify permission checks
- ✅ Test unauthorized access
- ✅ Verify delegation to Engine
- ✅ Check JSON response format

---

## Pattern Summary

**Layer 8 extracted**: 7 patterns (4 CRITICAL, 3 PREFERRED)

**Key takeaways**:
1. Engine tests use `:rpc_client_requests` and test full stack
2. Scriptdash tests mock Engine API and test permissions
3. Use factories for clean test data
4. Test both authorized and unauthorized cases
5. Follow file location conventions
6. Write clear test descriptions

**Common mistakes**:
- Forgetting `:rpc_client_requests` helper in Engine tests
- Not testing unauthorized access in Scriptdash
- Not mocking Core API in Scriptdash tests
- Unclear test descriptions

**Iteration 3 Complete!**

**Files created**:
- `controller_routes_patterns.md` (6 patterns)
- `testing_patterns.md` (7 patterns)

**Total patterns so far**: 30 patterns across 4 documents

**Next**: Scriptdash patterns (Core API + Permissions)
