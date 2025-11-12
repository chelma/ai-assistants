# Temporal Workflow Orchestration Patterns

**Project Root**: /Users/chris.helma/workspace/personal/time-cop

**Extraction Date**: 2025-11-10

**Source**: WorkflowDemoMixed implementation demonstrating cross-language workflow orchestration

---

## Iteration 1: Core Workflow & Activities Patterns

This section documents patterns extracted from analyzing 13 files (~800 lines) covering workflow definitions, activity implementations, and worker registration.

---

## Pattern 1: Cross-Language Activity Invocation [PRIORITY: CRITICAL]

**Purpose**: Enable workflows written in one language to invoke activities implemented in another language via Temporal's task queue routing.

**Problem Solved**: In polyglot systems, you need to orchestrate work across multiple language runtimes while maintaining type safety and clear routing semantics.

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

**Related patterns**: Task Queue Routing, Activity Name Coordination

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

**Related patterns**: Cross-Language Activity Invocation, Worker Registration

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

**Related patterns**: Task Queue Routing, Configuration Management

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

**Related patterns**: Cross-Language Activity Invocation, Activity Registration

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

**Related patterns**: Activity Definition Patterns, Task Queue Routing

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
2. Generate language-specific classes (covered in Iteration 2)
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

**Related patterns**: Activity Definition Patterns, Centralized Proto Generation (Iteration 2)

---

## Pattern 7: Timeout Configuration [PRIORITY: PREFERRED]

**Purpose**: Configure activity execution timeouts to handle failures and prevent workflows from hanging indefinitely.

**Problem Solved**: Activities can fail, hang, or take unexpectedly long. Timeouts provide guarantees about maximum execution time.

**Implementation**:

**Activity-Level Timeouts**:
```ruby
# See: ruby_worker/app/workflows/workflow_demo_mixed.rb:46-51
response = Temporalio::Workflow.execute_activity(
  ActivitySayHelloRuby,
  request,
  task_queue: task_queues.ruby,
  schedule_to_close_timeout: 300,  # 5 minutes maximum
)
```

**Timeout Types** (Temporal supports multiple):
- `schedule_to_close_timeout`: Maximum time from scheduling to completion (used in this pattern)
- `start_to_close_timeout`: Maximum execution time once started
- `schedule_to_start_timeout`: Maximum time activity can wait in queue

**Observed Values**:
- Both Ruby and Python activities use 300 seconds (5 minutes)
- Simple activities like "say hello" could use shorter timeouts
- Complex activities (LLM calls, external APIs) may need longer timeouts

**When to use**:
- All production activities (prevent indefinite hangs)
- Activities calling external services (network failures, slow responses)
- Long-running activities that could exceed expected duration

**When NOT to use**:
- Local testing (can be frustrating if timeouts are too short)
- When you want Temporal's default timeout behavior

**Trade-offs**:
- ✅ Prevents workflows from hanging indefinitely
- ✅ Clear expectations about activity duration
- ✅ Enables automatic retry logic on timeout
- ❌ Requires understanding of activity duration characteristics
- ❌ Too short: legitimate long-running activities fail
- ❌ Too long: slow failure detection

**Related patterns**: Cross-Language Activity Invocation, Retry Policies (not yet extracted)

---

## Pattern 8: Metrics Emission for Workflow Observability [PRIORITY: CRITICAL]

**Purpose**: Configure workers to emit metrics for workflow and activity performance monitoring, enabling production observability and alerting.

**Problem Solved**: Production workflow systems require metrics for:
- Monitoring workflow/activity durations and success rates
- Tracking task queue depths and worker health
- Alerting on errors and SLA violations
- Capacity planning and performance optimization

Without metrics emission, workflows are black boxes in production.

**Implementation**:

**Note**: This pattern demonstrates Prometheus as the metrics backend, but the principle applies to any metrics system (Datadog, CloudWatch, StatsD, etc.). The Temporal SDK's telemetry configuration is the integration point.

**Ruby Metrics Configuration** (ruby_worker/app/start_worker.rb:42-64):
```ruby
def self.configure_runtime_metrics
  Temporalio::Runtime.default = Temporalio::Runtime.new(
    telemetry: Temporalio::Runtime::TelemetryOptions.new(
      metrics: Temporalio::Runtime::MetricsOptions.new(
        prometheus: Temporalio::Runtime::PrometheusMetricsOptions.new(
          bind_address: "0.0.0.0:#{EnvVars::METRICS_PORT}",
          histogram_bucket_overrides: histogram_bucket_overrides,
        ),
      ),
    ),
  )
end

def self.histogram_bucket_overrides
  {
    'time_cop_workflow_durations_ms' => [1, 5, 10, 25, 50, 100, 250, 500, 1_000, 2_500, 5_000, 10_000],
    'time_cop_activity_durations_ms' => [1, 5, 10, 25, 50, 100, 250, 500, 1_000, 2_500, 5_000, 10_000],
  }
end
```

**Python Metrics Configuration** (python_worker/time_cop_worker/main.py:36-50):
```python
Runtime.set_default(
    Runtime(
        telemetry=TelemetryConfig(
            metrics=PrometheusConfig(
                bind_address=f"0.0.0.0:{METRICS_PORT}",
                histogram_bucket_overrides={
                    'time_cop_workflow_durations_ms': [1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000],
                    'time_cop_activity_durations_ms': [1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000],
                }
            )
        )
    )
)
```

**Key Observations**:
- **Metrics emission is mandatory** for production systems (CRITICAL)
- **Backend choice is flexible**: Prometheus shown here, but any metrics system works via SDK telemetry config
- Both workers use identical histogram buckets (synchronization challenge noted via `# TODO`)
- Custom histogram buckets tailored to expected duration ranges (1ms to 10s) - PREFERRED optimization
- Metrics exposed on configurable port via environment variable
- Prometheus example: Metrics available at `http://0.0.0.0:<METRICS_PORT>/metrics`

**When to use**:
- **All production workers** (CRITICAL for observability)
- Any metrics backend that integrates with Temporal SDK (Prometheus, Datadog, CloudWatch, etc.)
- Performance monitoring and SLO tracking
- Debugging workflow/activity latency issues

**When NOT to use**:
- Local development (unless testing metrics integration)
- When no metrics infrastructure is available (but this should be rare in production)

**Trade-offs**:
- ✅ Production-grade observability (CRITICAL requirement)
- ✅ Temporal SDK provides metrics backend abstraction (flexible choice)
- ✅ Custom histogram buckets enable accurate percentile calculations (PREFERRED optimization)
- ✅ Standard integration patterns for popular backends (Prometheus, Datadog, etc.)
- ❌ Configuration duplication across languages (noted in TODO comments)
- ❌ Requires metrics infrastructure deployment (Prometheus, Datadog agent, etc.)
- ❌ Backend-specific configuration (Prometheus config differs from Datadog config)

**Related patterns**: Worker Registration, Metrics Interceptor (implementation not yet extracted)

---

## Summary: Iteration 1 Patterns

**Files Analyzed**: 13 files, ~650 lines

**Pattern Categories**:
1. **Cross-language orchestration** (Patterns 1, 2, 4)
2. **Workflow/Activity abstractions** (Patterns 3, 4, 5)
3. **Type safety & contracts** (Pattern 6)
4. **Production readiness** (Patterns 7, 8)

**Priority Breakdown**:
- **CRITICAL**: 6 patterns (cross-language invocation, task queue routing, activity definitions, worker registration, protobuf messages, metrics emission)
- **PREFERRED**: 2 patterns (workflow base class, timeout configuration)

**Key Insights**:
- Ruby workflows can orchestrate both Ruby and Python activities via string names and task queue routing
- Task queues are the fundamental routing mechanism for polyglot systems
- Protobuf provides language-neutral type contracts
- Pattern accommodates language idioms (classes in Ruby, functions in Python) while maintaining interoperability
- Production concerns (timeouts, metrics) are first-class citizens in the pattern

**Next Iteration**: Protobuf schema management, centralized generation, and version enforcement patterns.

---

## Iteration 2: Protobuf & Type Safety Patterns

This section documents patterns extracted from analyzing 8 files (~600 lines) covering schema management, centralized generation, and version enforcement.

---

## Pattern 9: Single Source of Truth for Versions [PRIORITY: CRITICAL]

**Purpose**: Centralize all protobuf-related version requirements in one YAML file to ensure consistency across all consumers.

**Problem Solved**: In polyglot systems, protoc version and language-specific protobuf library versions must be compatible. Without centralized management, consumers can drift out of sync, leading to incompatible generated code and runtime errors.

