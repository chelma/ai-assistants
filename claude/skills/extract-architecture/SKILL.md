---
name: extract-architecture
description: Extract architectural patterns and design decisions from existing codebases to create AI-consumable reference guides. Use this skill when tasked with documenting architecture, creating pattern catalogs, building reference implementations, or producing prescriptive guides for AI coding assistants. Outputs are designed for Claude and other AI assistants to reference when implementing similar patterns. This skill builds on task-planning for comprehensive progress tracking and supports optional conversion to Claude Skills.
---

# Extract Architecture

## Overview

Extract architectural patterns, design decisions, and reusable abstractions from existing codebases to create comprehensive, AI-consumable reference guides. This skill provides a structured workflow for reconnaissance, iterative analysis, and refinement that produces pattern catalogs, prescriptive guides, and/or reference implementations.

**When to use this skill:**
- Documenting architecture from an existing codebase for AI assistant consumption
- Creating pattern catalogs for specific architectural approaches (e.g., multi-expert LLM systems, microservices)
- Building reference implementations from proven production code
- Producing prescriptive "how to build" guides for replicating architectural patterns
- Extracting reusable abstractions for framework/library development

**Key characteristics:**
- Builds on task-planning skill for comprehensive progress tracking
- Produces flexible deliverables based on extraction goals (patterns catalog, guide, reference implementation)
- Optimizes for AI consumption (file references, imperative form, progressive disclosure)
- Supports resumability via detailed progress documentation
- Optional skill conversion for distribution

## Workflow

### Step 1: Invoke task-planning Skill

Begin by invoking the task-planning skill to establish the extraction as a formal task with plan and progress tracking.

**Task name format**: `<issue-id>-<description>` or `<YYYY-MM-DD>-<description>`
- Example: `GH-456-extract_langchain_patterns` or `2025-11-01-document_microservices_architecture`

**Plan creation:**
- **Problem statement**: "Extract [specific patterns/architecture] from [repository/codebase] to create AI-consumable reference guide"
- **Acceptance criteria**:
  - Complete reconnaissance with file inventory
  - Pattern extraction via iterative analysis
  - Deliverables created (specify: pattern catalog / guide / reference implementation)
  - Progress file documents process for resumability
- **Implementation approach**: Will follow 3-8 phase workflow (reconnaissance → analysis → refinement → optional phases)

After task-planning creates the plan file, proceed to Step 2.

### Step 2: Reconnaissance Phase

Explore the codebase to understand structure, identify relevant files, and create comprehensive file inventory.

**2.1 Launch Explore Agent**

Use Task tool with subagent_type=Explore to survey the repository:
- Specify scope (entire repo or specific directories)
- Thoroughness level: "very thorough" for comprehensive coverage
- Focus: Identify files related to target architecture/patterns

**2.2 Review Reconnaissance Report**

Analyze Explore agent findings:
- Repository structure and organization
- Technology stack and key dependencies
- Architectural style and core components
- Initial pattern observations

**2.3 Create File Inventory**

Document in progress file under "Reconnaissance Summary" section (see `assets/progress_template_additions.md`):

**Repository Statistics:**
- Total files related to extraction target
- Total lines of code
- Key technologies and versions
- Architecture style

**Architecture Overview:**
- 2-3 paragraph summary of what's being extracted
- Core components and their roles
- Initial pattern observations

**Complete File Inventory:**
- Organize by architectural layer, domain, or concern
- Include line counts for each file
- Add checkmarks (✅/[ ]) to track analysis progress
- Group files into logical categories (e.g., "Core Abstractions", "Implementations", "Supporting Infrastructure")

**Example organization:**

```
#### Layer 1: Core Abstractions (5 files, 202 lines)
- [ ] backend/core/experts.py (74 lines) - Expert dataclass
- [ ] backend/core/tasks.py (36 lines) - Task abstraction
...

#### Layer 2: Implementations (10 files, 599 lines)
**Entities Expert** (5 files, 341 lines)
- [ ] backend/entities_expert/expert_def.py (87 lines)
...
```

