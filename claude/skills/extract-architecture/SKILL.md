---
name: extract-architecture
description: Extract architectural patterns and design decisions from existing codebases to create AI-consumable reference guides. Use this skill when tasked with documenting architecture, creating pattern catalogs, building reference implementations, or producing prescriptive guides for AI coding assistants. Builds on tag-team for progress tracking and composes with codebase-researcher for large-scale investigations. Outputs work with Claude and other AI assistants.
---

# Extract Architecture

## Overview

Extract architectural patterns, design decisions, and reusable abstractions from existing codebases to create comprehensive, AI-consumable reference guides.

**When to use this skill:**
- Documenting architecture from an existing codebase for AI assistant consumption
- Creating pattern catalogs for specific architectural approaches (e.g., multi-expert LLM systems, microservices, Temporal workflows)
- Building reference implementations from proven production code
- Producing prescriptive "how to build" guides for replicating architectural patterns
- Extracting reusable abstractions for framework/library development

**Key characteristics:**
- **Builds on tag-team**: Leverages checkpoint pattern (DO WORK → DOCUMENT → PAUSE → CONTINUE) for collaborative extraction
- **Composes with codebase-researcher**: Delegates large-scale investigation when needed (>3k lines)
- **Flexible deliverables**: Pattern catalog, prescriptive guide, reference implementation, or hybrid approaches
- **AI consumption optimized**: File references, imperative form, progressive disclosure, priority classifications
- **Resumable by design**: Comprehensive progress tracking enables multi-session work

---

## Core Workflow

Follow this checkpoint-driven workflow. Tag-team provides the rhythm, extract-architecture provides extraction-specific guidance.

### Phase 1: Plan with Tag-Team

**Invoke tag-team skill** to establish extraction as formal task with plan and progress tracking.

**Task name format**: `<issue-id>-<description>` or `<YYYY-MM-DD>-<description>`
- Example: `2025-11-01-extract-temporal-workflow-pattern`

**Plan essentials:**
- **Problem statement**: "Extract [specific patterns/architecture] from [repository] to create AI-consumable reference guide"
- **Acceptance criteria**: Reconnaissance complete, patterns extracted with priorities, deliverables created, process documented
- **Implementation approach**: "Will follow extraction workflow with 3-8 phases (reconnaissance → analysis → refinement)"

Tag-team handles workspace detection, project root tracking, and creates plan in `~/.claude/workspace/<workspace>/tasks/<task_name>_plan.md`.

After plan created, proceed to Phase 2.

---

### Phase 2: Reconnaissance & Iteration Planning

**Goal**: Understand codebase structure, create file inventory, plan iteration batches.

#### 2.1 Launch Explore Agent

Use `Task` tool with `subagent_type=Explore` (thoroughness: "very thorough") to survey repository and identify files related to target architecture/patterns.

#### 2.2 Create File Inventory

Document in progress file under "Reconnaissance Summary" section (see `assets/progress_template_additions.md`):

- **Repository Statistics**: Total files, lines of code, key technologies, architecture style
- **Architecture Overview**: 2-3 paragraph summary of what's being extracted
- **Complete File Inventory**: Organize by layer/domain/concern with line counts and checkboxes
  - Example: `#### Layer 1: Core Abstractions (5 files, 202 lines)`
  - Add checkboxes: `- [ ] backend/core/experts.py (74 lines) - Expert dataclass`

#### 2.3 Plan Iterations

Group files into batches (~1500 lines each) using vertical slices (complete subsystems) to preserve architectural context.

For each iteration, document:
- **Title/Focus**: What this iteration aims to understand
- **Files to analyze**: Specific files with line counts
- **Key patterns to extract**: Expected pattern categories
- **Rationale**: Why these files are grouped together

See `references/extraction_workflow_detailed.md` for iteration planning examples.

#### 2.4 Choose Investigation Approach

Calculate total lines from file inventory:

- **≤3,000 lines**: Direct reading (main session reads files, documents patterns)
- **>3,000 lines**: Delegated investigation (codebase-researcher per iteration, main session synthesizes)
- **Uncertain**: Start direct, switch to delegation if context strained

**Why 3k threshold?** Roughly 2 iterations at ~1500 lines each - early enough to pivot, late enough to validate patterns.

**Key insight**: For large extractions, delegating to codebase-researcher and synthesizing from findings may improve architectural insight by forcing progressive abstraction.

#### 2.5 Present Plan for Approval (CHECKPOINT)

Explain to user:
- Total iterations planned
- Analysis approach (direct vs delegated)
- Files per iteration with grouping rationale
- Expected deliverables

**Wait for user approval before proceeding.**

---

### Phase 3: Iterative Analysis

**Goal**: Extract patterns incrementally by analyzing files in planned batches.

#### For Direct Reading (≤3,000 lines)