**Implementation**:

**Version Configuration File** (protos/config/versions.yaml:1-12):
```yaml
# Single source of truth for protobuf tooling and library versions
# Used by centralized generation scripts and consumer validation scripts

protoc:
  required_version: "29.5"

python:
  protobuf_library: "5.29.*"

ruby:
  google_protobuf_gem: ">= 4.29.0, < 4.30"
```

**Key Principles**:
1. **One file defines all requirements** - protoc compiler + all language library versions
2. **Loaded by all validation scripts** - both centralized (protos/scripts/validate.py) and consumer-level (python_worker/scripts/validate_protoc.py, ruby_worker/Rakefile)
3. **Version alignment enforced** - protoc major version matches language library minor version (protobuf compatibility matrix)

**Usage Pattern**:
- **Centralized validation**: protos/scripts/validate.py reads this file before generation
- **Consumer validation**: Each worker validates its library version matches before copying generated files
- **Version updates**: Change one file, all consumers and generators adapt

**When to use**:
- All polyglot systems using protobuf for cross-language communication
- Systems with multiple deployment environments that need version consistency
- Teams where different engineers work on different language workers

**When NOT to use**:
- Single-language systems (library version can be in dependency file)
- Protobuf not used for cross-language serialization

**Trade-offs**:
- ✅ Single source of truth prevents version drift
- ✅ Easy to update versions (one file change)
- ✅ Clear documentation of compatibility requirements
- ✅ Enables validation automation across all consumers
- ❌ Requires all consumers to coordinate upgrades (can't upgrade independently)
- ❌ Additional file to maintain beyond language dependency files

**Related patterns**: Centralized Proto Generation, Two-Level Validation

---

## Pattern 10: Centralized Proto Generation [PRIORITY: CRITICAL]

**Purpose**: Generate protobuf code for all languages from a single location using a unified workflow, then distribute to consumers.

**Problem Solved**: Without centralized generation, each consumer generates independently, leading to:
- Inconsistent protoc versions
- Duplicate generation logic
- No guarantee all consumers regenerate after schema changes
- Difficult to enforce generation best practices

**Implementation**:

**Centralized Makefile** (protos/Makefile:1-43):
```makefile
# Centralized protobuf generation Makefile

.PHONY: all python ruby validate clean help

# Default target
all: python ruby

# Validate protoc version
validate:
	@echo "Validating protoc version..."
	@python3 scripts/validate.py

# Generate Python protobuf interfaces
python: validate
	@bash scripts/generate_python.sh

# Generate Ruby protobuf interfaces and Sorbet RBI files
ruby: validate
	@bash scripts/generate_ruby.sh

# Clean all generated files
clean:
	@echo "Cleaning generated files..."
	@rm -rf generated/python generated/ruby generated/rbi
	@echo "✓ Clean complete"
```

**Generation Scripts**:

**Python Generation** (protos/scripts/generate_python.sh:19-46):
```bash
# Find all .proto files and generate Python code
cd "${PROTOS_DIR}"
proto_files=$(find . -name "*.proto" -type f)

# Generate for each proto file
for proto_file in $proto_files; do
    echo "  Processing: $proto_file"
    protoc \
        --proto_path=. \
        --python_out="${OUTPUT_DIR}" \
        --pyi_out="${OUTPUT_DIR}" \
        "$proto_file"
done

# Create __init__.py files in all directories
find "${OUTPUT_DIR}" -type d -exec touch {}/__init__.py \;
```

**Ruby Generation** (protos/scripts/generate_ruby.sh:44-52):
```bash
# Generate for each proto file
for proto_file in $proto_files; do
    echo "  Processing: $proto_file"
    protoc \
        --proto_path=. \
        --ruby_out="${RUBY_OUTPUT_DIR}" \
        --rbi_out="${RBI_OUTPUT_DIR}" \
        "$proto_file"
done
```

**Output Structure**:
```
protos/
├── generated/
│   ├── python/        # Python _pb2.py and _pb2.pyi files
│   ├── ruby/          # Ruby _pb.rb files
│   └── rbi/           # Sorbet .rbi type annotations for Ruby
```

**When to use**:
- Polyglot systems with multiple language consumers
- Systems where schema evolution needs careful coordination
- Teams that want to enforce generation best practices centrally

**When NOT to use**:
- Single consumer of protobufs (can generate inline)
- Tight coupling between schema and single consumer acceptable

**Trade-offs**:
- ✅ Consistent protoc version across all consumers
- ✅ DRY principle - generation logic defined once
- ✅ Easy to add new languages (one new script)
- ✅ Validation happens before any generation
- ✅ Output can be inspected before distribution to consumers
- ❌ Two-step workflow: generate centrally, then copy to consumers
- ❌ Requires build coordination (must run `make` before consumer builds)
- ❌ Generated files not directly in consumer source trees

**Related patterns**: Single Source of Truth, Consumer Copy Pattern

---

## Pattern 11: Two-Level Validation Pattern [PRIORITY: CRITICAL]

**Purpose**: Validate protobuf version compatibility at two levels: centralized (protoc only) and consumer-level (protoc + language library).

**Problem Solved**: Different stakeholders need different validation:
- **Centralized generation**: Only needs protoc validation (libraries aren't installed)
- **Consumers**: Need to validate protoc + their specific language library compatibility

**Implementation**:

**Level 1: Centralized Protoc Validation** (protos/scripts/validate.py:73-87):
```python
def main() -> int:
    """Main validation logic."""
    config = load_version_config()
    required_version = config['protoc']['required_version']
    installed_version = get_protoc_version()

    if validate_protoc_version(installed_version, required_version):
        print(f"✓ protoc version {installed_version} meets requirements ({required_version})")
        return 0
    else:
        return 1
```

**Validates**: System protoc version matches config/versions.yaml

**Level 2: Consumer-Level Validation**

**Python Consumer** (python_worker/scripts/validate_protoc.py:111-172):
```python
def main() -> int:
    """Main validation function."""
    # Load centralized version requirements
    config = load_version_config()
    required_protoc = config['protoc']['required_version']
    required_protobuf = config['python']['protobuf_library']

    # Check system protoc
    protoc_version = get_system_protoc_version()

    # Check Python protobuf library
    protobuf_version = get_python_protobuf_version()

    # Validate against requirements
    errors = []

    if not validate_protoc_requirement(protoc_version, required_protoc):
        errors.append(f"❌ protoc version mismatch...")

    if not validate_protobuf_requirement(protobuf_version, required_protobuf):
        errors.append(f"❌ Python protobuf version mismatch...")

    # Also validate internal compatibility (protoc major == protobuf minor)
    if not validate_compatibility(protoc_version, protobuf_version):
        errors.append(f"❌ protoc/protobuf internal incompatibility...")

    return 0 if not errors else 1
```

**Ruby Consumer** (ruby_worker/Rakefile:17-42):
```ruby
def validate_system_protoc
  puts '🔍 Validating protoc/protobuf compatibility for Ruby Worker...'

  config = load_version_config
  required_protoc = config['protoc']['required_version']
  required_gem = config['ruby']['google_protobuf_gem']

  protoc_version = installed_protoc_version
  gem_version = protobuf_gem_version

  errors = collect_validation_errors(
    protoc_version,
    required_protoc,
    gem_version,
    required_gem,
  )

  raise_errors_if_present(errors)
  puts '✅ All version checks passed!'
end
```

**Validation Hierarchy**:
```
Centralized (protos/scripts/validate.py)
├─ Protoc version only
└─ Runs before: make python, make ruby

Consumer Level (run before copying generated files)
├─ Python (python_worker/scripts/validate_protoc.py)
│  ├─ Protoc version
│  ├─ Python protobuf library version
│  └─ Compatibility: protoc.major == protobuf.minor
│
└─ Ruby (ruby_worker/Rakefile ProtosHelper)
   ├─ Protoc version
   ├─ Ruby google-protobuf gem version
   └─ Compatibility: protoc.major == gem.minor
```

**When to use**:
- Polyglot systems with multiple language consumers
- Systems where version mismatches cause subtle bugs
- CI/CD pipelines that need to fail fast on version issues

**When NOT to use**:
- Single-language systems (one validation sufficient)
- When protobuf library versions are tightly controlled (e.g., Docker with pinned versions)

**Trade-offs**:
- ✅ Fail fast at both generation and consumption time
- ✅ Clear error messages with resolution steps
- ✅ Catches incompatibilities before runtime
- ✅ Each consumer validates only what it needs
- ❌ Validation logic duplicated across languages (Ruby, Python, Shell)
- ❌ Must maintain validation scripts in sync with compatibility matrix

**Related patterns**: Single Source of Truth, Protoc Compatibility Rules

---

## Pattern 12: Consumer Copy Pattern [PRIORITY: CRITICAL]

**Purpose**: Consumers copy centrally-generated protobuf files to their local directories after validation, ensuring generated code is co-located with consumer code.

**Problem Solved**: Generated files need to be:
1. In consumer source tree for import resolution
2. Gitignored (not checked in, regenerated on build)
3. Validated before copying (ensure compatibility)

**Implementation**:

**Python Consumer** (python_worker/pyproject.toml:56-80):
```toml
[tool.poe.tasks.validate-protoc]
# Validate protoc/protobuf compatibility before generation
script = "scripts.validate_protoc:main"

[tool.poe.tasks.protos]
# Generate Python protobuf interfaces using centralized generation, then copy to local directory
deps = ["validate-protoc"]
shell = """
# Clean centralized generated files to ensure fresh start
make -C ../protos clean

# Generate using centralized Makefile
make -C ../protos python

# Clean out any existing local protobuf files
rm -rf time_cop_worker/protos
mkdir -p time_cop_worker/protos

# Copy generated files to local directory
cp -r ../protos/generated/python/* time_cop_worker/protos/

echo "✅ Python protobuf files copied to time_cop_worker/protos/"
"""
```

**Ruby Consumer** (ruby_worker/Rakefile:189-215):
```ruby
desc 'Generate Ruby classes from protobuf definitions using centralized generation'
task :generate do
  validate_system_protoc

  chdir '..' do
    # Clean centralized generated files to ensure fresh start
    sh 'make -C protos clean'

    # Generate using centralized Makefile
    sh 'make -C protos ruby'

    # Clean out any existing local protobuf files
    FileUtils.rm_rf('ruby_worker/protos')
    FileUtils.rm_rf('ruby_worker/sorbet/rbi/protos')
    FileUtils.mkdir_p('ruby_worker/protos')
    FileUtils.mkdir_p('ruby_worker/sorbet/rbi/protos')

    # Copy generated files to local directories
    FileUtils.cp_r(Dir.glob('protos/generated/ruby/*'), 'ruby_worker/protos/')
    FileUtils.cp_r(Dir.glob('protos/generated/rbi/*'), 'ruby_worker/sorbet/rbi/protos/')

    puts '✅ Ruby protobuf files copied to ruby_worker/protos/ and ruby_worker/sorbet/rbi/protos/'
  end
end
```

**Workflow**:
1. **Validate** consumer library compatibility
2. **Clean** centralized generated/ directory (fresh start)
3. **Generate** via centralized `make` target
4. **Clean** local consumer proto directories
5. **Copy** generated files to consumer-local paths
6. **Import** protobuf classes using relative imports

**Consumer Directory Structure**:
```
python_worker/
├── time_cop_worker/
│   ├── protos/                    # Gitignored - copied from ../protos/generated/python/
│   │   ├── __init__.py
│   │   ├── workflow_demo_mixed_pb2.py
│   │   ├── workflow_demo_mixed_pb2.pyi
│   │   └── ...
│   └── activities/
│       └── activity_say_hello_python.py  # Imports: from ..protos.activity_say_hello_pb2 import ...

ruby_worker/
├── protos/                         # Gitignored - copied from ../protos/generated/ruby/
│   ├── workflow_demo_mixed_pb.rb
│   └── ...
├── sorbet/rbi/protos/              # Gitignored - copied from ../protos/generated/rbi/
│   ├── workflow_demo_mixed_pb.rbi
│   └── ...
└── app/
    └── workflows/
        └── workflow_demo_mixed.rb  # Requires: require 'workflow_demo_mixed_pb'
```

**When to use**:
- Centralized generation pattern (Pattern 10)
- Generated files should be co-located with consumer source code
- Generated files should not be checked into version control

**When NOT to use**:
- Single consumer (can generate directly into source tree)
- Generated files are checked in (copy not needed, generate once)

**Trade-offs**:
- ✅ Generated files co-located with consumer code (easy imports)
- ✅ Gitignored files don't pollute version control
- ✅ Clean separation: centralized generation vs consumer consumption
- ✅ Validation happens before copying (fail early)
- ❌ Two-step process (generate, then copy)
- ❌ Must remember to run consumer task after schema changes
- ❌ Build tool dependency (poe, rake, make)

**Related patterns**: Centralized Proto Generation, Fresh Start Pattern

---

## Pattern 13: Protoc Compatibility Rules [PRIORITY: CRITICAL]

**Purpose**: Enforce protobuf's version compatibility matrix to prevent runtime serialization/deserialization errors.

**Problem Solved**: Protobuf has strict compatibility rules between protoc compiler version and language library versions. Mismatches cause:
- Different message encoding/decoding behavior
- Missing features in generated code
- Subtle runtime bugs in cross-language communication

**Official Compatibility Matrix**:
- **Python**: `protobuf_library.minor == protoc.major`
  - Example: protoc 29.5 requires Python protobuf 5.29.x
  - See: https://protobuf.dev/support/version-support/#python-support

- **Ruby**: `google_protobuf_gem.minor == protoc.major`
  - Example: protoc 29.5 requires Ruby google-protobuf 4.29.x
  - See: https://protobuf.dev/support/version-support/#ruby-support

**Implementation**:

**Python Compatibility Check** (python_worker/scripts/validate_protoc.py:98-109):
```python
def validate_compatibility(protoc_version: Tuple[int, int, int],
                          protobuf_version: Tuple[int, int, int]) -> bool:
    """
    Validate protoc/protobuf compatibility based on official support matrix.
    According to the matrix, the Python protobuf minor version should align
    with the protoc major version.  For example, if protoc is 29.x, then
    Python protobuf version should be 5.29.x.

    See: https://protobuf.dev/support/version-support/#python-support
    """
    protoc_major, _, _ = protoc_version
    _, protobuf_minor, _ = protobuf_version

    return protobuf_minor == protoc_major
```

**Ruby Compatibility Check** (ruby_worker/Rakefile:170-183):
```ruby
def compatible_versions?(protoc_version, protobuf_version)
  # Extract major versions
  protoc_match = protoc_version.match(/(\d+)\./)
  protoc_major = protoc_match[1].to_i
  protobuf_minor = protobuf_version.split('.')[1].to_i

  # The Ruby Protobuf gem minor version should match the protoc major version
  # See - https://protobuf.dev/support/version-support/#ruby-support
  protobuf_minor == protoc_major
end
```

**Version Configuration Example** (protos/config/versions.yaml):
```yaml
protoc:
  required_version: "29.5"    # Major = 29

python:
  protobuf_library: "5.29.*"  # Minor = 29 (matches protoc major)

ruby:
  google_protobuf_gem: ">= 4.29.0, < 4.30"  # Minor = 29 (matches protoc major)
```

**When to use**:
- All protobuf-based cross-language systems
- When upgrading protoc or language library versions
- CI/CD pipelines to prevent incompatible deployments

**When NOT to use**:
- N/A - this is a hard requirement from protobuf project

**Trade-offs**:
- ✅ Prevents subtle cross-language serialization bugs
- ✅ Catches incompatibilities before runtime
- ✅ Documents compatibility requirements explicitly
- ❌ Restricts version upgrades (all languages must upgrade together)
- ❌ Requires understanding of protobuf compatibility matrix

**Related patterns**: Two-Level Validation, Single Source of Truth

---

## Pattern 14: Multi-Output Generation (Ruby + RBI) [PRIORITY: PREFERRED]

**Purpose**: Generate both runtime Ruby code and Sorbet type annotations (.rbi files) from protobuf schemas to enable static type checking.

**Problem Solved**: Ruby is dynamically typed, but Sorbet enables gradual typing. Generated protobuf classes need type annotations so Sorbet can type-check code using protobuf messages.

**Implementation**:

**Ruby Generation with RBI** (protos/scripts/generate_ruby.sh:21-56):
```bash
# Check for protoc-gen-rbi
if ! command -v protoc-gen-rbi &> /dev/null; then
    echo "Error: protoc-gen-rbi is not installed" >&2
    echo "Install with: go install github.com/sorbet/protoc-gen-rbi@v0.2.0" >&2
    exit 1
fi

# Create output directories
mkdir -p "${RUBY_OUTPUT_DIR}"
mkdir -p "${RBI_OUTPUT_DIR}"

# Generate for each proto file
for proto_file in $proto_files; do
    echo "  Processing: $proto_file"
    protoc \
        --proto_path=. \
        --ruby_out="${RUBY_OUTPUT_DIR}" \
        --rbi_out="${RBI_OUTPUT_DIR}" \   # Sorbet type annotations
        "$proto_file"
done

echo "✓ Ruby protobuf generation complete:"
echo "  Ruby classes: ${RUBY_OUTPUT_DIR}"
echo "  Sorbet RBI files: ${RBI_OUTPUT_DIR}"
```

**Dual Output Structure**:
```
protos/generated/
├── ruby/                              # Runtime Ruby code
│   ├── workflow_demo_mixed_pb.rb
│   └── activity_say_hello_pb.rb
└── rbi/                               # Sorbet type annotations
    ├── workflow_demo_mixed_pb.rbi
    └── activity_say_hello_pb.rbi
```

**Consumer Integration** (ruby_worker/Rakefile:203-211):
```ruby
# Copy generated files to local directories
FileUtils.cp_r(Dir.glob('protos/generated/ruby/*'), 'ruby_worker/protos/')
FileUtils.cp_r(Dir.glob('protos/generated/rbi/*'), 'ruby_worker/sorbet/rbi/protos/')
```

**Sorbet Type Checking**:
Ruby workflows with `# typed: strict` can use protobuf messages with full type safety:
```ruby
# See: ruby_worker/app/workflows/workflow_demo_mixed.rb:23-24
sig { params(request: Timecop::Workflows::WorkflowDemoMixedRequest)
        .returns(Timecop::Workflows::WorkflowDemoMixedResponse) }
def execute(request)
  # Sorbet knows the types from .rbi files
end
```

**When to use**:
- Ruby codebases using Sorbet for gradual typing
- Teams that want static type checking for protobuf messages in Ruby
- Systems where type safety across language boundaries is critical

**When NOT to use**:
- Ruby codebases not using Sorbet (RBI files won't be used)
- Python (has built-in .pyi stub generation, not RBI)

**Trade-offs**:
- ✅ Static type checking for protobuf messages in Ruby
- ✅ Editor autocomplete and type hints
- ✅ Catch type errors at compile time (via Sorbet)
- ✅ Generated RBI files don't pollute runtime code
- ❌ Requires protoc-gen-rbi installation (Go-based tool)
- ❌ Additional output directory to manage
- ❌ Ruby-specific (other languages have different type annotation mechanisms)

**Related patterns**: Activity Definition Patterns (Ruby), Centralized Proto Generation

---

## Pattern 15: Fresh Start Pattern [PRIORITY: PREFERRED]

**Purpose**: Clean both centralized and local generated directories before regeneration to ensure stale files don't persist after schema changes.

**Problem Solved**: Without cleaning:
- Renamed/deleted .proto files leave orphaned generated files
- Schema changes can leave outdated code
- Hard to debug issues from stale generated files

**Implementation**:

**Python Consumer** (python_worker/pyproject.toml:65-79):
```toml
shell = """
# Clean centralized generated files to ensure fresh start
make -C ../protos clean

# Generate using centralized Makefile
make -C ../protos python

# Clean out any existing local protobuf files
rm -rf time_cop_worker/protos
mkdir -p time_cop_worker/protos

# Copy generated files to local directory
cp -r ../protos/generated/python/* time_cop_worker/protos/
```

**Ruby Consumer** (ruby_worker/Rakefile:193-211):
```ruby
chdir '..' do
  # Clean centralized generated files to ensure fresh start
  puts 'Cleaning centralized generated files...'
  sh 'make -C protos clean'

  # Generate using centralized Makefile
  puts 'Generating via centralized Makefile...'
  sh 'make -C protos ruby'

  # Clean out any existing local protobuf files
  FileUtils.rm_rf('ruby_worker/protos')
  FileUtils.rm_rf('ruby_worker/sorbet/rbi/protos')
  FileUtils.mkdir_p('ruby_worker/protos')
  FileUtils.mkdir_p('ruby_worker/sorbet/rbi/protos')

  # Copy generated files to local directories
  FileUtils.cp_r(Dir.glob('protos/generated/ruby/*'), 'ruby_worker/protos/')
end
```

**Centralized Clean** (protos/Makefile:24-28):
```makefile
clean:
	@echo "Cleaning generated files..."
	@rm -rf generated/python generated/ruby generated/rbi
	@echo "✓ Clean complete"
```

**Clean Stages**:
1. **Centralized clean** (`make -C protos clean`) - removes protos/generated/
2. **Centralized generate** (`make -C protos python|ruby`) - regenerates from scratch
3. **Local clean** (`rm -rf consumer/protos`) - removes consumer's local copy
4. **Local copy** (`cp -r ...`) - copies fresh generated files

**When to use**:
- All protobuf generation workflows
- When .proto files are renamed, moved, or deleted
- CI/CD pipelines (ensure reproducible builds)

**When NOT to use**:
- Incremental development where full regeneration is slow (though this pattern is usually fast enough)

**Trade-offs**:
- ✅ No stale generated files after schema changes
- ✅ Reproducible builds (always fresh generation)
- ✅ Easier debugging (know all files are current)
- ✅ Catch schema deletion issues immediately
- ❌ Slightly slower than incremental generation
- ❌ More disk I/O (delete, regenerate, copy)

**Related patterns**: Consumer Copy Pattern, Centralized Proto Generation

---

## Summary: Iteration 2 Patterns

**Files Analyzed**: 8 files, ~600 lines

**Pattern Categories**:
1. **Version management** (Patterns 9, 11, 13)
2. **Centralized generation** (Patterns 10, 12, 15)
3. **Language-specific concerns** (Pattern 14)

**Priority Breakdown**:
- **CRITICAL**: 5 patterns (single source of truth, centralized generation, two-level validation, consumer copy, compatibility rules)
- **PREFERRED**: 2 patterns (multi-output Ruby+RBI, fresh start)

**Key Insights**:
- Version management is sophisticated: single source of truth + two-level validation + compatibility matrix enforcement
- Centralized generation with consumer copy enables both consistency and co-located imports
- Ruby's Sorbet integration requires dual output (runtime .rb + type annotations .rbi)
- Fresh start pattern prevents subtle bugs from stale generated files
- Pattern enforces protobuf compatibility matrix as code (not just documentation)

**Architectural Significance**:
The protobuf pattern is CRITICAL for cross-language reliability. Version mismatches cause subtle serialization bugs that are hard to debug. This pattern treats version management as a first-class concern with validation at multiple levels.

**Next Iteration**: Dispatcher & HTTP Integration patterns (FastAPI endpoints, Temporal client management, workflow triggering).

---

## Iteration 3: Dispatcher & HTTP Integration Patterns

This section documents patterns extracted from analyzing 5 files (~400 lines) covering HTTP workflow triggering, Temporal client management, and endpoint organization.

---

## Pattern 16: FastAPI Lifespan Pattern for Temporal Client [PRIORITY: CRITICAL]

**Purpose**: Manage Temporal client lifecycle using FastAPI's lifespan pattern to ensure a single long-lived connection is shared across all HTTP requests.

**Problem Solved**: Creating a new Temporal client connection for every HTTP request is inefficient and can exhaust connection pools. The client should be created once at application startup and reused for all requests.

**Implementation**:

**Lifespan Context Manager** (dispatcher/dispatcher/temporal_client.py:8-14):
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    client = await Client.connect(
        target_host=TEMPORAL_HOST,
        namespace=TEMPORAL_NAMESPACE,
    )
    yield { "client": client }
```

**FastAPI Application Setup** (dispatcher/dispatcher/main.py:22):
```python
app = FastAPI(title="Time Cop Dispatcher", lifespan=lifespan)
```

**Dependency Injection** (dispatcher/dispatcher/temporal_client.py:16-17):
```python
def get_client(request: Request) -> Client:
    return request.state.client
```

**Usage in Endpoints** (dispatcher/dispatcher/api/ruby_worker.py:14, 28):
```python
@router.post("/demo")
async def ruby_demo(name: str, client = Depends(get_client)):
    # Use injected client
    handle = await client.start_workflow(...)
```

**Lifecycle**:
1. **Startup**: FastAPI calls lifespan manager, creates Temporal client
2. **Yield**: Client stored in app state, available to all requests
3. **Request**: Dependency injection provides client to endpoint handlers
4. **Shutdown**: Lifespan manager cleanup (implicit connection close)

**When to use**:
- HTTP services triggering Temporal workflows
- Any long-lived connection that should be shared across requests (database, message queue, etc.)
- FastAPI applications needing request-scoped resource injection

**When NOT to use**:
- Short-lived scripts (create client inline)
- When each request needs isolated client configuration

**Trade-offs**:
- ✅ Single connection reused across all requests (efficient)
- ✅ FastAPI dependency injection provides clean endpoint signatures
- ✅ Explicit lifecycle management (startup/shutdown)
- ✅ Type-safe (client type preserved through dependency injection)
- ❌ All requests share same client configuration (namespace, host)
- ❌ Requires understanding of FastAPI lifespan pattern

**Related patterns**: HTTP Workflow Triggering, Environment Variable Configuration

---

## Pattern 17: HTTP Workflow Triggering Pattern [PRIORITY: CRITICAL]

**Purpose**: Expose Temporal workflows via REST API endpoints, translating HTTP requests to Temporal workflow executions.

**Problem Solved**: External systems need to trigger workflows without Temporal SDK knowledge. HTTP provides a universal integration point.

**Implementation**:

**Endpoint Pattern** (dispatcher/dispatcher/api/ruby_worker.py:27-39):
```python
@router.post("/demo-mixed")
async def mixed_demo(name: str, client = Depends(get_client)):
    try:
        # 1. Create protobuf request from HTTP params
        request = WorkflowDemoMixedRequest(name=name)

        # 2. Start workflow via Temporal client
        handle = await client.start_workflow(
            "WorkflowDemoMixed",              # Workflow name
            request,                          # Protobuf request
            id=f"WorkflowDemoMixed-{name}-{int(time.time()*1000)}",  # Unique ID
            task_queue=RUBY_TASK_QUEUE,      # Target task queue
        )

        # 3. Return workflow identifiers
        return {"run_id": handle.result_run_id, "workflow_id": handle.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
```

**Workflow Triggering Parameters**:
- **Workflow name** (string): Must match registered workflow name in worker
- **Request** (protobuf): Typed workflow input
- **Workflow ID**: Unique identifier for idempotency and tracking
- **Task queue**: Routes workflow to correct language worker

**Response Format**:
```json
{
  "run_id": "abc-123-def",       // Temporal run ID
  "workflow_id": "WorkflowDemoMixed-alice-1699123456789"  // Client-provided ID
}
```

**Error Handling**:
- Catch all exceptions from Temporal client
- Convert to HTTP 500 with error details
- FastAPI automatically serializes HTTPException to JSON

**Multiple Endpoint Examples**:

**Python Worker Endpoint** (dispatcher/dispatcher/api/python_worker.py:11-23):
```python
@router.post("/demo")
async def python_demo(name: str, client = Depends(get_client)):
    request = WorkflowDemoPythonRequest(name=name)
    handle = await client.start_workflow(
        "WorkflowDemoPython",
        request,
        id=f"WorkflowDemoPython-{name}-{int(time.time()*1000)}",
        task_queue=PYTHON_TASK_QUEUE,  # Python task queue
    )
    return {"run_id": handle.result_run_id, "workflow_id": handle.id}
```

**Ruby Worker Endpoint** (dispatcher/dispatcher/api/ruby_worker.py:13-25):
```python
@router.post("/demo")
async def ruby_demo(name: str, client = Depends(get_client)):
    request = WorkflowDemoRubyRequest(name=name)
    handle = await client.start_workflow(
        "WorkflowDemoRuby",
        request,
        id=f"WorkflowDemoRuby-{name}-{int(time.time()*1000)}",
        task_queue=RUBY_TASK_QUEUE,  # Ruby task queue
    )
    return {"run_id": handle.result_run_id, "workflow_id": handle.id}
```

**When to use**:
- External systems need to trigger workflows (web apps, microservices, scheduled jobs)
- Workflows should be accessible without Temporal SDK installation
- Building user-facing APIs that orchestrate backend workflows
- Integration with non-Temporal systems

**When NOT to use**:
- Internal services that can use Temporal SDK directly (no HTTP overhead)
- High-throughput scenarios where HTTP adds unacceptable latency
- When workflow inputs are too large for HTTP request bodies

**Trade-offs**:
- ✅ Universal integration (any HTTP client can trigger workflows)
- ✅ No Temporal SDK required for clients
- ✅ Standard REST API conventions (POST for workflow start)
- ✅ Protobuf types ensure valid workflow inputs
- ✅ Workflow and run IDs returned for tracking
- ❌ HTTP overhead vs direct Temporal SDK calls
- ❌ Additional service to deploy and monitor (dispatcher)
- ❌ Must map HTTP params to protobuf requests

**Related patterns**: FastAPI Lifespan, Router-Based Organization, Workflow ID Generation

---

## Pattern 18: Router-Based Endpoint Organization [PRIORITY: PREFERRED]

**Purpose**: Organize HTTP endpoints by target worker using FastAPI routers for clear separation and prefix namespacing.

**Problem Solved**: Dispatcher exposes workflows from multiple workers. Without organization, endpoints become a flat list with unclear ownership.

**Implementation**:

**Router Definition by Worker**:

**Python Worker Router** (dispatcher/dispatcher/api/python_worker.py:9):
```python
router = APIRouter(prefix="/python")

@router.post("/demo")
async def python_demo(...):
    # Triggers Python worker workflows
```

**Ruby Worker Router** (dispatcher/dispatcher/api/ruby_worker.py:11):
```python
router = APIRouter(prefix="/ruby")

@router.post("/demo")
async def ruby_demo(...):
    # Triggers Ruby worker workflows

@router.post("/demo-mixed")
async def mixed_demo(...):
    # Triggers Ruby workflow (cross-language)
```

**Main Application Registration** (dispatcher/dispatcher/main.py:25-26):
```python
app.include_router(python_router)
app.include_router(ruby_router)
```

**Resulting URL Structure**:
```
POST /python/demo                       # Python worker workflows
POST /ruby/demo                         # Ruby worker workflows
POST /ruby/demo-mixed                   # Ruby worker workflows (cross-language)
POST /ruby/summarize-patient-context    # Ruby worker workflows (domain-specific)
```

**Directory Structure**:
```
dispatcher/dispatcher/
├── main.py                    # FastAPI app, router registration
├── api/
│   ├── python_worker.py      # /python/* endpoints
│   └── ruby_worker.py        # /ruby/* endpoints
```

**When to use**:
- Multiple routers for different domains, workers, or subsystems
- Clear URL namespacing (e.g., /python/*, /ruby/*)
- Large API with logical groupings
- When different teams own different router sets

**When NOT to use**:
- Single worker system (one router sufficient)
- When URL prefix doesn't align with logical grouping

**Trade-offs**:
- ✅ Clear endpoint organization by target worker
- ✅ URL prefix indicates which worker will execute workflow
- ✅ Easy to add new workers (new router file)
- ✅ File organization mirrors URL structure
- ✅ FastAPI automatically generates OpenAPI docs per router
- ❌ Additional indirection (main.py → router file → endpoint)
- ❌ Requires understanding FastAPI router pattern

**Related patterns**: HTTP Workflow Triggering, Task Queue Routing

---

## Pattern 19: Workflow ID Generation Pattern [PRIORITY: PREFERRED]

**Purpose**: Generate unique, deterministic workflow IDs that encode workflow type, input parameters, and timestamp for idempotency and debugging.

**Problem Solved**: Temporal requires unique workflow IDs. IDs should be:
- Unique (prevent duplicate workflow starts)
- Readable (human can identify workflow from ID)
- Deterministic (same inputs within short time window produce same ID for idempotency)

**Implementation**:

**ID Format**: `{WorkflowName}-{key_param}-{timestamp_ms}`

**Examples** (dispatcher/dispatcher/api/ruby_worker.py and python_worker.py):
```python
# Simple name-based workflow
id=f"WorkflowDemoMixed-{name}-{int(time.time()*1000)}"
# Result: "WorkflowDemoMixed-alice-1699123456789"

# Patient ID-based workflow
id=f"SummarizePatientContextWorkflow-{patient_id}-{int(time.time()*1000)}"
# Result: "SummarizePatientContextWorkflow-42-1699123456789"

# Python workflow
id=f"WorkflowDemoPython-{name}-{int(time.time()*1000)}"
# Result: "WorkflowDemoPython-bob-1699123456789"
```

**ID Components**:
1. **Workflow name**: Identifies workflow type
2. **Key parameter**: Domain-specific identifier (name, patient_id, order_id, etc.)
3. **Timestamp milliseconds**: Ensures uniqueness, provides rough execution time

**Why milliseconds, not seconds**:
- Multiple requests within same second get unique IDs
- Higher resolution for debugging (narrow time window)
- Still human-readable (convertible to datetime)

**Idempotency Behavior**:
- Same ID within short window (< ms resolution) → idempotent (Temporal rejects duplicate)
- Different ms timestamp → new workflow execution
- Balance: unique enough to avoid collisions, deterministic enough for debugging

**When to use**:
- All workflow triggering via HTTP or programmatic API
- When workflow IDs should be human-readable for debugging
- When key input parameters should be visible in workflow ID

**When NOT to use**:
- When workflow IDs must be truly random (security-sensitive scenarios)
- When timestamp shouldn't be exposed (though generally harmless)

**Trade-offs**:
- ✅ Human-readable IDs aid debugging
- ✅ Key parameters visible in Temporal UI
- ✅ Timestamp provides rough execution time
- ✅ Format is deterministic and understandable
- ❌ Not cryptographically secure (timestamp visible)
- ❌ Millisecond collisions possible under extreme load (rare)
- ❌ Long IDs if many parameters included

**Related patterns**: HTTP Workflow Triggering

---

## Pattern 20: Environment Variable Configuration [PRIORITY: PREFERRED]

**Purpose**: Externalize all deployment-specific configuration (hosts, ports, task queues) via environment variables with sensible defaults.

**Problem Solved**: Hard-coded configuration prevents deploying same code to multiple environments (dev, staging, prod) and makes local development difficult.

**Implementation**:

**Configuration Module** (dispatcher/dispatcher/env_vars.py:1-11):
```python
import os

TEMPORAL_HOST: str = os.getenv("TEMPORAL_HOST", "localhost:7233")
TEMPORAL_NAMESPACE: str = os.getenv("TEMPORAL_NAMESPACE", "time-cop")

PYTHON_TASK_QUEUE: str = os.getenv("PYTHON_TASK_QUEUE", "time-cop-python")
RUBY_TASK_QUEUE: str = os.getenv("RUBY_TASK_QUEUE", "time-cop-ruby")

DISPATCHER_PORT: int = int(os.getenv("DISPATCHER_PORT", "7070"))
METRICS_PORT: int = int(os.getenv("METRICS_PORT", "9090"))
```

**Configuration Categories**:
1. **Temporal Connection**: `TEMPORAL_HOST`, `TEMPORAL_NAMESPACE`
2. **Task Queues**: `PYTHON_TASK_QUEUE`, `RUBY_TASK_QUEUE`
3. **Service Ports**: `DISPATCHER_PORT`, `METRICS_PORT`

**Default Values**:
- **Local development defaults**: `localhost:7233`, `time-cop` namespace
- **Standard ports**: 7070 (dispatcher), 9090 (metrics)
- **Descriptive task queues**: `time-cop-python`, `time-cop-ruby`

**Usage in Code** (dispatcher/dispatcher/temporal_client.py:10-12):
```python
client = await Client.connect(
    target_host=TEMPORAL_HOST,       # From env_vars
    namespace=TEMPORAL_NAMESPACE,    # From env_vars
)
```

**Usage in Endpoints** (dispatcher/dispatcher/api/ruby_worker.py:21):
```python
handle = await client.start_workflow(
    "WorkflowDemoMixed",
    request,
    task_queue=RUBY_TASK_QUEUE,  # From env_vars
)
```

**Deployment Override** (Kubernetes, Docker Compose):
```yaml
env:
  - name: TEMPORAL_HOST
    value: temporal.production.svc.cluster.local:7233
  - name: TEMPORAL_NAMESPACE
    value: time-cop-production
  - name: DISPATCHER_PORT
    value: "8080"
```

**When to use**:
- All services deployed to multiple environments
- Configuration varies by environment (dev vs prod hosts)
- Local development needs different config than production
- Containerized deployments (Docker, Kubernetes)

**When NOT to use**:
- Configuration never changes (hard-code for clarity)
- Secrets (use secret management, not plain env vars)

**Trade-offs**:
- ✅ Same code deploys to all environments
- ✅ Local development works without code changes
- ✅ Clear defaults for common local setup
- ✅ Type annotations document expected types
- ✅ Single source of truth for configuration
- ❌ Must remember to set env vars in new environments
- ❌ Typos in env var names fail at runtime (not compile time)
- ❌ No validation of env var values (e.g., invalid port numbers)

**Related patterns**: FastAPI Lifespan (uses these vars), Task Queue Routing

---

## Summary: Iteration 3 Patterns

**Files Analyzed**: 5 files, ~400 lines

**Pattern Categories**:
1. **Client lifecycle management** (Pattern 16)
2. **HTTP integration** (Patterns 17, 19)
3. **Code organization** (Pattern 18)
4. **Configuration management** (Pattern 20)

**Priority Breakdown**:
- **CRITICAL**: 2 patterns (FastAPI lifespan for Temporal client, HTTP workflow triggering)
- **PREFERRED**: 3 patterns (router organization, workflow ID generation, environment variables)

**Key Insights**:
- FastAPI lifespan pattern enables efficient connection reuse with clean dependency injection
- HTTP workflow triggering provides universal integration point for non-Temporal systems
- Router-based organization aligns URL structure with worker architecture
- Workflow ID generation balances uniqueness with human readability for debugging
- Environment variable pattern enables same code across all environments

**Architectural Significance**:
The dispatcher is the integration boundary between external systems and Temporal workflows. These patterns ensure the boundary is efficient (single client connection), clear (router organization), and flexible (environment configuration). The HTTP API makes Temporal workflows accessible to any system that can make HTTP requests.

**Next Iteration**: Testing & Deployment patterns (Helm tests, Containerfiles, Kubernetes resources, load generation).

---

## Iteration 4: Testing & Deployment Patterns

This section documents patterns extracted from analyzing 6 files (~600 lines) covering end-to-end testing, containerization, and Kubernetes deployment.

---

## Pattern 21: Multi-Stage Container Build with Protobuf Generation [PRIORITY: CRITICAL]

**Purpose**: Build container images with protobuf generation during build, using multi-stage builds to separate build tools from runtime image.

**Problem Solved**: Container images need:
- Generated protobuf files (can't be gitignored and pulled from source control)
- Build tools (protoc, compilers) for generation
- Minimal runtime image without build tools (security, size)

**Implementation**:

**Ruby Worker Containerfile** (ruby_worker/Containerfile:1-83):

**Stage 1: Builder** (lines 2-56):
```dockerfile
FROM ruby:3.2-slim-bullseye AS builder

# Install system dependencies + protoc + protoc-gen-rbi
RUN apt-get update && apt-get install -y build-essential git curl unzip make python3 python3-pip
RUN pip3 install pyyaml  # For centralized validation script

# Install protoc (matches protos/config/versions.yaml)
ARG PROTOC_VERSION=29.5
RUN curl -LO https://github.com/protocolbuffers/protobuf/releases/download/v${PROTOC_VERSION}/protoc-${PROTOC_VERSION}-linux-aarch_64.zip && \
    unzip protoc-${PROTOC_VERSION}-linux-aarch_64.zip -d /usr/local/ && \
    chmod +x /usr/local/bin/protoc

# Install Go + protoc-gen-rbi (for Sorbet RBI generation)
RUN curl -LO https://go.dev/dl/go${GO_VERSION}.linux-arm64.tar.gz && \
    tar -C /usr/local -xzf go${GO_VERSION}.linux-arm64.tar.gz
RUN go install github.com/sorbet/protoc-gen-rbi@v0.2.0

# Copy source and generate protobuf
COPY protos ./protos
COPY ruby_worker/ ./ruby_worker
RUN bundle exec rake protos:generate  # Uses centralized generation
```

**Stage 2: Runtime** (lines 58-83):
```dockerfile
FROM ruby:3.2-slim-bullseye AS runtime

# Install only runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y curl ca-certificates

# Copy installed gems and application code from builder
COPY --from=builder /usr/local/bundle /usr/local/bundle
COPY --from=builder /workspace/ruby_worker ./

# Security: non-root user
RUN groupadd -g 1000 app && useradd -u 1000 -g app -m -s /bin/bash app
USER app

CMD ["bundle", "exec", "ruby", "bin/run.rb"]
```

**Python Worker Containerfile** (python_worker/Containerfile:1-68):

**Similar pattern with Python-specific tooling**:
- Builder installs: `protoc`, `poetry`, Python dependencies (including pyyaml for validation)
- Builder runs: `poetry run poe protos` (centralized generation with validation)
- Runtime stage: Minimal Python image, no build tools

**Key Characteristics**:
1. **protoc version** specified via `ARG` (matches `protos/config/versions.yaml`)
2. **Validation tools** installed (PyYAML for validation scripts)
3. **Language-specific plugins** (protoc-gen-rbi for Ruby Sorbet)
4. **Centralized generation** invoked during build (`rake protos:generate`, `poe protos`)
5. **Layer caching** optimized (dependencies before source code copy)
6. **Security**: Non-root user in runtime stage

**When to use**:
- Containerized applications using protobuf
- Generated files should not be in source control (gitignored)
- Build tools (compilers, protoc) should not be in production image
- Consistent build regardless of developer machine state

**When NOT to use**:
- Pre-generated protobufs checked into source (single-stage build sufficient)
- When build time doesn't matter (but multi-stage is still best practice)

**Trade-offs**:
- ✅ Reproducible builds (generated files always fresh)
- ✅ Minimal runtime image (no build tools, smaller attack surface)
- ✅ Version alignment enforced during build
- ✅ Generated files always match protoc version in image
- ❌ Slower builds (protobuf generation on every build)
- ❌ Requires understanding multi-stage Docker builds
- ❌ Build failures if protoc version not available for platform

**Related patterns**: Centralized Proto Generation, Consumer Copy Pattern

---

## Pattern 22: Helm Test for End-to-End Workflow Execution [PRIORITY: CRITICAL]

**Purpose**: Validate that deployed Temporal system can execute workflows end-to-end using Helm test pods.

**Problem Solved**: After deploying Temporal + workers + dispatcher, need to verify:
- Dispatcher HTTP API is accessible
- Workflows can be triggered and execute successfully
- Cross-language activity invocation works
- Full integration chain is functional

**Implementation**:

**Helm Test Manifest** (helm-chart/time-cop-stack/templates/tests/test-mixed-workflow-executes.yaml:1-80):

**Test Pod Structure**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  annotations:
    "helm.sh/hook": test                      # Marks as Helm test
    "helm.sh/hook-weight": "4"                # Execution order
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded  # Cleanup

spec:
  # Init container: Start workflow via dispatcher
  initContainers:
    - name: start-workflow
      image: curlimages/curl:8.7.1
      command:
        - /bin/sh
        - -c
        - |
          # 1. Start workflow via HTTP dispatcher
          RESPONSE=$(curl -fsS -X POST "http://{{ dispatcher-service }}:{{ port }}/ruby/demo-mixed?name=helm-test")

          # 2. Extract workflow_id and run_id from response
          WORKFLOW_ID=$(echo "$RESPONSE" | grep -o '"workflow_id":"[^"]*' | cut -d'"' -f4)
          RUN_ID=$(echo "$RESPONSE" | grep -o '"run_id":"[^"]*' | cut -d'"' -f4)

          # 3. Validate extraction succeeded
          if [ -z "$WORKFLOW_ID" ] || [ -z "$RUN_ID" ]; then
            echo "Failed to extract workflow_id or run_id from response"
            exit 1
          fi

          # 4. Save workflow ID for main container
          echo "$WORKFLOW_ID" > /shared/workflow_id
      volumeMounts:
        - name: shared-data
          mountPath: /shared

  # Main container: Wait for workflow completion
  containers:
    - name: wait-for-completion
      image: "temporal-admin-tools:{{ tag }}"
      command:
        - /bin/sh
        - -c
        - |
          # 1. Read workflow ID from init container
          WORKFLOW_ID=$(cat /shared/workflow_id)

          # 2. Wait for completion using Temporal CLI
          timeout 30 temporal workflow show \
            --address {{ temporal-frontend }}:7233 \
            --namespace {{ namespace }} \
            --workflow-id "$WORKFLOW_ID" \
            --follow

          # 3. Check exit code
          if [ $? -ne 0 ]; then
            echo "Error following workflow"
            exit 1
          fi

          echo "Workflow completed successfully!"
      volumeMounts:
        - name: shared-data
          mountPath: /shared

  volumes:
    - name: shared-data
      emptyDir: {}    # Shared volume between init container and main container

  restartPolicy: Never
```

**Test Workflow**:
1. **Init container** triggers workflow via dispatcher HTTP API
2. **Init container** parses response, extracts workflow ID, saves to shared volume
3. **Main container** reads workflow ID from shared volume
4. **Main container** uses `temporal CLI` with `--follow` to wait for completion
5. **Pod succeeds** if workflow completes, fails otherwise

**Running Tests**:
```bash
# Run all Helm tests
helm test time-cop-stack

# Check test results
kubectl logs time-cop-stack-test-mixed-workflow
```

**When to use**:
- All Helm charts deploying workflow orchestration systems
- Validation that full integration chain works after deployment
- CI/CD pipelines (automated validation)
- Post-upgrade validation

**When NOT to use**:
- Unit tests (Helm tests are for integration/E2E)
- Tests requiring external dependencies not in chart

**Trade-offs**:
- ✅ Validates full integration stack (dispatcher → Temporal → workers → activities)
- ✅ Runs in deployed environment (not local simulation)
- ✅ Helm test standard pattern (kubectl/helm know how to run)
- ✅ Automated cleanup via hook-delete-policy
- ✅ Can test cross-language workflows
- ❌ Requires deployed Temporal environment (not fast)
- ❌ Init container + main container coordination adds complexity
- ❌ Debugging test failures requires kubectl logs inspection

**Related patterns**: HTTP Workflow Triggering, Init Container Coordination

---

## Pattern 23: Init Container Pattern for Workflow Coordination [PRIORITY: PREFERRED]

**Purpose**: Use Kubernetes init containers to trigger workflows and pass workflow IDs to main containers for monitoring.

**Problem Solved**: Helm tests need to:
1. Start a workflow (returns workflow ID)
2. Wait for that specific workflow to complete
3. Share workflow ID between trigger step and wait step

**Implementation**:

**Init Container** (workflow trigger):
```yaml
initContainers:
  - name: start-workflow
    image: curlimages/curl:8.7.1
    command:
      - /bin/sh
      - -c
      - |
        # Start workflow, extract ID, save to shared volume
        RESPONSE=$(curl -X POST "http://dispatcher/ruby/demo-mixed?name=test")
        WORKFLOW_ID=$(echo "$RESPONSE" | grep -o '"workflow_id":"[^"]*' | cut -d'"' -f4)
        echo "$WORKFLOW_ID" > /shared/workflow_id
    volumeMounts:
      - name: shared-data
        mountPath: /shared
```

**Main Container** (workflow monitor):
```yaml
containers:
  - name: wait-for-completion
    image: temporal-admin-tools
    command:
      - /bin/sh
      - -c
      - |
        # Read workflow ID from init container
        WORKFLOW_ID=$(cat /shared/workflow_id)

        # Wait for completion
        temporal workflow show --workflow-id "$WORKFLOW_ID" --follow
    volumeMounts:
      - name: shared-data
        mountPath: /shared
```

**Shared Volume**:
```yaml
volumes:
  - name: shared-data
    emptyDir: {}    # In-memory volume, cleared when pod terminates
```

**Init Container Semantics**:
- **Init containers run to completion before main containers start**
- **Init containers run sequentially** (if multiple)
- **Pod fails if init container fails** (non-zero exit)

**Data Sharing via emptyDir**:
- **Lightweight**: In-memory volume (no disk I/O)
- **Ephemeral**: Cleared when pod terminates
- **Simple**: No external storage required

**When to use**:
- Multi-step Kubernetes jobs/tests requiring sequential execution
- Data passing between containers in same pod
- Setup/initialization tasks before main container starts

**When NOT to use**:
- Data should persist after pod termination (use PersistentVolume)
- Containers need to run concurrently (use regular containers, not init containers)

**Trade-offs**:
- ✅ Sequential execution guaranteed (init → main)
- ✅ Simple data passing via filesystem
- ✅ Failed init container prevents main container from running
- ✅ Standard Kubernetes pattern
- ❌ Can't run init and main containers concurrently
- ❌ Debug friction (must check init container logs separately)

**Related patterns**: Helm Test for Workflows

---

## Pattern 24: Load Generation Script for Observability Validation [PRIORITY: PREFERRED]

**Purpose**: Continuously trigger workflows to generate metrics/logs for validating observability stack integration.

**Problem Solved**: After deploying workflows + observability (Prometheus, Grafana, Loki):
- Need continuous workflow executions to generate metrics
- Need variety of workflow types to test different code paths
- Should be easy to start/stop for demonstrations and testing

**Implementation**:

**Load Generation Script** (bin/sample-load.sh:1-50+):
```bash
#!/bin/bash

# Cleanup handler for graceful exit
cleanup() {
    warning_msg "Stopping workflow generator."
    exit 0
}
trap cleanup INT

info_msg "Continuously starting workflows. Press Ctrl+C to stop."

# Validate dispatcher is accessible
if ! curl -f -s http://localhost:9005/healthz > /dev/null 2>&1; then
    warning_msg "Dispatcher not accessible at localhost:9005"
    exit 1
fi

# Infinite loop triggering workflows
while true; do
    section_header "Starting batch of workflows at $(date)"

    # Start Mixed Workflow (Ruby → Python + Ruby activities)
    curl -f -X POST 'http://localhost:9005/ruby/demo-mixed?name=Altoid'

    # Start Ruby Workflow (Ruby → Ruby activity)
    curl -f -X POST 'http://localhost:9005/ruby/demo?name=Altoid'

    # Start Python Workflow (Python → Python activity)
    curl -f -X POST 'http://localhost:9005/python/demo?name=Altoid'

    # Sleep between batches
    sleep 5
done
```

**Key Features**:
- **Graceful shutdown**: `trap cleanup INT` handles Ctrl+C
- **Health check**: Validates dispatcher before starting
- **Variety**: Multiple workflow types (mixed, Ruby-only, Python-only)
- **Continuous**: Infinite loop with sleep interval
- **Visibility**: Logs each workflow start with status

**Usage**:
```bash
# Prerequisites
make deploy               # Deploy full stack
make expose-services      # Expose localhost:9005

# Start load generation
./bin/sample-load.sh

# Stop (Ctrl+C)
```

**Workflow Types Generated**:
1. **Mixed workflows**: Tests cross-language pattern (Ruby → Python activities)
2. **Ruby workflows**: Tests same-language pattern
3. **Python workflows**: Tests Python worker in isolation

**Observability Impact**:
- **Metrics**: Workflow durations, activity durations, queue depths populate Prometheus
- **Logs**: Structured logs sent to Loki for querying
- **Grafana**: Dashboards show real-time metrics from generated workflows

**When to use**:
- Validating observability stack integration
- Load testing (increase frequency, add concurrent instances)
- Demonstrations showing live metrics/logs
- Local development workflow testing

**When NOT to use**:
- Production load testing (use proper load testing tools like k6, Locust)
- When workflow executions have side effects (database writes, external API calls)

**Trade-offs**:
- ✅ Simple bash script, easy to understand and modify
- ✅ Tests multiple workflow types in one script
- ✅ Generates continuous data for observability stack
- ✅ Graceful shutdown via Ctrl+C
- ❌ Not suitable for production load testing (no concurrency control, metrics)
- ❌ Hard-coded workflow names and parameters
- ❌ No configurable load patterns (constant rate only)

**Related patterns**: HTTP Workflow Triggering, Workflow ID Generation

---

## Pattern 25: Centralized Configuration via Helm Values [PRIORITY: PREFERRED]

**Purpose**: Centralize all deployment configuration in Helm `values.yaml` with clear namespace and task queue definitions.

**Problem Solved**: Temporal deployments require configuration across multiple components:
- Temporal namespace (workflow isolation)
- Task queue names (worker routing)
- Service ports
- Resource limits
- Observability stack settings

Without centralized configuration, these values are scattered across templates, leading to inconsistency.

**Implementation**:

**Helm Values Configuration** (helm-chart/time-cop-stack/values.yaml:1-80):
```yaml
# Global Temporal configuration
temporal:
  # Global task queue configuration
  taskQueues:
    ruby: "time-cop-ruby"
    python: "time-cop-python"

  # Global namespace
  namespace: "time-cop"

  # Server configuration
  server:
    replicaCount: 1

# Centralized metrics configuration
metrics:
  pollingInterval: 10s
  port: 9090

# Observability stack toggle
observability:
  enabled: true

# Loki configuration
loki:
  deploymentMode: SingleBinary
  singleBinary:
    replicas: 1
    resources:
      requests:
        cpu: 100m
        memory: 256Mi
```

**Template Usage** (example from ruby_worker deployment):
```yaml
env:
  - name: TEMPORAL_NAMESPACE
    value: {{ .Values.temporal.namespace }}
  - name: RUBY_TASK_QUEUE
    value: {{ .Values.temporal.taskQueues.ruby }}
  - name: PYTHON_TASK_QUEUE
    value: {{ .Values.temporal.taskQueues.python }}
```

**Configuration Categories**:
1. **Temporal Core**: namespace, task queues, server replicas
2. **Observability**: Prometheus, Grafana, Loki settings
3. **Workers**: Resource limits, replica counts
4. **Dispatcher**: Port configuration

**Override Pattern**:
```bash
# Development (defaults from values.yaml)
helm install time-cop ./helm-chart/time-cop-stack

# Production (override specific values)
helm install time-cop ./helm-chart/time-cop-stack \
  --set temporal.server.replicaCount=3 \
  --set observability.enabled=false

# Custom values file
helm install time-cop ./helm-chart/time-cop-stack \
  -f production-values.yaml
```

**When to use**:
- All Helm chart deployments
- Configuration that varies by environment (dev vs prod)
- Values referenced in multiple templates
- Settings that operators should easily adjust

**When NOT to use**:
- Values that never change (can hard-code in templates)
- Secrets (use Kubernetes Secrets, not values.yaml)

**Trade-offs**:
- ✅ Single source of truth for configuration
- ✅ Easy to override for different environments
- ✅ Clear documentation of configurable parameters
- ✅ Consistent values across all templates
- ✅ Helm diff shows configuration changes clearly
- ❌ Additional indirection (values → templates)
- ❌ Requires understanding Helm templating
- ❌ No validation of value types/ranges (can set invalid values)

**Related patterns**: Environment Variable Configuration (application-level), Task Queue Routing

---

## Summary: Iteration 4 Patterns

**Files Analyzed**: 6 files, ~600 lines

**Pattern Categories**:
1. **Containerization** (Pattern 21)
2. **End-to-end testing** (Patterns 22, 23)
3. **Observability validation** (Pattern 24)
4. **Deployment configuration** (Pattern 25)

**Priority Breakdown**:
- **CRITICAL**: 2 patterns (multi-stage container builds, Helm E2E tests)
- **PREFERRED**: 3 patterns (init container coordination, load generation, Helm values)

**Key Insights**:
- Multi-stage builds separate build tools (protoc, compilers) from runtime images
- Helm tests validate full integration chain in deployed environment
- Init containers enable sequential workflow trigger → wait pattern
- Load generation scripts provide simple observability validation
- Centralized Helm values prevent configuration drift across templates

**Architectural Significance**:
Testing and deployment patterns complete the production readiness story. Multi-stage builds ensure reproducible, minimal runtime images. Helm tests provide automated validation that the full stack works after deployment. These patterns bridge development (local workflows) and production (containerized, orchestrated) environments.

---

## Complete Pattern Summary

**Total Files Analyzed**: 32 files across 4 iterations, ~2,500 lines

**Pattern Count**: 25 patterns

**Priority Distribution**:
- **CRITICAL**: 15 patterns
  - Cross-language orchestration (Patterns 1, 2, 4, 5, 6)
  - Protobuf type safety (Patterns 9, 10, 11, 12, 13)
  - HTTP integration (Patterns 16, 17)
  - Production deployment (Patterns 21, 22)
  - Observability (Pattern 8)

- **PREFERRED**: 10 patterns
  - Code organization (Patterns 3, 18)
  - Version management (Patterns 14, 15)
  - Workflow management (Patterns 7, 19, 20)
  - Testing & deployment (Patterns 23, 24, 25)

**Pattern Categories**:
1. **Cross-Language Orchestration**: Task queue routing, activity invocation, protobuf contracts
2. **Type Safety**: Centralized proto generation, version enforcement, multi-language validation
3. **HTTP Integration**: Dispatcher lifecycle, workflow triggering, endpoint organization
4. **Testing & Deployment**: Container builds, Helm tests, load generation, configuration management
5. **Production Readiness**: Timeouts, metrics, observability, security

**Architectural Themes**:
- **Polyglot First**: System designed for Ruby + Python from the start
- **Type Safety**: Protobuf + Sorbet (Ruby) + Type Hints (Python) throughout
- **Version Alignment**: Strict enforcement prevents subtle cross-language bugs
- **HTTP as Integration Boundary**: Universal access without SDK requirements
- **Deployment Automation**: Helm tests validate post-deployment, Containerfiles ensure reproducibility

This pattern collection enables replicating Time Cop's cross-language workflow orchestration architecture in other polyglot Temporal systems.
