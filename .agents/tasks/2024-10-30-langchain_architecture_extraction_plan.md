# Plan: LangChain Architecture Extraction

**Status**: draft
**GitHub Issue**: N/A
**Created**: 2025-10-30

## Problem Statement

Currently, there's no systematic way to capture and transfer Chris's LangChain architectural patterns (Expert/Task/Tool abstractions, prompt engineering, validation strategies) to future Claude sessions working on LLM inference tasks. This leads to reinventing patterns and inconsistent architecture across LLM-powered projects.

## Acceptance Criteria

- [ ] **Comprehensive pattern extraction**: Document covers all core LangChain architecture patterns (Expert, Task, Tool abstractions, prompt engineering, validation)
- [ ] **Pattern examples**: Each pattern includes file references and code examples from ocsf-playground
- [ ] **Actionable guidance**: Guidelines are specific enough to guide future LangChain implementations
- [ ] **Portable patterns**: Focus on LLM/inference patterns independent of application framework (Django, Temporal, etc.)
- [ ] **Output format**: Final guide at `/Users/chris.helma/workspace/personal/ai-assistants/.agents/output/langchain_architecture_extraction/langchain_patterns.md`
- [ ] **Chris-approved**: Guidelines successfully represent Chris's LangChain architecture philosophy

---

## Current State Analysis

### Repository to Analyze
**ocsf-playground** (`/Users/chris.helma/workspace/personal/ocsf-playground`)
- Purpose: Django backend API that receives requests and performs LLM inference using AWS Bedrock via LangChain
- Domain: OCSF (Open Cybersecurity Schema Framework) analysis and transformation

### Key Architecture Components (from GitHub issue notes)

The codebase implements a sophisticated abstraction layer for LLM inference tasks:

1. **Expert System** - LLM API clients with configuration and tool bundles
   - Abstract base: `backend/core/experts.py`
   - Concrete implementations: `backend/entities_expert/expert_def.py`, `backend/regex_expert/expert_def.py`, `backend/categorization_expert/expert_def.py`

2. **Task System** - Domain-specific inference task definitions
   - Abstract base: `backend/core/tasks.py`
   - Concrete implementations: `backend/entities_expert/task_def.py`, `backend/regex_expert/task_def.py`, `backend/categorization_expert/task_def.py`

3. **Tool System** - LangChain tool bundles for each Expert
   - Tool definitions: `backend/entities_expert/tool_def.py`, `backend/regex_expert/tool_def.py`, `backend/categorization_expert/tool_def.py`

4. **Prompt Engineering System** - Template-based prompt generation with context injection
   - Prompt generators: `backend/entities_expert/prompting/generation.py`
   - Prompt templates: `backend/entities_expert/prompting/templates.py`, `backend/regex_expert/prompting/templates.py`, `backend/categorization_expert/prompting/templates.py`

5. **Validation System** - LLM output validation
   - Validators: `backend/entities_expert/validators.py`, `backend/transformers/validators.py`

6. **Inference Orchestration** - High-level coordination
   - Client setup: `backend/core/inference.py`
   - API entrypoint: `playground_api/views.py` (line ~303)

### Analysis Framework

The following categories will be systematically examined:

#### 1. Abstraction Architecture
- Expert base class design and lifecycle
- Task base class design and lifecycle
- Tool definition patterns
- How abstractions compose together
- Interface contracts and protocols

#### 2. LangChain Integration
- How LangChain clients are instantiated and configured
- Which LangChain components are used (agents, chains, tools, etc.)
- LangChain version and API patterns
- Custom extensions or wrappers around LangChain

#### 3. Prompt Engineering
- Template structure and organization
- Context injection strategies
- System vs user message patterns
- Knowledge embedding approaches
- Prompt versioning or variants

#### 4. Tool Management
- How tools are defined (Pydantic models, decorators, etc.)
- Tool bundling and registration strategies
- Tool parameter validation
- Tool execution patterns

#### 5. Validation & Error Handling
- Output validation strategies
- Validation report patterns
- Error handling for LLM failures
- Retry logic and fallbacks

#### 6. Inference Orchestration
- How Experts execute Tasks
- Request/response flow
- State management during inference
- Result transformation patterns

