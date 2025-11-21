# Scriptdash Patterns (Core API & Permissions)

**Scope**: Scriptdash-specific patterns for Core API integration and permissions
**Source**: PRs #48986, #535, Scriptdash codebase
**Last Updated**: 2025-11-20

---

## Overview

Scriptdash endpoints add a permissions layer on top of Engine APIs. Key patterns:

1. **Endpoint Delegation** - Scriptdash endpoint checks permissions, then calls Engine
2. **Core API Wiring** - Module structure for local/RPC client switching
3. **Dotted Accessor** - Clean API like `Actions.action_partnerships.fetch_all`
4. **Permissions** - Can CanCan integration for authorization

---

## Layer 6: Core API Integration

### Pattern 6.1: Core API Module Structure [CRITICAL]

**Priority**: CRITICAL

**Purpose**: Wire up Engine client with automatic local/RPC switching. Enables `Actions.action_partnerships.fetch_all` syntax.

**When to use**: Always. Every Scriptdash resource that wraps an Engine API needs this.

**Implementation**:

```ruby
# typed: strict

module Actions
  # @owners { team: care, domain: actions, followers: [unified-workflow] }
  module ActionPartnerships
    extend T::Sig
    include Core::API

    add_api ActionsAPI::V2::ActionPartnershipsEndpoint::Client
    self.action_partnerships_endpoint = ActionsEngine::ActionPartnerships::Endpoint
  end
end
```

**Key elements**:

1. **`include Core::API`** - Provides client switching logic
2. **`add_api Client`** - Adds generated client module methods
3. **`self.{resource}_endpoint = Endpoint`** - Configure which endpoint to use locally

**What this provides**:
- `Actions.action_partnerships.fetch_all` method
- Automatic local vs RPC switching based on environment
- Type-safe client methods

**How it works**:
```ruby
# When you call:
Actions.action_partnerships.fetch_all

# Core::API checks:
# 1. Is Engine mounted locally? → Call Engine::Endpoint.new.fetch_all (fast)
# 2. Is RPC configured? → Use RPCClient.new.fetch_all (HTTP call)
# 3. Default: Use local endpoint
```

**Trade-offs**:
- ✅ Clean API (`Actions.action_partnerships.fetch_all`)
- ✅ Automatic local/RPC switching
- ✅ Type-safe (Sorbet knows about methods)
- ✅ Consistent pattern across all resources
- ❌ Requires understanding Core::API internals
- ❌ One module per resource (some boilerplate)

**Common Error**: Wrong endpoint class name

```ruby
# ❌ Wrong: Endpoint class doesn't match
module ActionPartnerships
  include Core::API
  add_api ActionsAPI::V2::ActionPartnershipsEndpoint::Client
  self.action_partnerships_endpoint = ActionTypes::Endpoint  # Wrong!
end

# ✅ Correct: Name matches
module ActionPartnerships
  include Core::API
  add_api ActionsAPI::V2::ActionPartnershipsEndpoint::Client
  self.action_partnerships_endpoint = ActionsEngine::ActionPartnerships::Endpoint
end
```

---

### Pattern 6.2: Dotted Accessor Pattern [CRITICAL]

**Priority**: CRITICAL

**Purpose**: Expose sub-modules via clean, hierarchical API. Enables `Actions.action_partnerships` syntax.

**When to use**: Always. Parent modules must expose resource submodules.

**Implementation**:

**In parent module** (`app/services/actions.rb`):
```ruby
module Actions
  extend T::Sig
  include Core::API

  # ... other code ...

  # Expose ActionPartnerships submodule
  sig { returns(T.class_of(ActionPartnerships)) }
  def self.action_partnerships
    ActionPartnerships
  end

  # Expose other submodules
  sig { returns(T.class_of(ActionTypes)) }
  def self.action_types
    ActionTypes
  end

  sig { returns(T.class_of(ActionPods)) }
  def self.action_pods
    ActionPods
  end
end
```

