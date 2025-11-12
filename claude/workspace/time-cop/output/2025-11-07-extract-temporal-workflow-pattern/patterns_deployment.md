# Deployment Patterns

**Project Root**: /Users/chris.helma/workspace/personal/time-cop

**Pattern Coverage**: Patterns 21-25 from WorkflowDemoMixed extraction

**Focus**: Containerization, Helm testing, Kubernetes deployment, observability validation

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

