---
name: langchain-expert-builder
description: Build LangChain-based multi-expert systems using the Expert-Task-Tool pattern. Use when implementing LLM workflows with structured output, multi-turn conversations, validation pipelines, or task-specific AI agents. Provides production-ready Python abstractions and complete reference implementation for code generation, analysis, or classification experts.
---

# LangChain Expert Builder

## Overview

Build production-ready LangChain multi-expert systems using the **Expert-Task-Tool** architecture pattern. This skill provides copy-paste ready Python code and comprehensive guidance for creating specialized LLM experts with:

- **Structured output**: Force LLMs to produce validated, type-safe results via tool schemas
- **Multi-turn conversations**: Tasks accumulate context for validation retry loops
- **Compositional design**: Experts, Tasks, and Tools combine cleanly
- **Provider flexibility**: Works with any LangChain-compatible LLM (Bedrock, OpenAI, etc.)

**When to use this skill:**
- Implementing LLM workflows requiring structured, validated output
- Creating task-specific AI agents (code generation, data analysis, classification)
- Building multi-phase expert pipelines (analysis → generation → validation)
- Designing LLM systems that need validation retry loops or fine-tuning observability

## Core Philosophy: Narrow Scope, Deep Specialization

The multi-expert architecture follows a foundational principle: **LLMs perform best when given narrowly-scoped domains to operate within**. Achieve this through:

1. **Focused prompts**: Each expert gets a highly specialized system prompt for one specific task type
2. **Specially-tailored tools**: Tools define precise output schemas as API contracts, not prose instructions
3. **Carefully filtered context**: Inject only relevant information (progressive detail loading pattern)

**Why narrow scope matters:**
- Eliminate ambiguity (expert knows its singular purpose)
- Improve output quality (prompt optimized for one task type)
- Enable fine-tuning (collect validation data per expert type)
- Simplify debugging (narrow scope = easier to diagnose failures)

**Trade-off**: Creating multiple experts requires upfront work, but spinning up experts is lightweight at runtime (factory pattern) and pays dividends in reliability and maintainability.

## Quick Start Workflow

### Step 1: Copy the Foundation

Copy `assets/reference_implementation/core/` to the target project. These files provide domain-agnostic, production-ready abstractions:

```
your_project/
└── core/                    # ← Copy from assets/reference_implementation/core/
    ├── experts.py           # Expert dataclass + invoke_expert() orchestration
    ├── tasks.py             # Task ABC for work items + conversation context
    ├── tools.py             # ToolBundle for structured output
    ├── messages.py          # Framework-agnostic message types
    ├── base_validator.py    # Dependency-injected validation
    ├── inference.py         # Async batch inference
    └── validation_report.py # Validation accumulation for observability
```

### Step 2: Study the Reference Implementation

Review `assets/reference_implementation/json_transformer_expert/` to understand the complete pattern:

- **Two-phase workflow**: Mapping expert (analysis) → Transform expert (code generation)
- **Progressive detail loading**: Full schema in phase 1, filtered schema in phase 2 (70% token reduction)
- **Contrasting LLM configs**: temp=1 + extended thinking (analysis) vs temp=0 + disabled thinking (code gen)
- **Multi-stage validation**: Syntax → loading → invocation → output validation with retry loops

### Step 3: Build Domain-Specific Expert

Follow the seven-step expert creation process (see "Building Your First Expert" section below). The reference implementation demonstrates each step with production code.

## Building Your First Expert

### Step 1: Define Domain Models

**See:** `assets/reference_implementation/json_transformer_expert/models.py`

Create dataclasses for work items (e.g., `FieldMapping`, `MappingReport`, `TransformCode`).

**Key patterns:**
- All domain models are dataclasses with type hints
- Every model has `to_json()` method for serialization
- Keep models simple: pure data containers, no business logic

### Step 2: Implement Task

**See:** `assets/reference_implementation/json_transformer_expert/task_def.py:18-51` (MappingTask) and `task_def.py:55-91` (TransformTask)

Subclass `Task` with:
- **Input fields**: Domain-specific data (e.g., `source_json`, `target_schema`)
- **Work item field**: Result type (e.g., `mapping_report: Optional[MappingReport]`)
- **`get_work_item()`**: Return the work item
- **`set_work_item()`**: Set with runtime type checking (raise TypeError if wrong type)
- **`get_tool_name()`**: Return tool name string (must match StructuredTool name)
- **`to_json()`**: Serialize task state for debugging

### Step 3: Define Tool

**See:** `assets/reference_implementation/json_transformer_expert/tool_def.py:20-75` (mapping tool) and `tool_def.py:82-125` (transform tool)

Create three components:
1. **Pydantic input schema**: Nested BaseModel classes for LLM arguments (use Field descriptions heavily)
2. **Tool function**: Converts Pydantic models → domain dataclasses
3. **StructuredTool**: Created via `StructuredTool.from_function(func=..., name=..., args_schema=...)`

**Field description best practices** (from tool_def.py:23-33):
- Use constraints: "MUST", "exact path that exists"
- Provide format examples: "e.g., 'user.email'"
- Explain semantics: "represents the source IP address, not destination"