#### 7. Configuration & Extensibility
- How new Experts/Tasks/Tools are added
- Configuration management for inference
- Extensibility patterns

## Proposed Solution

### Overview
A three-phase approach modeled after the successful Python coding style analysis:

1. **Reconnaissance**: Survey the ocsf-playground repository to understand the full LangChain architecture
2. **Iterative Analysis**: Extract patterns incrementally and build the architecture guide
3. **Human-Led Refinement**: Polish and finalize the guide with Chris's input

### Phase 1: Reconnaissance
**Goal**: Survey the codebase and create an analysis plan

**Approach**:
- Launch Explore agent with "medium" thoroughness
- Focus on the 7 analysis categories above
- Identify all Expert/Task/Tool implementations
- Map out the architecture hierarchy and relationships

**Agent Deliverables**:
1. Repository overview and architectural summary
2. Complete inventory of Expert, Task, and Tool implementations
3. Key architectural decisions and patterns observed
4. Recommended focus areas for deep analysis

**Claude Actions After Reconnaissance**:
1. Create implementation tracking document with:
   - Complete file inventory organized by pattern type
   - File prioritization (core abstractions → concrete implementations → utilities)
   - Iteration plan grouping files into logical analysis batches
2. Present iteration plan to Chris for approval

### Phase 2: Iterative Analysis
**Goal**: Extract patterns and incrementally build the architecture guide

**Iteration Strategy**:
- Group files by architectural layer (abstractions → implementations → utilities)
- Analyze 8-12 files per iteration (focusing on related components together)
- Extract patterns across the 7 analysis categories

**Per Iteration Workflow**:
1. **Read** next batch of files (based on iteration plan)
2. **Analyze** files against the 7-category framework
3. **Extract/Refine** architectural patterns observed
4. **Write/Edit** `/Users/chris.helma/workspace/personal/ai-assistants/.agents/output/langchain_architecture_extraction/langchain_patterns.md`:
   - Add new patterns discovered
   - Refine existing patterns with additional evidence
   - Include file references and code snippets
   - Track confidence levels (high/medium/low)
5. **Update** implementation tracking doc:
   - Mark files as analyzed
   - Note current focus areas
   - Identify next batch
6. **Sync with Chris**: Present findings from this iteration
7. **Incorporate feedback** before proceeding

**Key Principles**:
- `langchain_patterns.md` is a **living document** that evolves with each iteration
- Insights are written **immediately** to the output file
- Implementation doc is **lean**: just progress tracking and file lists
- Each iteration ends with human review before proceeding
- Focus on **portable patterns** independent of Django/web framework

### Phase 3: Human-Led Refinement
**Goal**: Polish the architecture guide to production quality

**Approach**:
1. Chris reviews `langchain_patterns.md` end-to-end
2. Collaborative refinement session:
   - Correct patterns that aren't quite right
   - Add missing nuance or context
   - Reorganize for clarity and usability
   - Adjust tone and actionability
   - Add priority levels (CRITICAL/PREFERRED/OBSERVED)
3. Claude edits `langchain_patterns.md` based on feedback
4. Final version ready for deployment

**Output**: Polished architecture guide ready to inform future Claude sessions on LangChain projects

## Implementation Steps

### Phase 1: Reconnaissance
1. **Launch Explore agent** - Survey ocsf-playground repository for LangChain architecture
2. **Review reconnaissance report** - Assess architectural patterns, file inventory, and recommendations
3. **Create implementation tracking doc** - Build file inventory with prioritization and iteration plan
4. **Approve iteration plan** - Review and finalize iteration batches with Chris

### Phase 2: Iterative Analysis
5. **Iteration 1**: Analyze core abstractions (Expert, Task, Tool base classes)
   - Analyze against 7-category framework
   - Write initial patterns to `langchain_patterns.md`
   - Update implementation doc progress
   - Review findings with Chris

6. **Iteration 2**: Analyze concrete Expert implementations
   - Extract implementation patterns
   - Refine abstract patterns in `langchain_patterns.md`
   - Update progress tracking
   - Review findings with Chris

7. **Iteration 3**: Analyze Task and Tool implementations
   - Extract task/tool patterns
   - Refine patterns in `langchain_patterns.md`
   - Update progress tracking
   - Review findings with Chris

