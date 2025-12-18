# Building Cross-Language Temporal Workflows: A Prescriptive Guide

**Extracted from**: Time Cop WorkflowDemoMixed implementation
**Project Root**: ~/workspace/personal/time-cop
**Last Updated**: 2025-11-10

---

## Overview

This guide provides a prescriptive workflow for adding new Temporal workflows to Time Cop following the WorkflowDemoMixed pattern.

**Use cases**:
- Implementing cross-language workflow orchestration (Ruby workflows calling Python and/or Ruby activities)
- Adding type-safe workflow inputs/outputs via protobuf
- Exposing workflows via HTTP API (dispatcher)
- Deploying workflows to Kubernetes with automated testing

**Guide coverage**:
- 10-step process for creating a complete workflow from schema to deployment
- Architecture rationale for each design decision
- CRITICAL patterns for production-ready workflows

**Prerequisites**:
- Ruby 3.2+ and Python 3.10+ installed
- protoc 29.5 installed system-wide
- Temporal development environment running (or `make deploy` in Time Cop)
- Familiarity with Temporal concepts (workflows, activities, task queues)

---

## Quick Start

**Repository Structure** (key directories):
```
time-cop/
├── protos/                           # Protobuf schemas (centralized)
│   ├── *.proto                       # Workflow and activity message definitions
│   ├── config/versions.yaml          # Single source of truth for protoc/library versions
│   ├── Makefile                      # Centralized generation targets
│   └── scripts/                      # Validation and generation scripts
├── ruby_worker/
│   ├── app/
│   │   ├── workflows/                # Ruby workflow definitions
│   │   └── activities/               # Ruby activity implementations
│   ├── Rakefile                      # Includes protos:generate task
│   └── Containerfile                 # Multi-stage build with proto generation
├── python_worker/
│   ├── time_cop_worker/
│   │   ├── workflows/                # Python workflow definitions
│   │   └── activities/               # Python activity implementations
│   ├── pyproject.toml                # Includes `poe protos` task
│   └── Containerfile                 # Multi-stage build with proto generation
├── dispatcher/
│   ├── dispatcher/
│   │   ├── api/                      # HTTP endpoints per worker
│   │   ├── temporal_client.py        # Client lifecycle management
│   │   └── main.py                   # FastAPI application
│   └── Containerfile
└── helm-chart/time-cop-stack/
    ├── templates/
    │   ├── tests/                    # End-to-end Helm tests
    │   ├── ruby-worker.yaml          # Worker deployment
    │   └── dispatcher.yaml           # Dispatcher deployment
    └── values.yaml                   # Centralized configuration
```

**Canonical Example**: WorkflowDemoMixed demonstrates the complete pattern across all these directories.

---

## Core Concepts

### Workflows vs Activities

**Workflows** orchestrate work by calling activities. They define the business logic sequence but don't perform I/O directly.

**Activities** perform actual work (API calls, database queries, computations). They can fail and be retried.

**Canonical Examples**: `ruby_worker/app/workflows/workflow_demo_mixed.rb:8-71`, `ruby_worker/app/activities/activity_say_hello_ruby.rb:6-18`, `python_worker/time_cop_worker/activities/activity_say_hello_python.py:8-16`

### Cross-Language Invocation

Ruby workflows call activities in any language by:
1. **Same-language**: Pass class reference (e.g., `ActivitySayHelloRuby`)
2. **Cross-language**: Pass string name (e.g., `'ActivitySayHelloPython'`)
3. **Both**: Specify target `task_queue`

**Example**: `ruby_worker/app/workflows/workflow_demo_mixed.rb:62-69`

**Why Ruby for Orchestration?** Historical artifact with established code and infrastructure. This choice is not an imperative and may evolve.

**Details**: See patterns_core_orchestration.md Pattern 1.

### Task Queues

Task queues route workflow/activity executions to specific workers:
- `time-cop-ruby`: Ruby worker
- `time-cop-python`: Python worker

Workflows specify task queue when invoking activities to route cross-language calls.

**Config**: `ruby_worker/app/start_worker.rb:80`, `python_worker/time_cop_worker/main.py:67`

**Details**: See patterns_core_orchestration.md Pattern 2.

### Protobuf Type Safety

All workflow and activity inputs/outputs use protobuf messages for type safety across language boundaries, schema evolution, and clear contracts.

