
---

## Layer 3: Implementation - Engine Endpoints

The implementation layer contains the business logic for your endpoints. This is where you write the actual code that fetches data, transforms it, and returns proto structs.

### Pattern 3.1: Endpoint Class Structure [CRITICAL]

**Priority**: CRITICAL

**Purpose**: Extend the generated abstract interface to implement your endpoint logic with type safety.

**When to use**: Always. Every endpoint needs an implementation class.

**Implementation**:

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
        # Implementation here
      end
    end
  end
end
```

**Key elements**:
- `# typed: strict` - Enable Sorbet strict mode for type safety
- Extend the generated `AbstractXxxEndpoint` class
- `extend T::Sig` - Enable Sorbet type signatures
- Use `sig { override.returns(...) }` for all method signatures
- `@owners` annotation - Track team ownership

**Trade-offs**:
- ✅ Type safety catches errors at compile time
- ✅ IDE autocomplete and refactoring support
- ✅ Must implement all abstract methods (enforced by Sorbet)
- ❌ Must match exact signature from abstract class
- ❌ Sorbet can be strict about types

**Common Error**: Forgetting `override` keyword

```ruby
# ❌ Wrong: Missing override
sig { returns(T::Array[ActionsAPI::Types::V2::ActionPartnership]) }
def fetch_all
end

# ✅ Correct: Include override
sig { override.returns(T::Array[ActionsAPI::Types::V2::ActionPartnership]) }
def fetch_all
end
```

---

### Pattern 3.2: FetchAll - Simple Implementation [CRITICAL]

**Priority**: CRITICAL

**Purpose**: Fetch all records from database and convert to proto structs. Simplest pattern for small datasets.

**When to use**: Small reference data (< 1000 records), dropdowns, static lists.

**Implementation**:

```ruby
sig do
  override.returns(T::Array[ActionsAPI::Types::V2::ActionPartnership])
end
def fetch_all
  ActionPartnership.all.map do |action_partnership|
    ActionsAPI::Types::V2::ActionPartnership.new(
      id: action_partnership.id,
      name: action_partnership.name,
      value: action_partnership.value,
    )
  end
end
```

**Pattern breakdown**:
1. `Model.all` - Fetch all records from database
2. `.map` - Transform each record
3. `ProtoStruct.new(...)` - Create proto struct directly
4. Map ActiveRecord attributes to proto fields

**When NOT to use**:
- Large datasets (use pagination or filtering)
- Complex transformations (use adapter pattern)
- Need eager loading (use includes)

**Trade-offs**:
- ✅ Simple, easy to understand
- ✅ No extra classes needed
- ✅ Good for simple types (few fields, no nesting)
- ❌ Not scalable for large datasets
- ❌ Tight coupling to database schema
- ❌ Harder to test transformations in isolation

---

### Pattern 3.3: FetchAll - With Adapter Pattern [PREFERRED]

**Priority**: PREFERRED

**Purpose**: Use adapter class to encapsulate transformation logic. Better separation of concerns and testability.

**When to use**: Complex transformations, nested objects, reusable conversion logic.

**Implementation**:

**Endpoint**:
```ruby
sig do
  override.params(ids: T::Array[Integer]).returns(T::Array[ActionsAPI::V1::Types::ActionType])
end
def fetch_all(ids:)
  action_types = TaskThreshold.active.order(:pod, :task_type)
  if ids.present?
    action_types = action_types.where(id: ids)
  end

  action_types.map { |action_type| ActionTypeAdapter.new(action_type).to_struct }
end
```

**Adapter**:
```ruby
# typed: strict

module ActionsEngine
  class ActionTypeAdapter
    extend T::Sig
    include Adapter::Timestamps

    sig { params(action_type: TaskThreshold).void }
    def initialize(action_type)
      @action_type = action_type
    end

    sig { returns(ActionsAPI::V1::Types::ActionType) }
    def to_struct
      ActionsAPI::V1::Types::ActionType.new(
        id: @action_type.id.to_i,
        labels: Adapter::ActionTypeLabels.new(@action_type).to_struct,
        tags: @action_type.tags,
        task_type: @action_type.task_type,
        tier: @action_type.tier,
        complete_in_minutes: @action_type.complete_in,
        escalate_in_minutes: @action_type.escalate_in,
        primary_roles: @action_type.primary_roles,
        secondary_roles: @action_type.secondary_roles,
        trigger_type: @action_type.trigger_type || '',
        description: @action_type.description,
        create_conditions: @action_type.create_conditions,
        created_at: timestamp!(@action_type.created_at),
        updated_at: timestamp!(@action_type.updated_at),
        deleted_at: timestamp(@action_type.deleted_at),
        support_windows: format_support_windows,
      )
    end

    private

    sig { returns(T::Array[ActionsAPI::V1::Types::SupportWindow]) }
    def format_support_windows
      @action_type.action_support_windows.map do |support_window|
        SupportWindowAdapter.new(support_window).to_struct
      end
    end
  end
end
```

