# Plan: Python Coding Style Analysis

**Status**: complete
**GitHub Issue**: N/A
**Created**: 2025-10-29
**Completed**: 2025-10-30

## Problem Statement

There is currently no systematic way to capture and transfer Chris's Python coding style and engineering philosophy to Claude for future sessions. Each new Claude session starts without knowledge of specific preferences, patterns, and approaches that define Chris's engineering identity. This leads to:
- Code suggestions that don't match established patterns
- Time spent correcting style and approach mismatches
- Inconsistent code quality across Claude-assisted work
- Lost opportunity to leverage personal coding conventions

## Acceptance Criteria

- ✅ **Phase 1 Complete**: Reconnaissance of both repositories with file inventory and iteration plan
- ✅ **Phase 2 Complete**: All prioritized files analyzed across 12 categories
- ✅ **Guidelines Comprehensive**: Document covers all 12 analysis categories with specific patterns
- ✅ **Guidelines Actionable**: Patterns include file references, code examples, and priority levels
- ✅ **Output Format**: Final style guide at `/Users/chris.helma/workspace/personal/ai-assistants/python_style.md`
- ✅ **Phase 3 Complete**: Chris-approved polished guide ready for production use
- ✅ **Engineering Fingerprint Captured**: Guidelines successfully represent Chris's coding philosophy and can inform future Claude sessions

---

## Current State Analysis

### Repositories to Analyze
1. **ocsf-playground** (`/Users/chris.helma/workspace/personal/ocsf-playground`)
   - Purpose: [To be determined during exploration]
   - Language: Python

2. **aws-aio** (`/Users/chris.helma/workspace/personal/aws-aio`)
   - Purpose: [To be determined during exploration]
   - Language: Python

### Analysis Framework

The following categories will be systematically examined across both repositories:

#### 1. Code Organization & Architecture
- Project structure patterns (src/, lib/, module organization)
- How concerns are separated (layers, domains, utilities)
- Package/module naming conventions
- File naming patterns
- Directory hierarchy philosophy

#### 2. Type System & Annotations
- Type hints usage patterns (comprehensive, selective, none?)
- Custom types and type aliases
- Use of typing module constructs (Optional, Union, Protocol, TypeVar, etc.)
- Runtime type checking approaches
- Generic types and variance

#### 3. Documentation Philosophy
- Docstring style (Google, NumPy, reStructuredText, custom?)
- What gets documented (all public APIs, selective, internal details)
- Comment style and when they're used
- README and high-level documentation approach
- Inline documentation patterns

#### 4. Error Handling & Robustness
- Exception hierarchy and custom exceptions
- Error handling patterns (EAFP vs LBYL)
- Logging approaches and log levels
- Input validation strategies
- Defensive programming patterns

#### 5. Testing Approach
- Test framework preferences (pytest, unittest, etc.)
- Test organization and naming conventions
- Coverage philosophy and standards
- Fixture and mock patterns
- Test data management
- Integration vs unit test balance

#### 6. Code Style & Idioms
- Naming conventions (variables, functions, classes, constants, modules)
- Line length and formatting preferences
- Import organization and grouping (stdlib, third-party, local)
- Use of comprehensions vs loops
- Functional vs OOP tendencies
- Lambda usage patterns
- Context manager preferences

#### 7. Dependencies & Tooling
- Dependency management approach (pip, poetry, pipenv)
- Use of standard library vs third-party libraries
- Dev tool choices (linters, formatters, type checkers)
- Configuration file preferences (pyproject.toml, setup.py, etc.)

#### 8. Design Patterns & Principles
- Common patterns used (factory, builder, dependency injection, singleton, etc.)
- Abstraction levels and interface design
- Composition vs inheritance preferences
- How configuration and settings are handled
- Plugin/extensibility patterns
- Separation of concerns strategies

#### 9. Data Handling
- Data structure choices (dict, class, dataclass, etc.)
- Serialization approaches (JSON, YAML, pickle, etc.)
- Data validation patterns
- Use of dataclasses, NamedTuples, Pydantic, attrs, etc.
- Immutability preferences

#### 10. Async & Concurrency
- Async/await usage patterns
- Threading/multiprocessing approaches
- How async code is structured
- Synchronization primitives usage
- Async library preferences

