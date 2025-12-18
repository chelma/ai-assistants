# Detailed Extraction Workflow

This document provides step-by-step guidance for each phase of architecture extraction. Load this when you need detailed instructions beyond the high-level workflow in SKILL.md.

---

## Phase 1: Plan with Tag-Team

### Invoke Tag-Team

Begin by invoking the tag-team skill to establish the extraction as a formal task with plan and progress tracking.

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

**Note**: tag-team skill automatically handles:
- Workspace detection (from git repo name or asks user)
- Project root detection (for portable file references)
- Creates plan in `~/.claude/workspace/<workspace>/tasks/<task_name>_plan.md`

After tag-team creates the plan file, proceed to Phase 2.

---

## Phase 2: Reconnaissance & Iteration Planning

### 2.1 Launch Explore Agent

Use Task tool with subagent_type=Explore to survey the repository:
- Specify scope (entire repo or specific directories)
- Thoroughness level: "very thorough" for comprehensive coverage
- Focus: Identify files related to target architecture/patterns

### 2.2 Review Reconnaissance Report

Analyze Explore agent findings:
- Repository structure and organization
- Technology stack and key dependencies
- Architectural style and core components
- Initial pattern observations

### 2.3 Create File Inventory

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

### 2.4 File Prioritization

Determine analysis order based on:
- **Foundation-first**: Core abstractions → implementations → utilities
- **Vertical slices**: Complete subsystems (all files for one feature/expert)
- **Complexity-first**: Most complex examples first (establishes patterns), then simpler examples
- **Domain separation**: Reusable vs domain-specific code

### 2.5 Create Iteration Plan

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

### 2.6 Assess Investigation Scale & Choose Approach

Calculate total lines from file inventory. Choose analysis approach:

**Direct Analysis (Default for ≤3,000 lines)**
- Main session reads files directly (~1500 lines per iteration)
- Typical extractions: 1-2 iterations, 20-30 files
- Proceed to Phase 3: Iterative Analysis (direct reading)

**Delegated Investigation (For >3,000 lines)**
- Use codebase-researcher sub-agent for iteration-level investigations
- Main session synthesizes from findings across iterations
- See Phase 3 delegated workflow below

**When uncertain**: Start with direct analysis for first 2 iterations (~3k lines). If context becomes strained or patterns remain unclear, switch to delegation for remaining iterations.

**Why 3k line threshold?**
- Roughly 2 analysis iterations at ~1500 lines each
- Early enough to pivot before context pollution
- Late enough to validate patterns are emerging
- Based on production experience from multiple architecture extractions

**Key insight**: Gestalt understanding comes from pattern synthesis, not code memorization. For large extractions (>3k lines), delegating investigation to codebase-researcher and synthesizing from curated findings may actually improve architectural insight by forcing progressive abstraction.

### 2.7 Present Plan for Approval (CHECKPOINT)

Explain iteration strategy to user:
- Total iterations planned
- Analysis approach (direct vs delegated)
- Files per iteration and grouping rationale
- Estimated timeline
- Expected deliverables

**Wait for user approval before proceeding to analysis phase.**

---

## Phase 3: Iterative Analysis

Extract patterns incrementally by analyzing files in planned batches.

### Direct Reading Workflow (≤3,000 lines)

**For each iteration:**

#### 3.1 Read Files Sequentially

