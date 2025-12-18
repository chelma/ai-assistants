# LangChain Architecture Extraction: Case Study

## Overview

This document captures the complete process of extracting LangChain architectural patterns from the ocsf-playground codebase, which resulted in the creation of the `langchain-expert-builder` Claude Skill. Use this as a reference example when performing architecture extractions from other codebases.

**Source Repository**: ocsf-playground (private)
**Extraction Target**: Multi-expert LLM system architecture using LangChain
**Duration**: 2025-10-30 to 2025-10-31
**Final Output**: `langchain-expert-builder` skill with reference implementation and comprehensive guide
**Total Phases**: 8 phases from reconnaissance to skill packaging

## High-Level Process Summary

The extraction followed a three-phase approach that evolved into eight distinct phases:

1. **Reconnaissance** - Explore codebase, understand structure, create file inventory
2. **Iterative Analysis** - Extract patterns in batches (~1500 lines per iteration)
3. **Human-Led Refinement** - Transform findings into prescriptive guidance
4. **Token Optimization** - Eliminate duplication, use file references
5. **Code Organization Refinement** - Ensure domain-agnostic abstractions
6. **Invocation Workflow Documentation** - Document complete usage patterns
7. **Design Philosophy Documentation** - Capture "why" behind decisions
8. **Claude Skill Creation** - Package as distributable skill

## Phase 1: Reconnaissance

### Objective
Understand the codebase structure and identify all relevant files for pattern extraction.

### Process

**Step 1: Launched Explore Agent**
- Used Task tool with subagent_type=Explore
- Scope: ocsf-playground repository, focus on LangChain/LLM inference patterns
- Thoroughness level: "very thorough"

**Step 2: Reviewed Reconnaissance Report**
- Analyzed agent's findings about repository structure
- Identified core architectural components
- Noted technology stack (LangChain, AWS Bedrock, Claude 3.5 Sonnet)

**Step 3: Created Complete File Inventory**
- Listed 50 Python files related to LangChain/LLM inference
- Total: 2,916 lines of code
- Organized by architectural layer (5 layers identified)

**Step 4: File Prioritization**
- Strategy: Core abstractions → concrete implementations → utilities
- Rationale: Understand foundation before studying specific use cases

**File Layers Identified:**
1. **Core Abstractions** (5 files, 202 lines): Expert, Task, Tool, Inference, ValidationReport
2. **Expert Implementations** (10 files, 599 lines): Three experts with complete workflows
3. **Prompt Engineering** (12 files, 463 lines): Templates and factories per expert
4. **Validation & Transformation** (3 files, 469 lines): Multi-stage validation patterns
5. **Supporting Infrastructure** (20 files, 1,183 lines): OCSF schemas, REST clients (domain-specific, excluded)

**Step 5: Created Iteration Plan**
- Target: ~1500 lines per iteration
- Estimated iterations: 2 (actual: 2 completed)
- Approach: Group by complete expert systems (vertical slices)
- Rationale: Maintain context by studying full implementations

**Iteration Plan:**
- **Iteration 1**: Core abstractions + complete Entities Expert (13 files, 805 lines)
- **Iteration 2**: Simpler experts + validation patterns (20 files, 944 lines)

**Step 6: Presented Plan for Approval**
- Explained iteration strategy to user
- User approved approach
- Proceeded to analysis phase

### Key Decisions

1. **Larger batch size**: 1500 lines per iteration (vs smaller chunks) to preserve architectural context
2. **Vertical slices**: Complete expert implementations rather than horizontal layers
3. **Excluded domain-specific code**: Focused on portable LangChain patterns, skipped OCSF schema infrastructure
4. **Living documentation**: Created progress file immediately, updated after each phase

### Tools Used

- Task tool with Explore agent for initial codebase survey
- Manual file inventory creation in progress file
- Line counting via Read tool on identified files

### Deliverables

- Complete file inventory organized by layer (documented in progress file)
- Iteration plan with specific files per batch
- Repository statistics and architecture overview
- User-approved approach for analysis phase

## Phase 2: Iterative Analysis

### Objective
Extract architectural patterns incrementally by analyzing files in planned batches.

### Process

**Iteration 1: Core Abstractions + Complete Entities Expert**
- **Files analyzed**: 13 files, 805 lines
- **Focus**: Foundational abstractions + most sophisticated expert implementation
- **Method**: Read files sequentially, document patterns in markdown
- **Output**: Initial patterns document with 10+ patterns identified

