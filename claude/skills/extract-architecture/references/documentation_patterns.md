# Documentation Patterns for Architecture Extraction

## Overview

When extracting architecture from a codebase, the deliverables should match the extraction goals and target audience. This document provides guidance on common output structures and when to use each pattern.

**Key Principle**: Architecture extraction outputs should be **AI-consumable** first, human-readable second. The primary audience is future Claude (or other AI coding assistant) instances that will use the documentation to implement similar patterns.

## Common Output Structures

### Pattern Catalog

**Structure:**
```
patterns.md or architecture_patterns.md
- Pattern categories (organized by architectural layer, concern, or domain)
- Each pattern includes:
  - Name and purpose
  - Implementation examples with file references + line numbers
  - When to use / when not to use
  - Trade-offs and alternatives
  - Related patterns
```

**When to use:**
- Codebase contains multiple distinct patterns worth documenting separately
- Patterns can be understood independently (loosely coupled)
- Goal is comprehensive coverage of architectural decisions
- Audience needs reference material for specific patterns

**Example from LangChain extraction:**
- 17 patterns across 7 categories
- Each pattern documented with file references (e.g., `backend/core/experts.py:40-51`)
- Categories: Core Abstractions, LLM Configuration, Prompting, Validation, etc.

**Token considerations:**
- Pattern catalogs can be large (500-1000+ lines)
- Best placed in `references/` directory for on-demand loading
- Main guide should point to catalog, not duplicate it

### Prescriptive Guide

**Structure:**
```
guide.md or <domain>_guide.md
- Quick Start: "Copy these files, follow this structure"
- Core Concepts: Explain foundational abstractions with "why"
- Step-by-step workflow: "Building Your First X"
- Key Design Decisions: Configuration choices, trade-offs
- Advanced Patterns: Multi-phase workflows, composition strategies
- Resources: Point to reference implementation, pattern catalog
```

**When to use:**
- Goal is to enable someone to **build** similar architecture
- Clear "getting started" path is essential
- Workflow can be broken into discrete steps
- Design decisions need explanation and context

**Example from LangChain extraction:**
- `langchain_guide.md` with 7-step "Building Your First Expert" workflow
- Quick Start: "Copy core/, review example, build your expert"
- Design Decisions: Tool-forcing, LLM config spectrum, progressive detail, validation
- Advanced Patterns: Multi-turn conversations, expert chaining

**Token considerations:**
- Guides should be lean (350-500 lines for SKILL.md, 400-650 for standalone)
- Use file references instead of inline code examples
- Progressive disclosure: main workflow in guide, details in references

### Reference Implementation

**Structure:**
```
reference_implementation/ or examples/
├── core/ or foundation/          # Generic, reusable abstractions
│   ├── README.md                 # Overview of core components
│   └── *.py or *.ts or *.java    # Implementation files
└── example_<domain>/             # Complete example demonstrating patterns
    ├── README.md                 # Purpose, structure, key patterns
    └── *.py or *.ts or *.java    # Domain-specific implementation
```

**When to use:**
- Patterns are best understood through working code
- Core abstractions are reusable across projects
- Example demonstrates multiple patterns in combination
- Code can be copy-pasted as starting point

**Example from LangChain extraction:**
- `core/` - Domain-agnostic abstractions (Expert, Task, Tool, Inference, ValidationReport)
- `json_transformer_expert/` - Complete example (mapping → transform workflow)
- All files have enhanced docstrings with "PATTERN DEMONSTRATED" sections

