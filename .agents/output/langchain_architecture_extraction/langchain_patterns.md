# LangChain Architecture Patterns

**Last Updated**: 2025-10-30
**Source Repository**: ocsf-playground
**Analysis Status**: Iteration 2 Complete (All Experts + Validation)

---

## How to Use This Guide

This document captures architectural patterns and best practices for structuring LangChain/LLM inference systems. These patterns are drawn from production code and represent battle-tested approaches to common challenges.

**Guiding Principles:**
1. **Adapt to context**: These patterns should inform your design, not constrain it
2. **Question assumptions**: If a pattern doesn't fit your use case, understand why and adapt accordingly
3. **Focus on architecture**: This guide emphasizes structural patterns, not framework-specific details
4. **Maintain portability**: Patterns are independent of application framework (Django, Temporal, etc.)

**When to deviate**: When your requirements conflict with these patterns, when simpler approaches suffice, or when you have better alternatives. Always prioritize clarity, maintainability, and fit-for-purpose design.

---

## Analysis Categories

1. [Abstraction Architecture](#1-abstraction-architecture)
2. [LangChain Integration](#2-langchain-integration)
3. [Prompt Engineering](#3-prompt-engineering)
4. [Tool Management](#4-tool-management)
5. [Validation & Error Handling](#5-validation--error-handling)
6. [Inference Orchestration](#6-inference-orchestration)
7. [Configuration & Extensibility](#7-configuration--extensibility)

---

## 1. Abstraction Architecture

### 1.1 Core Pattern: Expert-Task-Tool Trinity

**Pattern**: Separate concerns into three core abstractions that compose together.

```python
@dataclass
class Expert:
    llm: Runnable[LanguageModelInput, BaseMessage]
    system_prompt_factory: Callable[[Dict[str, Any]], SystemMessage]
    tools: ToolBundle
```

**Expert Responsibilities**:
- Encapsulates LLM client + configuration
- Bundles system prompt generation logic
- Associates LLM with available tools
- Represents a complete "inference capability"

**Source**: `backend/core/experts.py:28-32`

**When to use**: When you need multiple inference "modes" with different prompts, tools, or LLM configurations.

---

### 1.2 Task Abstraction Pattern

**Pattern**: Abstract base class with lifecycle methods for work item management.

```python
@dataclass
class PlaygroundTask(ABC):
    task_id: str
    context: List[BaseMessage]  # LangChain message history

    @abstractmethod
    def get_work_item(self) -> Any: pass

    @abstractmethod
    def set_work_item(self, new_work_item: Any): pass

    @abstractmethod
    def get_tool_name(self) -> str: pass

    @abstractmethod
    def to_json(self) -> Dict[str, Any]: pass

    def to_inference_task(self) -> InferenceRequest:
        return InferenceRequest(
            task_id=self.task_id,
            context=self.context
        )
```

**Task Responsibilities**:
- Encapsulates work to be performed (input data)
- Maintains conversation context (LangChain messages)
- Manages work item lifecycle (get/set work item)
- Provides serialization (to_json)
- Converts to inference requests

**Source**: `backend/core/tasks.py:12-37`

**Concrete Example** (`backend/entities_expert/task_def.py:11-33`):
```python
@dataclass
class AnalysisTask(PlaygroundTask):
    input: str
    entities_report: EntityReport = None  # Work item

    def get_work_item(self) -> Any:
        return self.entities_report

    def set_work_item(self, new_work_item: Any):
        if not isinstance(new_work_item, EntityReport):
            raise TypeError("new_work_item must be of type EntityReport")
        self.entities_report = new_work_item

    def get_tool_name(self) -> str:
        return "CreateEntitiesReport"
```

**Key Observations**:
- Task enforces type safety on work items (TypeError if wrong type)
- Work item starts as None, gets populated after inference
- tool_name links Task to its corresponding Tool
- context accumulates messages across multiple inference rounds

---

### 1.3 Tool Bundling Pattern

**Pattern**: Wrap tools in a simple dataclass with conversion method.

```python
@dataclass
class ToolBundle:
    task_tool: StructuredTool

    def to_list(self) -> List[StructuredTool]:
        return [self.task_tool]
```

**Source**: `backend/core/tools.py:11-16`

**Why this pattern**:
- Single tool per Expert (one task = one tool call)
- to_list() provides consistent interface for bind_tools()
- Could be extended to support multiple tools per Expert
- Maintains separation between "tool definition" and "tool usage"

**Observation**: Current pattern is "one Expert, one Tool" but the ToolBundle abstraction allows future extension to multi-tool Experts.

---

### 1.4 Dataclass-Heavy Architecture

**Pattern**: Extensive use of Python dataclasses for all domain objects.

**Examples**:
- `Expert`, `ToolBundle`, `InferenceRequest`, `InferenceResult` (core abstractions)
- `Entity`, `EntityMapping`, `EntityReport` (domain entities)
- `ExtractionPattern` (work products)
- `ValidationReport` (validation results)

**Common Dataclass Features**:
```python
@dataclass
class EntityReport:
    data_type: str
    type_rationale: str
    mappings: List[EntityMapping]

    def to_json(self) -> dict:
        return {
            "data_type": self.data_type,
            "type_rationale": self.type_rationale,
            "mappings": [mapping.to_json() for mapping in self.mappings]
        }
```

**Source**: `backend/entities_expert/entities.py:48-59`

**Dataclass Patterns Observed**:
1. **Serialization**: Every dataclass has `to_json()` method
2. **Deserialization**: Some have `@classmethod from_json()` for round-tripping
3. **Type hints**: All fields are type-hinted
4. **Nested serialization**: Recursive `to_json()` calls for nested dataclasses
5. **Optional fields**: Use `= None` for fields populated later

**Why dataclasses**: Type safety, IDE support, clean serialization, immutability by default (frozen=False allows mutation).

---

### 1.5 Composition Over Inheritance

**Pattern**: Expert dataclass *contains* LLM, prompt factory, and tools rather than inheriting from them.

```python
# NOT using inheritance
class Expert(LLM):  # ❌ Avoid
    ...

# INSTEAD using composition
@dataclass
class Expert:  # ✅ Prefer
    llm: Runnable[LanguageModelInput, BaseMessage]
    system_prompt_factory: Callable[[Dict[str, Any]], SystemMessage]
    tools: ToolBundle
```

**Benefits**:
- Swap LLM implementations without changing Expert interface
- Test with mock LLMs easily
- Clear separation of concerns
- Expert focuses on orchestration, not LLM internals

**Source**: `backend/core/experts.py:28-32`

---

## 2. LangChain Integration

### 2.1 LangChain Component Selection

**Components Used**:
- `langchain_aws.ChatBedrockConverse` - AWS Bedrock LLM client
- `langchain_core.tools.StructuredTool` - Tool definition with schema
- `langchain_core.messages.*` - Message types (SystemMessage, AIMessage, ToolMessage)
- `langchain_core.runnables.Runnable` - Base protocol for LLM chains
- `Runnable.bind_tools()` - Attach tools to LLM
- `Runnable.ainvoke()` - Async LLM invocation

**Source**: Imports across `backend/core/experts.py`, `backend/core/inference.py`, `backend/entities_expert/expert_def.py`

**Key Decisions**:
1. **AWS-specific client**: Uses `ChatBedrockConverse` (not generic OpenAI client)
2. **Tool-forcing**: Binds tools to LLM to enforce structured output
3. **Async by default**: Uses `ainvoke()` not `invoke()`
4. **Message-based context**: Explicit message history management

---

### 2.2 Tool-Forcing Pattern

**Pattern**: Force LLM to produce structured output via tool calls.

```python
# Bind tools to LLM (forces tool usage)
llm_w_tools = llm.bind_tools(tool_bundle.to_list())

# Expert uses bound LLM
Expert(
    llm=llm_w_tools,  # LLM is pre-configured to require tool use
    system_prompt_factory=...,
    tools=tool_bundle
)
```

**Source**: `backend/entities_expert/expert_def.py:35, 71`

**Invocation validates tool call** (`backend/core/experts.py:52-53`):
```python
if not isinstance(inference_result.response, AIMessage) or not inference_result.response.tool_calls:
    raise ExpertInvocationError("The LLM did not create a tool call for the task...")
```

**Why this pattern**:
- Guarantees structured output (Pydantic schema validation)
- Eliminates output parsing errors
- LLM is forced to "complete the task" via tool call
- Tool arguments are validated by LangChain automatically

**Observation**: This is a "tool-required" approach, not "tool-optional". Every Expert invocation MUST produce a tool call.

---

### 2.3 Message Context Management

**Pattern**: Explicit conversation history with LangChain message types.

**Message Flow** (`backend/core/experts.py:37-74`):

```python
# 1. Task contains initial context (may be empty or contain prior messages)
task.context: List[BaseMessage]

# 2. Convert task to inference request
inference_task = task.to_inference_task()  # Wraps context

# 3. Perform inference (context passed to LLM)
inference_result = perform_inference(expert.llm, [inference_task])[0]

# 4. Append LLM response to context
task.context.append(inference_result.response)  # AIMessage

# 5. Execute tool, append tool result to context
task.context.append(
    ToolMessage(
        name=task.get_tool_name(),
        content="Executed the expert task",
        tool_call_id=tool_call["id"]
    )
)
```

**Message Types**:
- `SystemMessage`: System prompt (generated by prompt factory)
- `AIMessage`: LLM response (contains `tool_calls` attribute)
- `ToolMessage`: Tool execution result

**Key Observations**:
1. Context is **mutable** (append messages after each turn)
2. Context is **persistent** across multiple invocations (multi-turn conversations)
3. Context is **serializable** (to_json() on all messages)
4. Tool call ID links AIMessage to ToolMessage

**Source**: `backend/core/experts.py:56-70`

---

### 2.4 AWS Bedrock Configuration

**Pattern**: Aggressive retry configuration for Bedrock throttling.

```python
from botocore.config import Config

DEFULT_BOTO_CONFIG = Config(
    read_timeout=120,  # Wait 2 minutes for a response
    retries={
        'max_attempts': 20,  # Retry up to 20 times
        'mode': 'adaptive'   # Adaptive retry strategy
    }
)
```

**Source**: `backend/core/experts.py:20-26`

**ChatBedrockConverse Configuration** (`backend/entities_expert/expert_def.py:22-34, 59-70`):

```python
# Analysis Expert (creative, extended thinking)
llm = ChatBedrockConverse(
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    temperature=1,  # Must be 1 for "thinking" mode
    max_tokens=30001,
    region_name="us-west-2",  # Limited availability
    additional_model_request_fields={
        "thinking": {
            "type": "enabled",
            "budget_tokens": 30000
        }
    },
    config=DEFULT_BOTO_CONFIG
)

# Extraction Expert (deterministic code generation)
llm = ChatBedrockConverse(
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    temperature=0,  # Deterministic
    max_tokens=30000,
    region_name="us-west-2",
    additional_model_request_fields={
        "thinking": {
            "type": "disabled"
        }
    },
    config=DEFULT_BOTO_CONFIG
)
```

**Configuration Decisions**:
- **Model**: Claude 3.5 Sonnet (us.anthropic.claude-3-7-sonnet-20250219-v1:0)
- **Region**: us-west-2 (limited model availability)
- **Temperature**: 1 for creative tasks (analysis), 0 for deterministic tasks (code generation)
- **Extended Thinking**: Enabled for analysis (budget=30000 tokens), disabled for extraction
- **Timeout**: 120s (long prompts + tool calls)
- **Retries**: 20 attempts with adaptive mode (handles Bedrock throttling)

**Observation**: Extended thinking budget (30000 tokens) is nearly equal to max_tokens (30001), suggesting thinking is a major part of the analysis task.

---

## 3. Prompt Engineering

### 3.1 System Prompt Factory Pattern

**Pattern**: Factory function that returns a closure generating dynamic system prompts.

```python
def get_analyze_system_prompt_factory(
    ocsf_version: OcsfVersion,
    ocsf_event_name: str
) -> Callable[[Dict[str, Any]], SystemMessage]:

    def factory(input_entry: str) -> SystemMessage:
        # Fetch context-specific data
        event_schema = get_ocsf_event_schema(ocsf_version, ocsf_event_name, [])
        object_schemas = get_ocsf_object_schemas(ocsf_version, ocsf_event_name, [])

        # Generate prompt from template
        return SystemMessage(
            content=analyze_prompt_template.format(
                ocsf_version=ocsf_version,
                ocsf_event_class=get_ocsf_event_class_knowledge(ocsf_version, ocsf_event_name),
                ocsf_event_class_schema=json.dumps(event_schema.to_dict(), indent=4),
                ocsf_object_schemas=json.dumps([obj.to_dict() for obj in object_schemas], indent=4),
                input_entry=input_entry
            )
        )

    return factory
```

**Source**: `backend/entities_expert/prompting/generation.py:15-33`

**Why this pattern**:
1. **Partial application**: Version and event name are "baked in" at Expert creation time
2. **Late binding**: input_entry is provided at invocation time
3. **Dynamic context**: Schema data fetched per-invocation (allows for version/event-specific schemas)
4. **Separation**: Prompt generation logic is decoupled from Expert definition
5. **Testability**: Factory can be tested independently with mock inputs

**Factory Lifecycle**:
```python
# 1. Create factory at Expert instantiation
prompt_factory = get_analyze_system_prompt_factory(version, event_name)

# 2. Store factory in Expert
expert = Expert(llm=..., system_prompt_factory=prompt_factory, tools=...)

# 3. Generate prompt at invocation time (in invoke_expert())
system_prompt = expert.system_prompt_factory(task.input)
```

---

### 3.2 Template Structure

**Pattern**: Multi-section prompt template with XML-style tags.

**Example** (`backend/entities_expert/prompting/templates.py:1-67`):

```
You are an AI assistant whose goal is to assist users in transforming their log and
data entries into an OCSF normalized format...

While working towards your goal, you will ALWAYS follow the below general guidelines:
<guidelines>
- Do not attempt to be friendly in your responses.  Be as direct and succinct as possible.
- Think through the problem carefully.
- Never assume any parameter values while invoking a tool or function.
- You may NOT ask clarifying questions to the user if you need more information.
</guidelines>

Additionally, you must ALWAYS follow these output_guidelines for output you produce:
<output_guidelines>
- When selecting entities, your goal is to fill out the OCSF schema as completely as possible.
- You may map the same entity to multiple fields in the OCSF schema if it is relevant to those fields.
...
</output_guidelines>

The specific schema version of OCSF is:
<ocsf_version>{ocsf_version}</ocsf_version>

If there is any grounded knowledge on this ocsf_event_class, it will be provided here:
<ocsf_event_class>{ocsf_event_class}</ocsf_event_class>

...

The input entry is:
<input_entry>{input_entry}</input_entry>
```

**Template Sections**:
1. **Goal/Role**: What the AI is trying to accomplish
2. **General Guidelines**: Behavioral constraints (`<guidelines>`)
3. **Output Guidelines**: Output format/structure constraints (`<output_guidelines>`)
4. **Extraction/Transformation Guidelines**: Task-specific rules (extract prompt only)
5. **Context Injection**: Dynamic data insertion (`<ocsf_version>`, `<input_entry>`, etc.)

**Template Features**:
- **XML tags**: Semantic markers for different sections
- **Explicit constraints**: "ALWAYS", "MUST", "MUST NOT"
- **Placeholders**: `{ocsf_version}`, `{input_entry}`, etc. for .format()
- **Multi-paragraph**: Detailed explanations and examples

**Source**: `backend/entities_expert/prompting/templates.py` (analyze_prompt_template: 171 lines, extract_prompt_template: 103 lines)

---

### 3.3 Dynamic Context Injection

**Pattern**: Fetch and embed request-specific context at prompt generation time.

**Example - Extraction Prompt Factory** (`backend/entities_expert/prompting/generation.py:35-64`):

```python
def get_extract_system_prompt_factory(ocsf_version: OcsfVersion, ocsf_event_name: str) -> Callable:

    def factory(input_entry: str, mapping_list: List[EntityMapping]) -> SystemMessage:
        ocsf_paths = [mapping.ocsf_path for mapping in mapping_list]

        # FILTER: Get only schema attributes relevant to the mapping paths
        event_schema = get_ocsf_event_schema(ocsf_version, ocsf_event_name, ocsf_paths)
        event_schema_simplified = json.dumps(
            event_schema.to_dict(filter_attributes=True),  # ← Filter flag
            indent=4
        )

        # FILTER: Get only object schemas relevant to the mapping paths
        object_schemas = get_ocsf_object_schemas(ocsf_version, ocsf_event_name, ocsf_paths)
        object_schemas_simplified = [obj.to_dict(filter_attributes=True) for obj in object_schemas]
        # Further filter: only include objects with attributes
        object_schemas_final = json.dumps(
            [schema for schema in object_schemas_simplified if schema.get("attributes", None)],
            indent=4
        )

        return SystemMessage(
            content=extract_prompt_template.format(
                ocsf_version=ocsf_version,
                ocsf_event_class=get_ocsf_event_class_knowledge(ocsf_version, ocsf_event_name),
                ocsf_event_class_schema=event_schema_simplified,
                ocsf_object_schemas=object_schemas_final,
                input_entry=input_entry,
                mapping_list=json.dumps([obj.to_json() for obj in mapping_list], indent=4)
            )
        )

    return factory
```

**Key Observations**:
1. **Schema filtering**: Only include relevant schema attributes to reduce token count
2. **Path-based filtering**: Use OCSF paths from mappings to filter schemas
3. **JSON serialization**: Convert dataclasses to JSON for prompt embedding
4. **Conditional filtering**: Second-stage filter removes objects without attributes
5. **Logging**: Debug logs show what schemas are provided to LLM

**Performance Optimization**:
- Analyze prompt: No filtering (needs full schema for entity discovery)
- Extract prompt: Heavy filtering (only needs schemas for known mappings)

---

### 3.4 Knowledge Module Strategy Pattern

**Pattern**: Dispatch to version-specific knowledge based on OCSF version.

```python
def get_ocsf_event_class_knowledge(ocsf_version: OcsfVersion, ocsf_event_name: str) -> str:
    if ocsf_version == OcsfVersion.V1_1_0:
        event_details = next(
            event for event in ocsf_events_V1_1_0 if event["event_name"] == ocsf_event_name
        )
        return json.dumps(event_details, indent=4)

    return ""
```

**Source**: `backend/entities_expert/prompting/knowledge/__init__.py:10-17`

**Pattern**: Strategy pattern with if-elif dispatch.

**Responsibilities**:
- `get_ocsf_event_class_knowledge()`: Fetch event metadata (name, description, etc.)
- `get_ocsf_event_schema()`: Fetch event schema structure
- `get_ocsf_object_schemas()`: Fetch related object schemas

**Why this pattern**:
- Supports multiple OCSF versions without changing core code
- Centralizes version-specific logic
- Returns empty string if version not supported (graceful degradation)

---

## 4. Tool Management

### 4.1 StructuredTool.from_function() Pattern

**Pattern**: Define tool using Pydantic schema + Python function.

**Example - CreateEntitiesReport** (`backend/entities_expert/tool_def.py:22-66`):

```python
# 1. Define Pydantic schema for tool input
class EntityInput(BaseModel):
    value: str = Field(description="The raw value extracted from the input data...")
    description: str = Field(description="A precise explanation of what the value represents...")

class EntityMappingInput(BaseModel):
    entities: List[EntityInput] = Field(description="The list of entities extracted...")
    ocsf_path: str = Field(description="Period-delimited path through the OCSF schema...")
    path_rationale: str = Field(description="A precise explanation of how the mapping relates...")

class CreateEntitiesReport(BaseModel):
    """Create a list of mappings for entities extracted from a data entry"""
    data_type: str = Field(description="A brief, but precise, explanation of the data entry's type...")
    type_rationale: str = Field(description="A detailed and precise justification...")
    mappings: List[EntityMappingInput] = Field(description="List of entity mappings created...")

# 2. Define Python function that executes the tool
def create_entities_report(
    data_type: str,
    type_rationale: str,
    mappings: List[EntityMappingInput]
) -> EntityReport:
    return EntityReport(
        data_type=data_type,
        type_rationale=type_rationale,
        mappings=[
            EntityMapping(
                id=str(uuid.uuid4()),
                entities=[Entity(value=e.value, description=e.description) for e in mapping.entities],
                ocsf_path=mapping.ocsf_path,
                path_rationale=mapping.path_rationale
            )
            for mapping in mappings
        ]
    )

# 3. Create StructuredTool from function
create_entities_resport_tool = StructuredTool.from_function(
    func=create_entities_report,
    name="CreateEntitiesReport",
    args_schema=CreateEntitiesReport
)
```

**Tool Lifecycle**:
1. LLM generates tool call with arguments matching Pydantic schema
2. LangChain validates arguments against schema
3. Tool function is invoked with validated arguments
4. Function returns domain object (EntityReport)
5. Domain object is set as task work item

**Key Observations**:
- **Nested schemas**: EntityMappingInput contains List[EntityInput]
- **Detailed descriptions**: Field descriptions guide LLM on what to provide
- **Domain object return**: Tool returns EntityReport (not dict or JSON)
- **ID generation**: UUID assigned inside tool function (not by LLM)
- **Transformation**: Pydantic input models transformed to dataclass output models

---

### 4.2 Tool Factory Pattern

**Pattern**: Factory function that returns ToolBundle.

```python
def get_analyze_tool_bundle(ocsf_version: OcsfVersion) -> ToolBundle:
    # Use the same tool for all versions
    return ToolBundle(
        task_tool=create_entities_resport_tool,
    )
```

**Source**: `backend/entities_expert/tool_def.py:16-20`

**Why this pattern**:
- Allows version-specific tool selection (even though current impl doesn't vary by version)
- Consistent interface with prompt factories
- Tool creation logic is centralized
- Easy to extend with version-specific tool variations

---

### 4.3 Pydantic Field Descriptions

**Pattern**: Detailed, instructive descriptions in Field() definitions.

**Example**:
```python
class EntityInput(BaseModel):
    value: str = Field(
        description="The raw value extracted from the input data. It MUST have "
                    "the exact value as it appears in the input entry."
    )
    description: str = Field(
        description="A precise explanation of what the value represents in the "
                    "context of the entry. For example, 'Source IP address' is "
                    "much better than 'IP address' or 'source address'. Similarly, "
                    "'Event creation timestamp' is much better than 'timestamp' or 'time'."
    )
```

**Source**: `backend/entities_expert/tool_def.py:24-25`

**Description Patterns**:
1. **Constraints**: "MUST", "MUST NOT", "EXACT SAME"
2. **Examples**: "For example, X is much better than Y"
3. **Comparisons**: "much better than", "rather than"
4. **Context**: "in the context of", "represents in"
5. **Type info**: "period-delimited path", "executable code"

**Why detailed descriptions**: LangChain passes Field descriptions to LLM as JSON Schema, guiding the LLM on what to provide.

---

### 4.4 Tool Invocation Pattern

**Pattern**: Execute tool with LLM-generated arguments.

```python
# 1. LLM produces AIMessage with tool_calls
inference_result = perform_inference(expert.llm, [inference_task])[0]

# 2. Validate tool call exists
if not isinstance(inference_result.response, AIMessage) or not inference_result.response.tool_calls:
    raise ExpertInvocationError("The LLM did not create a tool call...")

# 3. Extract tool call (use last tool call if multiple)
tool_call = inference_result.response.tool_calls[-1]

# 4. Execute tool with LLM arguments
result = expert.tools.task_tool(tool_call["args"])

# 5. Set work item on task
task.set_work_item(result)
```

**Source**: `backend/core/experts.py:47-61`

**Key Observations**:
- Uses **last** tool call if LLM produces multiple (allows LLM to "think" with intermediate tool calls)
- tool_call structure: `{"name": str, "args": dict, "id": str}`
- Result is strongly-typed domain object (not dict)
- set_work_item() enforces type checking

---

## 5. Validation & Error Handling

### 5.1 ValidationReport Accumulation Pattern

**Pattern**: Dataclass that accumulates validation log entries.

```python
@dataclass
class ValidationReport:
    input: str
    output: Dict[str, Any]
    report_entries: List[str]
    passed: bool

    def append_entry(self, entry: str, logging_function: Callable[..., None]):
        logging_function(entry)
        self.report_entries.append(entry)
```

**Source**: `backend/core/validation_report.py:4-30`

**Usage Pattern**:
1. Create ValidationReport with input
2. Perform validation steps
3. Append log entries with `append_entry(msg, logger.info)` or similar
4. Set passed=True/False based on validation result
5. Serialize with `to_json()` for storage/transmission

**Key Observations**:
- **Dual logging**: Logs to logger AND accumulates in report_entries
- **Callable logging**: Accepts any logging function (info, warning, error)
- **Serializable**: Has to_json() and from_json() for persistence
- **Flexible output**: output dict can contain any validation-specific data

**Observation**: ValidationReport is created in core but primarily used in domain-specific validation (see Iteration 2 for validation patterns).

---

### 5.2 Custom Exception Pattern

**Pattern**: Domain-specific exceptions for clear error semantics.

```python
class ExpertInvocationError(Exception):
    pass
```

**Source**: `backend/core/experts.py:34-35`

**Usage**:
```python
if not isinstance(inference_result.response, AIMessage) or not inference_result.response.tool_calls:
    raise ExpertInvocationError("The LLM did not create a tool call for the task.  Final LLM message: " + str(inference_result.response.content))
```

**Why custom exceptions**:
- Distinguishes inference errors from other errors
- Allows targeted exception handling
- Includes LLM response content for debugging

**Observation**: This is a "fail-fast" approach - if LLM doesn't produce tool call, abort immediately.

---

### 5.3 Type Checking in set_work_item()

**Pattern**: Runtime type validation in Task lifecycle methods.

```python
def set_work_item(self, new_work_item: Any):
    if not isinstance(new_work_item, EntityReport):
        raise TypeError("new_work_item must be of type EntityReport")
    self.entities_report = new_work_item
```

**Source**: `backend/entities_expert/task_def.py:19-22`

**Why this pattern**:
- Catches type errors at work item assignment (not at task creation)
- Provides clear error messages
- Supplements type hints with runtime checks
- Prevents silent failures from wrong work item types

---

### 5.4 Multi-Stage Validation Pattern

**Pattern**: Layered validation with progressive refinement - syntax → loading → invocation → output.

**Stage 1: Syntax Validation** (`backend/entities_expert/validators.py:131-135`):
```python
try:
    extract_module = ModuleType("extract")
    exec(f"{pattern.dependency_setup}\n\n{pattern.extract_logic}", extract_module.__dict__)
except SyntaxError as e:
    raise PythonLogicInvalidSyntaxError(f"Syntax error: {str(e)}")
```

**Stage 2: Loading Validation** (`backend/entities_expert/validators.py:138-142`):
```python
if not hasattr(extract_module, "extract"):
    raise PythonLogicNotInModuleError("Missing 'extract' function")
if not callable(extract_module.extract):
    raise PythonLogicNotExecutableError("'extract' must be callable")
```

**Stage 3: Invocation Validation** (`backend/entities_expert/validators.py:35-43`):
```python
try:
    output = extract_logic(report.input)
    report.append_entry("Invoked the extract logic without exceptions", logger.info)
except Exception as e:
    report.append_entry("The extract logic invocation has failed", logger.error)
    raise e
```

**Stage 4: Output Validation** (`backend/entities_expert/validators.py:47-61`):
```python
if isinstance(extract_output, list):
    report.append_entry(f"The extract output matches the expected type: 'list'", logger.info)
else:
    raise ValueError(f"The extract output does NOT match the expected type: 'list'")
if len(extract_output) == 0:
    raise ValueError(f"The extract output is empty")
```

**Validation Orchestration** (`backend/entities_expert/validators.py:103-126`):
```python
report = ValidationReport(input=..., output=dict(), report_entries=[], passed=False)
try:
    extract_logic = self._try_load_extract_logic(report, self.pattern)
    extract_output = self._try_invoke_extract_logic(extract_logic, report)
    self._try_validate_extract_output(self.input_entry, self.pattern, extract_output, report)

    transform_logic = self._try_load_transform_logic(report, self.pattern)
    transform_output = self._try_invoke_transform_logic(transform_logic, extract_output, report)
    self._try_validate_transform_output(self.input_entry, self.pattern, extract_output, transform_output, report)

    report.passed = True
except Exception as e:
    report.passed = False
    report.append_entry(f"Error: {str(e)}", logger.error)
```

**Key Observations**:
- Each stage has specific exception types for precise error reporting
- ValidationReport accumulates entries across all stages
- passed flag only set True if ALL stages succeed
- Early exit on first failure (fail-fast)
- Same pattern repeated for both extract and transform logic

**Why this pattern**:
- Progressive refinement catches errors early (syntax before execution)
- Custom exceptions enable precise error handling
- ValidationReport provides detailed error trace
- Separates concerns (syntax vs semantics vs output validity)

---

### 5.5 Dynamic Python Code Loading Pattern

**Pattern**: Use `ModuleType` + `exec()` to load and execute LLM-generated Python code.

```python
from types import ModuleType

def _load_extract_logic(self, pattern: ExtractionPattern) -> Callable[[str], str]:
    # Create isolated module namespace
    extract_module = ModuleType("extract")

    # Execute code string in module's namespace
    exec(f"{pattern.dependency_setup}\n\n{pattern.extract_logic}", extract_module.__dict__)

    # Validate module structure
    if not hasattr(extract_module, "extract"):
        raise PythonLogicNotInModuleError("Missing 'extract' function")
    if not callable(extract_module.extract):
        raise PythonLogicNotExecutableError("'extract' must be callable")

    # Return callable from module
    return extract_module.extract
```

**Source**: `backend/entities_expert/validators.py:129-144`

**Same pattern for transform logic** (`backend/transformers/validators.py:183-197`):
```python
def _load_transformer_logic(self, transformer: Transformer) -> Callable[[str], str]:
    transformer_module = ModuleType("transformer")
    exec(f"{transformer.dependency_setup}\n\n{transformer.transformer_logic}", transformer_module.__dict__)

    if not hasattr(transformer_module, "transformer"):
        raise PythonLogicNotInModuleError("Missing 'transformer' function")
    if not callable(transformer_module.transformer):
        raise PythonLogicNotExecutableError("'transformer' must be callable")

    return transformer_module.transformer
```

**Key Observations**:
1. **Isolated namespace**: ModuleType creates fresh namespace for each code execution
2. **Dependency injection**: pattern.dependency_setup contains imports/helpers
3. **String concatenation**: Combines setup + logic with newlines
4. **Attribute extraction**: Uses hasattr() + callable() to validate module structure
5. **Callable return**: Returns function object (not module)

**Why this pattern**:
- Enables LLM-generated Python code execution with controlled scope
- Module namespace prevents pollution of global scope
- Dependency setup allows LLM to specify required imports
- Validation ensures expected function exists and is callable
- Can reload code without restarting process

**Security Note**: exec() with untrusted code is dangerous. This pattern assumes code comes from trusted LLM within controlled environment.

---

### 5.6 Custom Exception Hierarchy

**Pattern**: Domain-specific exception types for precise error semantics.

```python
class PythonLogicInvalidSyntaxError(Exception):
    pass

class PythonLogicNotInModuleError(Exception):
    pass

class PythonLogicNotExecutableError(Exception):
    pass
```

**Source**: `backend/core/validators.py:1-9`

**Usage in validation**:
```python
try:
    exec(f"{pattern.dependency_setup}\n\n{pattern.extract_logic}", extract_module.__dict__)
except SyntaxError as e:
    raise PythonLogicInvalidSyntaxError(f"Syntax error: {str(e)}")

if not hasattr(extract_module, "extract"):
    raise PythonLogicNotInModuleError("Missing 'extract' function")

if not callable(extract_module.extract):
    raise PythonLogicNotExecutableError("'extract' must be callable")
```

**Exception Hierarchy Benefits**:
1. **Precise error identification**: Distinguish syntax errors from missing functions from non-callable attributes
2. **Targeted handling**: Can catch specific exception types for different recovery strategies
3. **Clear semantics**: Exception name describes exact failure mode
4. **Error messages**: Custom exception allows custom error messages

**Observation**: Simple exception hierarchy (flat, not nested) with descriptive names. No additional exception attributes (just messages).

---

### 5.7 Recursive Schema Validation Pattern

**Pattern**: Recursive descent validation with path tracking for nested objects.

```python
def _validate_object(
    self,
    object_schemas_by_name: Dict[str, PrintableOcsfObject],
    obj_data: Dict[str, Any],
    schema_obj: PrintableOcsfObject,
    report: ValidationReport,
    path: str = ""
):
    valid = True

    # Validate all keys in obj_data exist in schema
    for key in obj_data:
        full_key_path = f"{path}.{key}" if path else key
        if key not in schema_obj.attributes:
            report.append_entry(f"Field '{full_key_path}' not found in schema", logger.warning)
            valid = False
            continue

        attr = schema_obj.attributes[key]

        # Recursively validate nested objects
        if attr.is_object() and obj_data[key] is not None:
            obj_schema = object_schemas_by_name[attr.object_type]

            # Handle arrays of objects
            if attr.is_array:
                for i, item in enumerate(obj_data[key]):
                    if item is not None:
                        full_array_key_path = f"{full_key_path}[{i}]"
                        if not self._validate_object(object_schemas_by_name, item, obj_schema, report, full_array_key_path):
                            valid = False
            else:
                # Single nested object
                if not self._validate_object(object_schemas_by_name, obj_data[key], obj_schema, report, full_key_path):
                    valid = False

    # Check all required attributes are present
    for attr_name, attr in schema_obj.attributes.items():
        if attr.requirement == "Required" and attr_name not in obj_data:
            report.append_entry(f"Required field '{path + attr_name}' missing", logger.warning)
            valid = False

    return valid
```

**Source**: `backend/transformers/validators.py:89-154`

**Key Observations**:
1. **Path tracking**: Builds full path string for error reporting (e.g., "user.email", "events[2].src_ip")
2. **Recursive descent**: Calls itself for nested objects
3. **Array handling**: Iterates arrays with index tracking
4. **Two-way validation**: Checks data against schema AND schema against data
5. **Accumulates errors**: Doesn't stop at first error, reports ALL validation issues
6. **Boolean return**: Returns whether subtree is valid

**Validation Phases**:
- **Phase 1**: Validate all keys in data exist in schema
- **Phase 2**: Recursively validate nested objects
- **Phase 3**: Validate all required attributes are present

**Why this pattern**:
- Comprehensive validation finds ALL issues (not just first)
- Path tracking provides precise error locations
- Handles arbitrary nesting depth
- Validates both presence and absence (extra fields + missing required fields)

---

### 5.8 Transformer Assembly Pattern

**Pattern**: String concatenation to assemble composite function from templates.

```python
def create_transformer_python(transformer_id: str, patterns: List[ExtractionPattern]) -> Transformer:
    transformer_logic = ""

    # Add individual pattern functions
    for pattern in patterns:
        function_code = _get_pattern_function_code(pattern)
        transformer_logic += function_code

    # Add helper code
    helper_code = _get_helper_code()  # set_path(), _convert_to_json_if_possible()
    transformer_logic += helper_code

    # Add wrapper function that chains all patterns
    transformer_logic += _get_transformer_wrapper_code(patterns)

    return Transformer(
        id=transformer_id,
        dependency_setup=patterns[0].dependency_setup if patterns else "",
        transformer_logic=transformer_logic
    )
```

**Source**: `backend/transformers/transformers.py:85-104`

**Pattern Function Template** (`backend/transformers/transformers.py:31-46`):
```python
def _get_pattern_function_code(pattern: ExtractionPattern) -> str:
    # Indent extract and transform logic
    indented_extract_logic = "\n    ".join(pattern.extract_logic.splitlines())
    indented_transform_logic = "\n    ".join(pattern.transform_logic.splitlines())

    # Generate function code
    return f"""
def {_get_pattern_function_name(pattern)}(input_data: str) -> str:
    {indented_extract_logic}

    {indented_transform_logic}

    extracted_data = extract(input_data)
    transformed_data = transform(extracted_data)
    return transformed_data
"""
```

**Wrapper Template** (`backend/transformers/transformers.py:66-82`):
```python
def _get_transformer_wrapper_code(patterns: List[ExtractionPattern]) -> str:
    wrapper_code = "\n"
    wrapper_code += "def transformer(input_data: str) -> typing.Dict[str, typing.Any]:\n"
    wrapper_code += "    output = {}\n\n"

    for pattern in patterns:
        pattern_path = pattern.mapping.ocsf_path
        function_name = _get_pattern_function_name(pattern)
        wrapper_code += f"    {function_name}_result = {function_name}(input_data)\n"
        wrapper_code += f"    {function_name}_result = _convert_to_json_if_possible({function_name}_result)\n"
        wrapper_code += f"    set_path(output, '{pattern_path}', {function_name}_result)\n\n"

    wrapper_code += "    return output\n"
    return wrapper_code
```

**Key Observations**:
1. **Code generation from templates**: Uses f-strings to generate Python code
2. **Indentation management**: Adds proper indentation with splitlines() + join()
3. **Helper injection**: Injects helper functions (set_path, _convert_to_json_if_possible)
4. **Wrapper pattern**: Single transformer() function calls all pattern functions
5. **Path-based assembly**: Uses ocsf_path to determine where to set each value
6. **Type conversion**: Attempts JSON parsing before setting value

**Assembly Flow**:
```
ExtractionPattern(s)
  → Individual pattern functions (extract + transform)
  → Helper functions (set_path, JSON conversion)
  → Wrapper function (chains all patterns)
  → Single Transformer with complete logic
```

**Why this pattern**:
- Combines multiple LLM-generated patterns into single executable
- Maintains isolation between patterns (separate functions)
- Provides unified interface (single transformer() function)
- Enables validation of assembled code via exec() + ModuleType

**Observation**: This is "code generation via string concatenation" - simple but effective for structured code assembly.

---

## 6. Inference Orchestration

### 6.1 Async Batch Inference Pattern

**Pattern**: Wrap async inference in sync interface with batch support.

```python
def perform_inference(
    llm: Runnable[LanguageModelInput, BaseMessage],
    batched_tasks: List[InferenceRequest]
) -> List[InferenceResult]:
    return asyncio.run(_perform_async_inference(llm, batched_tasks))

async def _perform_async_inference(
    llm: Runnable[LanguageModelInput, BaseMessage],
    batched_tasks: List[InferenceRequest]
) -> List[InferenceResult]:
    async_responses = [llm.ainvoke(task.context) for task in batched_tasks]
    responses = await asyncio.gather(*async_responses)

    return [
        InferenceResult(task_id=task.task_id, response=response)
        for task, response in zip(batched_tasks, responses)
    ]
```

**Source**: `backend/core/inference.py:35-47`

**Key Observations**:
1. **Sync wrapper**: perform_inference() is synchronous (easier for callers)
2. **Async implementation**: _perform_async_inference() uses asyncio.gather()
3. **Batch-ready**: Accepts List[InferenceRequest], returns List[InferenceResult]
4. **Parallel execution**: asyncio.gather() runs all inference calls concurrently
5. **Current usage**: invoke_expert() only batches one task at a time (could scale to true batching)

**Comment in code** (`backend/core/inference.py:38-42`):
> Ideally, we'd be using Bedrock's batch inference API, but Bedrock's approach to that is an asynchronous process that writes the results to S3 and returns a URL to the results. This is not implemented by default in the ChatBedrockConverse class, so we'll skip true batch processing for now.

**Observation**: Architecture supports batch processing, but current implementation uses it for single-task inference with parallelization infrastructure in place for future scaling.

---

### 6.2 Expert Invocation Flow

**Pattern**: Multi-step orchestration with context updates.

```python
def invoke_expert(expert: Expert, task: PlaygroundTask) -> PlaygroundTask:
    logger.debug(f"Initial Task: {json.dumps(task.to_json(), indent=4)}")

    # 1. Convert task to inference request (wraps context)
    inference_task = task.to_inference_task()

    # 2. Perform inference (LLM call with context)
    inference_result = perform_inference(expert.llm, [inference_task])[0]
    logger.debug(f"Inference Result: {json.dumps(inference_result.to_json(), indent=4)}")

    # 3. Validate tool call
    if not isinstance(inference_result.response, AIMessage) or not inference_result.response.tool_calls:
        raise ExpertInvocationError("The LLM did not create a tool call...")

    # 4. Append LLM response to context
    task.context.append(inference_result.response)

    # 5. Execute tool with LLM arguments
    tool_call = inference_result.response.tool_calls[-1]
    result = expert.tools.task_tool(tool_call["args"])
    task.set_work_item(result)

    # 6. Append tool message to context
    task.context.append(
        ToolMessage(
            name=task.get_tool_name(),
            content="Executed the expert task",
            tool_call_id=tool_call["id"]
        )
    )

    logger.debug(f"Updated Task: {json.dumps(task.to_json(), indent=4)}")

    return task
```

**Source**: `backend/core/experts.py:37-74`

**Invocation Sequence**:
```
Task (with context)
  → InferenceRequest
  → LLM invocation
  → InferenceResult (with AIMessage)
  → Tool execution
  → Work item set
  → Context updated (AIMessage + ToolMessage)
  → Updated Task returned
```

**Key Observations**:
1. **Immutable inputs**: Expert and Task passed in, only Task is mutated
2. **Debug logging**: Logs task state at entry and exit
3. **Context mutation**: Task.context is appended to (not replaced)
4. **Fail-fast**: Raises exception immediately if no tool call
5. **Tool message**: Generic content ("Executed the expert task"), real result in work_item

---

### 6.3 InferenceRequest/InferenceResult Pattern

**Pattern**: Lightweight DTOs for request/response.

```python
@dataclass
class InferenceRequest:
    task_id: str
    context: List[BaseMessage]

    def to_json(self) -> dict:
        return {
            "task_id": self.task_id,
            "context": [turn.to_json() for turn in self.context]
        }

@dataclass
class InferenceResult:
    task_id: str
    response: BaseMessage  # AIMessage from LLM

    def to_json(self) -> dict:
        return {
            "task_id": self.task_id,
            "response": self.response.to_json()
        }
```

**Source**: `backend/core/inference.py:12-32`

**Why separate DTOs**:
- Decouples Task from inference layer
- InferenceRequest has minimal data (task_id + context)
- InferenceResult is generic (works for any task type)
- Serializable for logging/debugging

**Observation**: These are "thin" wrappers around LangChain messages, not domain-specific.

---

### 6.4 Factory Function Pattern for Experts

**Pattern**: Factory functions (get_*_expert()) instantiate Experts.

```python
def get_analysis_expert(ocsf_version: OcsfVersion, ocsf_event_name: str) -> Expert:
    logger.info(f"Building expert for: {ocsf_version}")

    tool_bundle = get_analyze_tool_bundle(ocsf_version)

    # Define Bedrock LLM and attach tools
    llm = ChatBedrockConverse(
        model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        temperature=1,  # Must be 1 for "thinking" mode
        max_tokens=30001,
        region_name="us-west-2",
        additional_model_request_fields={"thinking": {"type": "enabled", "budget_tokens": 30000}},
        config=DEFULT_BOTO_CONFIG
    )
    llm_w_tools = llm.bind_tools(tool_bundle.to_list())

    return Expert(
        llm=llm_w_tools,
        system_prompt_factory=get_analyze_system_prompt_factory(ocsf_version, ocsf_event_name),
        tools=tool_bundle
    )
```

**Source**: `backend/entities_expert/expert_def.py:16-44`

**Factory Responsibilities**:
1. Instantiate LLM client with configuration
2. Bind tools to LLM
3. Create prompt factory
4. Create tool bundle
5. Assemble Expert

**Why factory functions**:
- Centralize Expert creation logic
- Consistent naming: get_<expert_type>_expert()
- Easy to test (mock factory outputs)
- Clear initialization order (LLM → tools → bind → Expert)

**Observation**: Each "expert mode" has its own factory (get_analysis_expert, get_extraction_expert).

---

### 6.5 Invoke Wrapper Functions

**Pattern**: Type-specific invoke wrappers around generic invoke_expert().

```python
def invoke_analysis_expert(expert: Expert, task: AnalysisTask) -> AnalysisTask:
    logger.info(f"Invoking the Analysis Expert for task_id: {task.task_id}")
    invoke_expert(expert, task)
    logger.info(f"Analysis performed for task_id: {task.task_id}")
    return task
```

**Source**: `backend/entities_expert/expert_def.py:46-51`

**Why wrapper functions**:
- Type-specific signatures (AnalysisTask vs ExtractTask)
- Task-specific logging
- Centralizes task_id logging
- Provides extension point for task-specific logic (though not used here)

**Observation**: Currently these wrappers only add logging, but they provide a hook for future task-specific logic (e.g., metrics, retries, validation).

---

## 7. Configuration & Extensibility

### 7.1 Version-Based Dispatch Pattern

**Pattern**: Use enum for version, dispatch to version-specific implementations.

```python
from enum import Enum

class OcsfVersion(Enum):
    V1_1_0 = "1.1.0"

def get_ocsf_event_schema(ocsf_version: OcsfVersion, event_name: str, paths: List[str]) -> PrintableOcsfEvent:
    if ocsf_version == OcsfVersion.V1_1_0:
        return make_get_ocsf_event_schema(v1_1_0_schema)(event_name, paths)

    return None
```

**Source**: `backend/entities_expert/prompting/knowledge/__init__.py:19-23`

**Why this pattern**:
- Type-safe version selection (enum vs string)
- Easy to add new versions (add enum value + if branch)
- Centralized version logic (all version dispatch in knowledge module)
- Graceful degradation (returns None/empty for unsupported versions)

---

### 7.2 Extensibility via Factory Functions

**Pattern**: All creation logic in factory functions (not constructors).

**Factories observed**:
- `get_analyze_system_prompt_factory()` - Prompt generation
- `get_extract_system_prompt_factory()` - Prompt generation
- `get_analyze_tool_bundle()` - Tool selection
- `get_extract_tool_bundle()` - Tool selection
- `get_analysis_expert()` - Expert instantiation
- `get_extraction_expert()` - Expert instantiation

**Extensibility benefits**:
1. **Version-specific logic**: Factories can dispatch on version/type
2. **Configuration injection**: Factories encapsulate configuration decisions
3. **Testing**: Easy to provide mock factories
4. **Conditional creation**: Factories can choose what to create based on context

---

### 7.3 Module-Level Loggers

**Pattern**: Module-level logger created at import time.

```python
import logging

logger = logging.getLogger("backend")
```

**Source**: All modules

**Why this pattern**:
- Hierarchical logging (all backend modules under "backend" logger)
- Consistent logger naming
- Easy to configure at application level
- Logger is immutable (created once at import)

---

### 7.4 LLM Configuration Spectrum (Iteration 2)

**Pattern**: Different LLM configurations for different task complexities.

**Simple/Deterministic Tasks** (Regex, Categorization):
```python
# Regex Expert - Code generation
llm = ChatBedrockConverse(
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    temperature=0,  # Deterministic
    max_tokens=16000,
    additional_model_request_fields={"thinking": {"type": "disabled"}},
    config=DEFULT_BOTO_CONFIG
)
```

**Source**: `backend/regex_expert/expert_def.py:24-35`, `backend/categorization_expert/expert_def.py:23-34`

**Complex/Creative Tasks** (Entities Analysis):
```python
# Entities Expert - Analysis with extended thinking
llm = ChatBedrockConverse(
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    temperature=1,  # Creative
    max_tokens=30001,
    additional_model_request_fields={
        "thinking": {"type": "enabled", "budget_tokens": 30000}
    },
    config=DEFULT_BOTO_CONFIG
)
```

**Source**: `backend/entities_expert/expert_def.py:22-34`

**Configuration Decision Matrix**:

| Task Type | Temperature | Thinking | Max Tokens | Use Case |
|-----------|-------------|----------|------------|----------|
| Code Generation | 0 | Disabled | 16K | Regex, Python code |
| Classification | 0 | Disabled | 16K | Category selection |
| Analysis/Discovery | 1 | Enabled | 30K+ | Entity extraction, reasoning |
| Code Generation (Complex) | 0 | Disabled | 30K | Transformer assembly |

**Key Observations**:
- **Temperature 0**: Deterministic tasks where consistency matters (code, classification)
- **Temperature 1**: Creative tasks requiring exploration (entity discovery, analysis)
- **Extended thinking OFF**: When task is straightforward (select from list, generate simple regex)
- **Extended thinking ON**: When task requires complex reasoning (entity relationships, schema mapping)
- **Token budget**: Thinking budget ~= max_tokens suggests thinking is major cost

**Why this pattern**:
- Matches LLM configuration to task characteristics
- Reduces cost for simple tasks (no thinking overhead)
- Maximizes quality for complex tasks (full thinking budget)
- Consistent model (same Claude Sonnet) across all tasks

---

### 7.5 Knowledge Module Strategy Pattern (Iteration 2)

**Pattern**: Enum-based dispatch to flavor/version-specific knowledge modules.

**Regex Expert - Flavor Dispatch** (`backend/regex_expert/prompting/knowledge/__init__.py:6-15`):
```python
from backend.regex_expert.parameters import RegexFlavor
from backend.regex_expert.prompting.knowledge.javascript import REGEX_GUIDANCE, REGEX_KNOWLEDGE

def get_regex_guidance(regex_flavor: RegexFlavor) -> str:
    if regex_flavor == RegexFlavor.JAVASCRIPT:
        return javascript_guidance
    return ""

def get_regex_knowledge(regex_flavor: RegexFlavor) -> str:
    if regex_flavor == RegexFlavor.JAVASCRIPT:
        return javascript_knowledge
    return ""
```

**Categorization Expert - Version Dispatch** (`backend/categorization_expert/prompting/knowledge/__init__.py:6-15`):
```python
from backend.core.ocsf.ocsf_versions import OcsfVersion
from backend.categorization_expert.prompting.knowledge.ocsf_v1_1_0 import OCSF_GUIDANCE, OCSF_KNOWLEDGE

def get_ocsf_guidance(ocsf_version: OcsfVersion) -> str:
    if ocsf_version == OcsfVersion.V1_1_0:
        return v1_1_0_guidance
    return ""

def get_ocsf_knowledge(ocsf_version: OcsfVersion) -> str:
    if ocsf_version == OcsfVersion.V1_1_0:
        return v1_1_0_knowledge
    return ""
```

**Enum Definitions**:

**RegexFlavor** (`backend/regex_expert/parameters.py:7-13`):
```python
class RegexFlavor(Enum):
    JAVA = "Java"
    JAVASCRIPT = "JavaScript"
    PCRE = "PCRE"
    POSIX = "POSIX"
    PYTHON = "Python"
    RE2 = "RE2"
```

**OcsfVersion** (from core):
```python
class OcsfVersion(Enum):
    V1_1_0 = "1.1.0"
```

**Knowledge Module Structure**:
```
prompting/knowledge/
├── __init__.py          # Dispatch functions
├── javascript.py        # RegexFlavor.JAVASCRIPT knowledge
└── ocsf_v1_1_0.py       # OcsfVersion.V1_1_0 knowledge
```

**Key Observations**:
1. **Consistent pattern**: All experts use same dispatch structure
2. **Empty string fallback**: Unsupported versions return "" (graceful degradation)
3. **Module per variant**: Each flavor/version gets dedicated module
4. **Constants**: Knowledge exported as module-level constants (GUIDANCE, KNOWLEDGE)
5. **Separation**: Guidance (rules) vs Knowledge (data) kept separate

**Why this pattern**:
- Type-safe version/flavor selection (enum vs string)
- Easy to add new variants (add module + if branch)
- Centralized dispatch logic (all in __init__.py)
- Testable (mock knowledge modules)
- Scales to many versions/flavors without complexity

---

### 7.6 Tool Simplicity Spectrum (Iteration 2)

**Pattern**: Tool complexity matches output complexity.

**Simplest: Categorization (3 fields)** (`backend/categorization_expert/tool_def.py:20-24`):
```python
class SelectOcsfCategory(BaseModel):
    """Select an OCSF category for specific data entry."""
    name: str = Field(description="The full OCSF Category name and NOTHING ELSE.")
    id: str = Field(description="The OCSF Category id and NOTHING ELSE.")
    rationale: str = Field(description="A thorough explanation of why...")
```

**Simple: Regex (2 fields)** (`backend/regex_expert/tool_def.py:26-29`):
```python
class MakeJavascriptRegex(BaseModel):
    """Makes a standard ECMAScript regex."""
    value: str = Field(description="The string value of the regular expression...")
    rationale: str = Field(description="A thorough explanation of how the regex works...")
```

**Complex: Entities (20+ fields across nested structures)** (`backend/entities_expert/tool_def.py:22-60`):
```python
class EntityInput(BaseModel):
    value: str = Field(...)
    description: str = Field(...)

class EntityMappingInput(BaseModel):
    entities: List[EntityInput] = Field(...)
    ocsf_path: str = Field(...)
    path_rationale: str = Field(...)

class CreateEntitiesReport(BaseModel):
    """Create a list of mappings for entities..."""
    data_type: str = Field(...)
    type_rationale: str = Field(...)
    mappings: List[EntityMappingInput] = Field(...)
```

**Complexity Spectrum**:

| Expert | Tool Fields | Nested Structures | Output Complexity |
|--------|-------------|-------------------|-------------------|
| Categorization | 3 | None | Simple (name + id) |
| Regex | 2 | None | Simple (string) |
| Entities | 20+ | 3 levels deep | Complex (nested lists) |

**Key Observations**:
1. **Field count varies 10x**: 2-3 fields for simple tasks, 20+ for complex
2. **Nesting matches complexity**: Simple tasks have flat schemas, complex tasks have nested schemas
3. **rationale always present**: Even simplest tools require explanation
4. **Consistent pattern**: Pydantic BaseModel + Field descriptions

**Why this pattern**:
- Simpler tools reduce LLM token usage and error rates
- Complex tools enable rich structured output
- Rationale field provides transparency across all tasks
- Field descriptions guide LLM without increasing schema complexity

**Observation**: Tool complexity is NOT driven by framework constraints - it's an intentional design choice matching task needs.

---

## Summary: Key Architectural Patterns

### Core Patterns Identified (Iteration 1)

1. **Expert-Task-Tool Trinity**: Three-abstraction composition pattern
2. **Tool-Forcing**: Bind tools to LLM to guarantee structured output
3. **System Prompt Factories**: Late-binding prompt generation with closures
4. **Message Context Management**: Explicit conversation history with LangChain messages
5. **Async Batch Infrastructure**: Async inference wrapped in sync interface
6. **Dataclass-Heavy Architecture**: Type-safe domain modeling with serialization
7. **Version-Based Dispatch**: Enum + if-elif for version-specific logic
8. **Factory Functions**: Centralized creation logic for Experts, Tools, Prompts
9. **ValidationReport Accumulation**: Dual logging + structured validation reports

### Additional Patterns Identified (Iteration 2)

10. **Multi-Stage Validation**: Progressive refinement (syntax → loading → invocation → output)
11. **Dynamic Python Code Loading**: ModuleType + exec() for LLM-generated code execution
12. **Custom Exception Hierarchy**: Domain-specific exceptions for precise error semantics
13. **Recursive Schema Validation**: Path-tracked validation for nested object structures
14. **Transformer Assembly**: String concatenation to build composite functions from templates
15. **LLM Configuration Spectrum**: Task-specific temperature/thinking/token settings
16. **Knowledge Module Strategy**: Enum-based dispatch to version/flavor-specific knowledge
17. **Tool Simplicity Spectrum**: Tool complexity matches task complexity (2-20+ fields)

### Confidence Levels

- **HIGH**: Expert-Task-Tool trinity, Tool-forcing, Message context, Dataclass patterns, Multi-stage validation, Dynamic code loading, Recursive validation
- **MEDIUM**: Prompt factory pattern, Async batch (not fully utilized yet), Transformer assembly (domain-specific)
- **OBSERVED**: Version dispatch (only one version implemented so far), LLM configuration spectrum (consistent across 3 experts)

### Pattern Categories

**Architectural Abstractions**:
- Expert-Task-Tool Trinity
- Dataclass-Heavy Architecture
- Composition Over Inheritance

**LangChain Integration**:
- Tool-Forcing Pattern
- Message Context Management
- Async Batch Infrastructure

**Prompt Engineering**:
- System Prompt Factories
- Knowledge Module Strategy
- Dynamic Context Injection

**Tool Management**:
- Tool Simplicity Spectrum
- Factory Pattern for Tools
- Pydantic Field Descriptions

**Validation & Error Handling**:
- Multi-Stage Validation
- Dynamic Python Code Loading
- Custom Exception Hierarchy
- Recursive Schema Validation
- ValidationReport Accumulation

**Code Generation**:
- Transformer Assembly Pattern
- Template-Based Code Generation

**Configuration**:
- LLM Configuration Spectrum
- Version-Based Dispatch
- Factory Functions

---

**Status**: Analysis complete. All 33 LangChain-relevant files analyzed across 2 iterations (1,749 lines of code).