**Patterns extracted in Iteration 1:**
- Expert dataclass pattern (LLM + system prompt factory + tool bundle)
- Task abstraction (work item + message context + lifecycle methods)
- Tool-forcing pattern (bind_tools() for structured output)
- Async batch inference infrastructure
- ValidationReport accumulation pattern
- Prompt factory pattern (dynamic system message generation)
- Progressive detail loading (schema filtering between phases)
- Multi-phase expert workflow (analysis → generation)

**Iteration 2: Simpler Experts + Validation**
- **Files analyzed**: 20 files, 944 lines
- **Focus**: Contrast patterns (simpler expert configs) + post-inference validation
- **Method**: Continue pattern extraction, compare with Iteration 1 findings
- **Output**: Expanded patterns document to 17 patterns across 7 categories

**Additional patterns extracted in Iteration 2:**
- LLM configuration spectrum (temp=0 vs temp=1, extended thinking on/off)
- Simpler expert patterns (fewer fields, simpler prompts)
- Multi-stage validation (syntax → loading → invocation → output)
- Python code validation with exec() + ModuleType
- Custom exception hierarchies for validation
- Knowledge module organization (domain-specific prompts)
- Strategy pattern for prompt variations

**Iteration 3-N**: Not needed - all relevant files covered in 2 iterations

### Key Decisions

1. **Living document approach**: Wrote patterns to markdown incrementally, not at end
2. **Pattern categorization**: Organized into 7 categories (core abstractions, LLM config, prompting, validation, etc.)
3. **File references with line numbers**: Every pattern cited specific files and line ranges
4. **Contrasting examples**: Showed both complex (Entities Expert) and simple (Regex/Categorization) implementations

### Tools Used

- Read tool for file analysis (sequential reading of planned files)
- Write/Edit tools for updating `langchain_patterns.md` incrementally
- No additional Explore/Grep - followed predetermined iteration plan

### Deliverables

- `langchain_patterns.md` - 17 architectural patterns across 7 categories
- Pattern documentation included file references, code examples, and "when to use" guidance
- Total analyzed: 33 files, 1,749 lines of LangChain-relevant code

### Outcome Assessment

**What worked well:**
- Vertical slice approach maintained architectural context
- Living documentation kept findings organized
- Pattern categorization helped identify missing patterns (compared Iteration 1 vs 2)

**Critical gap identified** (led to Phase 3 pivot):
- Output was **descriptive** ("here's what we found") not **prescriptive** ("here's how to build")
- Patterns documented in isolation, not as cohesive system
- No clear "getting started" narrative for someone wanting to build similar system
- Reusable code not explicitly called out (core/ files were nearly copy-paste ready but not positioned that way)

## Phase 3: Human-Led Refinement

### Objective
Transform descriptive pattern documentation into prescriptive guidance with reference implementation.

### Process

**Critical Assessment**
- User reviewed `langchain_patterns.md` output from Phase 2
- Identified it reads like "archaeological report" not "construction guide"
- Key insight: **Descriptive vs Prescriptive** - need "how to build" not "what exists"

**Problem Statement:**
- Missing "how to build" narrative
- Reusable code not identified as foundation
- No directory structure template
- Missing decision guides (when to use temp=0 vs temp=1, etc.)
- Weak integration story (shows pieces but not assembly)

**Revised Strategy:**
1. **Preserve historical artifact**: Keep `langchain_patterns.md` as research documentation
2. **Create practical guide**: New `langchain_guide.md` with prescriptive guidance
3. **Provide reference implementation**: Create `reference_implementation/` directory

**Reference Implementation Design:**
- `core/` - Generic, ready-to-run abstractions (copied from ocsf-playground, made domain-agnostic)
- `json_transformer_expert/` - Complete but minimal example showing two-phase pattern
  - Mapping phase: Identify JSON field mappings (creative, temp=1)
  - Transform phase: Generate Python transform code (deterministic, temp=0)
  - Demonstrates: Progressive detail loading, validation mechanics, two-expert workflow

**Why JSON Transformer Example:**
- Direct analog to ocsf-playground entities_expert (proven pattern)
- Clear two-phase workflow: mapping (analysis) → transform (code generation)
- Progressive detail is obvious: "full schema" → "filtered schema for identified paths"
- Validation is essential: recursive schema validation, Python code execution checks
- Generic domain: JSON transformation is universally applicable