**Message Naming**: `{WorkflowName}Request` / `{WorkflowName}Response` pairs

**Examples**: `protos/workflow_demo_mixed.proto:5-13`, `protos/activity_say_hello.proto:6-13`

**Details**: See patterns_core_orchestration.md Pattern 6 for message structure, patterns_type_safety.md Patterns 9-15 for generation and version management.

---

## Step-by-Step: Workflow Creation

### Step 1: Define Protobuf Schema

**Goal**: Create type-safe message definitions for workflow and activities.

**Process**:
1. Create `.proto` file in `protos/` directory
2. Define request/response message pairs for workflow
3. Define request/response message pairs for each activity

**Naming Conventions**:
- Workflow messages: `{WorkflowName}Request` / `{WorkflowName}Response`
- Activity messages: `{ActivityName}Request` / `{ActivityName}Response`
- Package: `timecop.workflows` for workflows, `timecop.activities` for activities

**Canonical Examples**:
- Workflow schema: `protos/workflow_demo_mixed.proto:5-13`
- Activity schema: `protos/activity_say_hello.proto:6-13`

**Why Protobuf?** Protobuf is an established and successful paradigm in the company's technical architecture, providing type-safe cross-language communication with schema evolution capabilities.

---

### Step 2: Generate Protobuf Classes

**Goal**: Generate Ruby and Python classes from your `.proto` files using centralized generation with version validation.

**Process** (centralized generation):
1. **Validate system protoc version**: `make -C protos validate`
2. **Generate for all languages**: `make -C protos all` (or `make -C protos ruby` / `make -C protos python`)
3. **Copy to consumers**:
   - Ruby: `cd ruby_worker && bundle exec rake protos:generate`
   - Python: `cd python_worker && poetry run poe protos`
   - Dispatcher: `cd dispatcher && poetry run poe protos`

**Why Centralized?** Centralized protobuf generation reduces duplicated behavior across the various sub-applications and facilitates version synchronization across them. This ensures all workers use compatible protobuf definitions.

**Version Management**:
- Single source of truth: `protos/config/versions.yaml`
- Defines protoc version and language library requirements
- Validated before generation (both centralized and consumer-level)

See:
- Version config: `protos/config/versions.yaml:1-12`
- Centralized Makefile: `protos/Makefile:1-43`
- Validation script: `protos/scripts/validate.py:73-87`
- Python consumer validation: `python_worker/scripts/validate_protoc.py:111-172`
- Ruby consumer validation: `ruby_worker/Rakefile:17-42`

**Output Locations**:
- Centralized: `protos/generated/python/`, `protos/generated/ruby/`, `protos/generated/rbi/`
- Ruby worker: `ruby_worker/protos/`, `ruby_worker/sorbet/rbi/protos/` (gitignored)
- Python worker: `python_worker/time_cop_worker/protos/` (gitignored)
- Dispatcher: `dispatcher/dispatcher/protos/` (gitignored)

**Key Insight**: Generated files are gitignored and regenerated on every build (local dev and containerized). This ensures version alignment.

---

### Step 3: Implement Activities

**Goal**: Create activity functions/classes that perform actual work.

**Language-Specific Patterns**:
- **Ruby**: Class-based with `execute` method, extends `Temporalio::Activity::Definition`, Sorbet type signatures
- **Python**: Function-based with `@activity.defn` decorator, type hints
- **Both**: Use protobuf request/response types for cross-language compatibility

**Activity Naming**:
- Ruby: Class name used for same-language invocation
- Python: `name` parameter in decorator defines cross-language reference string

**Canonical Examples**:
- Ruby activity: `ruby_worker/app/activities/activity_say_hello_ruby.rb:6-18`
- Python activity: `python_worker/time_cop_worker/activities/activity_say_hello_python.py:8-16`

**Pattern Details**: See patterns_core_orchestration.md Pattern 4 for complete implementation guidance and trade-offs.

---

### Step 4: Create Workflow

**Goal**: Define workflow orchestration logic that calls activities.

**Ruby Workflow Pattern** (class-based, orchestrates cross-language):
- Inherit from `WorkflowDefinition` (provides `task_queues` configuration)
- Define `execute(request)` method with Sorbet signatures
- Use `Temporalio::Workflow.execute_activity` to invoke activities

