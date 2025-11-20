# Troubleshooting Guide

**Scope**: Common errors, gotchas, and fixes for FetchAll/FetchOne endpoints
**Source**: Patterns analysis + common issues
**Last Updated**: 2025-11-20

---

## Overview

This guide covers common errors when creating FetchAll/FetchOne endpoints, organized by layer.

Quick links:
- [Proto Issues](#proto-layer-issues)
- [Generated Code Issues](#generated-code-issues)
- [Implementation Issues](#implementation-issues)
- [Controller Issues](#controller-issues)
- [Routes Issues](#routes-issues)
- [Core API Issues](#core-api-issues)
- [Permission Issues](#permission-issues)
- [Testing Issues](#testing-issues)

---

## Proto Layer Issues

### Error: `LoadError: cannot load such file -- actions_api`

**Symptom**: After running `bin/protos`, getting load errors.

**Cause**: Proto generator deletes `actions_api.rb` file during generation.

**Fix**:
```bash
bin/protos
git checkout actions_api/lib/actions_api.rb  # Restore the deleted file
```

**Prevention**: Always restore after running `bin/protos`:
```bash
#!/bin/bash
# Add to your workflow
bin/protos && git checkout actions_api/lib/actions_api.rb
```

---

### Error: Generated code not matching proto

**Symptom**: Changes to proto file don't appear in generated Ruby code.

**Cause**: Forgot to regenerate after proto changes.

**Fix**:
```bash
cd engine-actions  # or scriptdash
bin/protos
git checkout actions_api/lib/actions_api.rb  # If Engine
```

**Verification**:
```bash
# Check generated file timestamp
ls -l actions_api/lib/actions_api/v2/action_partnerships_endpoint/interface.rb

# Should be recent (just regenerated)
```

---

### Error: Service V2.0 not generating controllers

**Symptom**: No controller or routes modules generated.

**Cause**: Missing `option (opts.service_value) = {version: "v2.0"}`

**Fix**:
```protobuf
service ActionPartnershipsEndpoint {
  option (opts.service_value) = {version: "v2.0"};  // ← Add this

  rpc FetchAll(...) returns (...);
}
```

---

## Generated Code Issues

### Error: `NameError: uninitialized constant AbstractXxxEndpoint`

**Symptom**: Can't find abstract endpoint class.

**Cause**: Proto not generated, or wrong package name.

**Fix**:
1. Verify proto package matches Ruby module:
   ```protobuf
   package actions_api.v2;  // → ActionsAPI::V2
   ```

2. Regenerate protos:
   ```bash
   bin/protos
   git checkout actions_api/lib/actions_api.rb
   ```

3. Check endpoint extends correct abstract class:
   ```ruby
   class Endpoint < ActionsAPI::V2::ActionPartnershipsEndpoint::Interface::AbstractActionPartnershipsEndpoint
   ```

---

### Error: Method signature doesn't match abstract class

**Symptom**: Sorbet error: `Method fetch_all does not match parent signature`.

**Cause**: Implementation signature doesn't match abstract interface.

**Fix**:
```ruby
# ❌ Wrong: Missing override, wrong parameter type
sig { params(ids: T::Array[String]).returns(T::Array[...]) }
def fetch_all(ids:)
end

# ✅ Correct: Include override, match exact signature
sig { override.params(ids: T::Array[Integer]).returns(T::Array[...]) }
def fetch_all(ids:)
end
```

**Debugging tip**:
```bash
# Check abstract interface for exact signature
cat actions_api/lib/actions_api/v2/action_partnerships_endpoint/interface.rb | grep -A5 "def fetch_all"
```

---

## Implementation Issues

### Error: N+1 Query Problem

**Symptom**: Slow endpoint, many database queries.

**Cause**: Not eager-loading associations used in adapter.

**Detection**:
```ruby
# In Rails console or test:
ActiveRecord::Base.logger = Logger.new(STDOUT)

Actions.action_partnerships.fetch_all

# Look for:
# Action Load (0.1ms) SELECT * FROM actions...
# ActionRelation Load (0.1ms) SELECT * FROM action_relations WHERE action_id = 1  # ← N+1!
# ActionRelation Load (0.1ms) SELECT * FROM action_relations WHERE action_id = 2  # ← N+1!
```

**Fix**:
```ruby
sig { override.params(ids: T::Array[Integer]).returns(...) }
def fetch_all(ids:)
  actions = Action
    .includes(              # ← Add eager loading
      :action_relations,    # For each association used in adapter
      :action_labels,
      :task_threshold,
    )
    .find(ids)

  actions.map { |action| ActionAdapter.new(action).to_struct }
end
```

**How to identify what to include**:
1. Look at adapter's `to_struct` method
2. Find all `@model.association` calls
3. Add to `.includes()` list

---

### Error: `ActiveRecord::RecordNotFound`

**Symptom**: 500 error when record doesn't exist.

**Cause**: Expected behavior for FetchOne! Rails automatically returns 404.

**Not an error**: This is correct behavior. Rails middleware catches `RecordNotFound` and returns 404.

**If you want custom error handling**:
```ruby
def fetch_one(id:)
  action = Action.find_by(id: id)
  return [] if action.nil?  # Or custom error response

  ActionAdapter.new(action).to_struct
rescue ActiveRecord::RecordNotFound
  # Custom handling
end
```

**Testing**: Verify 404 response in specs (see testing_patterns.md).

---

### Error: Wrong Adapter Class

**Symptom**: `NameError: uninitialized constant ActionPartnershipAdapter`.

**Cause**: Adapter class doesn't exist or wrong name.

**Fix**:
1. Check if adapter file exists:
   ```bash
   find app/services -name "*action_partnership*adapter.rb"
   ```

2. If missing, create adapter:
   ```ruby
   # app/services/actions_engine/action_partnership_adapter.rb
   module ActionsEngine
     class ActionPartnershipAdapter
       extend T::Sig

       sig { params(action_partnership: ActionPartnership).void }
       def initialize(action_partnership)
         @action_partnership = action_partnership
       end

       sig { returns(ActionsAPI::Types::V2::ActionPartnership) }
       def to_struct
         ActionsAPI::Types::V2::ActionPartnership.new(
           id: @action_partnership.id,
           name: @action_partnership.name,
           value: @action_partnership.value,
         )
       end
     end
   end
   ```

3. Or use direct struct creation (simpler types):
   ```ruby
   def fetch_all
     ActionPartnership.all.map do |ap|
       ActionsAPI::Types::V2::ActionPartnership.new(
         id: ap.id,
         name: ap.name,
         value: ap.value,
       )
     end
   end
   ```

---

## Controller Issues

### Error: `NameError` - Can't find endpoint class

**Symptom**: `uninitialized constant ActionPartnerships::Endpoint`.

**Cause**: Missing namespace prefix or wrong module.

**Engine Fix**:
```ruby
# ❌ Wrong: Missing ActionsEngine namespace
def endpoint
  @endpoint ||= ActionPartnerships::Endpoint.new
end

# ✅ Correct: Full path
def endpoint
  @endpoint ||= ActionsEngine::ActionPartnerships::Endpoint.new
end
```

**Scriptdash Fix**:
```ruby
# ❌ Wrong: Missing :: prefix
def endpoint
  @endpoint ||= Actions::Wunderbar::ActionPartnershipsEndpoint.new
end

# ✅ Correct: Global namespace with ::
def endpoint
  @endpoint ||= ::Actions::Wunderbar::ActionPartnershipsEndpoint.new
end
```

---

### Error: Sorbet type error in endpoint accessor

**Symptom**: Sorbet complains about `T.nilable` types.

**Cause**: Memoization pattern not typed correctly.

**Fix**:
```ruby
# ❌ Wrong: Missing T.let
sig { returns(ActionPartnerships::Endpoint) }
def endpoint
  @endpoint ||= ActionPartnerships::Endpoint.new  # Sorbet error!
end

# ✅ Correct: Use T.let for memoization
sig { returns(ActionPartnerships::Endpoint) }
def endpoint
  @endpoint ||= T.let(
    ActionPartnerships::Endpoint.new,
    T.nilable(ActionPartnerships::Endpoint),
  )
end
```

---

## Routes Issues

### Error: `NoMethodError` - undefined method for routing

**Symptom**: Routes error when loading Rails.

**Cause**: Forgot to extend generated Routes module.

**Fix**:
```ruby
# config/routes.rb

# ❌ Wrong: Missing extend
ActionsEngine::Engine.routes.draw do
  # Routes not defined - 404 errors
end

# ✅ Correct: Extend generated routes
ActionsEngine::Engine.routes.draw do
  extend ActionsAPI::V2::ActionPartnershipsEndpoint::Routes
end
```

---

### Error: 404 - Route not found

**Symptom**: `ActionController::RoutingError: No route matches [GET] "/v2/action_partnerships/fetch_all"`.

**Cause**: Routes not extended or controller not found.

**Debugging**:
```bash
# List all routes
rails routes | grep action_partnerships

# Should see:
# GET  /v2/action_partnerships/fetch_all  actions_engine/v2/action_partnerships#index

# If missing, check routes.rb has extend line
```

**Fix**: Add extend to routes.rb (see above).

---

## Core API Issues

### Error: `NoMethodError` - undefined method `fetch_all` for module

**Symptom**: `NoMethodError: undefined method 'fetch_all' for Actions::ActionPartnerships:Module`.

**Cause**: Forgot `add_api` or wrong client module.

**Fix**:
```ruby
# ❌ Wrong: Missing add_api
module Actions
  module ActionPartnerships
    extend T::Sig
    include Core::API
    # Missing: add_api ...
    self.action_partnerships_endpoint = ActionsEngine::ActionPartnerships::Endpoint
  end
end

# ✅ Correct: Include add_api
module Actions
  module ActionPartnerships
    extend T::Sig
    include Core::API
    add_api ActionsAPI::V2::ActionPartnershipsEndpoint::Client  # ← Required
    self.action_partnerships_endpoint = ActionsEngine::ActionPartnerships::Endpoint
  end
end
```

---

### Error: Endpoint using RPC when local expected

**Symptom**: Slow responses, HTTP errors, endpoint works differently than expected.

**Cause**: Core::API using RPC client instead of local endpoint.

**Debugging**:
```ruby
# Check which endpoint is being used:
puts Actions.action_partnerships.action_partnerships_endpoint.class

# Local: ActionsEngine::ActionPartnerships::Endpoint
# RPC: ActionsAPI::V2::ActionPartnershipsEndpoint::RPCClient
```

**Fix** (force local):
```ruby
module Actions
  module ActionPartnerships
    include Core::API
    add_api ActionsAPI::V2::ActionPartnershipsEndpoint::Client

    # Explicitly set local endpoint
    self.action_partnerships_endpoint = ActionsEngine::ActionPartnerships::Endpoint
  end
end

# Verify ENV vars not forcing RPC:
puts ENV['ACTIONS_API_BASE_URL']  # Should be nil or empty for local
```

---

### Error: Missing dotted accessor

**Symptom**: `NoMethodError: undefined method 'action_partnerships' for Actions:Module`.

**Cause**: Forgot to add accessor in parent module.

**Fix**:
```ruby
# app/services/actions.rb

module Actions
  extend T::Sig

  # ❌ Missing accessor - Actions.action_partnerships fails

  # ✅ Correct: Add accessor
  sig { returns(T.class_of(ActionPartnerships)) }
  def self.action_partnerships
    ActionPartnerships
  end
end
```

---

## Permission Issues

### Error: `CanCan::AccessDenied` - Permission denied

**Symptom**: 403 Forbidden error when accessing endpoint.

**Cause**: User doesn't have required permission.

**Debugging**:
```ruby
# Check user's abilities
ability = Ability.new(current_user)
ability.can?(:read, ActionsAPI::Types::V2::ActionPartnership)  # false = no permission
```

**Fix**: Add permission to Ability classes:
```ruby
# app/models/abilities/ability.rb
def manager(_wunderbar_user = nil)
  can :read, ActionsAPI::Types::V2::ActionPartnership  # ← Add this
end

# app/models/abilities/wunderbar_ability.rb
def grant_abilities_for_role(role)
  case role
  when :manager
    can :read, ActionsAPI::Types::V2::ActionPartnership  # ← And this
  end
end
```

---

### Error: Permission check on wrong type

**Symptom**: `CanCan::AccessDenied` even though permissions look correct.

**Cause**: Checking permission on ActiveRecord model instead of proto type.

**Fix**:
```ruby
# ❌ Wrong: Checking model
current_ability.authorize! :read, ActionPartnership  # ActiveRecord model

# ✅ Correct: Check proto type
current_ability.authorize! :read, ActionsAPI::Types::V2::ActionPartnership
```

---

### Error: Permissions work in some contexts but not others

**Symptom**: Endpoint works in some parts of app, fails in Wunderbar.

**Cause**: Forgot to update WunderbarAbility.

**Fix**: Update BOTH ability files:
```ruby
# app/models/abilities/ability.rb
def manager
  can :read, ActionsAPI::Types::V2::ActionPartnership
end

# app/models/abilities/wunderbar_ability.rb (DON'T FORGET!)
def grant_abilities_for_role(role)
  when :manager
    can :read, ActionsAPI::Types::V2::ActionPartnership  # ← Add here too
end
```

---

## Testing Issues

### Error: RPC client tests fail with connection errors

**Symptom**: `Errno::ECONNREFUSED` or similar errors.

**Cause**: Missing `:rpc_client_requests` helper.

**Fix**:
```ruby
# ❌ Wrong: Missing helper
RSpec.describe ActionsEngine::V2::ActionPartnershipsController, type: :request do
  let(:client) { ActionsAPI::V2::ActionPartnershipsEndpoint::RPCClient.new }
  # Connection errors!
end

# ✅ Correct: Include helper
RSpec.describe ActionsEngine::V2::ActionPartnershipsController,
               :rpc_client_requests,  # ← Required
               type: :request do
  let(:client) { ActionsAPI::V2::ActionPartnershipsEndpoint::RPCClient.new }
end
```

---

### Error: Scriptdash tests fail - not logged in

**Symptom**: Tests fail with authorization errors.

**Cause**: Forgot to login user before test.

**Fix**:
```ruby
RSpec.describe Wunderbar::Actions::V1::ActionPartnershipsController, type: :controller do
  # ❌ Wrong: No login
  it 'returns action partnerships' do
    get :index  # Fails - not authenticated
  end

  # ✅ Correct: Login before each test
  before(:each) do
    @wunderbar_user = FactoryBot.create(:manager_wb_user)
    login_wunderbar_user(@wunderbar_user)
  end

  it 'returns action partnerships' do
    allow(Actions.action_partnerships).to receive(:fetch_all).and_return([])
    get :index  # Works!
  end
end
```

---

### Error: Scriptdash tests making real Engine calls

**Symptom**: Tests slow, fail when Engine not running.

**Cause**: Forgot to mock Core API calls.

**Fix**:
```ruby
it 'returns action partnerships' do
  # ❌ Wrong: No mock - makes real call
  get :index

  # ✅ Correct: Mock the Engine call
  mock_data = [ActionsAPI::Types::V2::ActionPartnership.new(id: 1, name: 'Test', value: 'test')]
  allow(Actions.action_partnerships).to receive(:fetch_all).and_return(mock_data)

  get :index
end
```

---

## General Debugging Tips

### Enable query logging

```ruby
# In Rails console or test setup
ActiveRecord::Base.logger = Logger.new(STDOUT)

# Now all SQL queries print to console
Actions.action_partnerships.fetch_all
# Shows: SELECT * FROM action_partnerships...
```

### Check generated code

```bash
# View generated interface
cat actions_api/lib/actions_api/v2/action_partnerships_endpoint/interface.rb

# View generated controller
cat actions_api/lib/actions_api/v2/action_partnerships_endpoint/controller.rb

# View generated routes
cat actions_api/lib/actions_api/v2/action_partnerships_endpoint/routes.rb
```

### Verify proto compilation

```bash
# Check proto file syntax
protoc --proto_path=protos/src \
       --ruby_out=/tmp \
       protos/src/actions_api/v2/action_partnerships_endpoint.proto

# No output = valid proto
# Errors = fix proto syntax
```

### Check Core::API client selection

```ruby
# In Rails console
puts Actions.action_partnerships.action_partnerships_endpoint.class

# Local: ActionsEngine::ActionPartnerships::Endpoint
# RPC: ActionsAPI::V2::ActionPartnershipsEndpoint::RPCClient

# Check environment
puts ENV['ACTIONS_API_BASE_URL']
puts ENV['USE_RPC']
```

---

## Quick Reference: Common Fix Checklist

When creating a new FetchAll/FetchOne endpoint, verify:

**Proto Layer**:
- [ ] Proto type defined in `types/v{version}/`
- [ ] Proto endpoint defined in `v{version}/`
- [ ] Service V2.0 annotation present
- [ ] Request/Response messages follow naming convention
- [ ] Ran `bin/protos` and restored `actions_api.rb`

**Implementation Layer**:
- [ ] Endpoint extends abstract interface
- [ ] Method signature matches abstract (use `override`)
- [ ] Eager loading for associations (`.includes()`)
- [ ] Adapter class exists (if using adapter pattern)
- [ ] Sorbet strict mode enabled

**Controller Layer**:
- [ ] Controller includes generated Controller mixin
- [ ] Endpoint accessor with correct class path
- [ ] Sorbet T.let for memoization
- [ ] Inherits from correct base controller

**Routes Layer**:
- [ ] Extended generated Routes module in `config/routes.rb`
- [ ] Can see route in `rails routes`

**Scriptdash Layer** (if applicable):
- [ ] Core API module with `include Core::API` and `add_api`
- [ ] Endpoint configuration set
- [ ] Dotted accessor in parent module
- [ ] Scriptdash endpoint includes `Auth::CurrentAbility`
- [ ] Permission check before delegation
- [ ] Permissions in both Ability and WunderbarAbility

**Testing Layer**:
- [ ] Engine tests use `:rpc_client_requests` helper
- [ ] Scriptdash tests login user before each
- [ ] Scriptdash tests mock Core API calls
- [ ] Both authorized and unauthorized cases tested

---

## Getting Help

If you're still stuck after checking this guide:

1. **Check the other pattern documents** - Detailed examples in each layer
2. **Look at working examples** - Find similar endpoint in codebase
3. **Enable logging** - See what's actually happening (SQL, HTTP calls)
4. **Ask for help** - Slack channels: #unified-workflow, #care

**Iteration 6 Complete!**