### Step 4: Write Prompt Template

**See:** `assets/reference_implementation/json_transformer_expert/prompting/templates.py`

Create multi-section templates with XML tags:
- Use `<guidelines>`, `<source_json>`, `<target_schema>` for structure
- Include explicit constraints: "ALWAYS", "MUST", "NEVER"
- Use placeholders: `{source_json}`, `{target_schema}`

### Step 5: Create Prompt Factory

**See:** `assets/reference_implementation/json_transformer_expert/prompting/generation.py:19-36` (mapping factory) and `generation.py:39-69` (transform factory with progressive detail)

Create factory functions that:
- Take domain inputs as arguments
- Return `SystemMessage` with formatted prompt
- Support dynamic context injection (e.g., filtering schemas based on earlier results)

**Why factory pattern?** Enables late binding, testability, and dynamic context loading (progressive detail pattern).

### Step 6: Wire Together in Expert Factory

**See:** `assets/reference_implementation/json_transformer_expert/expert_def.py:32-85` (mapping expert) and `expert_def.py:88-140` (transform expert)

Create `get_*_expert()` functions that:
1. Get tool bundle
2. Configure LLM client (TODO in reference impl - replace with your provider)
3. Bind tools: `llm.bind_tools(tool_bundle.to_list())`
4. Return `Expert(llm=llm_w_tools, system_prompt_factory=..., tools=...)`

**LLM config examples** in comments show temp=1 (creative) vs temp=0 (deterministic) patterns.

### Step 7: Invoke the Expert

**Complete invocation pattern** (5 steps):

```python
from langchain_core.messages import HumanMessage
from core.experts import invoke_expert
from your_expert.expert_def import get_your_expert
from your_expert.task_def import YourTask

# 1. Get Expert (factory creates LLM + tools + prompt factory)
expert = get_your_expert()

# 2. Generate SystemMessage via prompt factory
system_message = expert.system_prompt_factory(
    input_data=your_input_data,
    other_context=additional_params
)

# 3. Build conversation turns (SystemMessage + HumanMessage trigger)
turns = [
    system_message,
    HumanMessage(content="Please perform the task.")
]

# 4. Create Task with input data + conversation context + empty work item
task = YourTask(
    task_id=task_id,
    input=your_input_data,
    context=turns,
    work_item=None  # Will be populated by invoke_expert()
)

# 5. Invoke Expert (runs LLM inference, captures tool call, sets work item)
result = invoke_expert(expert, task)

# 6. Access structured result via work item
output = result.get_work_item()
```

**Key insights:**
- **Prompt factory separation**: Call `expert.system_prompt_factory()` explicitly to control when/how context loads
- **Conversation turns pattern**: Construct `[SystemMessage, HumanMessage]`, then pass to Task
- **HumanMessage trigger**: Signals "start now" - exact content doesn't matter much
- **Task initialization**: Create with `work_item=None`, `invoke_expert()` populates it via tool call
- **Result access**: `result.get_work_item()` returns structured output (validated by Pydantic, converted to domain dataclass)

## Key Design Decisions

### Tool-Forcing Pattern

Bind tools to LLM to **force** structured output:

```python
llm_w_tools = llm.bind_tools(tool_bundle.to_list())
```

**Core rationale**: Tools turn response format from prose instructions into API specifications. Instead of asking the LLM to "return a JSON object with these fields...", define a Pydantic schema that LangChain enforces automatically.

**Why this works:**
- **No parsing ambiguity**: Tool schema is an API contract, not a natural language description
- **Automatic validation**: LangChain validates tool arguments against Pydantic schema
- **Type safety**: Pydantic enforces field types, required/optional status, nested structures
- **Clear success signal**: Tool call = task completion
- **Structured debugging**: Validation failures produce clear error messages

**The alternative (prose instructions)** leads to: inconsistent formatting, parsing failures, ambiguous success, version drift.

**Trade-off**: Every expert invocation MUST produce a tool call. For free-form responses, use separate experts or add optional "explanation" field to tool schema.

### LLM Configuration Spectrum

Match LLM configuration to task characteristics:

| Task Type | Temperature | Extended Thinking | Max Tokens | Use Case |
|-----------|-------------|-------------------|------------|----------|
| **Analysis/Discovery** | 1 | Enabled | 30K+ | Entity extraction, pattern discovery, complex reasoning |
| **Code Generation** | 0 | Disabled | 16K | Regex, Python functions, deterministic transforms |
| **Classification** | 0 | Disabled | 16K | Category selection, yes/no decisions |

### Progressive Detail Loading

Inject less context in later prompts based on earlier results.

**Example from reference implementation:**
- **Mapping phase**: Full source JSON + full target schema (~5000 tokens)
- **Transform phase**: Full source JSON + **filtered** target schema (~1500 tokens)
  - Filtered to only paths identified in mapping phase
  - 70% token reduction, focuses LLM attention

**Implementation** (see `prompting/generation.py:39-69`):
1. Extract mapped paths from phase 1 results
2. Filter target schema to only include those paths
3. Pass filtered schema in phase 2 prompt

