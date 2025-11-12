# Core Orchestration Patterns

**Project Root**: /Users/chris.helma/workspace/personal/time-cop

**Pattern Coverage**: Patterns 1-6 from WorkflowDemoMixed extraction

**Focus**: Cross-language workflow orchestration, task queue routing, activity definitions, worker registration, and protobuf message structure

---

## Pattern 1: Cross-Language Activity Invocation [PRIORITY: CRITICAL]

**Purpose**: Enable workflows written in one language to invoke activities implemented in another language via Temporal's task queue routing.

**Problem Solved**: In polyglot systems, orchestration across multiple language runtimes must maintain type safety and clear routing semantics.

**Implementation**:

Ruby workflows invoke activities differently based on the target language:

- **Ruby activity** (same-language): Pass class reference
  ```ruby
  # See: ruby_worker/app/workflows/workflow_demo_mixed.rb:46-54
  response = Temporalio::Workflow.execute_activity(
    ActivitySayHelloRuby,  # Class reference
    request,
    task_queue: task_queues.ruby,
    schedule_to_close_timeout: 300,
  )
  ```

- **Python activity** (cross-language): Pass string name
  ```ruby
  # See: ruby_worker/app/workflows/workflow_demo_mixed.rb:62-69
  response = Temporalio::Workflow.execute_activity(
    'ActivitySayHelloPython',  # String name
    request,
    task_queue: task_queues.python,
    schedule_to_close_timeout: 300,
  )
  ```

**Activity Name Coordination**:
The string name in the workflow MUST match the activity's registered name:
- Python: `@activity.defn(name="ActivitySayHelloPython")` (python_worker/time_cop_worker/activities/activity_say_hello_python.py:8)
- Ruby workflow reference: `'ActivitySayHelloPython'` (ruby_worker/app/workflows/workflow_demo_mixed.rb:63)

**When to use**:
- Building polyglot workflow orchestration systems
- Migrating activities between languages without rewriting workflows
- Leveraging language-specific libraries for specific activities

**When NOT to use**:
- Single-language systems (use class/function references for better type safety)
- When workflow and activities will always be co-located in same language

**Trade-offs**:
- ✅ Language flexibility - activities can be implemented in any Temporal-supported language
- ✅ Incremental migration - move activities between languages without workflow changes
- ✅ Specialization - use best language for each activity's domain
- ❌ Type safety reduced for cross-language calls (string references vs class references)
- ❌ Refactoring difficulty - renaming activities requires string search across languages
- ❌ Runtime errors if activity names don't match (no compile-time validation)

**Related patterns**: Task Queue Routing (Pattern 2), Activity Definition Patterns (Pattern 4)

---

## Pattern 2: Task Queue Routing [PRIORITY: CRITICAL]

**Purpose**: Route activity execution to workers running specific language runtimes using Temporal's task queue mechanism.

**Problem Solved**: In polyglot systems, each worker listens on a language-specific task queue. Activities must specify their target queue to reach the correct worker.

**Implementation**:

**Worker Configuration**:
Each worker registers on a language-specific task queue:

- Ruby worker: `task_queue: EnvVars::RUBY_TASK_QUEUE` (ruby_worker/app/start_worker.rb:80)
- Python worker: `task_queue=PYTHON_TASK_QUEUE` (python_worker/time_cop_worker/main.py:67)

**Workflow Activity Invocation**:
Activities specify target task queue:
```ruby
# Ruby activity → Ruby task queue (ruby_worker/app/workflows/workflow_demo_mixed.rb:49)
task_queue: task_queues.ruby

# Python activity → Python task queue (ruby_worker/app/workflows/workflow_demo_mixed.rb:65)
task_queue: task_queues.python
```

**Task Queue Configuration**:
Base workflow class provides task queue access via configuration:
```ruby
# See: ruby_worker/app/workflows/workflow_definition.rb:9-16, 49-52
class WorkflowDefinition < Temporalio::Workflow::Definition
  class TaskQueues < T::Struct
    const :python, String
    const :ruby, String
  end

  def task_queues
    self.class.config.task_queues
  end
end
```