#### 11. API Design
- Public vs private API boundaries (naming, documentation)
- Interface consistency patterns
- Parameter patterns (args, kwargs, explicit params)
- Return value conventions
- Method chaining preferences
- Builder patterns

#### 12. Meta Patterns
- How versioning and compatibility are handled
- Deprecation strategies
- Code evolution patterns (refactoring style)
- Performance optimization tendencies
- Security consciousness patterns

## Proposed Solution

### Overview
A three-phase approach that balances context efficiency with comprehensive analysis:
1. **Reconnaissance**: Survey both repositories to create file inventory and iteration plan
2. **Iterative Analysis**: Incrementally read files, extract patterns, and build style guide
3. **Human-Led Refinement**: Polish and finalize the guide with Chris's input

### Phase 1: Reconnaissance
**Goal**: Survey the landscape and create an analysis plan

**Approach**:
- Launch Explore agents in parallel (one per repository)
- Agents use "medium" thoroughness for efficient reconnaissance
- Focus on structure, file inventory, and identifying representative files

**Agent Deliverables (per repo)**:
1. Repository overview (purpose, domain, tech stack)
2. File inventory with estimated line counts/sizes
3. Structural observations (directory patterns, entry points)
4. Recommended focus areas (most representative files)

**Claude Actions After Reconnaissance**:
1. Create implementation tracking document with:
   - Complete file inventory from both repos
   - File prioritization (core → supporting → tests/config)
   - Iteration plan grouping files into batches
2. Present iteration plan to Chris for approval

**Context Management**: Reconnaissance reports will be summarized if needed to preserve context.

### Phase 2: Iterative Analysis
**Goal**: Extract patterns and incrementally build the style guide

**Iteration Size Heuristic**:
- Target: 2,000-4,000 lines of Python per iteration (~8k-16k tokens)
- File count: 10-20 files depending on average file size
  - Files < 200 lines: take up to 20 files
  - Files 200-400 lines: take 10-15 files
  - Files > 400 lines: take 8-12 files

**Per Iteration Workflow**:
1. **Read** next batch of files (based on iteration plan)
2. **Analyze** files against 12-category framework:
   - Code Organization & Architecture
   - Type System & Annotations
   - Documentation Philosophy
   - Error Handling & Robustness
   - Testing Approach
   - Code Style & Idioms
   - Dependencies & Tooling
   - Design Patterns & Principles
   - Data Handling
   - Async & Concurrency
   - API Design
   - Meta Patterns
3. **Extract/Refine** patterns observed in this batch
4. **Write/Edit** `/Users/chris.helma/workspace/personal/ai-assistants/python_style.md`:
   - Add new patterns discovered
   - Refine existing patterns with additional evidence
   - Include file references and code snippets for traceability
   - Track confidence levels (high/medium/low based on consistency)
5. **Update** implementation tracking doc:
   - Mark files as analyzed (checkboxes)
   - Note current focus areas
   - Identify next batch
6. **Sync with Chris**: Present findings and refinements from this iteration
7. **Incorporate feedback** before proceeding to next iteration

**Iteration continues until**: All prioritized files have been analyzed

**Key Principles**:
- `python_style.md` is a **living document** that evolves with each iteration
- Insights are written **immediately** to the output file (not stored in implementation doc)
- Implementation doc is **lean**: just progress tracking and file lists
- Each iteration ends with human review before proceeding

**Context Resilience Strategy**:
- `python_style.md` includes file references and code snippets for each pattern
- If context compaction needed: re-read implementation doc + python_style.md to resume
- All insights are persisted in output file, safe across context disruptions

### Phase 3: Human-Led Refinement
**Goal**: Polish the style guide to production quality

**Approach**:
1. Chris reviews `python_style.md` end-to-end
2. Collaborative refinement session:
   - Correct patterns that aren't quite right
   - Add missing nuance or context
   - Reorganize for clarity and usability
   - Adjust tone and actionability
   - Remove or consolidate redundant sections
3. Claude edits `python_style.md` based on feedback
4. Final version ready for deployment

**Output**: Polished `/Users/chris.helma/workspace/personal/ai-assistants/python_style.md` ready to inform future Claude sessions

## Implementation Steps