**Adapter pattern benefits**:
- Transformation logic in separate class
- Reusable across multiple endpoints
- Testable in isolation
- Can compose multiple adapters
- Clean endpoint code

**Trade-offs**:
- ✅ Better separation of concerns
- ✅ Testable in isolation
- ✅ Reusable transformation logic
- ✅ Handles complex nesting (support_windows example)
- ❌ More files to maintain
- ❌ Extra indirection (one more class to understand)

---

### Pattern 3.4: FetchAll - Optional IDs Parameter [PREFERRED]

**Priority**: PREFERRED

**Purpose**: Support both "fetch all" and "fetch specific IDs" with one endpoint.

**When to use**: When you need flexibility - sometimes fetch everything, sometimes filter by IDs.

**Implementation**:

```ruby
sig do
  override.params(ids: T::Array[Integer]).returns(T::Array[ActionsAPI::V1::Types::ActionType])
end
def fetch_all(ids:)
  action_types = TaskThreshold.active.order(:pod, :task_type)
  
  # Apply ID filter only if IDs provided
  if ids.present?
    action_types = action_types.where(id: ids)
  end

  action_types.map { |action_type| ActionTypeAdapter.new(action_type).to_struct }
end
```

**Pattern breakdown**:
1. Start with base query (`TaskThreshold.active.order(...)`)
2. Check if IDs provided (`if ids.present?`)
3. Apply filter conditionally (`.where(id: ids)`)
4. Transform results

**HTTP behavior**:
- `GET /v1/action_types/fetch_all` → Returns all action types
- `GET /v1/action_types/fetch_all?ids=1&ids=2` → Returns only IDs 1 and 2

**Trade-offs**:
- ✅ Flexible API (one endpoint, multiple use cases)
- ✅ Client can choose behavior
- ✅ Supports both dropdown (all) and detail (filtered) use cases
- ❌ Ambiguous semantics (document clearly!)
- ❌ Can't enforce "must provide IDs" at proto level

**Common Error**: Not handling empty array vs nil

```ruby
# ❌ Wrong: Empty array passes .present? check
if ids
  action_types = action_types.where(id: ids)  # WHERE id IN () - invalid SQL!
end

# ✅ Correct: Use .present? to check for nil OR empty
if ids.present?
  action_types = action_types.where(id: ids)
end
```

---

### Pattern 3.5: FetchOne Implementation [CRITICAL]

**Priority**: CRITICAL

**Purpose**: Fetch single record by ID. Standard pattern for detail views.

**When to use**: Whenever you need to retrieve one specific record.

**Implementation**:

**Simple (no adapter)**:
```ruby
sig { override.params(id: Integer).returns(ActionsAPI::Types::V2::ActionPartnership) }
def fetch_one(id:)
  partnership = ActionPartnership.find(id)
  ActionsAPI::Types::V2::ActionPartnership.new(
    id: partnership.id,
    name: partnership.name,
    value: partnership.value,
  )
end
```

**With adapter**:
```ruby
sig { override.params(id: Integer).returns(ActionsAPI::V1::Types::Action) }
def fetch_one(id:)
  action = Action.find(id)
  ActionAdapter.new(action).to_struct
end
```

**Pattern breakdown**:
1. `Model.find(id)` - Raises ActiveRecord::RecordNotFound if not found
2. Transform to proto struct (directly or via adapter)

**Error handling**:
```ruby
# ActiveRecord::RecordNotFound is automatically handled by Rails
# Returns HTTP 404 with error response
def fetch_one(id:)
  action = Action.find(id)  # Raises if not found - Rails handles it
  ActionAdapter.new(action).to_struct
end
```

**Trade-offs**:
- ✅ Simple, standard Rails pattern
- ✅ Automatic 404 handling (Rails middleware)
- ✅ No explicit error handling needed
- ❌ Can't customize error message easily
- ❌ Raises exception (not proto errors array)

---

### Pattern 3.6: Database Query Optimization [PREFERRED]

**Priority**: PREFERRED

**Purpose**: Use eager loading to avoid N+1 queries. Critical for performance.

**When to use**: When your proto struct includes related data (associations).

**Implementation**:

**Without optimization (N+1 problem)**:
```ruby
def fetch_all(ids:)
  actions = Action.find(ids)
  
  # Each action_adapter.to_struct triggers queries for:
  # - action.action_relations (1 query PER action)
  # - action.action_labels (1 query PER action)
  # - action.task_threshold (1 query PER action)
  actions.map { |action| ActionAdapter.new(action).to_struct }  # ← N+1!
end
```

**With optimization (eager loading)**:
```ruby
sig { override.params(ids: T::Array[Integer]).returns(T::Array[ActionsAPI::V1::Types::Action]) }
def fetch_all(ids:)
  actions = Action
    .includes(              # ← Eager load associations
      :action_relations,
      :action_labels,
      :task_threshold,
    )
    .find(ids)
    
  action_structs = actions.map { |action| ActionAdapter.new(action).to_struct }
  PrioritySort.new(action_structs).call
end
```

