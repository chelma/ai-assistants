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

### Core Philosophy: Narrow Scope, Deep Specialization

The multi-expert architecture is built on a foundational principle: **LLMs perform best when given narrowly-scoped domains to operate within**. This is achieved through three mechanisms:

1. **Focused prompts**: Each expert gets a highly specialized system prompt tailored to one specific task type
2. **Specially-tailored tools**: Tools define precise output schemas, eliminating ambiguity about response format
3. **Carefully filtered context**: Only relevant information is injected into each expert's prompt (see [Progressive Detail Loading](#progressive-detail-loading))

**Why narrow scope matters**: Generic "do everything" LLM interfaces produce inconsistent results because the model must interpret intent, choose output format, and perform the task simultaneously. By creating task-specific experts, you:
- Eliminate ambiguity (expert knows its singular purpose)
- Improve output quality (prompt optimized for one task type)
- Enable fine-tuning (collect validation data per expert type)
- Simplify debugging (narrow scope = easier to diagnose failures)

**Development/runtime trade-off**: Spinning up experts is lightweight at runtime (factory creates LLM + tools + prompt) and relatively simple at development time (copy pattern, customize for your domain). The upfront work of creating multiple experts pays dividends in reliability and maintainability.

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

**See:** `reference_implementation/core/experts.py:40-51`

An **Expert** encapsulates a complete LLM inference capability with three components:
- `llm`: LangChain Runnable (LLM with tools bound via `bind_tools()`)
- `system_prompt_factory`: Callable that generates SystemMessage dynamically
- `tools`: ToolBundle containing structured output schema(s)

**Why Expert?**
- Bundles LLM + prompts + tools into a single, reusable unit
- Enables multiple expert "modes" (analysis, generation, classification)
- Factory pattern makes configuration changes easy

**Lifecycle** (see `experts.py:59-117` for `invoke_expert()` implementation):
1. Create Expert via factory function (`get_*_expert()`)
2. Pass Expert + Task to `invoke_expert()`
3. Expert produces structured output in Task

---

### Task

**See:** `reference_implementation/core/tasks.py:24-103`

A **Task** represents work to be performed with:
- `task_id`: Unique identifier
- `context`: List of LangChain messages (conversation history)
- Abstract methods: `get_work_item()`, `set_work_item()`, `get_tool_name()`, `to_json()`

**Why Task?**
- Encapsulates input data + result (work item)
- Maintains conversation context for multi-turn workflows
- Type-safe work item access (enforced by `set_work_item()`)

**Concrete example:** See `reference_implementation/json_transformer_expert/task_def.py:18-51` (MappingTask)

<!-- COMMENTARY NEEDED: Please explain when/why you'd want multi-turn conversations vs single-shot. -->

---

### Tool

**See:** `reference_implementation/json_transformer_expert/tool_def.py:20-75` for complete example

Tools define the **structured output schema** using Pydantic BaseModel + LangChain StructuredTool.

**Three-part pattern:**
1. **Pydantic schema**: BaseModel classes with Field descriptions
2. **Tool function**: Converts Pydantic args → domain dataclasses
3. **StructuredTool**: Created via `StructuredTool.from_function(func=..., name=..., args_schema=...)`

**Why Pydantic + StructuredTool?**
- LangChain validates LLM arguments against schema automatically
- Field descriptions guide the LLM on what to produce
- Tool function converts Pydantic input → domain dataclass
- Guarantees structured output (no parsing errors)

**Field description best practices** (see tool_def.py:23-33):
- Use constraints: "MUST", "exact path that exists"
- Provide examples: "e.g., 'user.email' not just 'email'"
- Explain semantics: "represents the source IP address, not destination"

---

### ToolBundle

**See:** `reference_implementation/core/tools.py:16-43`

**ToolBundle** wraps tools for an Expert:
- `task_tool`: The primary StructuredTool
- `to_list()`: Returns list of tools for `bind_tools()`

**Why ToolBundle?**
- Consistent interface for `bind_tools()`
- Current pattern: one tool per Expert
- Extensible: add `helper_tools` field for multi-tool Experts (see extensibility comment in tools.py:27-32)

---

## Building Your First Expert

