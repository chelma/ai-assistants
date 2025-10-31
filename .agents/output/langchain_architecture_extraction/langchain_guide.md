# LangChain Multi-Expert Architecture Guide

**Last Updated**: 2025-10-31
**Source**: Patterns extracted from ocsf-playground (AWS Bedrock + LangChain)
**Applicability**: Universal LangChain patterns (provider-agnostic)

---

## Overview

This guide explains how to build LangChain-based multi-expert systems using the **Expert-Task-Tool** pattern. This architecture provides:

- **Structured output**: LLMs forced to produce validated, type-safe results
- **Multi-turn conversations**: Tasks accumulate context across invocations
- **Compositional design**: Experts, Tasks, and Tools combine cleanly
- **Provider flexibility**: Works with any LangChain-compatible LLM

### What's a Multi-Expert System?

A multi-expert system uses **multiple LLM "experts"**, each configured for a specific task:
- **Analysis Expert**: Creative exploration (temp=1, extended thinking)
- **Code Generation Expert**: Deterministic output (temp=0, no thinking)
- **Classification Expert**: Category selection (temp=0)

Each expert has its own prompts, tools, and configuration, but shares the same core abstractions.

---

## Quick Start

### 1. Copy the Foundation

Copy `reference_implementation/core/` to your project. These files provide ready-to-run abstractions:

```
your_project/
└── core/                    # ← Copy this entire directory
    ├── experts.py
    ├── tasks.py
    ├── tools.py
    ├── inference.py
    ├── validation_report.py
    └── validators.py
```

### 2. Review the Example

Study `reference_implementation/json_transformer_expert/` to understand the pattern:
- Two-phase workflow (mapping → transform)
- Progressive detail loading (full schema → filtered schema)
- Contrasting LLM configs (creative vs deterministic)
- Multi-stage validation

### 3. Build Your First Expert

