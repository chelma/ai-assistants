# Production Readiness Patterns

**Project Root**: ~/workspace/personal/time-cop

**Pattern Coverage**: Patterns 7-8 from WorkflowDemoMixed extraction

**Focus**: Timeout configuration and metrics emission for production observability

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
- When Temporal's default timeout behavior is acceptable

**Trade-offs**:
- ✅ Prevents workflows from hanging indefinitely
- ✅ Clear expectations about activity duration
- ✅ Enables automatic retry logic on timeout
- ❌ Requires understanding of activity duration characteristics
- ❌ Too short: legitimate long-running activities fail
- ❌ Too long: slow failure detection

**Related patterns**: Cross-Language Activity Invocation (Pattern 1, see patterns_core_orchestration.md), Retry Policies (not yet extracted)

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

**Related patterns**: Worker Registration (Pattern 5, see patterns_core_orchestration.md), Metrics Interceptor (implementation not yet extracted)

---

## Summary

**Pattern Count**: 2 patterns

**Priority Breakdown**:
- **CRITICAL**: 1 pattern (8 - metrics emission)
- **PREFERRED**: 1 pattern (7 - timeout configuration)

**Key Architectural Insights**:
- Production workflows require both timeout configuration (prevent hangs) and metrics emission (observability)
- Timeout values should be calibrated to expected activity duration
- Metrics backend choice is flexible (Prometheus, Datadog, CloudWatch, etc.)
- Custom histogram buckets improve percentile accuracy for latency metrics

**Related Pattern Files**:
- **Core Orchestration**: patterns_core_orchestration.md (Patterns 1-6) - Cross-language invocation, task queues, activities
- **Deployment**: patterns_deployment.md (Patterns 21-25) - Containerization and Helm deployment