The complete reference implementation is in `reference_implementation/json_transformer_expert/`. Below is a walkthrough of the key files and patterns to adapt for your domain.

### Step 1: Define Your Domain Models

**See:** `reference_implementation/json_transformer_expert/models.py`

Create dataclasses for your work items (e.g., `FieldMapping`, `MappingReport`, `TransformCode`).

**Key patterns:**
- All domain models are dataclasses with type hints
- Every model has `to_json()` method for serialization
- Keep models simple: pure data containers, no business logic

---

### Step 2: Implement Your Task

**See:** `reference_implementation/json_transformer_expert/task_def.py:18-51` (MappingTask) and `task_def.py:55-91` (TransformTask)

Subclass `Task` with:
- **Input fields**: Domain-specific data (e.g., `source_json`, `target_schema`)
- **Work item field**: Result type (e.g., `mapping_report: Optional[MappingReport]`)
- **`get_work_item()`**: Return the work item
- **`set_work_item()`**: Set with runtime type checking (raise TypeError if wrong type)
- **`get_tool_name()`**: Return tool name string (must match StructuredTool name)
- **`to_json()`**: Serialize task state for debugging

---

### Step 3: Define Your Tool

**See:** `reference_implementation/json_transformer_expert/tool_def.py:20-75` (mapping tool) and `tool_def.py:82-125` (transform tool)

Create three components:
1. **Pydantic input schema**: Nested BaseModel classes for LLM arguments (use Field descriptions heavily)
2. **Tool function**: Converts Pydantic models → domain dataclasses
3. **StructuredTool**: Created via `StructuredTool.from_function(func=..., name=..., args_schema=...)`

**Field description best practices** (from tool_def.py:23-33):
- Use constraints: "MUST", "exact path that exists"
- Provide format examples: "e.g., 'user.email'"
- Explain semantics: "represents the source IP address, not destination"

---

### Step 4: Write Prompt Template

**See:** `reference_implementation/json_transformer_expert/prompting/templates.py`

Create multi-section templates with XML tags:
- Use `<guidelines>`, `<source_json>`, `<target_schema>` for structure
- Include explicit constraints: "ALWAYS", "MUST", "NEVER"
- Use placeholders: `{source_json}`, `{target_schema}`

<!-- COMMENTARY NEEDED: Please explain when to use single-section vs multi-section templates, and whether XML tags are required or just a convention. -->

---

### Step 5: Create Prompt Factory

**See:** `reference_implementation/json_transformer_expert/prompting/generation.py:19-36` (mapping factory) and `generation.py:39-69` (transform factory with progressive detail)

Create factory functions that:
- Take domain inputs as arguments
- Return `SystemMessage` with formatted prompt
- Support dynamic context injection (e.g., filtering schemas based on earlier results)

**Why factory pattern?** Enables late binding, testability, and dynamic context loading.

---

### Step 6: Wire Together in Expert Factory

**See:** `reference_implementation/json_transformer_expert/expert_def.py:32-85` (mapping expert) and `expert_def.py:88-140` (transform expert)

Create `get_*_expert()` functions that:
1. Get tool bundle
2. Configure LLM client (TODO in reference impl - replace with your provider)
3. Bind tools: `llm.bind_tools(tool_bundle.to_list())`
4. Return `Expert(llm=llm_w_tools, system_prompt_factory=..., tools=...)`

**LLM config examples** in comments show temp=1 (creative) vs temp=0 (deterministic) patterns.

---

### Step 7: Invoke Your Expert

**See:** `reference_implementation/json_transformer_expert/README.md:33-57` (Phase 1 workflow) and `README.md:62-85` (Phase 2 workflow)

The invocation workflow has five distinct steps that wire together all the abstractions:

**Complete invocation pattern** (reference: `~/workspace/personal/ocsf-playground/playground/playground_api/views.py:303-325`):

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

**Key invocation insights:**

1. **Prompt factory separation**: The `expert.system_prompt_factory()` is called *explicitly* by you, not by `invoke_expert()`. This gives you control over when/how context is loaded.

2. **Conversation turns pattern**: The `context` field is a list of LangChain messages. You construct the initial conversation with `[SystemMessage, HumanMessage]`, then pass it to the Task. Multi-turn workflows append additional turns.