**2.4 File Prioritization**

Determine analysis order based on:
- **Foundation-first**: Core abstractions → implementations → utilities
- **Vertical slices**: Complete subsystems (all files for one feature/expert)
- **Complexity-first**: Most complex examples first (establishes patterns), then simpler examples
- **Domain separation**: Reusable vs domain-specific code

**2.5 Create Iteration Plan**

Plan file batches for analysis (see "Iteration Plan" section in progress template):

**Target**: ~1500 lines per iteration (adjust for complexity)
**Strategy**: Group by vertical slices (complete subsystems) to preserve architectural context
**Estimated iterations**: Calculate based on total lines / 1500

For each iteration, document:
- **Title/Focus**: What this iteration aims to understand
- **Files to analyze**: Specific files with line counts
- **Key patterns to extract**: Expected pattern categories
- **Rationale**: Why these files are grouped together

**Example iteration:**

```
### Iteration 1: Core Abstractions + Complete Example (~800 lines, 13 files)
**Focus**: Foundational abstractions + most sophisticated implementation

**Files to analyze**:
- backend/core/experts.py (74 lines)
- backend/entities_expert/expert_def.py (87 lines)
...

**Key Patterns to Extract**:
- Core abstractions (Expert, Task, Tool)
- Factory pattern for expert creation
- Multi-phase workflow patterns

**Rationale**: Understand foundation before studying specific use cases
```

**2.6 Present Plan for Approval**

Explain iteration strategy to user:
- Total iterations planned
- Files per iteration and grouping rationale
- Estimated timeline
- Expected deliverables

Wait for user approval before proceeding to analysis phase.

### Step 3: Iterative Analysis Phase

Extract patterns incrementally by analyzing files in planned batches.

**For each iteration:**

**3.1 Read Files Sequentially**