**When to use**: Multi-phase workflows where later phases can use earlier results to reduce context.

### Multi-Stage Validation

Validate LLM output through progressive stages, accumulating detailed results in `ValidationReport`.

**Four-stage validation example** (see `validators.py:26-139`):
1. **Syntax validation**: Can Python parse it? (uses `exec()` with ModuleType)
2. **Loading validation**: Does it define expected functions? (uses `hasattr()`)
3. **Invocation validation**: Does it run without errors? (calls the function)
4. **Output validation**: Does output match schema? (type/structure checks)

**Key patterns:**
- Use `ValidationReport` to accumulate results
- Define custom exceptions in expert's validators.py for semantic clarity
- `report.append_entry()` provides dual logging (logger + report)
- Early exit on failure with `report.passed = False`

**The role of ValidationReport - three critical use cases:**

1. **Human debugging**: Detailed report entries show exactly where/why LLM output failed
2. **LLM self-correction**: Feed ValidationReport back to same expert for retry (see Multi-Turn Conversations below)
3. **Model tuning dataset**: ValidationReport + Task context = complete training example
   - **Input**: Task.context (system prompt + user message)
   - **Output**: Task work item (LLM's structured response)
   - **Label**: ValidationReport.passed (True/False) + report_entries
   - **Use case**: Collect (prompt, response, validation) tuples for fine-tuning
   - **Benefit**: Improve baseline success rate for specific expert tasks

## Advanced Patterns

### Multi-Turn Conversations

Tasks accumulate context across invocations for validation-driven refinement.

**Common pattern - validation retry loop:**
```python
MAX_RETRIES = 3
for attempt in range(MAX_RETRIES):
    task = invoke_expert(expert, task)
    validation_report = validate(task.get_work_item())

    if validation_report.passed:
        break

    # Append validation feedback to conversation
    feedback_message = HumanMessage(
        content=f"Validation failed:\n{validation_report.to_json()}\nPlease revise."
    )
    task.context.append(feedback_message)
```

**When to use multi-turn vs new task:**
- **Multi-turn**: When LLM should "remember" previous attempt and refine it (same problem, iterative improvement)
- **New task**: When problem/context has fundamentally changed (different input data, different requirements)

**Context accumulation gotchas:**
- Each turn adds tokens (SystemMessage + AIMessage + ToolMessage ≈ 500-5000 tokens)
- Long conversations may hit context limits (monitor total token count)
- Validation reports in feedback should be concise (detailed logs bloat context)

### Multi-Tool Experts

**Pattern**: Experts can expose multiple tools for closely related outcomes from the same specialized prompt.

**Current implementation**: Each expert has one primary tool (see `core/tools.py:16-43`)

**When to use multiple tools**: When single specialized expert could produce different but closely related structured outputs:

1. **Retry with different strategy**: `submit_solution` vs `request_clarification`
2. **Validation-aware generation**: `generate_code` vs `revise_code` (includes extra fields for what changed)
3. **Hierarchical results**: `high_confidence_result` vs `low_confidence_result` (uncertainty fields)

**Implementation guidance:**
- Extend `ToolBundle` to accept list of tools (currently single `task_tool`)
- All tools must produce compatible work item types (or use discriminated union in Task)
- Tool selection is LLM's choice based on prompt instructions

**Why this is rare**: Narrow-scope philosophy usually means "one expert, one output type". Multi-tool appropriate when *prompt* is identical but *outcome format* varies based on runtime conditions LLM detects (e.g., confidence level, data quality).

### Chaining Multiple Experts

**Two-phase pattern from reference implementation:**
1. **Phase 1 (Mapping)**: Analysis expert produces mappings
2. **Phase 2 (Transform)**: Code generation expert uses mappings to generate transform code

**Key principles:**
- Each phase is independent (separate Expert + Task)
- Results passed explicitly via Task initialization (e.g., `mappings=...`)
- Each phase can have different LLM config (temp=1 vs temp=0)
- Progressive detail loading: Phase 2 gets filtered context based on Phase 1 results

## Resources

### references/langchain_patterns.md

Detailed pattern extraction from the original ocsf-playground codebase. Contains 17 architectural patterns across 7 categories with implementation examples. Load this when need deeper understanding of specific patterns or want to see original source material.

### assets/reference_implementation/

Complete, copy-paste ready Python implementation:

**core/** - Domain-agnostic abstractions (copy to every project):
- `experts.py` - Expert dataclass + `invoke_expert()` orchestration
- `tasks.py` - Task ABC for work items + conversation context
- `tools.py` - ToolBundle for structured output tools
- `inference.py` - Async batch inference with `perform_inference()`
- `validation_report.py` - ValidationReport for observability

**json_transformer_expert/** - Complete reference implementation demonstrating all patterns:
- Two-phase expert workflow (mapping → transform)
- Progressive detail loading (schema filtering)
- Multi-stage validation (syntax → loading → invocation → output)
- Contrasting LLM configurations (creative vs deterministic)
- Production-ready code for JSON-to-JSON transformation use case

Use the reference implementation as a template: copy the structure, replace domain-specific logic with your use case.
