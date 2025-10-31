# JSON Transformer Expert - Reference Implementation

This directory provides a complete (but minimal) example of a multi-expert LangChain system.

## Purpose

This is an **instructive** reference implementation, not a production system. It demonstrates:

1. **Two-phase workflow**: Mapping (analysis) → Transform (code generation)
2. **Progressive detail loading**: Full schema → filtered schema based on mappings
3. **LLM configuration spectrum**: Creative (temp=1, thinking) vs deterministic (temp=0, no thinking)
4. **Validation mechanics**: Multi-stage validation of generated Python code
5. **Factory pattern**: Centralized Expert creation with clear configuration

## Structure

```
json_transformer_expert/
├── models.py            # Domain dataclasses (FieldMapping, MappingReport, TransformCode)
├── task_def.py          # Concrete Task implementations (MappingTask, TransformTask)
├── tool_def.py          # Pydantic schemas + StructuredTools
├── expert_def.py        # Expert factory functions (get_mapping_expert, get_transform_expert)
├── validators.py        # Multi-stage validation for generated code
└── prompting/
    ├── templates.py     # Prompt templates with XML tags
    └── generation.py    # Prompt factory functions (with progressive detail)
```

## Workflow

### Phase 1: Mapping

```python
from core.experts import invoke_expert
from json_transformer_expert.expert_def import get_mapping_expert
from json_transformer_expert.task_def import MappingTask

# Create mapping expert
expert = get_mapping_expert()

# Create task
task = MappingTask(
    task_id="map-001",
    context=[],  # Empty for first invocation
    source_json='{"user": "john@example.com", "timestamp": "2024-01-01T12:00:00Z"}',
    target_schema='{"email": "string", "event_time": "datetime"}'
)

# Invoke expert
task = invoke_expert(expert, task)

# Result is in task.mapping_report
# MappingReport(
#     mappings=[FieldMapping(source_path="user", target_path="email", ...)],
#     data_type_analysis="User event data"
# )
```

### Phase 2: Transform

```python
from json_transformer_expert.expert_def import get_transform_expert
from json_transformer_expert.task_def import TransformTask

# Create transform expert
expert = get_transform_expert()

# Create task with mappings from phase 1
task = TransformTask(
    task_id="transform-001",
    context=[],
    source_json='...',
    target_schema='...',
    mappings=[m.to_json() for m in mapping_task.mapping_report.mappings]
)

# Invoke expert
task = invoke_expert(expert, task)

# Result is in task.transform_code
# TransformCode(
#     dependency_setup="import json",
#     transform_logic="def transform(source_json_str): ...",
#     rationale="..."
# )
```

### Phase 3: Validation

```python
from json_transformer_expert.validators import TransformCodeValidator

# Validate generated code
validator = TransformCodeValidator(
    source_json=source_json,
    transform_code=task.transform_code
)

report = validator.validate()
if report.passed:
    print("✓ Transform code is valid and executable")
else:
    print("✗ Validation failed:", report.report_entries)
```

## Key Patterns Demonstrated

### 1. Tool-Forcing Pattern
Both experts use `bind_tools()` to guarantee structured output. The LLM must produce a tool call matching the Pydantic schema.

### 2. Factory Pattern
Expert creation is centralized in factory functions (`get_mapping_expert()`, `get_transform_expert()`), making configuration changes easy.

### 3. Progressive Detail Loading
Transform phase prompt includes FILTERED schema (only mapped paths), reducing token count and focusing LLM.

### 4. Multi-Stage Validation
Validation proceeds through stages: syntax → loading → invocation → output. Each stage has specific exception types.

### 5. LLM Configuration Spectrum
- **Mapping**: temp=1, thinking enabled (creative analysis)
- **Transform**: temp=0, thinking disabled (deterministic code generation)

## Next Steps

To adapt this pattern for your use case:

1. **Replace domain models** (`models.py`): Define your work items
2. **Update task definitions** (`task_def.py`): Match your workflow
3. **Define tool schemas** (`tool_def.py`): Specify your structured output
4. **Write prompt templates** (`prompting/templates.py`): Customize for your domain
5. **Configure LLM** (`expert_def.py`): Replace TODOs with your provider setup
6. **Add validation** (`validators.py`): Implement domain-specific checks

See `../langchain_guide.md` for detailed guidance on each step.