Use Read tool to analyze files in the batch:
- Read complete files (don't use offset/limit unless files are very large >2000 lines)
- Take notes on patterns, abstractions, and design decisions
- Identify relationships between files

**3.2 Document Patterns**

Create or update patterns document in `.agents/output/<task_name>/`:

**Initial iterations**: Create `patterns.md` or `architecture_patterns.md`
**Subsequent iterations**: Append findings to existing document

**Pattern documentation format:**

```markdown
## [Pattern Name]

**Purpose**: [What problem does this pattern solve]

**Implementation**: See `path/to/file.py:line-range` for example

**When to use**:
- [Scenario 1]
- [Scenario 2]

**When NOT to use**:
- [Anti-pattern scenario 1]

**Trade-offs**:
- ✅ [Benefit 1]
- ✅ [Benefit 2]
- ❌ [Limitation 1]
- ❌ [Limitation 2]

**Related patterns**: [Pattern A], [Pattern B]
```

**3.3 Update Progress File**

Mark files as analyzed (✅) in file inventory
Document iteration completion in "Phase Progress Tracking" section

**3.4 Continue Until Complete**

Repeat for each planned iteration
Actual iterations may differ from plan (document deviations)

**Outcome**: Comprehensive pattern catalog with file references

### Step 4: Critical Review Phase

Assess extraction output to determine if additional deliverables are needed.

**4.1 Review Pattern Documentation**

Ask these questions:
- Is output **descriptive** ("here's what exists") or **prescriptive** ("here's how to build")?
- Can someone use this to implement similar architecture?
- Are reusable abstractions clearly identified?
- Is there a clear "getting started" path?

**4.2 Determine Additional Deliverables**

Based on review, decide what to create (see `references/documentation_patterns.md`):

**If patterns are loosely coupled and independently useful:**
- Primary: Pattern Catalog (already created)
- Optional: Quick reference guide

**If architecture should be replicated:**
- Primary: Prescriptive Guide (workflow-based)
- Secondary: Reference Implementation (if code is reusable)

**If creating a framework/library:**
- Primary: Prescriptive Guide + Reference Implementation
- Secondary: Pattern Catalog in references/

**4.3 Plan Refinement Work**

Create task list for deliverables:
- Prescriptive guide creation (if needed)
- Reference implementation extraction (if needed)
- Token optimization pass
- Process documentation

### Step 5: Refinement Phase (if needed)

Transform descriptive findings into prescriptive guidance and/or reference implementation.

**5.1 Create Prescriptive Guide (if applicable)**

**Structure** (see `references/documentation_patterns.md` for details):
- **Quick Start**: "Copy these files, follow this structure"
- **Core Concepts**: Explain foundational abstractions with "why"
- **Step-by-step workflow**: "Building Your First X" (7-10 steps)
- **Key Design Decisions**: Configuration choices, trade-offs, rationale
- **Advanced Patterns**: Multi-phase workflows, composition strategies
- **Resources**: Point to reference implementation, pattern catalog

**Writing guidelines:**
- Use imperative/infinitive form (not second person)
- Use file references instead of inline code: `See path/to/file.py:line-range`
- Include "why" and "when" for all design decisions
- Document anti-patterns and trade-offs
- Keep lean via progressive disclosure (detailed info in references/)

**5.2 Create Reference Implementation (if applicable)**

**Extract reusable abstractions:**
- Create `reference_implementation/core/` directory in output
- Copy reusable files from original codebase
- Make domain-agnostic:
  - Remove project-specific imports
  - Rename domain-specific classes (e.g., PlaygroundTask → Task)
  - Add TODO markers for LLM provider configuration
  - Enhance docstrings with pattern explanations

**Create instructive example:**
- Create `reference_implementation/example_<domain>/` directory
- Build minimal but complete example demonstrating key patterns
- Token-efficient: Use TODO comments instead of full implementation
- Self-documenting: Add "PATTERN DEMONSTRATED", "KEY CONCEPTS", "WHEN TO USE" sections to docstrings
- Include minimal README (structure tree + key patterns, no usage examples)

**5.3 Update Pattern Catalog (if applicable)**

If created prescriptive guide and/or reference implementation:
- Keep pattern catalog as research documentation
- Move to `references/` directory for on-demand loading
- Update guide to reference patterns as needed

### Step 6: Token Optimization Phase

Eliminate duplication and optimize for AI consumption.

**6.1 Identify Duplication**

Common duplication sources:
- Inline code examples in guide that duplicate reference implementation
- Usage examples in READMEs that duplicate guide content
- Pattern descriptions in multiple locations

**6.2 Apply File References**

Replace inline code examples with file references:
- Before: Multi-line code block in guide
- After: `See reference_implementation/path/to/file.py:line-range for [example type]`

**Token savings**: ~15-20 lines per example → ~200-300 lines in typical guide

**6.3 Enhance Docstrings**

Make reference implementation self-teaching:
- Add module-level docstrings with "PATTERN DEMONSTRATED" sections
- Include "KEY CONCEPTS", "WHEN TO USE THIS PATTERN", "DESIGN CHOICE" sections
- Explain rationale directly in code
- Reference guide sections as needed

**6.4 Trim READMEs**

Keep minimal READMEs:
- Directory structure tree
- Key patterns demonstrated (bullet points with file references)
- Remove usage examples (guide covers this)

**6.5 Progressive Disclosure**

Ensure lean main documents:
- Guide: 350-500 lines for SKILL.md, 400-650 for standalone
- Pattern catalog in references/ if large (>500 lines)
- Detailed documentation on-demand

**Outcome**: 25-30% token reduction while improving clarity

### Step 7: Process Documentation Phase

Capture lessons learned and document process for future extractions.

**7.1 Complete Phase Summaries**

For each major phase, add "Phase [N] Completion Summary" section to progress file:

**Deliverables Created:**
- List each deliverable with location
- Describe key features and improvements

**Process Documentation:**
- What worked well
- Key decisions made and rationale
- Process pattern for reuse

**Artifacts for Future Extractions:**
- Reusable process patterns
- Key principles learned
- Tool usage notes

**7.2 Document Lessons Learned**

Capture insights in progress file:
- What worked better than expected
- What was more difficult than anticipated
- Process improvements for next time
- Decisions that should be codified

**7.3 Update File Inventory**

Ensure file inventory is complete and accurate:
- All files marked as analyzed (✅)
- Line counts verified
- Organization clear and logical

**7.4 Note Skill Conversion Option**

If architecture guide is broadly applicable:
- Note in progress file that guide can be converted to Claude Skill
- Reference skill-creator skill for future conversion
- Do NOT automatically invoke skill-creator (manual decision)

### Step 8: Final Deliverables Review

Present complete set of deliverables to user.

**8.1 Summarize Output**

List all deliverables created:
- Pattern catalog (if created)
- Prescriptive guide (if created)
- Reference implementation (if created)
- Progress file with comprehensive process documentation

**8.2 Explain Structure**

Show output directory structure:

```
.agents/
├── tasks/
│   ├── <task_name>_plan.md
│   └── <task_name>_progress.md
└── output/
    └── <task_name>/
        ├── patterns.md or guide.md
        ├── reference_implementation/ (if applicable)
        │   ├── core/
        │   └── example_domain/
        └── README.md
```

**8.3 Highlight Key Insights**

Summarize most important findings:
- Core architectural patterns identified
- Reusable abstractions extracted
- Design principles and rationale
- Process lessons learned

**8.4 Suggest Next Steps**

Based on deliverables:
- Review and validation by domain expert
- Testing reference implementation
- Skill conversion (if appropriate)
- Distribution to team

## Key Principles

**1. Progressive Disclosure**
- Chunk analysis into ~1500 line iterations
- Don't load entire codebase into context at once
- Use Explore agent for initial survey, Read tool for detailed analysis

**2. Living Documentation**
- Update progress file after each phase
- Write patterns incrementally (not at end)
- Document decisions and rationale as you go

**3. Flexible Deliverables**
- Adapt output to extraction goals
- Pattern catalog for understanding
- Prescriptive guide for implementation
- Reference implementation for reusable code
- Hybrid approaches common

**4. Token Efficiency**
- Use file references instead of inline code
- Enhance docstrings to make code self-teaching
- Single source of truth (no duplication)
- Progressive disclosure (lean main docs, detailed references/)

**5. AI Consumption Focus**
- Write in imperative/infinitive form (not second person)
- Include file references with line numbers
- Document "why" and "when" for all patterns
- Provide decision guidance (not just descriptions)
- Mark uncertainty explicitly

**6. Resumability**
- Progress file enables resuming at any phase
- Comprehensive process documentation
- File inventory tracks analysis progress
- Iteration plan shows remaining work
- Lessons learned captured for future sessions

**7. Vertical Slices Over Horizontal Layers**
- Group files by complete subsystems when possible
- Preserves architectural context
- Shows patterns in combination
- Easier to understand relationships

**8. Descriptive vs Prescriptive**
- Pattern catalogs are descriptive ("here's what exists")
- Guides are prescriptive ("here's how to build")
- Reference implementations demonstrate patterns
- Aim for prescriptive output when goal is replication

## Code/Documentation Scanning Guidance

When scanning large amounts of code or documentation:

**Default chunk size**: ~1500 lines per iteration
**Confirm with user**: Before proceeding, verify chunk size works for their needs
**Scope**: This guidance applies ONLY to content being pulled into the current session's context window
**Rationale**: Larger chunks (vs 500-800 lines) preserve architectural context while staying within token limits

**Note**: Sub-agents (like Explore agent) manage their own context and are not bound by this guidance.

## Integration with task-planning

This skill builds directly on task-planning:

**Step 1**: Invoke task-planning to create plan and progress files
**Throughout**: Update progress file using architecture-specific sections (see `assets/progress_template_additions.md`)
**Progress file sections**:
- Reconnaissance Summary (repository stats, architecture overview, file inventory)
- Iteration Plan (batching strategy, file groupings, pattern targets)
- Phase Progress Tracking (checkmarks for each phase, outcomes documented)
- Phase Completion Summaries (deliverables, process documentation, lessons learned)

**Benefits**:
- Structured planning before analysis begins
- Comprehensive progress tracking
- Resumability across sessions
- Process documentation for future extractions
- Clean separation between plan (what to do) and progress (what was done)

## Resources

### references/langchain_case_study.md

Complete case study of extracting LangChain multi-expert architecture from ocsf-playground codebase. This resulted in the creation of the `langchain-expert-builder` skill.

**Contents**:
- 8-phase workflow from reconnaissance to skill packaging
- Process decisions and rationale
- What worked well and lessons learned
- Detailed phase-by-phase documentation
- Deliverables created at each phase

**When to load**: Reference when need concrete example of complete extraction process, especially for understanding how phases evolved and what deliverables were created.

### references/documentation_patterns.md

Guide for structuring output deliverables based on extraction goals.

**Contents**:
- Common output structures (pattern catalog, prescriptive guide, reference implementation, hybrid)
- When to use each structure
- Token optimization strategies
- Decision matrix for choosing deliverables
- Best practices for AI consumption
- Examples of each pattern

**When to load**: Reference when deciding what deliverables to create or how to structure output for specific extraction goals.

### assets/progress_template_additions.md

Architecture extraction-specific sections to add to task-planning's progress template.

**Contents**:
- Reconnaissance Summary structure
- Iteration Plan format
- Phase Progress Tracking sections
- Phase Completion Summary templates
- Integration guidance with standard task-planning template

**When to load**: Reference when setting up progress file or documenting phase completions. Copy relevant sections into `<task_name>_progress.md` created by task-planning.

## Common Pitfalls

**1. Loading entire codebase at once**
- Solution: Use Explore agent for survey, then iterative analysis in batches

**2. Creating descriptive catalog when prescriptive guide needed**
- Solution: Step 4 critical review assesses if output matches goals

**3. Inline code duplication**
- Solution: Step 6 token optimization replaces inline code with file references

**4. Domain-specific abstractions in "core" code**
- Solution: Ensure core abstractions are generic, move domain-specific code to examples

**5. Forgetting to update progress file**
- Solution: Update after each phase completion, not at end

**6. Skipping rationale documentation**
- Solution: Always document "why" behind design decisions, not just "what"

**7. Analysis without iteration plan**
- Solution: Complete Step 2 reconnaissance fully before starting analysis

## Example Invocation

```
User: I want to extract the multi-expert LLM architecture from ocsf-playground
      and create a reference guide that other AI assistants can use.

Claude: I'll help extract the LangChain multi-expert architecture from ocsf-playground.
        Let me start by invoking the task-planning skill to set up this extraction
        as a formal task.

[Invokes task-planning skill, creates plan and progress files]

Claude: I've created the extraction plan. Now let me begin reconnaissance by launching
        an Explore agent to survey the ocsf-playground repository...

[Follows Step 2: Reconnaissance Phase]

Claude: Reconnaissance complete. I've identified 50 Python files (2,916 lines) related
        to LangChain patterns. I'll analyze these in 2 iterations: Iteration 1 covers
        core abstractions + complete Entities Expert (13 files, 805 lines), Iteration 2
        covers simpler experts + validation patterns (20 files, 944 lines).

User: That sounds good, proceed.

[Follows Steps 3-8: Analysis → Review → Refinement → Optimization → Documentation → Deliverables]

Claude: Extraction complete! I've created:
        - langchain_patterns.md (17 patterns across 7 categories)
        - langchain_guide.md (prescriptive guide with 7-step workflow)
        - reference_implementation/ (domain-agnostic core/ + json_transformer_expert/ example)

        Progress file documents the complete 8-phase process for resumability.

        This guide is ready for AI assistant consumption. If you'd like to convert it
        to a Claude Skill for broader distribution, we can use the skill-creator skill.
```