**Implementation:**
1. Created `reference_implementation/core/` (7 files, ~440 lines)
   - Renamed `PlaygroundTask` → `Task` (domain-agnostic)
   - Added comprehensive docstrings explaining "why" and "how"
   - Included TODO markers for LLM provider configuration
   - Made imports relative and generic
2. Created `reference_implementation/json_transformer_expert/` (9 files, ~875 lines)
   - Token-efficient: Used TODO comments instead of full Bedrock setup
   - Instructive over functional: Focus on showing patterns
   - Two-phase workflow with contrasting configs
3. Wrote `langchain_guide.md` (650 lines initially)
   - Quick Start: "Copy core/, review example, build your first expert"
   - Core Abstractions: Expert, Task, Tool explained with "why"
   - Building Your First Expert: 7-step process with code examples
   - Key Design Decisions: Tool-forcing, LLM config, progressive detail, validation
   - Advanced Patterns: Multi-turn, chaining, async batching

### Key Decisions

1. **Token efficiency over completeness**: Example expert uses TODO comments, not production-ready LLM config
2. **Instructive code**: Comments explain patterns ("// TODO: Replace with your LLM config")
3. **Two outputs**: Keep patterns.md (research) + create guide.md (practical)
4. **Mark commentary spots**: Explicitly marked 4 places needing human expertise input
5. **Process documentation**: Updated progress file with Phase 3 process for future reference

### Tools Used

- Write tool for creating new files (reference implementation + guide)
- Read tool to review original ocsf-playground files
- Edit tool for minor adjustments

### Deliverables

- `langchain_guide.md` - Prescriptive guide (650 lines)
- `reference_implementation/core/` - Generic abstractions (7 files)
- `reference_implementation/json_transformer_expert/` - Complete example (9 files)
- Total: ~1,315 lines of code + documentation

### Outcome

Successfully pivoted from descriptive patterns to prescriptive guidance. Output now answers "I want to build a multi-expert LLM system - where do I start?"

## Phase 4: Token Optimization

### Objective
Eliminate code duplication between guide and reference implementation for LLM consumption efficiency.

### Context
Guide will be converted to Claude Skill where both guide and reference code load into context. Need single source of truth.

### Problem Identified
- `langchain_guide.md` (692 lines) contained substantial inline code examples
- These examples were pedagogical simplifications duplicating reference implementation concepts
- `json_transformer_expert/README.md` (136 lines) contained usage examples overlapping with guide
- Token waste and confusion about which version is authoritative

### Refactoring Performed

**1. Simplified langchain_guide.md**
- **Before**: 692 lines with inline code examples
- **After**: 461 lines with file references
- **Reduction**: -231 lines (-33%)
- **Changes**: Replaced concrete code examples with file references pattern: `See reference_implementation/path/to/file.py:line-range`
- **Kept**: Abstract concept explanations with signatures only

**2. Trimmed json_transformer_expert/README.md**
- **Before**: 136 lines with full usage examples
- **After**: 56 lines with pattern descriptions
- **Reduction**: -80 lines (-59%)
- **Changes**: Removed Phase 1/2/3 workflow code blocks, kept structure tree and pattern bullet points

**3. Enhanced Reference Implementation Docstrings**
- Added to each module: `PATTERN DEMONSTRATED:`, `KEY CONCEPTS:`, `WHEN TO USE THIS PATTERN:`, `DESIGN CHOICE:`
- Files enhanced: models.py, task_def.py, tool_def.py, templates.py, generation.py, validators.py
- **Result**: Reference implementation became self-teaching

### Key Decisions

1. **Single source of truth**: Implementation is authoritative, guide is roadmap
2. **File references everywhere**: Guide points to specific line ranges, no duplication
3. **Self-documenting code**: Enhanced docstrings make code teach patterns directly

### Total Token Savings
- **Markdown reduction**: 311 lines removed from guide/READMEs
- **Net effect**: ~25-30% reduction in documentation tokens while improving instructive value

## Phase 5: Code Organization Refinement

### Objective
Ensure `core/` package is completely domain-agnostic and reusable.

### Problem Identified
- `core/validators.py` contained Python-specific validation exceptions (PythonLogic*)
- These exceptions only used by `json_transformer_expert/validators.py`
- Exception names explicitly reference "PythonLogic", making them domain-specific
- Blocked `core/` from being truly framework-agnostic