**For each iteration:**

1. **Read files** using Read tool (complete files, preserve architectural context)
2. **Document patterns** in `~/.claude/workspace/<workspace>/output/<task_name>/patterns.md`:
   - Use format: Purpose → Implementation (file refs) → When to use → Trade-offs
   - Use paths **relative to project root**: `backend/core/experts.py:40-51`
   - Add priority tags: `[PRIORITY: CRITICAL]`, `[PRIORITY: PREFERRED]`, or `[PRIORITY: OBSERVED]`
3. **Update progress file immediately** after iteration (not batched) - prevents context strain
4. **Mark files analyzed** (✅) in file inventory

**Pattern priority classifications:**
- **CRITICAL**: Core abstractions, cross-cutting patterns, define the architecture
- **PREFERRED**: Stylistic improvements, recommended practices
- **OBSERVED**: Implementation details, domain-specific choices

See `references/extraction_workflow_detailed.md` for pattern documentation format and examples.

#### For Delegated Investigation (>3,000 lines)

**For each iteration:**

1. **Invoke codebase-researcher** with iteration-specific objective (files to analyze, patterns to extract, context)
2. **Review findings** from `~/.claude/workspace/<workspace>/research/<timestamp>-iteration-N/`
3. **Synthesize into patterns.md** (integrate new patterns, cross-reference, note evolution)
4. **Update progress file** (mark iteration complete)

Main session never loads source code - only curated findings. Benefits: clean context, preserved investigations, forced abstraction.

See `references/extraction_workflow_detailed.md` for delegation workflow details.

#### Continue Until All Iterations Complete

Actual iterations may differ from plan (document deviations in progress file under "Evolution and Adaptations").

#### Human Priority Review (CHECKPOINT)

After all iterations complete, pause for human alignment on pattern priorities:

1. **Present pattern breakdown** (CRITICAL/PREFERRED/OBSERVED counts)
2. **Human reviews and adjusts** priority tags based on extraction goals
3. **Document priority breakdown** in progress file

**Why essential**: Extraction goals emerge during analysis. Priority review helps discover what's architecturally significant and prevents wasted effort on non-essential patterns in later phases.

**Expected time**: 15-30 minutes for ~15-25 patterns

---

### Phase 4: Critical Review & Deliverable Scoping

**Goal**: Assess patterns extracted, determine deliverables needed, choose output format.

#### 4.1 Review Pattern Documentation

Ask these questions:
- Is output **descriptive** ("what exists") or **prescriptive** ("how to build")?
- Can someone use this to implement similar architecture?
- Are reusable abstractions clearly identified?
- What is the distribution of CRITICAL vs PREFERRED vs OBSERVED patterns?

#### 4.2 Determine Deliverables

Based on validated priorities from Phase 3, decide what to create:

**Pattern Catalog only** (loosely coupled patterns, descriptive focus):
- Already created in Phase 3
- Optional: Quick reference guide

**Prescriptive Guide** (architecture should be replicated):
- "How to build" narrative with CRITICAL patterns
- Step-by-step workflow
- Design decisions with rationale
- Secondary: Reference implementation if code reusable

**Guide + Reference Implementation** (creating framework/library):
- Prescriptive guide with file references
- Domain-agnostic `core/` + instructive `example_domain/`
- Self-documenting code (enhanced docstrings)
- Pattern catalog in `references/` for deep dives

See `references/documentation_patterns.md` for detailed deliverable patterns.

#### 4.3 Choose Output Format (CHECKPOINT)

**CRITICAL**: This prevents deliverable rework. Format choice affects directory structure and documentation format.

Present options to user:

```
[1] Shared Reference (AI-agnostic format in .agents/)
    - Works with any AI coding assistant
    - Can be converted to Claude Skill later
    - Checked into git for team sharing

[2] Claude Skill (Claude Code-specific format)
    - Immediately usable in Claude Code
    - Lives in ~/.claude/skills/ or .claude/skills/

Which would you prefer? [1/2]
```

**Document choice in progress file** before proceeding to Phase 5.

---

### Phase 5: Refinement

**Goal**: Transform descriptive findings into prescriptive guidance and/or reference implementation.

**Priority-driven approach**: Focus on CRITICAL patterns (deep coverage), light coverage of key PREFERRED patterns, OBSERVED patterns stay in references/.

#### 5.1 Create Prescriptive Guide (if applicable)

**Structure**:
- Quick Start: "Copy these files, follow this structure"
- Core Concepts: Foundational abstractions with "why"
- Step-by-step workflow: "Building Your First X" (7-10 steps)
- Key Design Decisions: Configuration choices, trade-offs, rationale
- Advanced Patterns: Multi-phase workflows, composition
- Resources: Point to reference implementation, pattern catalog