**Usage**:
```ruby
# Instead of:
Actions::ActionPartnerships.fetch_all  # Works but verbose

# Use:
Actions.action_partnerships.fetch_all  # Clean dotted access
```

**Pattern benefits**:
- Discoverable API (IDE autocomplete)
- Reads like natural language
- Consistent across all resources
- Sorbet type-checked

**Trade-offs**:
- ✅ Clean, readable API
- ✅ IDE autocomplete works
- ✅ Type-safe with Sorbet
- ❌ Must add accessor for each submodule
- ❌ Extra method per resource

---

### Pattern 6.3: Core API File Structure [PREFERRED]

**Priority**: PREFERRED

**Purpose**: Consistent file organization for Core API modules.

**When to use**: Always.

**File Structure**:

```
app/services/{domain}/
├── {domain}.rb                    # Parent module with dotted accessors
└── {resource}.rb                  # Core API module
```

Examples:
```
app/services/actions/
├── actions.rb                     # Actions module with .action_partnerships accessor
└── action_partnerships.rb         # ActionPartnerships Core API module
```

**Parent module** (`actions.rb`):
```ruby
module Actions
  extend T::Sig
  include Core::API

  # Dotted accessor
  sig { returns(T.class_of(ActionPartnerships)) }
  def self.action_partnerships
    ActionPartnerships
  end
end
```

**Resource module** (`action_partnerships.rb`):
```ruby
module Actions
  module ActionPartnerships
    extend T::Sig
    include Core::API

    add_api ActionsAPI::V2::ActionPartnershipsEndpoint::Client
    self.action_partnerships_endpoint = ActionsEngine::ActionPartnerships::Endpoint
  end
end
```

**Trade-offs**:
- ✅ Predictable file locations
- ✅ One file per resource
- ✅ Easy to find and maintain
- ❌ Boilerplate (parent + resource modules)

---

### Pattern 6.4: Endpoint Configuration (Local vs RPC) [PREFERRED]

**Priority**: PREFERRED

**Purpose**: Configure whether to use local endpoint or RPC client. Core::API handles switching automatically.

**When to use**: When you need to understand or debug client behavior.

**How it works**:

**Default behavior** (Engine mounted locally in Scriptdash):
```ruby
module Actions
  module ActionPartnerships
    include Core::API
    add_api ActionsAPI::V2::ActionPartnershipsEndpoint::Client

    # Local endpoint - Engine runs in same process
    self.action_partnerships_endpoint = ActionsEngine::ActionPartnerships::Endpoint
  end
end

# Calling this:
Actions.action_partnerships.fetch_all

# Internally does:
ActionsEngine::ActionPartnerships::Endpoint.new.fetch_all  # ← Direct call, fast
```

**RPC mode** (Engine in separate service):
```ruby
# If ENV['ACTIONS_API_BASE_URL'] is set:
# OR if endpoint not configured:
# Core::API automatically uses RPCClient

Actions.action_partnerships.fetch_all

# Internally does:
ActionsAPI::V2::ActionPartnershipsEndpoint::RPCClient.new.fetch_all
# Makes HTTP GET to http://actions-engine/v2/action_partnerships/fetch_all
```

**When RPC is used**:
1. `ENV['ACTIONS_API_BASE_URL']` is set (explicit RPC URL)
2. Endpoint not configured (`self.{resource}_endpoint` not set)
3. `Core::API::RPCClient.use_rpc?(service: 'actions_api')` returns true

**Trade-offs**:
- ✅ Automatic switching (no code changes needed)
- ✅ Local is fast (no network)
- ✅ RPC enables microservices
- ❌ Harder to debug (which path is being taken?)
- ❌ Configuration can be confusing

**Debugging tip**:
```ruby
# Check which endpoint is being used:
puts Actions.action_partnerships.action_partnerships_endpoint.class
# Local: ActionsEngine::ActionPartnerships::Endpoint
# RPC: ActionsAPI::V2::ActionPartnershipsEndpoint::RPCClient
```

---