**Cross-Language Invocation Rules**:
- **Same-language** (Ruby → Ruby): Pass class reference (e.g., `MyActivityRuby`)
- **Cross-language** (Ruby → Python): Pass string name (e.g., `'MyActivityPython'`)
- **Both**: Specify correct `task_queue` to route to target worker
- **Both**: Set `schedule_to_close_timeout` (typically 300 seconds)

**Canonical Examples**:
- Base class: `ruby_worker/app/workflows/workflow_definition.rb:6-53`
- Complete workflow: `ruby_worker/app/workflows/workflow_demo_mixed.rb:8-71`

**Pattern Details**: See patterns_core_orchestration.md Patterns 1, 2, 3 for cross-language invocation, task queue routing, and base class abstraction.

---

### Step 5: Register with Worker

**Goal**: Register workflows and activities so workers can execute them.

**Registration Pattern**:
- **Ruby Worker**: Add to `WORKFLOW_LIST` (`ruby_worker/app/workflows/workflow_list.rb:7-11`) and `ACTIVITIES_LIST` (`ruby_worker/app/activities/activities_list.rb:7-11`)
- **Python Worker**: Add to `ACTIVITIES_LIST` (`python_worker/time_cop_worker/activities/__init__.py:6-9`)
- Workers automatically register all workflows/activities in these lists at startup

**Worker Initialization References**:
- Ruby worker init: `ruby_worker/app/start_worker.rb:77-85`
- Python worker init: `python_worker/time_cop_worker/main.py:65-72`

**Pattern Details**: See patterns_core_orchestration.md Pattern 5 for complete registration patterns and trade-offs.

---

### Step 6: Add Dispatcher Endpoint

**Goal**: Expose workflow via HTTP API for external triggering.

**Endpoint Pattern**:
1. Add router method to appropriate worker router (`dispatcher/dispatcher/api/ruby_worker.py` or `python_worker.py`)
2. Create protobuf request from HTTP params
3. Start workflow via Temporal client (injected with `Depends(get_client)`)
4. Return `{"run_id": ..., "workflow_id": ...}`

**Workflow ID Pattern**: `{WorkflowName}-{key_param}-{timestamp_ms}`
- Encodes workflow type, key parameter, and timestamp for debugging
- Millisecond precision prevents collisions

**Router Organization**:
- `/ruby/*` endpoints → Ruby worker task queue
- `/python/*` endpoints → Python worker task queue

**Canonical Examples**:
- Ruby worker router: `dispatcher/dispatcher/api/ruby_worker.py:27-39`
- Python worker router: `dispatcher/dispatcher/api/python_worker.py:11-23`
- Temporal client lifecycle: `dispatcher/dispatcher/temporal_client.py:8-17`

**Pattern Details**: See patterns_http_integration.md Patterns 16, 17, 19 for FastAPI lifespan, HTTP triggering, and workflow ID generation.

---

### Step 7: Add Metrics Emission

**Goal**: Ensure your workflow emits metrics for production observability.

**Pattern**: Metrics emission is already configured at the worker level (not per-workflow). Your workflow automatically emits:
- Workflow duration
- Activity durations
- Task queue depths
- Error rates

**Verification**:
- Ruby worker metrics config: `ruby_worker/app/start_worker.rb:42-64`
- Python worker metrics config: `python_worker/time_cop_worker/main.py:36-50`
- Metrics endpoint: `http://localhost:{METRICS_PORT}/metrics` (after `make expose-services`)

**Custom Metrics** (optional):
If you need workflow-specific metrics, use the metrics interceptor pattern:
- Ruby: `ruby_worker/app/observability/metrics_interceptor.rb`
- Python: `python_worker/time_cop_worker/observability/metrics_interceptor.py`

**Why Metrics Are CRITICAL**: Tracking the performance of Temporal Activities and Workflows is critical for all the standard reasons you track distributed systems: debugging latency issues, detecting failures, capacity planning, and understanding system behavior in production.

---

### Step 8: Test Locally

**Goal**: Verify workflow executes correctly before containerization.