Default configuration sources from environment variables:
```ruby
# See: ruby_worker/app/workflows/workflow_definition.rb:18-23
DEFAULT_CONFIG = T.let(Config.new(
  task_queues: TaskQueues.new(
    python: EnvVars::PYTHON_TASK_QUEUE,
    ruby: EnvVars::RUBY_TASK_QUEUE,
  ),
), Config)
```

**When to use**:
- Polyglot systems with workers in multiple languages
- Scaling specific activity types independently (e.g., CPU-heavy Python workers vs IO-heavy Ruby workers)
- Isolating activities with different resource requirements

**When NOT to use**:
- Single-language systems (use single task queue)
- When all activities have identical resource requirements

**Trade-offs**:
- ✅ Language-specific worker deployment and scaling
- ✅ Clear routing semantics (activity → task queue → worker)
- ✅ Isolation between language runtimes
- ❌ Configuration complexity (must coordinate task queue names across workflows and workers)
- ❌ Deployment coordination (workers must be running for their task queues)

**Related patterns**: Cross-Language Activity Invocation (Pattern 1), Worker Registration (Pattern 5)

---

## Pattern 3: Workflow Base Class Abstraction [PRIORITY: PREFERRED]

**Purpose**: Provide shared configuration and utilities to all workflows via inheritance from a common base class.

**Problem Solved**: Workflows need access to task queue configuration, and potentially other shared resources, without duplicating configuration code.

**Implementation**:

**Base Class Definition**:
```ruby
# See: ruby_worker/app/workflows/workflow_definition.rb:6-53
class WorkflowDefinition < Temporalio::Workflow::Definition
  class TaskQueues < T::Struct
    const :python, String
    const :ruby, String
  end

  class Config < T::Struct
    const :task_queues, TaskQueues
  end

  DEFAULT_CONFIG = T.let(Config.new(
    task_queues: TaskQueues.new(
      python: EnvVars::PYTHON_TASK_QUEUE,
      ruby: EnvVars::RUBY_TASK_QUEUE,
    ),
  ), Config)

  def task_queues
    self.class.config.task_queues
  end

  def self.configure(python_task_queue:, ruby_task_queue:)
    # Allow runtime configuration override
  end
end
```

**Concrete Workflow Usage**:
```ruby
# See: ruby_worker/app/workflows/workflow_demo_mixed.rb:8
class WorkflowDemoMixed < WorkflowDefinition
  def execute(request)
    # Access task queues from base class
    Temporalio::Workflow.execute_activity(
      ActivitySayHelloRuby,
      request,
      task_queue: task_queues.ruby,  # From base class
      schedule_to_close_timeout: 300,
    )
  end
end
```

**When to use**:
- Multiple workflows need shared configuration (task queues, timeouts, retry policies)
- Cross-cutting concerns like logging, metrics, or activity helpers
- Polyglot systems where workflows need to know about multiple task queues

**When NOT to use**:
- Single workflow in the system
- When workflows have completely different configuration needs
- When composition is preferred over inheritance

**Trade-offs**:
- ✅ DRY principle - configuration defined once
- ✅ Type safety via Sorbet T::Struct
- ✅ Runtime configuration override capability
- ✅ Clear extension point for workflow-wide features
- ❌ Inheritance coupling (workflows depend on base class)
- ❌ Less flexible than composition-based approaches

**Related patterns**: Task Queue Routing (Pattern 2), Environment Variable Configuration (Pattern 20, see patterns_http_integration.md)

---

## Pattern 4: Activity Definition Patterns (Ruby vs Python) [PRIORITY: CRITICAL]

**Purpose**: Define activities with language-appropriate patterns while maintaining cross-language compatibility via protobuf.

**Problem Solved**: Different languages have different idioms for defining activities. The pattern must support both while ensuring interoperability.

**Implementation**:

**Ruby Activity Pattern** (class-based):
```ruby
# See: ruby_worker/app/activities/activity_say_hello_ruby.rb:6-18
class ActivitySayHelloRuby < Temporalio::Activity::Definition
  extend T::Sig

  sig { params(request: Timecop::Activities::ActivitySayHelloRequest)
          .returns(Timecop::Activities::ActivitySayHelloResponse) }
  def execute(request)
    puts "ActivitySayHelloRuby started with name: #{request.name}\n"

    sleep(rand(0.01..0.05))

    greeting = "Hello from a Ruby Worker, #{request.name}!"
    Timecop::Activities::ActivitySayHelloResponse.new(greeting: greeting)
  end
end
```

**Python Activity Pattern** (function-based with decorator):
```python
# See: python_worker/time_cop_worker/activities/activity_say_hello_python.py:8-16
@activity.defn(name="ActivitySayHelloPython")
def activity_say_hello_python(request: ActivitySayHelloRequest) -> ActivitySayHelloResponse:
    set_activity_logger(activity.logger)
    activity.logger.info(f"ActivitySayHelloPython started with name: {request.name}")

    time.sleep(random.uniform(0.01, 0.05))

    response = ActivitySayHelloResponse(greeting=f"Hello from a Python Worker, {request.name}!")

    return response
```

**Key Differences**:
1. **Ruby**: Class-based with `execute` method, extends `Temporalio::Activity::Definition`
2. **Python**: Function-based with `@activity.defn` decorator
3. **Naming**:
   - Ruby: Class name used for same-language invocation
   - Python: `name` parameter in decorator defines cross-language reference
4. **Type annotations**:
   - Ruby: Sorbet `sig` for type safety
   - Python: Function type hints
5. **Both**: Use protobuf request/response types for cross-language type safety

**When to use**:
- Implementing activities in any Temporal-supported language
- Maintaining language idioms while ensuring cross-language compatibility
- Type-safe activity definitions with clear input/output contracts

**When NOT to use**:
- N/A - this is the standard pattern for Temporal activities

**Trade-offs**:
- ✅ Language-appropriate idioms (classes in Ruby, functions in Python)
- ✅ Type safety within each language (Sorbet, type hints)
- ✅ Cross-language type safety via protobuf
- ✅ Clear activity contracts (request → response)
- ❌ Different patterns per language (learning curve for polyglot teams)
- ❌ Protobuf overhead for simple activities

**Related patterns**: Cross-Language Activity Invocation (Pattern 1), Protobuf Message Structure (Pattern 6)

---

## Pattern 5: Worker Registration Pattern [PRIORITY: CRITICAL]

**Purpose**: Register workflows and activities with Temporal workers using centralized lists for easy discovery and modification.

**Problem Solved**: Workers need to know which workflows and activities they should execute. Centralized lists make it easy to add/remove implementations.

**Implementation**:

**Ruby Worker Registration**:

1. **Define Lists** (ruby_worker/app/workflows/workflow_list.rb:7-11, ruby_worker/app/activities/activities_list.rb:7-11):
```ruby
WORKFLOW_LIST = [
  WorkflowDemoRuby,
  WorkflowDemoMixed,
  SummarizePatientContextWorkflow,
].freeze

ACTIVITIES_LIST = [
  ActivitySayHelloRuby,
  FetchPatientEventsActivity,
  CreatePatientEventsSummaryActivity,
].freeze
```

2. **Register with Worker** (ruby_worker/app/start_worker.rb:77-85):
```ruby
def self.build_temporal_worker(client)
  Temporalio::Worker.new(
    client: client,
    task_queue: EnvVars::RUBY_TASK_QUEUE,
    workflows: WORKFLOW_LIST,
    activities: ACTIVITIES_LIST,
    interceptors: [MetricsInterceptor.new],
  )
end
```

**Python Worker Registration**:

1. **Define List** (python_worker/time_cop_worker/activities/__init__.py:6-9):
```python
ACTIVITIES_LIST = [
    activity_say_hello_python,
    summarize_patient_events,
]
```

2. **Register with Worker** (python_worker/time_cop_worker/main.py:65-72):
```python
worker = Worker(
    client,
    task_queue=PYTHON_TASK_QUEUE,
    workflows=[WorkflowDemoPython],
    activities=ACTIVITIES_LIST,
    activity_executor=activity_executor,
    interceptors=[MetricsInterceptor()],
)
```