### Refactoring Performed

**1. Moved Exceptions**
- Moved 3 exception classes from `core/validators.py` to `json_transformer_expert/validators.py`
- Added section header: `# CUSTOM EXCEPTIONS FOR PYTHON CODE VALIDATION`
- Kept all docstrings and examples intact
- **Rationale**: Co-locates exceptions with their only consumer, makes pattern clear

**2. Deleted core/validators.py**
- Removed file entirely
- Updated `core/__init__.py` to remove validators imports/exports
- Updated `core/README.md` to remove from file list
- **Rationale**: Keeps `core/` generic and reusable

**3. Updated Documentation References**
- `langchain_guide.md:335` - Changed "from `core/validators.py`" to "Define custom exceptions in your expert's validators.py"
- `core/README.md:19` - Added note about where validation exceptions should be defined

### Results

**Before**: `core/` contained domain-specific Python validation exceptions
**After**: `core/` contains only generic, reusable abstractions
**Benefit**: Clear pattern - experts define their own validation exceptions in domain-specific validators.py

## Phase 6: Invocation Workflow Documentation

### Objective
Enhance Step 7 in langchain_guide.md with detailed invocation workflow showing how all abstractions wire together.

### Motivation
Original Step 7 showed minimal invocation example but didn't explain:
- How prompt factory is called (explicitly by developer, not by invoke_expert)
- How conversation turns are constructed (SystemMessage + HumanMessage pattern)
- Why HumanMessage is needed (trigger for LLM to start)
- How work items are populated (invoke_expert sets via task.set_work_item())
- Complete five-step workflow tying Expert → Task → Tool together

### Enhancement Performed

**Added to Step 7:**
1. **Five-step workflow breakdown**: Get expert → generate system message → build turns → create task → invoke → access result
2. **Complete code example** with inline comments explaining each step
3. **Key invocation insights** (5 numbered points):
   - Prompt factory separation and control
   - Conversation turns pattern (list of LangChain messages)
   - HumanMessage trigger role
   - Task initialization with None work item
   - Result access via get_work_item()
4. **"Why this matters"** closing statement on fine-grained control

**Before**: 9 lines (minimal example)
**After**: 58 lines (complete workflow + insights + rationale)

### Reference Source
- File: `~/workspace/personal/ocsf-playground/playground/playground_api/views.py:303-325`
- Method: `TransformerEntitiesV1_1_0AnalyzeView._analyze()`
- Pattern: Complete invocation workflow from production Django REST API

### Results
LLMs reading guide now understand complete invocation lifecycle and which operations developer controls vs framework handles.

## Phase 7: Design Philosophy Documentation

### Objective
Enhance documentation with underlying design rationale based on production experience.

### Motivation
Four key design principles from production usage weren't captured:
1. **Narrow scope philosophy**: LLMs perform best with focused prompts, tailored tools, filtered context
2. **Tool-forcing rationale**: Tools turn response format from prose to API spec
3. **Multi-tool expert pattern**: Single expert can have multiple tools for related outcomes
4. **ValidationReport observability**: Three use cases (debugging, self-correction, model tuning)

### Enhancements Performed

**1. Added Core Philosophy Section** (langchain_guide.md:18-32)
- Three mechanisms for narrow scope
- Why narrow scope matters (eliminate ambiguity, improve quality, enable tuning, simplify debugging)
- Development/runtime trade-off explanation
- Cross-reference to Progressive Detail Loading pattern

**2. Enhanced Tool-Forcing Pattern Section** (langchain_guide.md:307-330)
- Core rationale (tools = API spec, not prose instructions)
- Five benefits of tool forcing
- "The alternative" section explaining prose-based format instruction failures
- Expanded trade-off guidance

**3. Added Multi-Tool Expert Pattern** (langchain_guide.md:459-486)
- Pattern definition with current implementation status
- When to use multiple tools (3 concrete examples)
- Implementation guidance
- Why multi-tool is rare (narrow-scope philosophy)

**4. Enhanced Multi-Turn Conversations Section** (langchain_guide.md:412-456)
- Validation retry loop pattern with complete code example
- When to use multi-turn vs new task (decision criteria)
- Context accumulation gotchas (token counts, verbose reports)