3. **HumanMessage trigger**: The `HumanMessage("Please perform the task.")` acts as the LLM trigger. The exact content doesn't matter much—the SystemMessage contains the real instructions. The HumanMessage just signals "start now."

4. **Task initialization**: Tasks are created with `work_item=None`. The `invoke_expert()` function captures the LLM's tool call and uses `task.set_work_item()` to populate it (see `core/experts.py:59-117` for implementation).

5. **Result access**: After invocation, `result.get_work_item()` returns the structured output (validated by Pydantic, converted by your tool function to domain dataclass).

**Why this matters**: This explicit wiring gives you fine-grained control over context loading (progressive detail), multi-turn refinement, and separates concerns cleanly (factory creates expert, you orchestrate invocation).

---

## Key Design Decisions

### Tool-Forcing Pattern

**Pattern**: Bind tools to LLM to **force** structured output.

```python
llm_w_tools = llm.bind_tools(tool_bundle.to_list())
```

**Core rationale**: Tools turn response format from prose instructions into API specifications. Instead of asking the LLM to "return a JSON object with these fields...", you define a Pydantic schema that LangChain enforces automatically. This eliminates the entire class of "LLM didn't follow format instructions" failures.

**Why this works:**
- **No parsing ambiguity**: Tool schema is an API contract, not a natural language description
- **Automatic validation**: LangChain validates tool arguments against Pydantic schema before your code sees them
- **Type safety**: Pydantic enforces field types, required/optional status, nested structures
- **Clear success signal**: Tool call = task completion (no need to parse free-form response for success indicators)
- **Structured debugging**: Validation failures produce clear error messages (e.g., "field X missing", "expected int got string")

**The alternative (prose instructions)**: Asking LLMs to follow format instructions in natural language leads to:
- Inconsistent formatting (sometimes they add extra fields, sometimes they nest differently)
- Parsing failures (malformed JSON, inconsistent key names)
- Ambiguous success (did they complete the task or just acknowledge it?)
- Version drift (same prompt produces different structures over time)

**Trade-off**: Every expert invocation MUST produce a tool call. This pattern doesn't support free-form responses. If you need both structured output AND free-form explanation, use two separate experts or add an optional "explanation" field to your tool schema.

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

**See:** `reference_implementation/json_transformer_expert/prompting/generation.py:39-69` for complete implementation

**Example**: JSON Transformer Expert
- **Mapping phase**: Full source JSON + full target schema (~5000 tokens)
- **Transform phase**: Full source JSON + **filtered** target schema (~1500 tokens)
  - Filtered to only paths identified in mapping phase
  - Reduces tokens by 70%, focuses LLM attention

**Key technique** (from generation.py:51-59):
- Extract mapped paths from phase 1 results
- Filter target schema to only include those paths
- Pass filtered schema in phase 2 prompt
- Result: Smaller context, focused LLM attention

**When to use**: Multi-phase workflows where later phases can use results from earlier phases to reduce context.

---

### Multi-Stage Validation

**Pattern**: Validate LLM output through progressive stages, accumulating detailed results in a `ValidationReport`.

**See:** `reference_implementation/json_transformer_expert/validators.py:26-139` for complete implementation

**Four-stage validation** (from validators.py:38-69):
1. **Syntax validation**: Can Python parse it? (uses `exec()` with ModuleType)
2. **Loading validation**: Does it define expected functions? (uses `hasattr()`)
3. **Invocation validation**: Does it run without errors? (calls the function)
4. **Output validation**: Does output match schema? (type/structure checks)

**Key patterns:**
- Use `ValidationReport` (from `core/validation_report.py`) to accumulate results
- Define custom exceptions in your expert's validators.py for semantic clarity
- `report.append_entry()` provides dual logging (logger + report)
- Early exit on failure with `report.passed = False`

**The role of ValidationReport - three critical use cases:**

1. **Human debugging**: Detailed report entries show exactly where/why LLM output failed
   - Example: "✗ Syntax error on line 23: unexpected indent"
   - Humans can fix prompts, adjust schemas, or improve examples