**Writing guidelines**:
- Use imperative/infinitive form (not second person)
- Use **file references** instead of inline code: `See path/to/file.py:line-range`
- Include "why" and "when" for all design decisions
- Document anti-patterns and trade-offs

**Mark ambiguities** for Phase 5 checkpoint:
- `[TODO: WHY?]` where design rationale unclear (focus on CRITICAL decisions)
- `[TODO: PRINCIPLE?]` where guiding philosophy should be explained
- Claude cannot infer: production experience, historical context, trade-off reasoning

#### 5.2 Create Reference Implementation (if applicable)

**Focus on CRITICAL patterns**: Demonstrate all CRITICAL patterns plus select key PREFERRED patterns.

**Extract reusable abstractions** (`reference_implementation/core/`):
- Copy reusable files from original codebase
- Make domain-agnostic (remove project-specific imports, rename domain classes)
- Enhance docstrings with pattern explanations ("PATTERN DEMONSTRATED", "KEY CONCEPTS", "WHEN TO USE")

**Create instructive example** (`reference_implementation/example_<domain>/`):
- Minimal but complete example demonstrating CRITICAL patterns
- Token-efficient: TODO comments instead of full implementation
- Self-documenting: Pattern annotations in docstrings
- Minimal README: structure tree + key patterns (no usage examples)

**Mark ambiguities**: `# TODO: Why this approach?` for unclear rationale (focus on CRITICAL decisions)

#### 5.3 Human Collaboration - Design Rationale (CHECKPOINT)

Gather human insight on design rationale Claude cannot infer from code alone.

**Why essential**: Claude observes patterns but cannot infer why approaches were chosen, what production experience motivated decisions, what trade-offs were considered, or what guiding principles inform the architecture.

**Process:**

1. **Present marked deliverables** (guide/implementation with TODO markers from steps 5.1-5.2)
2. **Human provides context** for each marker:
   - Design rationale (why X over Y)
   - Trade-offs (what was gained/sacrificed)
   - Guiding principles
   - Production experience
   - When to deviate
3. **Incorporate feedback** (replace TODOs, add design principles sections, enhance guidance)
4. **Verify completeness** (brief check with human)

**Expected**: 10-15 focused questions on CRITICAL patterns, 30-45 minutes, single session.

**Impact**: Transforms "here's what the code does" to "here's why it's built this way and when you should replicate it."

#### 5.4 Token Optimization

Eliminate duplication and optimize for AI consumption:

- **Apply file references**: Replace inline code examples with `See path/to/file.py:line-range`
- **Enhance docstrings**: Make reference implementation self-teaching
- **Trim READMEs**: Keep minimal (structure tree + key patterns, remove usage examples)
- **Progressive disclosure**: Lean main documents (350-500 lines), detailed info in references/

**Outcome**: 25-30% token reduction while improving clarity.

See `references/extraction_workflow_detailed.md` for token optimization strategies.

---

### Phase 6: Finalize & Deliver

**Goal**: Document process learnings, format deliverables per Phase 4 choice, present to user.

#### 6.1 Process Documentation

Add "Phase Completion Summary" sections to progress file for major phases:

- **Deliverables Created**: List with locations, key features
- **Process Documentation**: What worked well, key decisions, process pattern for reuse
- **Artifacts for Future Extractions**: Reusable patterns, key principles, tool usage notes
- **Lessons Learned**: What worked better/harder than expected, process improvements

#### 6.2 Format & Deliver Based on Phase 4 Choice

**If Shared Reference** (Phase 4 choice):
- Check for `.agents/FORMAT.md` (read if exists, offer to generate if missing)
- Transform extraction output to match format specification
- Organize into `.agents/<reference-name>/`
- Inform user of location

**If Claude Skill** (Phase 4 choice):
- Invoke skill-creator skill
- Let skill-creator handle workflow (metadata, SKILL.md generation, organization)
- Skill created and ready to use

See `references/extraction_workflow_detailed.md` for detailed format/delivery workflows.

#### 6.3 Final Review

Present to user:
- All deliverables created (catalog, guide, implementation, progress)
- Output directory structure
- Key insights (core patterns, reusable abstractions, design principles)
- Suggested next steps (review, testing, conversion, distribution)

---

## Key Principles

### 1. Composition Over Duplication
- **Tag-team provides**: Plan/progress structure, checkpoint rhythm, workspace detection, portable file references
- **Extract-architecture provides**: Extraction phases, priority framework, human collaboration gates, deliverable patterns
- **Codebase-researcher provides** (if delegated): Iteration-level investigation, context health management, separate findings

### 2. Checkpoint Pattern (from tag-team)
- **DO WORK**: Each phase/iteration represents substantial work unit
- **DOCUMENT**: Update progress file immediately after each phase/iteration (not batched)
- **PAUSE FOR REVIEW**: 4 collaboration checkpoints (iteration approval, priority review, format choice, design rationale)
- **CONTINUE**: Clear progression via phase checklist and outcomes