8. **Iteration 4**: Analyze prompt engineering system
   - Extract prompt template and generation patterns
   - Refine patterns in `langchain_patterns.md`
   - Update progress tracking
   - Review findings with Chris

9. **Iteration 5**: Analyze validation and orchestration
   - Extract validation and inference flow patterns
   - Complete `langchain_patterns.md`
   - Update progress tracking
   - Review findings with Chris

10. **Iteration N**: Continue as needed until all key patterns extracted
    - Adapt batch sizes based on context and complexity
    - Flag surprising patterns immediately

### Phase 3: Human-Led Refinement
11. **Comprehensive review** - Chris reviews complete `langchain_patterns.md`
12. **Refinement session** - Collaborative editing and polishing
13. **Add priority levels** - Mark patterns as CRITICAL/PREFERRED/OBSERVED
14. **Finalize** - Complete production-ready architecture guide

## Risks and Considerations

### Analysis Quality Risks
- **Risk**: Patterns might be specific to OCSF domain rather than general LangChain architecture
  - *Mitigation*: Distinguish domain-specific logic from general architectural patterns; focus on abstraction structure

- **Risk**: Missing context for why certain architectural choices were made
  - *Mitigation*: Flag ambiguous patterns immediately; ask Chris during iteration reviews

- **Risk**: LangChain version-specific patterns that might not apply to newer versions
  - *Mitigation*: Document LangChain version used; note which patterns are version-dependent

- **Risk**: Over-abstracting from a single codebase (ocsf-playground is only example)
  - *Mitigation*: Frame as "observed patterns" rather than rigid rules; Chris can adjust during Phase 3

### Context Management Risks
- **Risk**: Phase 2 might require 4-6+ iterations, potentially spanning multiple sessions
  - *Mitigation*: Implementation doc + langchain_patterns.md provide durable state; can resume across sessions

- **Risk**: Context window exhaustion during analysis
  - *Mitigation*: Target 8-12 files per iteration; all insights in persistent files

### Usability Risks
- **Risk**: Guidelines might be too prescriptive and inhibit creative problem-solving
  - *Mitigation*: Frame as patterns and principles, not rigid rules; include "When to Deviate" section

- **Risk**: Guidelines might become stale as Chris's architecture evolves or LangChain changes
  - *Mitigation*: Include "Last updated" metadata; document as living guide

- **Risk**: Patterns might be too coupled to AWS Bedrock and not generalize to other LLM providers
  - *Mitigation*: Identify provider-specific vs provider-agnostic patterns

## Testing Strategy

### During Phase 2: Iterative Validation
- **After each iteration**: Chris reviews patterns extracted that iteration
- **Confidence tracking**: Patterns marked as high/medium/low confidence based on consistency
- **Immediate feedback**: Surprising or ambiguous patterns flagged for discussion
- **Pattern evolution**: Early patterns refined as more evidence accumulates

### Phase 3: Comprehensive Validation
1. **Accuracy Review**: Chris confirms patterns accurately reflect intent and philosophy
2. **Completeness Check**: All 7 analysis categories adequately covered
3. **Actionability Test**: Guidelines are specific enough to guide Claude's architectural decisions
4. **Portability Test**: Patterns are independent of Django/web framework specifics
5. **Organization Review**: Structure supports easy reference during LangChain projects

### Success Metrics
- ✓ Chris approves guidelines as accurate representation of LangChain architecture philosophy
- ✓ Guidelines cover the 7 analysis categories comprehensively
- ✓ Patterns include file references and code examples for traceability
- ✓ Guidelines are actionable (not generic LangChain best practices)
- ✓ Patterns are portable across different application contexts
- ✓ Document is organized for efficient reference by future Claude sessions

### Post-Deployment
- Collect feedback from actual Claude usage in LangChain projects
- Update guidelines as Chris's architecture evolves or LangChain changes
- Maintain "Last updated" metadata to track currency

## Notes

- This is a meta-task: using Claude to teach future Claude instances about LangChain architecture
- Quality over speed: thorough analysis is more valuable than quick completion
- Focus on **architectural patterns**, not Django integration specifics
- This creates reusable value: guidelines will improve all future LangChain work with Claude
- Consider this a living document that can evolve as Chris's patterns evolve