## Layer 7: Permissions

### Pattern 7.1: Scriptdash Endpoint with Authorization [CRITICAL]

**Priority**: CRITICAL

**Purpose**: Add permissions check before delegating to Engine. Ensures only authorized users can access data.

**When to use**: Always. Every Scriptdash endpoint needs authorization.

**Implementation**:

```ruby
# typed: strict

module Actions
  module Wunderbar
    # @owners { team: care, domain: actions, followers: [unified-workflow] }
    class ActionPartnershipsEndpoint < Alto::Actions::Wunderbar::V1::ActionPartnershipsEndpoint::Interface::AbstractActionPartnershipsEndpoint
      extend T::Sig
      include Auth::CurrentAbility  # ← Provides current_ability
      include Alto::Actions::Wunderbar::V1::ActionPartnershipsEndpoint::Interface

      sig do
        override.returns(T::Array[ActionsAPI::Types::V2::ActionPartnership])
      end
      def fetch_all
        # Check permissions FIRST
        current_ability.authorize! :read, ActionsAPI::Types::V2::ActionPartnership

        # Then delegate to Engine
        Actions.action_partnerships.fetch_all
      end
    end
  end
end
```

**Key elements**:

1. **Include `Auth::CurrentAbility`** - Provides `current_ability` method
2. **`current_ability.authorize!`** - Raises CanCan::AccessDenied if unauthorized
3. **Check on TYPE, not model** - `ActionsAPI::Types::V2::ActionPartnership` (proto struct)
4. **Delegate after authorization** - `Actions.action_partnerships.fetch_all`

**Authorization flow**:
```
1. HTTP Request → Controller
2. Controller → Endpoint.fetch_all
3. Endpoint: current_ability.authorize!(:read, Type)
   ├─ Authorized → Continue to step 4
   └─ Unauthorized → Raise CanCan::AccessDenied (403 response)
4. Endpoint: Actions.action_partnerships.fetch_all (Engine call)
5. Return data to controller → HTTP response
```

**Trade-offs**:
- ✅ Enforces permissions at gateway
- ✅ Engine stays permission-agnostic
- ✅ Standard CanCan pattern
- ✅ Automatic 403 error handling
- ❌ One more layer of indirection
- ❌ Must define permissions in Ability classes

**Common Error**: Authorizing against model instead of type

```ruby
# ❌ Wrong: ActionPartnership is the model, not exposed to frontend
current_ability.authorize! :read, ActionPartnership

# ✅ Correct: Use the proto type
current_ability.authorize! :read, ActionsAPI::Types::V2::ActionPartnership
```

---

### Pattern 7.2: Ability Class Permission Definitions [CRITICAL]

**Priority**: CRITICAL

**Purpose**: Define which roles can perform which actions on which types.

**When to use**: Always. Add permissions for every new type exposed to frontend.

**Implementation**:

**In `app/models/abilities/ability.rb`** (role-specific methods):
```ruby
module Abilities
  class Ability
    include CanCan::Ability

    def ops(_wunderbar_user = nil)
      can :read, ActionsAPI::Types::V2::ActionPartnership
      can :read, ActionsAPI::Types::V2::ActionPod
      can :manage, ActionsAPI::V1::Types::ActionType
      # ... more permissions
    end

    def manager(_wunderbar_user = nil)
      can :read, ActionsAPI::Types::V2::ActionPartnership
      can :read, ActionsAPI::Types::V2::ActionPod
      # ... more permissions
    end

    def engineer(_wunderbar_user = nil)
      can :read, ActionsAPI::Types::V2::ActionPartnership
      # ... more permissions
    end
  end
end
```

**In `app/models/abilities/wunderbar_ability.rb`** (Wunderbar-specific):
```ruby
module Abilities
  class WunderbarAbility
    include CanCan::Ability

    def grant_abilities_for_role(role)
      case role
      when :engineer, :manager, :ops
        can :read, ActionsAPI::Types::V2::ActionPartnership
        can :read, ActionsAPI::Types::V2::ActionPod
      when :admin
        can :manage, ActionsAPI::Types::V2::ActionPartnership
      end
    end
  end
end
```