**5. Expanded Multi-Stage Validation Section** (langchain_guide.md:388-428)
- Three critical use cases for ValidationReport:
  1. Human debugging (detailed diagnostics)
  2. LLM self-correction (feed report back for retry)
  3. Model tuning dataset (prompt + response + validation = training example)
- Why capture both input and output (complete observability)
- Tuning dataset structure explanation

**6. Updated core/validation_report.py Docstring** (lines 1-30)
- DESIGN PHILOSOPHY section
- WHY STRUCTURED REPORTS section
- Complete rationale for ValidationReport's role

**7. Updated core/tools.py Docstring** (lines 16-51)
- DESIGN PHILOSOPHY section
- WHEN TO USE MULTIPLE TOOLS (3 examples)
- WHEN NOT TO USE MULTIPLE TOOLS (3 anti-patterns)

### Total Changes
- 7 sections enhanced
- +146 lines of design philosophy documentation
- Clear rationale for all major design decisions
- Anti-patterns documented to prevent mistakes

### Key Insights Captured
1. Narrow scope = better performance
2. Tool forcing = API contract
3. ValidationReport = observability cornerstone
4. Multi-tool experts = rare but valid pattern

## Phase 8: Claude Skill Creation

### Objective
Convert langchain architecture guide into distributable Claude Skill using skill-creator.

### Motivation
Converting to Claude Skill enables:
- **Discoverability**: Automatic trigger when users mention LangChain multi-expert patterns
- **Progressive disclosure**: SKILL.md loads when triggered, references/assets load as needed
- **Reusability**: Copy-paste ready Python code bundled with guidance
- **Distribution**: Single .zip file shareable with others

### Process

**Step 1: Understanding the Skill**
- SKIPPED - Concrete examples already exist from Phases 1-7