Follow the [Building Your First Expert](#building-your-first-expert) section below.

---

## Core Abstractions

### Expert

An **Expert** encapsulates a complete LLM inference capability:

```python
@dataclass
class Expert:
    llm: Runnable[LanguageModelInput, BaseMessage]           # LLM with tools bound
    system_prompt_factory: Callable[[Dict], SystemMessage]  # Dynamic prompt generation
    tools: ToolBundle                                        # Structured output schema
```

**Why Expert?**
- Bundles LLM + prompts + tools into a single, reusable unit
- Enables multiple expert "modes" (analysis, generation, classification)
- Factory pattern makes configuration changes easy

**Lifecycle**:
1. Create Expert via factory function (`get_*_expert()`)
2. Pass Expert + Task to `invoke_expert()`
3. Expert produces structured output in Task

---

### Task

A **Task** represents work to be performed:

```python
@dataclass
class Task(ABC):
    task_id: str
    context: List[BaseMessage]  # Conversation history (SystemMessage, AIMessage, ToolMessage)

    @abstractmethod
    def get_work_item(self) -> Any: pass

    @abstractmethod
    def set_work_item(self, new_work_item: Any): pass

    @abstractmethod
    def get_tool_name(self) -> str: pass

    @abstractmethod
    def to_json(self) -> Dict[str, Any]: pass
```

**Why Task?**
- Encapsulates input data + result (work item)
- Maintains conversation context for multi-turn workflows
- Type-safe work item access (enforced by `set_work_item()`)

**Concrete Example**:
```python
@dataclass
class MappingTask(Task):
    source_json: str           # Input
    target_schema: str         # Input
    mapping_report: MappingReport = None  # Work item (result)

    def get_work_item(self) -> Any:
        return self.mapping_report

    def set_work_item(self, new_work_item: Any):
        if not isinstance(new_work_item, MappingReport):
            raise TypeError("new_work_item must be of type MappingReport")
        self.mapping_report = new_work_item

    def get_tool_name(self) -> str:
        return "CreateMappingReport"
```

<!-- COMMENTARY NEEDED: Please explain when/why you'd want multi-turn conversations vs single-shot. -->

---

### Tool

Tools define the **structured output schema** using Pydantic:

```python
class FieldMappingInput(BaseModel):
    source_path: str = Field(description="Dot-delimited path in source JSON...")
    target_path: str = Field(description="Dot-delimited path in target schema...")
    rationale: str = Field(description="Explanation of why this mapping makes sense...")

class CreateMappingReport(BaseModel):
    """Create a report of field mappings between source JSON and target schema."""
    mappings: List[FieldMappingInput] = Field(description="List of identified mappings...")
    data_type_analysis: str = Field(description="Brief analysis of source data type...")

def create_mapping_report(mappings, data_type_analysis) -> MappingReport:
    # Convert Pydantic models to domain dataclasses
    return MappingReport(...)

create_mapping_report_tool = StructuredTool.from_function(
    func=create_mapping_report,
    name="CreateMappingReport",
    args_schema=CreateMappingReport
)
```

**Why Pydantic + StructuredTool?**
- LangChain validates LLM arguments against schema automatically
- Field descriptions guide the LLM on what to produce
- Tool function converts Pydantic input → domain dataclass
- Guarantees structured output (no parsing errors)

**Field Description Best Practices**:
- Use constraints: "MUST", "MUST NOT", "exact value"
- Provide examples: "e.g., 'user.email' not just 'email'"
- Explain semantics: "represents the source IP address, not destination"

---

### ToolBundle

**ToolBundle** wraps tools for an Expert:

```python
@dataclass
class ToolBundle:
    task_tool: StructuredTool

    def to_list(self) -> List[StructuredTool]:
        return [self.task_tool]
```

**Why ToolBundle?**
- Consistent interface for `bind_tools()`
- Current pattern: one tool per Expert
- Extensible: add `helper_tools` field for multi-tool Experts

---

## Building Your First Expert

### Step 1: Define Your Domain Models

Create dataclasses for your work items:

```python
# models.py
from dataclasses import dataclass
from typing import List

@dataclass
class FieldMapping:
    source_path: str
    target_path: str
    rationale: str

    def to_json(self):
        return {"source_path": self.source_path, ...}

@dataclass
class MappingReport:
    mappings: List[FieldMapping]
    data_type_analysis: str

    def to_json(self):
        return {"mappings": [m.to_json() for m in self.mappings], ...}
```

**Pattern**: All domain models have `to_json()` for serialization.

---

### Step 2: Implement Your Task

Subclass `Task` with your inputs and work item:

```python
# task_def.py
from dataclasses import dataclass
from core.tasks import Task
from models import MappingReport

@dataclass
class MappingTask(Task):
    # Inputs
    source_json: str
    target_schema: str

    # Work item (result)
    mapping_report: MappingReport = None

    def get_work_item(self) -> Any:
        return self.mapping_report

    def set_work_item(self, new_work_item: Any):
        if not isinstance(new_work_item, MappingReport):
            raise TypeError("new_work_item must be of type MappingReport")
        self.mapping_report = new_work_item

    def get_tool_name(self) -> str:
        return "CreateMappingReport"  # Must match tool name

    def to_json(self):
        return {
            "task_id": self.task_id,
            "source_json": self.source_json,
            "target_schema": self.target_schema,
            "context": [turn.to_json() for turn in self.context],
            "mapping_report": self.mapping_report.to_json() if self.mapping_report else None
        }
```

---

### Step 3: Define Your Tool

Create Pydantic schema + tool function:

```python
# tool_def.py
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from core.tools import ToolBundle
from models import FieldMapping, MappingReport

class FieldMappingInput(BaseModel):
    source_path: str = Field(description="Dot-delimited path...")
    target_path: str = Field(description="Dot-delimited path...")
    rationale: str = Field(description="Explanation...")

class CreateMappingReport(BaseModel):
    """Create a report of field mappings."""
    mappings: List[FieldMappingInput] = Field(description="List of mappings...")
    data_type_analysis: str = Field(description="Brief analysis...")

def create_mapping_report(mappings, data_type_analysis) -> MappingReport:
    return MappingReport(
        mappings=[FieldMapping(**m.dict()) for m in mappings],
        data_type_analysis=data_type_analysis
    )

create_mapping_report_tool = StructuredTool.from_function(
    func=create_mapping_report,
    name="CreateMappingReport",
    args_schema=CreateMappingReport
)

def get_mapping_tool_bundle() -> ToolBundle:
    return ToolBundle(task_tool=create_mapping_report_tool)
```

---

### Step 4: Write Prompt Template

Create prompt template with XML tags for structure:

```python
# prompting/templates.py

mapping_prompt_template = """You are an AI assistant specialized in analyzing JSON data.

Your goal is to identify field mappings between source JSON and target schema.

<guidelines>
- Analyze the source JSON structure carefully
- Identify ALL fields that can map to target schema
- Provide clear rationale for each mapping
- Use exact dot-delimited paths
</guidelines>

<source_json>
{source_json}
</source_json>

<target_schema>
{target_schema}
</target_schema>

Create a comprehensive mapping report.
"""
```

**Template Best Practices**:
- Use XML tags for semantic sections
- Explicit constraints: "ALWAYS", "MUST", "NEVER"
- Provide context in placeholders
- Keep focused on single task

<!-- COMMENTARY NEEDED: Please explain when to use single-section vs multi-section templates, and whether XML tags are required or just a convention. -->

---

### Step 5: Create Prompt Factory

Factory function for dynamic prompt generation:

```python
# prompting/generation.py
from langchain_core.messages import SystemMessage
from prompting.templates import mapping_prompt_template

def get_mapping_system_prompt_factory():
    def factory(source_json: str, target_schema: str) -> SystemMessage:
        return SystemMessage(
            content=mapping_prompt_template.format(
                source_json=source_json,
                target_schema=target_schema
            )
        )
    return factory
```

**Why Factory Pattern?**
- Separates prompt logic from Expert creation
- Enables late binding (inputs provided at invocation time)
- Easy to test prompt generation independently
- Supports dynamic context injection (e.g., fetching schemas)

---

### Step 6: Wire Together in Expert Factory

Create Expert factory that assembles everything:

```python
# expert_def.py
from core.experts import Expert
from tool_def import get_mapping_tool_bundle
from prompting.generation import get_mapping_system_prompt_factory

def get_mapping_expert() -> Expert:
    tool_bundle = get_mapping_tool_bundle()

    # TODO: Configure your LLM client
    # Example for AWS Bedrock:
    # from langchain_aws import ChatBedrockConverse
    # llm = ChatBedrockConverse(
    #     model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    #     temperature=1,  # Creative analysis
    #     max_tokens=30000,
    #     ...
    # )
    # llm_w_tools = llm.bind_tools(tool_bundle.to_list())

    return Expert(
        llm=llm_w_tools,
        system_prompt_factory=get_mapping_system_prompt_factory(),
        tools=tool_bundle
    )
```

---

### Step 7: Invoke Your Expert

Use `invoke_expert()` to run inference:

```python
from core.experts import invoke_expert
from expert_def import get_mapping_expert
from task_def import MappingTask

# Create expert
expert = get_mapping_expert()

# Create task
task = MappingTask(
    task_id="map-001",
    context=[],  # Empty for first invocation
    source_json='{"user": "john@example.com"}',
    target_schema='{"email": "string"}'
)

# Invoke expert
task = invoke_expert(expert, task)

# Access result
print(task.mapping_report)
```

---

## Key Design Decisions

### Tool-Forcing Pattern

**Pattern**: Bind tools to LLM to **force** structured output.

```python
llm_w_tools = llm.bind_tools(tool_bundle.to_list())
```

**Why?**
- Guarantees structured output (no parsing errors)
- LangChain validates tool arguments automatically
- Eliminates "LLM didn't follow instructions" failures
- Tool call = task completion

**Trade-off**: Every expert invocation MUST produce a tool call. This pattern doesn't support free-form responses.

---

### LLM Configuration Spectrum

**Pattern**: Match LLM configuration to task characteristics.

| Task Type | Temperature | Extended Thinking | Max Tokens | Use Case |
|-----------|-------------|-------------------|------------|----------|
| **Analysis/Discovery** | 1 | Enabled | 30K+ | Entity extraction, pattern discovery, complex reasoning |
| **Code Generation** | 0 | Disabled | 16K | Regex, Python functions, deterministic transforms |
| **Classification** | 0 | Disabled | 16K | Category selection, yes/no decisions |

**Examples**:

```python
# Creative analysis
llm = ChatBedrockConverse(
    temperature=1,  # Exploratory
    max_tokens=30000,
    additional_model_request_fields={"thinking": {"type": "enabled", "budget_tokens": 30000}}
)

# Deterministic code generation
llm = ChatBedrockConverse(
    temperature=0,  # Consistent output
    max_tokens=16000,
    additional_model_request_fields={"thinking": {"type": "disabled"}}
)
```

<!-- COMMENTARY NEEDED: Please explain when extended thinking is worth the cost, and whether these configs apply to non-Anthropic models. -->

---

### Progressive Detail Loading

**Pattern**: Inject less context in later prompts based on earlier results.

**Example**: JSON Transformer Expert
- **Mapping phase**: Full source JSON + full target schema (~5000 tokens)
- **Transform phase**: Full source JSON + **filtered** target schema (~1500 tokens)
  - Filtered to only paths identified in mapping phase
  - Reduces tokens by 70%, focuses LLM attention

**Implementation**:
```python
def get_transform_system_prompt_factory():
    def factory(source_json, target_schema, field_mappings):
        # Filter schema to only mapped paths
        mapped_paths = {m['target_path'] for m in field_mappings}
        filtered_schema = filter_schema(target_schema, mapped_paths)

        return SystemMessage(
            content=transform_prompt_template.format(
                source_json=source_json,
                target_schema_filtered=filtered_schema,  # ← Reduced context
                field_mappings=json.dumps(field_mappings)
            )
        )
    return factory
```

**When to use**: Multi-phase workflows where later phases can use results from earlier phases to reduce context.

---

### Multi-Stage Validation

**Pattern**: Validate LLM output through progressive stages.

**Stages**:
1. **Syntax validation**: Can Python parse it?
2. **Loading validation**: Does it define expected functions?
3. **Invocation validation**: Does it run without errors?
4. **Output validation**: Does output match schema?

**Implementation** (see `reference_implementation/json_transformer_expert/validators.py`):
```python
report = ValidationReport(input=code, output={}, report_entries=[], passed=False)
try:
    # Stage 1: Syntax
    module = load_code(code)
    report.append_entry("Syntax valid", logger.info)

    # Stage 2: Loading
    if not hasattr(module, 'transform'):
        raise PythonLogicNotInModuleError("Missing 'transform'")
    report.append_entry("Module structure valid", logger.info)

    # Stage 3: Invocation
    output = module.transform(input_data)
    report.append_entry("Executed successfully", logger.info)

    # Stage 4: Output
    validate_output_schema(output)
    report.append_entry("Output valid", logger.info)

    report.passed = True
except Exception as e:
    report.append_entry(f"Failed: {e}", logger.error)
    report.passed = False
```

**When to use**: When LLM generates executable code or structured data that must meet specific constraints.

---

## Advanced Patterns

### Multi-Turn Conversations

Tasks accumulate context across invocations:

```python
# First invocation
task = invoke_expert(expert, task)
# task.context = [SystemMessage, AIMessage, ToolMessage]

# Second invocation (same task)
task = invoke_expert(expert, task)
# task.context = [SystemMessage, AIMessage, ToolMessage, SystemMessage, AIMessage, ToolMessage]
```

**Use cases**:
- Refinement: "Here's validation feedback, revise your output"
- Clarification: "Missing information detected, ask follow-up question"
- Iteration: "Iterate on design until constraints satisfied"

<!-- COMMENTARY NEEDED: Please explain when multi-turn is better than creating a new task, and any gotchas with context accumulation. -->

---

### Chaining Multiple Experts

Two-phase pattern from JSON Transformer example:

```python
# Phase 1: Mapping
mapping_expert = get_mapping_expert()
mapping_task = MappingTask(task_id="map-001", context=[], ...)
mapping_task = invoke_expert(mapping_expert, mapping_task)

# Phase 2: Transform (uses mapping results)
transform_expert = get_transform_expert()
transform_task = TransformTask(
    task_id="transform-001",
    context=[],
    mappings=[m.to_json() for m in mapping_task.mapping_report.mappings],  # ← Pass results
    ...
)
transform_task = invoke_expert(transform_expert, transform_task)
```

**Pattern**: Each phase is independent, results passed explicitly between phases.

---

### Async Batch Processing

Infrastructure is in place for batch processing (currently used for single tasks):

```python
# Current usage (single task)
inference_result = perform_inference(expert.llm, [inference_task])[0]

# Future scaling (multiple tasks)
inference_results = perform_inference(expert.llm, [task1, task2, task3])
```

The `perform_inference()` function uses `asyncio.gather()` for parallel execution.

<!-- COMMENTARY NEEDED: Please explain when batching makes sense and whether this works with all LLM providers. -->

---

## Common Patterns Reference

### Factory Pattern for Experts
- Centralize Expert creation in `get_*_expert()` functions
- Makes configuration changes easy (one place to update)
- Consistent interface across expert types

### Dataclass-Heavy Architecture
- Use dataclasses for all domain models (Tasks, work items, validation reports)
- Always include `to_json()` for serialization
- Type hints + runtime type checking in `set_work_item()`

### Custom Exception Hierarchy
- Domain-specific exceptions for validation errors
- Examples: `PythonLogicInvalidSyntaxError`, `PythonLogicNotInModuleError`
- Enables precise error handling and clear semantics

### Composition Over Inheritance
- Expert *contains* LLM, prompt factory, tools (not inherits)
- Easy to swap implementations (test with mock LLMs)
- Clear separation of concerns

---

## When to Deviate

**Use simpler approaches when**:
- Single expert, single task type (no need for multi-expert abstraction)
- Free-form LLM responses needed (tool-forcing too restrictive)
- No conversation history required (use basic LLM.invoke())
- Quick prototype (full architecture is heavy for experiments)

**Adapt patterns when**:
- Different LLM provider (replace Bedrock config, keep abstractions)
- Different tool requirements (extend ToolBundle for multi-tool experts)
- Complex orchestration (add orchestrator layer above Experts)

---

## Next Steps

1. **Study the reference**: Review `reference_implementation/json_transformer_expert/` in detail
2. **Copy core/**: Copy `reference_implementation/core/` to your project
3. **Adapt the example**: Modify JSON Transformer for your domain
4. **Configure your LLM**: Replace TODO comments in `expert_def.py` with your provider
5. **Test with validation**: Use `ValidationReport` pattern for generated outputs
6. **Iterate**: Start simple, add complexity as needed

---

## Additional Resources

- **Pattern Analysis**: See `langchain_patterns.md` for detailed pattern extraction from ocsf-playground
- **Reference Implementation**: `reference_implementation/` directory with complete example
- **Original Source**: ocsf-playground repository (AWS Bedrock + Django backend)

---

**Status**: Initial draft ready for review and refinement.