Use Read tool to analyze files in the batch:
- Read complete files (don't use offset/limit unless files are very large >2000 lines)
- Take notes on patterns, abstractions, and design decisions
- Identify relationships between files

#### 3.2 Document Patterns

Create or update patterns document in `~/.claude/workspace/<workspace>/output/<task_name>/`:

**Initial iterations**: Create `patterns.md` or `architecture_patterns.md`
- Include project root in header: `**Project Root**: ~/workspace/project-name` (use tilde for paths under $HOME)
- Create output directory with lazy creation: `mkdir -p ~/.claude/workspace/<workspace>/output/<task_name>/`

**Subsequent iterations**: Append findings to existing document

**File Reference Requirements**:
- Use paths **relative to project root** for all code references
- Example: `ruby_worker/app/workflows/workflow_demo_mixed.rb:15-30`
- NOT: `~/workspace/personal/time-cop/ruby_worker/...`
- Enables portability across machines and Claude sessions

**Pattern documentation format:**

```markdown
## [Pattern Name]

**Purpose**: [What problem does this pattern solve]

**Implementation**: See `path/to/file.py:line-range` for example (relative to project root)

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

#### 3.3 Pattern Priority Classification

As you document patterns during iterations, add priority tags to help focus later deliverables on architecturally significant patterns:

- `[PRIORITY: CRITICAL]` - Core abstractions, cross-cutting patterns, define the architecture
- `[PRIORITY: PREFERRED]` - Stylistic improvements, recommended practices
- `[PRIORITY: OBSERVED]` - Implementation details, domain-specific choices

**Initial classification guidance:**

- **CRITICAL**: Patterns in core abstractions, used across many files, define architectural structure (e.g., "Why factory pattern for client creation?")
- **PREFERRED**: Stylistic choices that improve the pattern but aren't essential (e.g., "Why module-level functions vs classes?")
- **OBSERVED**: Implementation details, one-off choices, domain-specific logic not part of the core architecture

**When uncertain:** Default to PREFERRED. Human will adjust in Phase 3 checkpoint.

**Example tagged pattern:**

```markdown
## Factory Pattern for Client Creation [PRIORITY: CRITICAL]

**Purpose**: Centralize AWS client instantiation and credential management
...
```

#### 3.4 Update Progress File

**IMPORTANT**: Update progress file **immediately after EACH iteration completion** (not in batches).

Mark files as analyzed (✅) in file inventory
Document iteration completion in "Phase Progress Tracking" section

#### 3.5 Continue Until All Iterations Complete

Repeat Steps 3.1-3.4 for each planned iteration.
Actual iterations may differ from plan (document deviations).

#### 3.6 Human Priority Review (CHECKPOINT)

After completing all analysis iterations, pause for human alignment on pattern priorities.

**Why this checkpoint is essential:**

Extraction goals often emerge during the process. Priority classification helps both Claude and the human collaborator discover what's architecturally significant as patterns are revealed. This prevents wasted effort in later phases while ensuring critical patterns receive appropriate focus.

**Process:**

1. **Present findings to human collaborator:**
   ```
   Phase 3 analysis complete. Documented [N] patterns across [M] iterations:
   - CRITICAL: [X] patterns (core abstractions, cross-cutting concerns)
   - PREFERRED: [Y] patterns (stylistic improvements, recommended practices)
   - OBSERVED: [Z] patterns (implementation details)

   Please review the priority classifications in [patterns file(s)].
   Adjust any tags based on your extraction goals, then let me know when ready to proceed.
   ```

2. **Human reviews pattern files:**
   - Scan each pattern and its `[PRIORITY: X]` tag
   - Upgrade/downgrade tags based on extraction goals
   - May discover that some OBSERVED patterns are actually CRITICAL
   - May realize some CRITICAL patterns are well-covered elsewhere (downgrade to PREFERRED)
   - May add notes about why certain patterns matter

3. **Human confirms readiness:**
   - "Priorities look good, proceed" (no changes needed)
   - "I've adjusted X patterns, proceed" (edits made directly in pattern files)
   - "Let's discuss pattern Y classification" (questions/clarifications)

4. **Update progress file:**
   Document priority breakdown and any significant adjustments in Phase 3 completion summary.

**Expected time:** 15-30 minutes for human review, depending on pattern count

**Outcome**: Comprehensive pattern catalog with validated priority classifications, ready for Phase 4 scoping decisions

---

### Delegated Investigation Workflow (>3,000 lines)

For large-scale extractions, delegate iteration-level investigation to codebase-researcher sub-agent:

**Workflow for each iteration:**

1. **Invoke codebase-researcher** with iteration-specific objective:
   ```
   Use codebase-researcher to analyze Iteration [N]: [iteration focus/title]

   Skills to load: extract-architecture (for pattern documentation format guidance)

   Files to analyze: [list from iteration plan with line counts]

   Pattern categories to extract: [from iteration plan]

   Current patterns documented: [reference to existing patterns.md if not first iteration]

   Deliverables:
   - Findings document with patterns identified in these files
   - File references for all observations (path:line-range format)
   - Priority classification for each pattern (CRITICAL/PREFERRED/OBSERVED)

   Context: This is iteration [N] of [M] for [extraction goal].
   ```

2. **Review findings returned** by codebase-researcher:
   - Read findings file from `~/.claude/workspace/<workspace>/research/<timestamp>-iteration-N/`
   - Main session never loads source code - only curated findings

3. **Synthesize into patterns.md** (main session):
   - Integrate new patterns from findings into growing pattern catalog
   - Cross-reference patterns across iterations
   - Note pattern evolution or refinement
   - Main session focuses on synthesis, not drowning in code

4. **Update progress file**: Mark iteration complete, files analyzed

5. **Continue to next iteration**: Repeat for remaining iterations

**Benefits of delegation:**
- ✅ Main session context stays clean (only sees findings, not raw code)
- ✅ Each iteration's investigation preserved separately for resumability
- ✅ Forces progressive abstraction (code → patterns → architecture)
- ✅ Better for context health on large extractions (>3k lines)

**Trade-offs:**
- ❌ Additional orchestration complexity
- ❌ Slight overhead from sub-agent invocation
- ❌ Pattern synthesis must bridge across separate investigation contexts

**When to switch mid-extraction**: If you started with direct reading but context is becoming strained after 2 iterations, switch to delegated approach for remaining iterations. Document the switch in progress file.

**After all iterations complete**: Proceed to step 3.6 (Human Priority Review) with the synthesized patterns document.

---

## Phase 4: Critical Review & Deliverable Scoping

### 4.1 Review Pattern Documentation

Read all pattern files (may be split across multiple files from Phase 3):

Ask these questions:
- Is output **descriptive** ("here's what exists") or **prescriptive** ("here's how to build")?
- Can someone use this to implement similar architecture?
- Are reusable abstractions clearly identified?
- Is there a clear "getting started" path?
- What is the distribution of CRITICAL vs PREFERRED vs OBSERVED patterns?

### 4.2 Determine Additional Deliverables Using Priority Classifications

Based on review and validated priorities from Phase 3 checkpoint, decide what to create (see `references/documentation_patterns.md`):

**Use priority classifications to scope deliverables:**
- **CRITICAL patterns** (must be in guide) - Deep coverage with rationale
- **PREFERRED patterns** (maybe in guide) - Light coverage or references
- **OBSERVED patterns** (references/ only) - Available for deeper dives

**If patterns are loosely coupled and independently useful:**
- Primary: Pattern Catalog (already created)
- Optional: Quick reference guide

**If architecture should be replicated:**
- Primary: Prescriptive Guide (workflow-based)
- Secondary: Reference Implementation (if code is reusable)

**If creating a framework/library:**
- Primary: Prescriptive Guide + Reference Implementation
- Secondary: Pattern Catalog in references/

### 4.3 Plan Refinement Work

Create task list for deliverables:
- Prescriptive guide creation (if needed)
- Reference implementation extraction (if needed)
- Token optimization pass
- Process documentation

### 4.4 CRITICAL: Choose Output Format (CHECKPOINT)

**This checkpoint prevents deliverable rework.** Format choice (Shared Reference vs Claude Skill) affects deliverable structure fundamentally.

Present options to user:

```
Pattern analysis complete! Before creating additional deliverables, please choose output format:

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

**Why this matters**: Affects directory structure, file organization, and documentation format for all deliverables created in Phase 5.

---

## Phase 5: Refinement

Transform descriptive findings into prescriptive guidance and/or reference implementation.

**Priority-driven approach:** Focus deliverables on CRITICAL patterns (from Phase 3 checkpoint), with light coverage of key PREFERRED patterns. OBSERVED patterns stay in references/ for on-demand loading.

### 5.1 Create Prescriptive Guide (if applicable)

**Structure** (see `references/documentation_patterns.md` for details):
- **Quick Start**: "Copy these files, follow this structure"
- **Core Concepts**: Explain foundational abstractions with "why"
- **Step-by-step workflow**: "Building Your First X" (7-10 steps)
- **Key Design Decisions**: Configuration choices, trade-offs, rationale
- **Advanced Patterns**: Multi-phase workflows, composition strategies
- **Resources**: Point to reference implementation, pattern catalog

**Pattern coverage:**
- **CRITICAL patterns**: Deep coverage with full rationale
- **PREFERRED patterns**: Light mention or brief coverage
- **OBSERVED patterns**: Omit (stay in references/)

**Writing guidelines:**
- Use imperative/infinitive form (not second person)
- Use file references instead of inline code: `See path/to/file.py:line-range`
- Include "why" and "when" for all design decisions
- Document anti-patterns and trade-offs
- Keep lean via progressive disclosure (detailed info in references/)

**Mark ambiguities for Phase 5 checkpoint:**
- Add `[TODO: WHY?]` markers where design rationale is unclear
- Add `[TODO: PRINCIPLE?]` where guiding philosophy should be explained
- Focus markers on CRITICAL design decisions
- Claude cannot infer: production experience, historical context, trade-off reasoning

### 5.2 Create Reference Implementation (if applicable)

**Focus on CRITICAL patterns:** Reference implementation should demonstrate all CRITICAL patterns plus select key PREFERRED patterns.

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
- Build minimal but complete example demonstrating CRITICAL patterns
- Token-efficient: Use TODO comments instead of full implementation
- Self-documenting: Add "PATTERN DEMONSTRATED", "KEY CONCEPTS", "WHEN TO USE" sections to docstrings
- Include minimal README (structure tree + key patterns, no usage examples)

**Mark ambiguities for Phase 5 checkpoint:**
- Add `# TODO: Why this approach?` comments where rationale is unclear
- Focus on CRITICAL design decisions in core abstractions

### 5.3 Update Pattern Catalog (if applicable)

If created prescriptive guide and/or reference implementation:
- Keep pattern catalog as research documentation
- Move to `references/` directory for on-demand loading
- Update guide to reference patterns as needed

### 5.4 Human Collaboration - Principles & Rationale (CHECKPOINT)

Gather human insight on design rationale that Claude cannot infer from code alone. This phase transforms descriptive pattern documentation into prescriptive architectural guidance with deep "why" explanations.

**Why this checkpoint is essential:**

Claude can observe patterns in code, but cannot infer:
- Why this approach was chosen over alternatives
- What production experience motivated decisions
- What trade-offs were considered
- What guiding principles inform the architecture
- What historical context or business requirements drove choices

This knowledge is critical for creating guides that enable confident pattern replication and skill conversion.

**Process:**

1. **Present marked deliverables to human collaborator**

Show guide and/or reference implementation with TODO markers from steps 5.1-5.2.
Frame each marker as an architectural question requiring human expertise.

**Expected markers:** ~10-15 for complex extraction, focused on CRITICAL patterns

2. **Human provides architectural context**

For each marker, explain:
- **Design rationale**: Why X over Y (not just "X is better")
- **Trade-offs**: What was gained, what was sacrificed
- **Guiding principles**: Philosophy that informed the decision
- **Production experience**: "We tried A, had problems, switched to B"
- **Historical context**: "Built this way because [business constraint]"
- **When to deviate**: Scenarios where this guidance doesn't apply

3. **Incorporate feedback**

- Replace TODO markers with human-provided explanations
- Add "Design Principles" or "Guiding Philosophy" section if patterns emerged
- Enhance "when to use" / "when NOT to use" guidance with trade-off reasoning
- Update pattern catalog in references/ if additional context needed

4. **Verify completeness**

Present updated deliverables to human:
- "I've incorporated your rationale for all N markers"
- "Are there other design decisions that need 'why' explanations?"
- Iterate once if needed (rarely required)

**Expected efficiency:**
- 10-15 focused questions (if Phase 3 priority classification used effectively)
- 30-45 minutes of human time
- Single collaboration session (no back-and-forth needed)

**Quality impact:**

Transforms output from "here's what the code does" to "here's why it's built this way and when you should replicate it." This depth is essential for guides targeting AI-consumable skill conversion.

### 5.5 Token Optimization

Eliminate duplication and optimize for AI consumption.

**Identify Duplication:**
Common duplication sources:
- Inline code examples in guide that duplicate reference implementation
- Usage examples in READMEs that duplicate guide content
- Pattern descriptions in multiple locations

**Apply File References:**
Replace inline code examples with file references:
- Before: Multi-line code block in guide
- After: `See reference_implementation/path/to/file.py:line-range for [example type]`

**Token savings**: ~15-20 lines per example → ~200-300 lines in typical guide

**Enhance Docstrings:**
Make reference implementation self-teaching:
- Add module-level docstrings with "PATTERN DEMONSTRATED" sections
- Include "KEY CONCEPTS", "WHEN TO USE THIS PATTERN", "DESIGN CHOICE" sections
- Explain rationale directly in code
- Reference guide sections as needed

**Trim READMEs:**
Keep minimal READMEs:
- Directory structure tree
- Key patterns demonstrated (bullet points with file references)
- Remove usage examples (guide covers this)

**Progressive Disclosure:**
Ensure lean main documents:
- Guide: 350-500 lines for SKILL.md, 400-650 for standalone
- Pattern catalog in references/ if large (>500 lines)
- Detailed documentation on-demand

**Outcome**: 25-30% token reduction while improving clarity

---

## Phase 6: Finalize & Deliver

### 6.1 Process Documentation

Capture lessons learned and document process for future extractions.

**Complete Phase Summaries**

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

**Document Lessons Learned**

Capture insights in progress file:
- What worked better than expected
- What was more difficult than anticipated
- Process improvements for next time
- Decisions that should be codified

### 6.2 Format & Deliver Based on Phase 4 Choice

**If User Chose Shared Reference (Format Choice from Phase 4)**

1. **Check for FORMAT.md**:
   ```
   Looking for .agents/FORMAT.md...
   ```

   - If found: Read `.agents/FORMAT.md` completely
   - If not found:
     ```
     No .agents/FORMAT.md found in this repository.

     Options:
     [a] Generate FORMAT.md based on Claude Skills specification
         (I'll create one for this repo)
     [b] Create Claude Skill format instead

     What would you like? [a/b]
     ```

2. **If user chooses to generate FORMAT.md**:
   - Load skill-creator skill to understand Claude Skills specification
   - Generate FORMAT.md adapted for AI-agnostic references
   - Write to .agents/FORMAT.md
   - Then proceed with transformation

3. **Follow FORMAT.md instructions**:
   - Read FORMAT.md to understand requirements
   - Transform extraction output to match specification
   - Organize into .agents/<reference-name>/

4. **Inform user**:
   ```
   Reference created at .agents/<reference-name>/

   Next steps:
   - Review the reference
   - Commit to git for team sharing
   - Convert to Claude Skill with reference-skill-converter (if desired)
   ```

**If User Chose Claude Skill (Format Choice from Phase 4)**

1. **Invoke skill-creator skill**:
   ```
   Loading skill-creator skill...
   ```

2. **Let skill-creator handle workflow**:
   - skill-creator reads extraction output
   - skill-creator follows its own workflow (metadata gathering, SKILL.md generation)
   - skill-creator asks any questions it needs
   - skill-creator organizes final output

3. **Completion**:
   ```
   [skill-creator completes its workflow]

   Skill created. Ready to use!
   ```

### 6.3 Update Progress File

Mark Phase 6 complete with chosen format and output location.

### 6.4 Final Deliverables Review

Present complete set of deliverables to user.

**Summarize Output**

List all deliverables created:
- Pattern catalog (if created)
- Prescriptive guide (if created)
- Reference implementation (if created)
- Progress file with comprehensive process documentation

**Explain Structure**

Show output directory structure based on format choice.

**Highlight Key Insights**

Summarize most important findings:
- Core architectural patterns identified
- Reusable abstractions extracted
- Design principles and rationale
- Process lessons learned

**Suggest Next Steps**

Based on deliverables:
- Review and validation by domain expert
- Testing reference implementation
- Skill conversion (if appropriate)
- Distribution to team

---

## Decision Trees

### When to Use Direct vs Delegated Investigation

```
Calculate total lines from file inventory
    ↓
≤ 3,000 lines?
    ↓
YES → Use Direct Reading
    - Main session reads files
    - Document patterns directly
    - 1-2 iterations typical
    ↓
NO → Use Delegated Investigation
    - codebase-researcher per iteration
    - Main session synthesizes findings
    - Better context health for large extractions
    ↓
UNCERTAIN (around 3k threshold)?
    - Start with direct reading (2 iterations)
    - If context strained, switch to delegation
    - Document switch in progress file
```

### When to Create Guide vs Catalog vs Reference Implementation

```
Review pattern catalog (Phase 4)
    ↓
Can architecture be replicated?
    ↓
NO → Pattern Catalog Only
    - Loosely coupled patterns
    - Descriptive documentation
    - Quick reference focus
    ↓
YES → Create Prescriptive Guide
    - "How to build" narrative
    - CRITICAL patterns with rationale
    - Step-by-step workflow
    ↓
Is code reusable?
    ↓
NO → Guide Only
    - Workflow-based guide
    - File references to examples
    - PREFERRED patterns as needed
    ↓
YES → Guide + Reference Implementation
    - Domain-agnostic core/
    - Instructive example/
    - Self-documenting code
    - Token-optimized guide (file references)
```

### Human Collaboration Checkpoints

```
CHECKPOINT 1: Iteration Plan Approval (Phase 2)
    - Present iteration strategy
    - Wait for approval
    - Purpose: Alignment before heavy work
    ↓
CHECKPOINT 2: Priority Review (Phase 3)
    - Present pattern classifications
    - Human adjusts CRITICAL/PREFERRED/OBSERVED
    - Purpose: Focus later phases on what matters
    ↓
CHECKPOINT 3: Format Choice (Phase 4)
    - Shared Reference OR Claude Skill
    - Document choice in progress
    - Purpose: Prevent deliverable rework
    ↓
CHECKPOINT 4: Design Rationale (Phase 5)
    - Present TODO markers (10-15)
    - Human provides "why" context
    - Purpose: Transform descriptive → prescriptive
```

---

## Common Patterns & Anti-Patterns

### Loading entire codebase at once
❌ **Anti-pattern**: Reading all files into context simultaneously
✅ **Pattern**: Use Explore agent for survey, then iterative analysis in ~1500 line batches

### Creating descriptive catalog when prescriptive guide needed
❌ **Anti-pattern**: Documenting "what exists" when goal is "how to build"
✅ **Pattern**: Phase 4 critical review assesses if output matches goals, creates guide if needed

### Inline code duplication
❌ **Anti-pattern**: Same code examples in guide and reference implementation
✅ **Pattern**: Phase 5 token optimization replaces inline code with file references

### Domain-specific abstractions in "core" code
❌ **Anti-pattern**: Python-specific exceptions in generic core package
✅ **Pattern**: Ensure core abstractions are generic, move domain-specific code to examples

### Forgetting to update progress file
❌ **Anti-pattern**: Batching updates, waiting until phase end
✅ **Pattern**: Update after EACH iteration/phase completion immediately

### Skipping rationale documentation
❌ **Anti-pattern**: Documenting only "what" without "why"
✅ **Pattern**: Always document design decisions, trade-offs, and when to deviate

### Analysis without iteration plan
❌ **Anti-pattern**: Starting analysis without planning file batches
✅ **Pattern**: Complete Phase 2 reconnaissance fully before starting analysis