### Phase 1: Reconnaissance
1. **Launch Explore agents** - Run parallel agents for both repositories (ocsf-playground, aws-aio)
2. **Review reconnaissance reports** - Assess file inventory, structure, and recommendations
3. **Create implementation tracking doc** - Build file inventory with prioritization and iteration plan
4. **Approve iteration plan** - Review and finalize iteration batches with Chris

### Phase 2: Iterative Analysis
5. **Iteration 1**: Read first batch of files (10-20 files, ~2k-4k lines)
   - Analyze against 12-category framework
   - Write initial patterns to `python_style.md`
   - Update implementation doc progress
   - Review findings with Chris
6. **Iteration 2**: Read second batch of files
   - Extract new patterns
   - Refine existing patterns in `python_style.md`
   - Update progress tracking
   - Review findings with Chris
7. **Iteration N**: Continue iterating until all prioritized files analyzed
   - Each iteration: read → analyze → write/edit → track → review
   - Adapt batch sizes based on context usage
   - Flag surprising patterns immediately

### Phase 3: Human-Led Refinement
8. **Comprehensive review** - Chris reviews complete `python_style.md`
9. **Refinement session** - Collaborative editing and polishing
10. **Finalize** - Complete production-ready style guide at `/Users/chris.helma/workspace/personal/ai-assistants/python_style.md`

## Risks and Considerations

### Context Management Risks
- **Risk**: Phase 2 might require 4-6+ iterations, potentially spanning multiple sessions
  - *Mitigation*: Implementation doc + python_style.md provide durable state; can resume across sessions

- **Risk**: Context window exhaustion before completing all files
  - *Mitigation*: Target 2k-4k lines per iteration; use /compact if needed; all insights in persistent files

- **Risk**: Post-compact performance degradation
  - *Mitigation*: python_style.md includes file references and code snippets; implementation doc tracks progress

### Analysis Quality Risks
- **Risk**: Patterns might be inconsistent across repos (different eras of development)
  - *Mitigation*: Track confidence levels; document pattern evolution; discuss inconsistencies with Chris

- **Risk**: Some patterns might be project-specific rather than general preference
  - *Mitigation*: Look for patterns in both repos; note domain-specific vs general preferences

- **Risk**: Missing context for why certain choices were made
  - *Mitigation*: Flag ambiguous patterns immediately; ask Chris during iteration reviews

- **Risk**: Small sample size (early iterations) might lead to incorrect pattern conclusions
  - *Mitigation*: Mark patterns with confidence levels; refine as more files are analyzed

### Usability Risks
- **Risk**: Guidelines might be too prescriptive and inhibit creative problem-solving
  - *Mitigation*: Frame as preferences and principles, not rigid rules

- **Risk**: Guidelines might become stale as Chris's style evolves
  - *Mitigation*: Include "Last updated" metadata; document as living guide

- **Risk**: python_style.md might become disorganized as it evolves iteratively
  - *Mitigation*: Maintain consistent structure; Phase 3 includes reorganization pass

## Testing Strategy

### During Phase 2: Iterative Validation
- **After each iteration**: Chris reviews patterns extracted that iteration
- **Confidence tracking**: Patterns marked as high/medium/low confidence based on consistency
- **Immediate feedback**: Surprising or ambiguous patterns flagged for discussion
- **Pattern evolution**: Early patterns refined as more evidence accumulates

### Phase 3: Comprehensive Validation
1. **Accuracy Review**: Chris confirms patterns accurately reflect intent and philosophy
2. **Completeness Check**: All 12 categories adequately covered
3. **Actionability Test**: Guidelines are specific enough to guide Claude's decisions
4. **Organization Review**: Structure supports easy reference during coding sessions

### Success Metrics
- ✓ Chris approves guidelines as accurate representation of engineering identity
- ✓ Guidelines cover the 12 analysis categories comprehensively
- ✓ Patterns include file references and code examples for traceability
- ✓ Guidelines are actionable (not generic best practices)
- ✓ Document is organized for efficient reference by future Claude sessions

### Post-Deployment
- Collect feedback from actual Claude usage in Python projects
- Update guidelines as Chris's style evolves
- Maintain "Last updated" metadata to track currency

## Notes

- This is a meta-task: using Claude to teach future Claude instances
- Quality over speed: thorough analysis is more valuable than quick completion
- This creates reusable value: guidelines will improve all future Python work with Claude
- Consider this a living document that can evolve as Chris's preferences evolve