**Process**:
1. Start Temporal dev environment: `make deploy`
2. Expose services to localhost: `make expose-services`
3. Trigger workflow via dispatcher: `curl -f -X POST 'http://localhost:9005/ruby/my-workflow?user_id=test&count=5'`
4. Monitor execution via Temporal UI (http://localhost:9002), dispatcher logs, and worker logs

**Debugging**:
- Check workflow appears in Temporal UI
- Verify activity task queues match worker task queues
- Check logs for protobuf serialization errors
- Confirm metrics appear at Grafana (http://localhost:9004)

---

### Step 9: Containerize and Deploy

**Goal**: Build container images with protobuf generation and deploy to Kubernetes.

**Container Build** (multi-stage pattern):

**Ruby Worker**:
```bash
# From repo root
podman build -f ruby_worker/Containerfile -t time-cop-ruby-worker .
```

**Python Worker**:
```bash
podman build -f python_worker/Containerfile -t time-cop-python-worker .
```

**Dispatcher**:
```bash
podman build -f dispatcher/Containerfile -t time-cop-dispatcher .
```

**Key Container Features**:
- **Build stage**: Installs protoc, generates protobuf files, compiles code
- **Runtime stage**: Minimal image, no build tools, non-root user
- **Protoc version**: Matches `protos/config/versions.yaml` via build ARG

**Helm Deployment**:
```bash
# Deploy with updated images
make deploy

# Or update specific component
helm upgrade time-cop ./helm-chart/time-cop-stack \
  --set rubyWorker.image.tag=my-new-tag
```

**Configuration**:
All workflow-specific config goes in `helm-chart/time-cop-stack/values.yaml`:
- Task queue names
- Worker replica counts
- Resource limits
- Environment variables

See:
- Ruby Containerfile: `ruby_worker/Containerfile:1-83`
- Python Containerfile: `python_worker/Containerfile:1-68`
- Helm values: `helm-chart/time-cop-stack/values.yaml:1-80`

**Why Multi-Stage Builds?** Multi-stage container builds reduce the final runtime size of the image, which reduces storage requirements and the attack surface of the deployed image. Build tools (protoc, compilers, dev dependencies) are excluded from the runtime image.

---

### Step 10: Add Helm Test and Validation

**Goal**: Create automated end-to-end test validating workflow execution in deployed environment.

**Helm Test Pattern** (init container + main container):
1. **Init container**: Triggers workflow via dispatcher HTTP API, extracts workflow ID, saves to shared `emptyDir` volume
2. **Main container**: Reads workflow ID, uses `temporal workflow show --follow` to wait for completion

**Test Annotations**:
- `helm.sh/hook: test` - Marks pod as Helm test
- `helm.sh/hook-weight` - Execution order
- `helm.sh/hook-delete-policy` - Cleanup behavior

**Running Tests**:
```bash
helm test time-cop-stack
kubectl logs <test-pod-name> -c start-workflow
kubectl logs <test-pod-name> -c wait-for-completion
```

**Canonical Example**: `helm-chart/time-cop-stack/templates/tests/test-mixed-workflow-executes.yaml:1-80`

**Pattern Details**: See patterns_deployment.md Patterns 22, 23 for Helm test implementation and init container coordination.

---

## Key Design Decisions

### Why Ruby Workflows Orchestrating Python Activities?

This is a historical artifact where existing Temporal Workflows were defined in Ruby, providing established code and infrastructure for Ruby-based workflow definitions. This choice is not an imperative and may evolve in the future.

### Why Centralized Protobuf Generation?

Centralized protobuf generation reduces duplicated behavior across the various sub-applications and facilitates version synchronization across them. This ensures all workers use compatible protobuf definitions and reduces maintenance overhead.

### Why Strict Protoc Version Enforcement?

**Rationale**: Different protoc versions generate incompatible code, causing subtle serialization bugs in cross-language communication. While there are strong arguments for allowing greater version flexibility, we decided to version lock in this iteration of the system to ensure we don't have subtle incompatibilities between the various polyglot sub-applications.

Strict enforcement prevents:
- Runtime serialization failures between Ruby/Python workers
- Missing methods in generated classes
- Inconsistent message encoding/decoding

**Compatibility Rules** (from protobuf project):
- Python: `protobuf_library.minor == protoc.major` (e.g., protoc 29.5 → protobuf 5.29.x)
- Ruby: `google_protobuf_gem.minor == protoc.major` (e.g., protoc 29.5 → gem 4.29.x)

See: `protos/config/versions.yaml:1-12`, `protos/scripts/validate.py:54-70`

**Trade-off**: Version locking provides safety at the cost of flexibility. Future iterations may relax this constraint once cross-language compatibility is better understood.

### Why Helm Tests for Workflows?

Helm tests serve as lightweight end-to-end tests of the entire stack. They validate that workflows execute correctly in the deployed Kubernetes environment, catching integration issues that unit tests miss (networking, configuration, cross-service communication).

### Why HTTP Dispatcher Layer?

The HTTP dispatcher abstracts the implementation of the system from its interface. This removes the need for consumers to install implementation-specific clients (e.g., Temporal SDK) and allows us to wrap Temporal Workflows in a shim layer to handle any discontinuities between consumer needs and Temporal capabilities that arise.

---

## Advanced Patterns

### Workflow Error Handling

[TODO: Pattern not yet extracted - refer to production workflows for retry policies, error handling, compensation logic]

### Workflow Signals and Queries

[TODO: Pattern not yet extracted - refer to Temporal documentation and production examples]

### Activity Heartbeats

[TODO: Pattern not yet extracted - important for long-running activities]

### Workflow Versioning

[TODO: Pattern not yet extracted - important for rolling deployments]

---

## Resources

### Pattern Catalog

Detailed pattern documentation organized by architectural layer. Each file provides patterns with implementation details, trade-offs, and related patterns:

- **Core Orchestration** (`patterns_core_orchestration.md`): Patterns 1-6
  - Cross-language activity invocation, task queue routing, workflow/activity definitions, worker registration, protobuf messages

- **Production Readiness** (`patterns_production.md`): Patterns 7-8
  - Timeout configuration, metrics emission for observability

- **Type Safety** (`patterns_type_safety.md`): Patterns 9-15
  - Protobuf version management, centralized generation, validation, compatibility rules, consumer copy, fresh start

- **HTTP Integration** (`patterns_http_integration.md`): Patterns 16-20
  - FastAPI lifespan, HTTP workflow triggering, router organization, workflow ID generation, environment configuration

- **Deployment** (`patterns_deployment.md`): Patterns 21-25
  - Multi-stage container builds, Helm tests, init containers, load generation, centralized Helm values

All pattern files located in: `~/.claude/workspace/time-cop/output/2025-11-07-extract-temporal-workflow-pattern/`

### Canonical Example Files
- **Workflow**: `ruby_worker/app/workflows/workflow_demo_mixed.rb`
- **Ruby Activity**: `ruby_worker/app/activities/activity_say_hello_ruby.rb`
- **Python Activity**: `python_worker/time_cop_worker/activities/activity_say_hello_python.py`
- **Protobuf Schema**: `protos/workflow_demo_mixed.proto`, `protos/activity_say_hello.proto`
- **Dispatcher Endpoint**: `dispatcher/dispatcher/api/ruby_worker.py:27-39`
- **Helm Test**: `helm-chart/time-cop-stack/templates/tests/test-mixed-workflow-executes.yaml`

### Temporal Documentation
- Official Temporal docs: https://docs.temporal.io
- Ruby SDK: https://github.com/temporalio/sdk-ruby
- Python SDK: https://github.com/temporalio/sdk-python

---

## Quick Reference

### Common Commands
```bash
# Protobuf generation
make -C protos all                           # Generate all languages
cd ruby_worker && bundle exec rake protos:generate
cd python_worker && poetry run poe protos

# Local testing
make deploy                                  # Deploy full stack
make expose-services                         # Expose to localhost
curl -X POST 'http://localhost:9005/ruby/demo-mixed?name=test'

# Container builds
podman build -f ruby_worker/Containerfile -t time-cop-ruby-worker .
podman build -f python_worker/Containerfile -t time-cop-python-worker .

# Helm operations
helm test time-cop-stack                     # Run E2E tests
helm upgrade time-cop ./helm-chart/time-cop-stack
```

### File Paths (relative to project root)
- Protobuf schemas: `protos/*.proto`
- Ruby workflows: `ruby_worker/app/workflows/`
- Ruby activities: `ruby_worker/app/activities/`
- Python activities: `python_worker/time_cop_worker/activities/`
- Dispatcher endpoints: `dispatcher/dispatcher/api/`
- Helm chart: `helm-chart/time-cop-stack/`

---

**Guide Status**: Token-optimized - all design rationale incorporated, inline code replaced with file references (Phases 6-7 complete)