**When to use**:
- Any Temporal worker setup
- Systems with multiple workflows or activities
- Teams that frequently add/modify workflows and activities

**When NOT to use**:
- N/A - this is the standard pattern for Temporal workers

**Trade-offs**:
- ✅ Single location to add new workflows/activities
- ✅ Easy to see all registered implementations
- ✅ Compile-time errors if implementations don't exist
- ✅ Supports interceptors for cross-cutting concerns (metrics, logging)
- ❌ Must remember to add to list when creating new workflow/activity
- ❌ Worker restart required to pick up new registrations

**Related patterns**: Activity Definition Patterns (Pattern 4), Task Queue Routing (Pattern 2)

---

## Pattern 6: Protobuf Message Structure [PRIORITY: CRITICAL]

**Purpose**: Define type-safe message contracts for workflow and activity input/output that work across language boundaries.

**Problem Solved**: Cross-language systems need a language-neutral serialization format with strong type contracts.

**Implementation**:

**Workflow Messages** (protos/workflow_demo_mixed.proto:1-13):
```protobuf
syntax = "proto3";

package timecop.workflows;

// The request message for WorkflowDemoMixed
message WorkflowDemoMixedRequest {
  string name = 1;
}

// The response message for WorkflowDemoMixed
message WorkflowDemoMixedResponse {
  string history_json = 1;
}
```

**Activity Messages** (protos/activity_say_hello.proto:1-13):
```protobuf
syntax = "proto3";

package timecop.activities;

// The request message containing the person's name.
message ActivitySayHelloRequest {
  string name = 1;
}

// The response message containing the greeting.
message ActivitySayHelloResponse {
  string greeting = 1;
}
```

**Usage Pattern**:
1. Define `.proto` file with Request/Response message pair
2. Generate language-specific classes (see patterns_type_safety.md Patterns 9-15)
3. Use generated classes in workflow/activity signatures:
   - Ruby: `sig { params(request: Timecop::Activities::ActivitySayHelloRequest).returns(Timecop::Activities::ActivitySayHelloResponse) }`
   - Python: `def activity_say_hello_python(request: ActivitySayHelloRequest) -> ActivitySayHelloResponse:`

**Naming Conventions**:
- **Workflow messages**: `Workflow<Name>Request` / `Workflow<Name>Response`
- **Activity messages**: `Activity<Name>Request` / `Activity<Name>Response`
- **Packages**: `timecop.workflows` / `timecop.activities`

**When to use**:
- Cross-language communication (workflows → activities, dispatcher → workflows)
- Any input/output that needs version compatibility guarantees
- Systems requiring backward/forward compatibility

**When NOT to use**:
- Internal single-language communication (can use native types)
- Prototypes where schema evolution isn't a concern

**Trade-offs**:
- ✅ Language-neutral serialization format
- ✅ Strong type contracts across languages
- ✅ Backward/forward compatibility via protobuf versioning
- ✅ Generated code provides type safety in statically-typed languages
- ❌ Schema management overhead (must regenerate on changes)
- ❌ Learning curve for protobuf syntax
- ❌ Additional build step required

**Related patterns**: Activity Definition Patterns (Pattern 4), Centralized Proto Generation (Pattern 10, see patterns_type_safety.md)

---

## Summary

**Pattern Count**: 6 patterns

**Priority Breakdown**:
- **CRITICAL**: 5 patterns (1, 2, 4, 5, 6)
- **PREFERRED**: 1 pattern (3)

**Key Architectural Insights**:
- Ruby workflows can orchestrate both Ruby and Python activities via string names and task queue routing
- Task queues are the fundamental routing mechanism for polyglot systems
- Protobuf provides language-neutral type contracts
- Pattern accommodates language idioms (classes in Ruby, functions in Python) while maintaining interoperability
- Base class abstraction centralizes configuration (task queues) across workflows

**Related Pattern Files**:
- **Type Safety**: patterns_type_safety.md (Patterns 9-15) - Protobuf generation and version management
- **Production Readiness**: patterns_production.md (Patterns 7-8) - Timeouts and metrics
- **HTTP Integration**: patterns_http_integration.md (Patterns 16-20) - Dispatcher and workflow triggering