**What `.includes` does**:
- Loads associations in separate queries upfront
- `Action` query: 1 query
- `action_relations`: 1 query for ALL actions
- `action_labels`: 1 query for ALL actions  
- `task_threshold`: 1 query for ALL actions
- **Total: 4 queries instead of 1 + (3 * N) queries**

**How to identify what to include**:
1. Look at adapter's `to_struct` method
2. Find all `@model.association` calls
3. Add those associations to `.includes()`

**Trade-offs**:
- ✅ Eliminates N+1 queries
- ✅ Much faster for multiple records
- ✅ Reduces database load
- ❌ Slightly more memory usage (loads all data upfront)
- ❌ Need to maintain includes list as adapter changes

**Common Error**: Forgetting to add new associations to includes

```ruby
# Added new field to adapter:
def to_struct
  ActionsAPI::Types::V2::Action.new(
    ...
    priority: @action.priority_level.name,  # ← NEW: References priority_level
  )
end

# ❌ Wrong: Missing from includes
def fetch_all(ids:)
  Action.includes(:action_relations, :action_labels).find(ids)
end

# ✅ Correct: Add priority_level to includes
def fetch_all(ids:)
  Action.includes(:action_relations, :action_labels, :priority_level).find(ids)
end
```

---

### Pattern 3.7: Applying Scopes and Ordering [PREFERRED]

**Priority**: PREFERRED

**Purpose**: Apply business logic filters and consistent ordering to queries.

**When to use**: When you need to filter records or ensure consistent ordering.

**Implementation**:

```ruby
sig do
  override.params(ids: T::Array[Integer]).returns(T::Array[ActionsAPI::V1::Types::ActionType])
end
def fetch_all(ids:)
  # Start with base query including scopes
  action_types = TaskThreshold
    .active                    # ← Scope: WHERE deleted_at IS NULL
    .order(:pod, :task_type)   # ← Ordering: Consistent sort

  # Apply ID filter if provided
  if ids.present?
    action_types = action_types.where(id: ids)
  end

  action_types.map { |action_type| ActionTypeAdapter.new(action_type).to_struct }
end
```

**Common scopes**:
- `.active` - Exclude soft-deleted records
- `.published` - Only published content
- `.visible_to(user)` - Permission-based filtering

**Why ordering matters**:
- Consistent UX (same order every time)
- Testable (assertions don't break randomly)
- Predictable pagination

**Trade-offs**:
- ✅ Consistent results
- ✅ Business logic in one place (scope)
- ✅ Reusable across endpoints
- ❌ Hidden logic (scope implementation not visible in endpoint)
- ❌ Can't override scope easily

---

### Pattern 3.8: Post-Processing Results [OBSERVED]

**Priority**: OBSERVED

**Purpose**: Apply transformations or sorting that can't be done in SQL.

**When to use**: When you need to sort by calculated fields or apply business logic after fetching.

**Implementation**:

```ruby
sig { override.params(ids: T::Array[Integer]).returns(T::Array[ActionsAPI::V1::Types::Action]) }
def fetch_all(ids:)
  actions = Action
    .includes(:action_relations, :action_labels, :task_threshold)
    .find(ids)
    
  # Convert to structs first
  action_structs = actions.map { |action| ActionAdapter.new(action).to_struct }
  
  # Apply custom sorting based on priority logic
  PrioritySort.new(action_structs).call  # ← Post-processing
end
```

**When to use post-processing**:
- Sorting by calculated/derived fields
- Filtering based on complex business rules
- Applying transformations that depend on all records

**Trade-offs**:
- ✅ Flexible (can do things SQL can't)
- ✅ Testable sorting logic
- ❌ Can't use database indexes for sorting
- ❌ Must load all data into memory first
- ❌ Slower for large datasets

---

## Iteration 2 Summary

**Patterns extracted**: 8 CRITICAL + PREFERRED patterns for Engine implementation
**Files analyzed**:
- `engine-actions/app/services/actions_engine/action_partnerships/endpoint.rb`
- `engine-actions/app/services/actions_engine/actions/endpoint.rb`
- `engine-actions/app/services/actions_engine/action_types/endpoint.rb`
- `engine-actions/app/services/actions_engine/action_type_adapter.rb`

**Key patterns**:
- Endpoint class structure (extend Abstract, Sorbet strict)
- Three FetchAll styles: Simple, Adapter, Optional IDs
- FetchOne pattern (find by ID, adapter transformation)
- Adapter pattern for complex transformations
- Database optimization (includes for N+1)
- Scopes and ordering for consistency
- Post-processing for complex logic

**Next iteration**: Scriptdash patterns (Core API, permissions, delegation)