**Permission levels**:
- **`:read`** - Can view/fetch (FetchOne, FetchAll, Search)
- **`:create`** - Can create new records
- **`:update`** - Can modify existing records
- **`:destroy`** - Can delete records
- **`:manage`** - Can do anything (`:create`, `:read`, `:update`, `:destroy`)

**Trade-offs**:
- ✅ Centralized permission definitions
- ✅ Role-based access control
- ✅ Easy to audit ("who can do what?")
- ✅ Standard CanCan pattern
- ❌ Must update two files (Ability + WunderbarAbility)
- ❌ Easy to forget adding permissions

**Common Error**: Forgetting to update WunderbarAbility

```ruby
# ❌ Wrong: Only updated Ability.rb
# app/models/abilities/ability.rb
def ops
  can :read, ActionsAPI::Types::V2::NewType  # ← Added
end

# app/models/abilities/wunderbar_ability.rb (FORGOT TO UPDATE!)
def grant_abilities_for_role(role)
  # Missing: can :read, ActionsAPI::Types::V2::NewType
end

# Result: Permissions work in some contexts but not Wunderbar

# ✅ Correct: Update both files
```

---

### Pattern 7.3: Permission Testing in Endpoint [PREFERRED]

**Priority**: PREFERRED

**Purpose**: Verify that your endpoint checks permissions correctly.

**When to use**: Always test both authorized and unauthorized cases.

**Implementation**:

```ruby
require 'rails_helper'

RSpec.describe Actions::Wunderbar::ActionPartnershipsEndpoint do
  describe '#fetch_all' do
    let(:endpoint) { described_class.new }

    context 'with read permission' do
      before do
        ability = instance_double(Ability)
        allow(endpoint).to receive(:current_ability).and_return(ability)
        allow(ability).to receive(:authorize!).with(:read, ActionsAPI::Types::V2::ActionPartnership)
      end

      it 'allows access and delegates to Engine' do
        mock_data = [ActionsAPI::Types::V2::ActionPartnership.new(id: 1, name: 'Test', value: 'test')]
        allow(Actions.action_partnerships).to receive(:fetch_all).and_return(mock_data)

        result = endpoint.fetch_all

        expect(result).to eq(mock_data)
      end
    end

    context 'without permission' do
      before do
        ability = instance_double(Ability)
        allow(endpoint).to receive(:current_ability).and_return(ability)
        allow(ability).to receive(:authorize!).and_raise(CanCan::AccessDenied)
      end

      it 'raises AccessDenied' do
        expect {
          endpoint.fetch_all
        }.to raise_error(CanCan::AccessDenied)
      end
    end
  end
end
```

**What to test**:
1. **With permission** - Call succeeds, delegates to Engine
2. **Without permission** - Raises CanCan::AccessDenied
3. **Correct permission checked** - `:read` action, correct Type

**Trade-offs**:
- ✅ Verifies authorization works
- ✅ Catches missing `authorize!` calls
- ✅ Documents expected behavior
- ❌ More test code to maintain

---

## Pattern Summary

**Layers 6-7 extracted**: 7 patterns (5 CRITICAL, 2 PREFERRED)

**Key takeaways**:
1. Core API modules wire up Engine clients with local/RPC switching
2. Dotted accessors provide clean API (`Actions.action_partnerships.fetch_all`)
3. Scriptdash endpoints check permissions, then delegate to Engine
4. Permissions defined in Ability and WunderbarAbility classes
5. Always test both authorized and unauthorized cases

**Common mistakes**:
- Forgetting to update WunderbarAbility when adding permissions
- Authorizing against model instead of proto type
- Not checking which endpoint is being used (local vs RPC)
- Missing dotted accessor in parent module

**Iteration 4 Complete!**

**Next**: Validation spot-checks in Scriptdash (Iteration 5)
