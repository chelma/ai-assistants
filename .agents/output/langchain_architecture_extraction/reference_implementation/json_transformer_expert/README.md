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

## Key Patterns Demonstrated

### 1. Tool-Forcing Pattern
Both experts use `bind_tools()` to guarantee structured output. The LLM must produce a tool call matching the Pydantic schema.

### 2. Factory Pattern
Expert creation is centralized in factory functions (`get_mapping_expert()`, `get_transform_expert()`), making configuration changes easy.

### 3. Progressive Detail Loading
Transform phase prompt includes FILTERED schema (only mapped paths), reducing token count and focusing LLM. See `prompting/generation.py:51-59`.

### 4. Multi-Stage Validation
Validation proceeds through stages: syntax → loading → invocation → output. Each stage has specific exception types. See `validators.py:71-139`.

### 5. LLM Configuration Spectrum
- **Mapping**: temp=1, thinking enabled (creative analysis) - see `expert_def.py:56-74`
- **Transform**: temp=0, thinking disabled (deterministic code generation) - see `expert_def.py:114-126`

## Adapting for Your Use Case

1. **Replace domain models** (`models.py`): Define your work items
2. **Update task definitions** (`task_def.py`): Match your workflow
3. **Define tool schemas** (`tool_def.py`): Specify your structured output
4. **Write prompt templates** (`prompting/templates.py`): Customize for your domain
5. **Configure LLM** (`expert_def.py`): Replace TODOs with your provider setup
6. **Add validation** (`validators.py`): Implement domain-specific checks

See `../../langchain_guide.md` for complete walkthrough of building your first expert.