**Step 2: Planning Reusable Skill Contents**
- **SKILL.md**: Adapted from langchain_guide.md
- **references/langchain_patterns.md**: Detailed pattern extraction (load on-demand)
- **assets/reference_implementation/**: Copy-paste ready Python code
- **Decision**: No scripts needed (code meant to be copied, not executed within skill)

**Step 3: Initialize the Skill**
- Ran `init_skill.py` script
- Created skill directory at `claude/skills/langchain-expert-builder/`

**Step 4: Edit the Skill**

**4.1 Populate Reusable Contents:**
```bash
cp -r .agents/output/langchain_architecture_extraction/reference_implementation \
  claude/skills/langchain-expert-builder/assets/

cp .agents/output/langchain_architecture_extraction/langchain_patterns.md \
  claude/skills/langchain-expert-builder/references/

# Removed example files
rm claude/skills/langchain-expert-builder/assets/example_asset.txt
rm claude/skills/langchain-expert-builder/references/api_reference.md
rm claude/skills/langchain-expert-builder/scripts/example.py
rmdir claude/skills/langchain-expert-builder/scripts
```

**4.2 Adapt langchain_guide.md into SKILL.md:**

**Key adaptations:**
1. **YAML frontmatter**: Added comprehensive description with trigger conditions
2. **Writing style conversion**: Explanatory → imperative/infinitive form
   - Before: "This guide explains how to build..."
   - After: "Build production-ready LangChain multi-expert systems..."
3. **Structure optimization for AI**: Kept Quick Start, Building Steps, Design Decisions, Advanced Patterns
4. **Removed sections**: "Last Updated", "Source", "Applicability", "When to Deviate", commentary placeholders
5. **Enhanced with skill-specific guidance**: "When to use this skill" section, Resources section

**Final SKILL.md stats:**
- 351 lines (vs 462 in langchain_guide.md)
- Token-optimized
- Imperative form throughout

**Step 5: Package the Skill**
- Ran `package_skill.py` script
- Automatic validation performed (YAML, naming, structure, descriptions)
- Package created: `langchain-expert-builder.zip`
- Contents: 19 files (1 SKILL.md, 1 references/, 17 assets/)

**Step 6: Iteration**
- DEFERRED for future testing and feedback

### Deliverables
- Single distributable `langchain-expert-builder.zip` file
- Automatic skill triggering on relevant topics
- Progressive disclosure structure
- Copy-paste ready Python code bundled

## Key Learnings

### What Worked Well

1. **Three-phase approach**: Reconnaissance → Analysis → Refinement clearly separated concerns
2. **Iteration strategy**: Grouping files by complete expert systems (vertical slices) maintained context
3. **Living documentation**: Writing to progress file immediately (not at end) kept findings organized
4. **Critical pivot in Phase 3**: Recognizing output was descriptive, not prescriptive, led to better deliverable
5. **Token optimization early**: Phases 4-5 reductions made skill conversion straightforward
6. **Design philosophy documentation**: Captured "why" behind decisions for future reference

### Key Principles for Future Extractions

1. **Separate reusable from domain-specific early**: Identify what's portable vs what's project-specific
2. **Document patterns with file references + line numbers**: Makes verification easy
3. **Include "why" and "when to use"**: Pattern documentation needs context and decision guidance
4. **Token efficiency via comments**: Use TODO comments for instruction, not exhaustive implementation
5. **Mark spots needing human input**: Explicitly flag where expert judgment is required
6. **Progressive disclosure**: Keep main documents lean, use references for deep dives
7. **Descriptive vs Prescriptive**: Aim for "how to build" guides, not just "what exists" catalogs

### Process Pattern for Architecture Extraction

1. **Reconnaissance**: Survey repository, create file inventory, understand structure
2. **Iteration Planning**: Group files by layer/system, plan ~1500 line iterations
3. **Pattern Extraction**: Analyze files against framework, extract patterns incrementally
4. **Living Documentation**: Write findings to persistent markdown immediately
5. **Critical Review**: Assess whether output is descriptive vs prescriptive
6. **Reference Implementation**: Create generic abstractions + minimal instructive example
7. **Practical Guide**: Write "how to build" guide, not "what exists" catalog
8. **Token Optimization**: Use file references, enhance docstrings, eliminate duplication
9. **Organization Refinement**: Ensure clean separation of concerns
10. **Workflow Documentation**: Capture complete usage patterns with examples
11. **Philosophy Documentation**: Explain design rationale and trade-offs
12. **Skill Conversion** (optional): Package for distribution if appropriate

### Documentation Strategy

**Progress File Structure:**
- **Status tracking**: Phase completion checkmarks
- **Process documentation**: What was done in each phase
- **Key decisions**: Why approaches were chosen
- **Deliverables tracking**: What was created
- **Deviations/Blockers/Gotchas**: Problems encountered
- **Lessons learned**: Insights for future work

**Output Structure:**
- **Patterns document**: Descriptive catalog (17 patterns across 7 categories)
- **Guide document**: Prescriptive workflow (Quick Start → Building → Decisions → Advanced)
- **Reference implementation**: Self-documenting code with enhanced docstrings
- **READMEs**: Directory overviews with structure trees

### Token Optimization Strategies

1. **File references over inline code**: `See path/to/file.py:line-range` instead of code blocks
2. **Enhanced docstrings**: Make code self-teaching via comprehensive module/class docstrings
3. **Single source of truth**: Reference implementation is authoritative, guide points to it
4. **Progressive disclosure**: Main documents lean, detailed info in references/
5. **TODO comments**: Instructive placeholders instead of production-ready code

### Skill Conversion Insights

**When to convert architecture guide to skill:**
- Patterns are broadly applicable (not project-specific)
- Guide provides procedural knowledge LLMs need
- Reusable code exists that others would copy-paste
- Workflow is repeatable across different contexts

**Skill structure decisions:**
- **SKILL.md**: Workflow-based (Quick Start → Building → Decisions → Advanced)
- **references/**: Detailed patterns (load when deeper understanding needed)
- **assets/**: Copy-paste ready code (not loaded to context, used in output)
- **scripts/**: Executable code (only when repeatedly rewritten or deterministic reliability needed)

**Adaptation for skill format:**
- Convert explanatory → imperative/infinitive form
- Remove meta-commentary (dates, source notes, update history)
- Add "When to use this skill" section with concrete triggers
- Comprehensive YAML description for discoverability
- Resources section documenting bundled files

## Recommended Workflow for Future Architecture Extraction Skills

1. Extract patterns from real codebase (reconnaissance + iterative analysis)
2. Create prescriptive guide + reference implementation
3. Optimize tokens via file references
4. Ensure code organization is domain-agnostic
5. Document invocation workflows concretely
6. Capture design philosophy and rationale
7. Convert to skill using skill-creator (if appropriate for distribution)

This complete workflow was successfully applied to create the `langchain-expert-builder` skill from the ocsf-playground codebase.