**Token considerations:**
- Reference implementations are typically NOT loaded into context
- Stored in `assets/` directory (for copying to user's project)
- Self-documenting code via comprehensive docstrings
- READMEs should be minimal (structure tree + key patterns)

### Hybrid: Guide + Reference Implementation

**Structure:**
```
guide.md                          # Prescriptive workflow pointing to code
reference_implementation/         # Copy-paste ready code
  ├── core/                       # Reusable abstractions
  └── example_domain/             # Instructive example
patterns.md (optional)            # Detailed pattern catalog in references/
```

**When to use:**
- Architecture is complex enough to need both explanation and code
- Patterns are best understood through concrete examples
- Goal is to enable rapid implementation with guidance
- Extraction resulted in reusable abstractions

**Example from LangChain extraction:**
- Combined all three: `langchain_guide.md` + `reference_implementation/` + `langchain_patterns.md`
- Guide points to reference implementation via file references
- Pattern catalog provides deep-dive for specific patterns
- Reference implementation is self-teaching via docstrings

**Token considerations:**
- Guide uses file references: `See reference_implementation/core/experts.py:40-51`
- No code duplication between guide and implementation
- Pattern catalog in `references/` for on-demand loading

## Structuring Your Output

### Step 1: Identify Extraction Goals

Ask these questions to determine output structure:

1. **What should someone be able to do after reading this?**
   - Understand architectural decisions → Pattern Catalog
   - Build similar system → Prescriptive Guide
   - Copy-paste starting code → Reference Implementation
   - All of the above → Hybrid approach

2. **How complex is the architecture?**
   - Single pattern/abstraction → Guide with inline examples
   - Multiple independent patterns → Pattern Catalog
   - Interconnected patterns → Guide + Reference Implementation

3. **What's the reusability potential?**
   - Project-specific patterns → Pattern Catalog only
   - Reusable abstractions → Reference Implementation required
   - Framework/library → Full hybrid approach

### Step 2: Choose Primary Deliverable

**For understanding-focused extractions:**
- Primary: Pattern Catalog
- Secondary: Guide (optional, if workflow exists)

**For implementation-focused extractions:**
- Primary: Prescriptive Guide
- Secondary: Reference Implementation (if code is reusable)

**For framework/library extractions:**
- Primary: Hybrid (Guide + Reference Implementation)
- Secondary: Pattern Catalog in references/

### Step 3: Structure Supporting Deliverables

**If creating Pattern Catalog:**
- Organize patterns by concern, layer, or category
- Include file references with line numbers
- Document when to use each pattern
- Include trade-offs and alternatives
- Place in `references/` if large (500+ lines)

**If creating Prescriptive Guide:**
- Start with Quick Start (minimal path to first success)
- Explain core concepts with "why" rationale
- Provide step-by-step workflow
- Document key design decisions
- Point to reference implementation or pattern catalog
- Keep lean via file references (not inline code)

**If creating Reference Implementation:**
- Separate reusable (core/) from example (example_domain/)
- Make code self-documenting via enhanced docstrings
- Include minimal READMEs (structure + key patterns)
- Ensure domain-agnostic abstractions (no project-specific imports)
- Place in `assets/` directory

## Token Optimization Strategies

### 1. File References Over Inline Code

**Instead of:**
```markdown
Here's how to define a Task:

\`\`\`python
class MappingTask(Task):
    def __init__(self, task_id: str, source_json: str):
        self.task_id = task_id
        self.source_json = source_json
        self.mapping_report: Optional[MappingReport] = None

    def get_work_item(self) -> Optional[MappingReport]:
        return self.mapping_report
\`\`\`
```

**Use:**
```markdown
See `reference_implementation/json_transformer_expert/task_def.py:18-51` for MappingTask example.
```

**Savings**: ~15-20 lines per example → ~300 lines in a typical guide

### 2. Enhanced Docstrings

**Instead of:**
Documenting patterns in guide AND providing code examples

**Use:**
Self-documenting code with comprehensive module/class docstrings:

```python
"""
PATTERN DEMONSTRATED: Multi-phase task workflow

This module shows how to create task classes for multi-phase expert workflows.
The JSON Transformer uses two tasks: MappingTask (analysis) and TransformTask (code gen).

KEY CONCEPTS:
- Each task has domain-specific input fields (source_json, target_schema)
- Work item field holds structured result (mapping_report, transform_code)
- Tasks are stateful: start with work_item=None, populate via invoke_expert()

WHEN TO USE THIS PATTERN:
- Multi-phase workflows where later phases depend on earlier results
- Progressive detail loading (phase 2 uses phase 1 results to filter context)
- Contrasting LLM configs (creative analysis → deterministic generation)
"""
```

**Savings**: Code teaches itself, guide just points to it

### 3. Progressive Disclosure

**Main document (SKILL.md or guide.md):**
- Quick Start workflow
- Core concepts (high-level)
- Step-by-step building process
- Key design decisions
- Resources section

**References directory:**
- Detailed pattern catalog
- Implementation deep-dives
- Decision matrices
- Case studies

**Assets directory:**
- Reference implementation (not loaded to context)
- Templates
- Examples

**Savings**: Main document stays under 500 lines, detailed info loaded on-demand

### 4. Single Source of Truth

**Anti-pattern:**
- Pattern described in guide
- Same pattern in pattern catalog
- Code example in reference implementation README
- Inline example in guide

**Better:**
- Pattern in catalog (detailed)
- Guide references catalog: "See patterns.md#tool-forcing-pattern"
- Reference implementation demonstrates pattern
- Guide references implementation: "See core/experts.py:40-51"

**Savings**: Eliminates 20-30% duplication

## Output Directory Structure

### Standard Structure (within .agents/)

```
.agents/
├── tasks/
│   ├── <task_name>_plan.md           # Created by tag-team skill
│   └── <task_name>_progress.md       # Created during extraction
└── output/
    └── <task_name>/                   # Extraction deliverables
        ├── patterns.md or guide.md    # Main documentation
        ├── reference_implementation/  # Code (if applicable)
        │   ├── core/
        │   └── example_domain/
        └── README.md                  # Overview of deliverables
```

### For Skill Conversion (future step)

If converting to Claude Skill later:

```
<skill_name>/
├── SKILL.md                           # Adapted from guide.md
├── references/
│   └── patterns.md                    # Pattern catalog (on-demand)
└── assets/
    └── reference_implementation/      # Copy-paste ready code
```

## Decision Matrix

| Extraction Goal | Primary Deliverable | Secondary | Token Strategy |
|----------------|-------------------|-----------|---------------|
| Understand architectural decisions | Pattern Catalog | Guide (optional) | Patterns in references/, guide if workflow exists |
| Build similar system | Prescriptive Guide | Reference Impl | File references, enhanced docstrings |
| Copy-paste starting code | Reference Impl | Guide | Self-documenting code, minimal READMEs |
| Create reusable framework | Guide + Reference Impl | Pattern Catalog | Hybrid: guide points to code, patterns in references/ |
| Document for future Claude | Pattern Catalog + Progress File | Reference Impl | Comprehensive progress tracking, resumable context |

## Best Practices

### For AI Consumption

1. **Use imperative/infinitive form** (not second person)
   - "Define task classes with domain-specific fields"
   - NOT "You should define task classes with domain-specific fields"

2. **Include file references with line numbers**
   - `See core/experts.py:40-51 for Expert dataclass definition`
   - Enables Claude to quickly locate and read relevant code

3. **Document "why" and "when"**
   - Why pattern exists (rationale, trade-offs)
   - When to use (applicability, anti-patterns)
   - Enables informed decision-making

4. **Provide decision guidance**
   - Temperature 0 vs 1 decision matrix
   - Multi-tool vs separate experts trade-offs
   - Progressive detail loading applicability

5. **Mark uncertainty explicitly**
   - "<!-- NEEDS REVIEW: This pattern may not be optimal for X use case -->"
   - Flags areas needing human expert input

### For Resumability

Progress files should enable resuming extraction at any phase:

1. **Status tracking**: Checkmarks for completed phases
2. **Process documentation**: What was done in each phase
3. **Key decisions**: Why approaches were chosen over alternatives
4. **Deliverables tracking**: What was created, where it lives
5. **Deviations/Blockers/Gotchas**: Problems encountered and solutions
6. **File inventory**: Complete list of analyzed files with line counts
7. **Iteration plan**: Batching strategy with specific file groupings
8. **Lessons learned**: Insights for future work or iteration

### For Skill Conversion

If architecture guide will become a Claude Skill:

1. **Token optimization from start**: Use file references, not inline code
2. **Progressive disclosure structure**: Lean main document, detailed references/
3. **Self-documenting code**: Enhanced docstrings in reference implementation
4. **Imperative form**: Write as instructions, not explanations
5. **Comprehensive YAML description**: Include trigger conditions for discoverability

## Examples

### Pattern Catalog Example (from LangChain extraction)

```markdown
## Tool-Forcing Pattern

**Purpose**: Bind tools to LLM to force structured output instead of prose responses.

**Implementation**: See `backend/core/experts.py:59-117` for invoke_expert() implementation.

**When to use**:
- Need guaranteed structured output format
- Want automatic validation via Pydantic schemas
- Building task-specific experts (not general conversation)

**When NOT to use**:
- Free-form responses required
- Conversational agents
- Exploratory use cases where structure isn't known upfront

**Trade-offs**:
- ✅ Eliminates parsing ambiguity
- ✅ Automatic type validation
- ✅ Clear success signal (tool call = task complete)
- ❌ Every invocation must produce tool call (no "I don't know" responses)
- ❌ Tool schema changes require client updates

**Related patterns**: Progressive Detail Loading, Multi-Stage Validation
```

### Prescriptive Guide Example (from LangChain extraction)

```markdown
## Building Your First Expert

### Step 1: Define Domain Models

Create dataclasses for work items (e.g., FieldMapping, MappingReport, TransformCode).

**See**: `reference_implementation/json_transformer_expert/models.py`

**Key patterns**:
- All domain models are dataclasses with type hints
- Every model has to_json() method for serialization
- Keep models simple: pure data containers, no business logic
```

### Reference Implementation README Example

```markdown
# JSON Transformer Expert

Complete reference implementation demonstrating two-phase expert workflow.

## Structure

\`\`\`
json_transformer_expert/
├── models.py              # Domain dataclasses (FieldMapping, MappingReport, TransformCode)
├── task_def.py            # MappingTask and TransformTask implementations
├── tool_def.py            # Pydantic schemas + StructuredTools
├── expert_def.py          # Expert factories (get_mapping_expert, get_transform_expert)
├── validators.py          # Multi-stage validation with custom exceptions
└── prompting/
    ├── templates.py       # Prompt templates for both phases
    └── generation.py      # Prompt factories with progressive detail loading
\`\`\`

## Key Patterns Demonstrated

- **Two-phase workflow**: Mapping (analysis, temp=1) → Transform (code gen, temp=0)
- **Progressive detail loading**: Full schema phase 1, filtered schema phase 2 (70% token reduction)
- **Multi-stage validation**: Syntax → loading → invocation → output validation
- **Contrasting LLM configs**: Creative vs deterministic configuration spectrum
```

## Conclusion

Choose output structure based on extraction goals, codebase complexity, and reusability potential. Optimize for AI consumption via file references, enhanced docstrings, and progressive disclosure. Document process comprehensively in progress file for resumability.