2. **LLM self-correction**: Feed ValidationReport back to same expert for retry (see [Multi-Turn Conversations](#multi-turn-conversations))
   - Example: "Validation failed: Missing required field 'timestamp'. Please revise."
   - LLM sees structured feedback, attempts correction in next turn

3. **Model tuning dataset**: ValidationReport + Task context = complete training example
   - **Input**: Task.context (system prompt + user message)
   - **Output**: Task work item (LLM's structured response)
   - **Label**: ValidationReport.passed (True/False) + report_entries (diagnostic details)
   - **Use case**: Collect thousands of (prompt, response, validation) tuples across production usage
   - **Benefit**: Fine-tune model on your specific expert's task to improve baseline success rate

**Why capture both input and output:**
- Task holds conversation history (input context)
- ValidationReport holds performance assessment (output quality)
- Together they form complete observability: "Given this prompt, LLM produced this output, which passed/failed for these reasons"

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
- **Validation-driven refinement**: "Here's validation feedback, revise your output"
- **Clarification dialogs**: "Missing information detected, ask follow-up question"
- **Iterative improvement**: "Iterate on design until constraints satisfied"

**Common pattern - validation retry loop**:
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
- **Multi-turn**: When you want the LLM to "remember" its previous attempt and refine it (same problem, iterative improvement)
- **New task**: When the problem/context has fundamentally changed (different input data, different requirements)

**Context accumulation gotchas:**
- Each turn adds tokens (SystemMessage + AIMessage + ToolMessage ≈ 500-5000 tokens)
- Long conversations may hit context limits (monitor total token count)
- Validation reports in feedback should be concise (detailed logs bloat context)

---

### Multi-Tool Experts

**Pattern**: Experts can expose multiple tools for closely related outcomes from the same specialized prompt.

**Current implementation**: Each expert has one primary tool (see `core/tools.py:16-43` for ToolBundle)

**When to use multiple tools**: When a single specialized expert could produce different but closely related structured outputs. Examples:

1. **Retry with different strategy**:
   - Tool 1: `submit_solution` - Primary solution attempt
   - Tool 2: `request_clarification` - Ask for more information if task is ambiguous

2. **Validation-aware generation**:
   - Tool 1: `generate_code` - Initial code generation
   - Tool 2: `revise_code` - Revision given validation feedback (includes extra fields for what changed)

3. **Hierarchical results**:
   - Tool 1: `high_confidence_result` - Solution with confidence ≥ 0.8
   - Tool 2: `low_confidence_result` - Solution with confidence < 0.8 (includes uncertainty fields)

**Implementation guidance**:
- Extend `ToolBundle` to accept list of tools (currently single `task_tool`)
- All tools must produce compatible work item types (or use discriminated union in Task)
- Tool selection is LLM's choice based on prompt instructions
- See `core/tools.py:27-32` for extensibility comment

**Why this is rare in current architecture**: The narrow-scope philosophy usually means "one expert, one output type". Multi-tool experts are appropriate when the *prompt* is identical but *outcome format* varies slightly based on runtime conditions the LLM detects (e.g., confidence level, data quality).

---

### Chaining Multiple Experts

**See:** `reference_implementation/json_transformer_expert/README.md:29-104` for complete two-phase workflow

**Two-phase pattern** from JSON Transformer example:
1. **Phase 1 (Mapping)**: Analysis expert produces mappings
2. **Phase 2 (Transform)**: Code generation expert uses mappings to generate transform code

**Key principles:**
- Each phase is independent (separate Expert + Task)
- Results passed explicitly via Task initialization (e.g., `mappings=...`)
- Each phase can have different LLM config (temp=1 vs temp=0)
- Progressive detail loading: Phase 2 gets filtered context based on Phase 1 results

**Pattern**: Each phase is independent, results passed explicitly between phases.

---

### Async Batch Processing

**See:** `reference_implementation/core/inference.py:59-112` for implementation

Infrastructure is in place for batch processing (currently used for single tasks in `invoke_expert()`).

**How it works** (from inference.py:80-112):
- `perform_inference()` wraps async implementation with `asyncio.run()`
- `_perform_async_inference()` uses `asyncio.gather()` for parallel LLM invocations
- Returns list of `InferenceResult` objects matching input order

**Current usage:** Single-task batches (future: parallelize multiple tasks)

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
