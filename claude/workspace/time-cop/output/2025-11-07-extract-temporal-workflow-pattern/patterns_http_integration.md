# HTTP Integration Patterns

**Project Root**: ~/workspace/personal/time-cop

**Pattern Coverage**: Patterns 16-20 from WorkflowDemoMixed extraction

**Focus**: FastAPI dispatcher, Temporal client lifecycle, HTTP workflow triggering, router organization, configuration

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