### 3. Priority-Driven Refinement
- **CRITICAL patterns**: Core abstractions, deep coverage in deliverables, human rationale essential
- **PREFERRED patterns**: Stylistic improvements, light coverage or references
- **OBSERVED patterns**: Implementation details, stay in references/ for on-demand loading

### 4. Progressive Disclosure
- **Main documents**: Lean (350-500 lines for guides), imperative form, file references
- **References directory**: Detailed patterns, implementation deep-dives, decision matrices
- **Assets directory**: Reference implementation (not loaded to context), templates, examples

### 5. Token Efficiency
- Use **file references** instead of inline code: `See path/to/file.py:line-range`
- Enhance **docstrings** to make code self-teaching
- **Single source of truth**: Implementation is authoritative, guide points to it
- **No duplication**: Between guide, implementation READMEs, and pattern catalog

### 6. AI Consumption Focus
- **Imperative/infinitive form** (not second person): "Define task classes" not "You should define"
- **File references with line numbers**: `See core/experts.py:40-51 for Expert dataclass`
- **Document "why" and "when"**: Rationale, trade-offs, applicability, anti-patterns
- **Decision guidance**: Not just descriptions, but when to use each approach
- **Mark uncertainty**: `[TODO: WHY?]` flags areas needing human expertise

### 7. Resumability by Design
- **Progress file as state document**: 90% self-contained, enables multi-session work
- **Incremental updates**: After each iteration/phase immediately (prevents context strain)
- **Outcome documentation**: Not just checkboxes, but what was accomplished and why
- **Process capture**: Learnings documented as discovered, not at end

### 8. Organic Phase Emergence
- Plan provides direction (3-8 phases typical)
- Additional phases may emerge from human reviews (quality-driven, not scope creep)
- Document evolution in "Evolution and Adaptations" section (positive framing)
- Natural stopping point when deliverables meet acceptance criteria

---

## Resources

### Main References

**references/extraction_workflow_detailed.md** - Load when you need detailed step-by-step guidance:
- Detailed instructions for each phase
- Decision trees (direct vs delegated, catalog vs guide)
- Pattern documentation format and examples
- Human collaboration question examples
- Delegation workflow specifics
- Common patterns and anti-patterns

**references/documentation_patterns.md** - Load when determining deliverable structure:
- Common output structures (catalog, guide, implementation, hybrid)
- When to use each structure
- Token optimization strategies
- Decision matrix for choosing deliverables
- Best practices for AI consumption
- Examples of each pattern

**references/langchain_case_study.md** - Load for complete extraction example:
- 8-phase workflow from reconnaissance to skill packaging
- Process decisions and rationale
- What worked well and lessons learned
- Detailed phase-by-phase documentation
- Shows organic phase emergence

### Templates

**assets/progress_template_additions.md** - Architecture extraction-specific progress file sections:
- Reconnaissance Summary structure
- Iteration Plan format
- Phase Progress Tracking
- Phase Completion Summary templates
- Integration with tag-team progress template

---

## Integration with Tag-Team

Extract-architecture builds directly on tag-team's checkpoint pattern:

**Tag-team provides**:
- Plan and progress file structure
- Workspace detection and project root tracking
- Core checkpoint rhythm (DO WORK → DOCUMENT → PAUSE → CONTINUE)
- Resumability framework
- Template flexibility for task-specific adaptations

**Extract-architecture adds**:
- Extraction-specific phases (reconnaissance, iterative analysis, refinement)
- Priority classification framework (CRITICAL/PREFERRED/OBSERVED)
- Human collaboration gates at strategic decision points
- Deliverable patterns (catalog vs guide vs implementation)
- Investigation approach decision criteria (direct vs delegated)
- Token optimization for AI consumption

**Result**: Structured extraction workflow with flexible, resumable execution that composes cleanly with tag-team and codebase-researcher.

---

## Common Pitfalls

**Loading entire codebase at once**
- Solution: Use Explore agent for survey, then ~1500 line iteration batches

**Creating descriptive catalog when prescriptive guide needed**
- Solution: Phase 4 critical review assesses if output matches goals

**Inline code duplication**
- Solution: Phase 5 token optimization replaces inline code with file references

**Domain-specific abstractions in "core" code**
- Solution: Ensure core abstractions generic, domain-specific code in examples

**Batching progress file updates**
- Solution: Update immediately after EACH phase/iteration completion

**Skipping rationale documentation**
- Solution: Mark ambiguities with TODO, gather human context in Phase 5 checkpoint

**Analysis without iteration plan**
- Solution: Complete Phase 2 reconnaissance fully before starting analysis

**Choosing format too late**
- Solution: Phase 4 format choice checkpoint before creating deliverables (prevents rework)
