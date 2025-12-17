---
name: tag-team
description: Collaborative pair programming workflow where Claude and user work together on substantive tasks through planning and implementation phases. ONLY invoke when user explicitly says "tag-team" - this is a user-initiated workflow, not for general requests. Establishes ~/.claude/workspace/ structure for version-controlled task tracking with portable file references.
---

# Tag Team

## Overview

This skill establishes a collaborative pair programming workflow for substantive engineering tasks. It creates working files in `~/.claude/workspace/<workspace>/` (symlinked to ai-assistants repo for version control) that track both planning and implementation, enabling extended collaboration across multiple Claude Code sessions.

**When to use this skill:** ONLY when the user explicitly says "tag-team". This is a user-initiated workflow for substantive collaborative work, not for general requests or quick tasks.

**Key characteristics:**
- Working files stored in `~/.claude/workspace/<workspace>/` for version control and cross-machine sync
- Automatic workspace detection from git repo name (or asks user if not in git repo)
- Project root tracking enables portable file references (relative to project root)
- Lazy directory creation (only when actually writing files)

## Workflow

When this skill is invoked, proceed directly to plan creation. The skill will create necessary directories as needed.

## Create New Plan

Interactive workflow to create a new plan file:

### Step 1: Gather Information

Ask the user these questions one at a time (don't overwhelm with all at once):

1. **Task description:**
   ```
   What task or feature would you like to plan?
   ```

2. **GitHub/JIRA/Ticket ID:**
   ```
   Is there a GitHub issue, JIRA ticket, or other tracking ID for this task?
   - If yes: Provide the ID (e.g., "GH-123", "PROJ-456", "ticket-789")
   - If no: I'll use a timestamp prefix (YYYY-MM-DD format)
   ```

3. **Problem statement:**
   ```
   What problem does this task address? (1-2 sentences)
   ```

4. **Acceptance criteria:**
   ```
   What are the key acceptance criteria? (I'll format these as checkboxes)
   ```

### Step 2: Construct Task Name

Based on the issue/ticket ID response, construct the full task name:

- **If issue/ticket ID provided:** `<ISSUE-ID>-<description>` (e.g., `GH-123-add_authentication`)
- **If no issue/ticket ID:** `<YYYY-MM-DD>-<description>` (e.g., `2025-10-31-add_authentication`)

**Key concept:** The task name is complete - it includes both the prefix and description as one entity. This full task name will be used everywhere: file names, output directories, and all references.

### Step 3: Detect Workspace and Project Root

**Workspace Detection** (determines where files are stored):
```bash
WORKSPACE=$(basename $(git rev-parse --show-toplevel 2>/dev/null) 2>/dev/null)
```

- **If in git repo:** Use repo name as workspace (e.g., "time-cop")
- **If not in git repo:** Ask user: "What workspace name should I use for this task?"

**Project Root Detection** (for portable file references):
```bash
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
# If empty, use current working directory
```

Store both values - they will be included in plan file header and used for all file operations.

### Step 4: Confirm Task Name

Based on the user's task description and prefix, suggest a task name:

```
Based on your description, I'll name this task:
  <PREFIX>-<descriptive_name>

For example:
  - GH-123-add_authentication (if GitHub issue #123)
  - PROJ-456-refactor_api (if JIRA ticket PROJ-456)
  - 2025-10-31-optimize_queries (if no tracking ID)

This will create files in workspace '<workspace>' at:
  - ~/.claude/workspace/<workspace>/tasks/GH-123-add_authentication_plan.md
  - ~/.claude/workspace/<workspace>/tasks/GH-123-add_authentication_progress.md (during implementation)
  - ~/.claude/workspace/<workspace>/output/GH-123-add_authentication/ (for deliverables)

Does this naming work for you, or would you prefer a different name?
```

**Important:** The task name includes the prefix - it's not a separate entity. Use the full task name everywhere (files, output directory, references).

Wait for confirmation or alternative name before proceeding.

### Step 5: Explore Codebase (if applicable)

If the task involves code changes:

```
Let me explore the codebase to understand the current state...
```

**Code/Documentation Scanning Guidance:**
When scanning large amounts of code or documentation to extract patterns, architecture, or context:
- **Default chunk size:** Target ~1500 lines of code/text per chunk
- **Confirm with user:** Before proceeding with chunked scanning, confirm this chunk size works for their needs
- **Scope limitation:** This guidance applies ONLY to pulling content into the context window of THIS session (the one running tag-team skill), NOT to sub-agents like the Explore agent which manage their own context

Use Task tool with subagent_type=Explore or appropriate search tools to gather context about:
- Existing patterns and architecture
- Related files and components
- Dependencies and integration points

Document findings for the "Current State Analysis" section.

**If reconnaissance reveals extensive investigation needed** (multiple complex modules, >3k lines to understand, architectural patterns to extract), consider using the codebase-researcher subagent for deeper investigation before finalizing plan. This prevents planning based on incomplete understanding and keeps main session context healthy.

### Step 6: Create Draft Plan

1. **Read the plan template from skill assets:**
   - Read `./assets/templates/plan_template.md` (relative to this skill's directory)

2. **Fill in the template** with:
   - Workspace (from Step 3 detection)
   - Project Root (from Step 3 detection)
   - Task name (from user)
   - Status: "draft"
   - GitHub Issue (from user, or "N/A")
   - Created: Today's date (from <env>)
   - Problem Statement (from user)
   - Acceptance Criteria (from user, formatted as checkboxes)
   - Current State Analysis (from codebase exploration)
   - Proposed Solution (high-level approach)
   - Implementation Steps (ordered, specific steps)
   - Risks and Considerations (potential issues)
   - Testing Strategy (how to verify it works)

3. **Write the plan file with lazy directory creation:**
   ```bash
   mkdir -p ~/.claude/workspace/<workspace>/tasks/
   ```
   Then write to: `~/.claude/workspace/<workspace>/tasks/<task_name>_plan.md`

4. **File reference requirements:**
   - All file paths in the plan should be **relative to project root**
   - Example: `ruby_worker/app/workflows/workflow_demo_mixed.rb:15-30`
   - NOT: `/Users/chris.helma/workspace/personal/time-cop/ruby_worker/...`
   - When Claude reads plan files later, it combines Project Root + relative path to resolve files

5. **Inform the user:**
   ```
   Created draft plan at: ~/.claude/workspace/<workspace>/tasks/<task_name>_plan.md

   The plan includes:
   ✓ Workspace and project root metadata for portable file references
   ✓ Problem statement and acceptance criteria
   ✓ Current state analysis based on codebase exploration
   ✓ Proposed solution and implementation steps
   ✓ Risks and testing strategy

   Please review and edit the plan file. Here are some follow-up topics we could refine together:
   - Implementation step details
   - Risk mitigation strategies
   - Testing approach
   - Dependencies or prerequisites
   - Alternative approaches to consider

   What would you like to discuss or refine?
   ```

### Step 7: Iterative Refinement

Remain available for iterative refinement of the plan:

- Answer questions about the proposed approach
- Explore additional codebase areas as needed
- Revise implementation steps based on user feedback
- Add more detail to specific sections
- Consider alternative approaches

Update the plan file as the conversation progresses using the Edit tool.

### Step 8: Plan Approval

When the user is satisfied with the plan:

```
Your plan is ready!

Next steps:
1. Review the plan file and make any final edits
2. Mark the Status field as "approved" when ready
3. Begin implementation (can continue in this session or start fresh)

I'll create a progress file and follow the tag-team checkpoint pattern:
work → document → pause for review → continue.
```

## Key Principles

When using this skill, follow these principles:

### For Plan Creation:
- **Always prompt for GitHub/JIRA issue** if not provided initially
- **Thoroughly explore codebase** before suggesting implementation approach
- **Be specific in implementation steps** - actionable, ordered, clear
- **Consider risks and edge cases** - better to identify issues during planning
- **Create draft plans** - user should review and approve before implementation

### For Implementation:

Tag-team provides a collaboration framework that works across all task types. The key is the **checkpoint pattern**, not prescriptive steps.

**The Checkpoint Pattern** (fundamental rhythm):
```
DO WORK → DOCUMENT PROGRESS → PAUSE FOR REVIEW → CONTINUE
```

**Never automatically proceed** from one step to the next without human approval.

**Progress file is the authoritative state document.** It must contain:
- What's complete (checked boxes + outcome descriptions)
- Current state (what's in progress, what's blocked)
- Key decisions made with rationale
- Evolution and adaptations from plan (with reasoning - use positive framing)
- "Resume from Here" section updated at major milestones for cold resumption
- Enough detail to resume without conversation history

**CRITICAL**: Update progress file IMMEDIATELY after EACH phase/step completion (not in batches). Batched updates cause context strain and reduce resumability.

**When to pause for human review:**
- After each plan step (always)
- Before making significant architectural/design decisions not covered in plan
- When encountering blockers that prevent progress
- After discovering evolution/adaptations from approved plan (note: frame positively - changes are often quality-driven discoveries, not problems)
- At phase boundaries for multi-phase work

**Task structure flexibility:**

Choose the approach that fits your task type:

- **Linear step-by-step** (coding tasks, refactoring, migrations): Simple checklist with detailed notes per step
- **Phase-based** (research, extraction, analysis): Organized by phase with outcome summaries
- **Mixed/emergent**: Structure evolves during work based on discoveries

The checkpoint pattern applies regardless of structure choice.

**Living document pattern for iterative tasks:**

For tasks with many iterations (5+ iterations of file analysis, pattern extraction, etc.):
- **Write insights immediately to deliverable files** (e.g., patterns.md, guide.md)
- **Keep Progress file lean** with just tracking and outcomes
- **Don't accumulate findings in Progress** - this causes context bloat
- Enables higher iteration counts without context exhaustion
- Example: Analysis task with 9 iterations writing to python_style.md succeeded by keeping Progress minimal

**Task-type patterns:**

How to adapt the single progress template for different work:

**Implementation tasks** (step-by-step coding, refactoring, migrations):
- **Structure**: Linear checklist of steps from plan
- **Notes per step**: Files changed, tests run, decisions made
- **Testing**: Validate at each step boundary (prevents defect propagation)
- **Documentation focus**: Concrete outcomes (metrics, test results, file paths)
- **Example**: Protobuf centralization - 7 sequential steps, testing per step, 2 deviations (both improvements)

**Extraction/Research tasks** (architecture analysis, pattern extraction):
- **Structure**: Phase-based (reconnaissance → analysis → review → refinement → delivery)
- **Outcomes**: Summary per phase (what discovered, decisions, metrics)
- **Sections**: Add reconnaissance summary, iteration plan, priority classification
- **Documentation focus**: Patterns observed, design decisions, rationale
- **Human collaboration**: Per-iteration or at phase boundaries
- **Examples**: AWS/LangChain/Temporal extractions - 8-10 phases with outcome summaries, organic evolution (LangChain 3→8 phases was healthy discovery-driven adaptation)

**Analysis tasks** (high-iteration pattern analysis, style extraction):
- **Structure**: Phase-based with high iteration count (5-9+ iterations)
- **Critical**: Use living document pattern (write to deliverable, keep Progress lean)
- **Sections**: Add file inventory with checkboxes for tracking coverage
- **Collaboration**: Consider two-mode (autonomous extraction → human refinement)
- **Documentation focus**: Concrete specifics, systematic coverage
- **Example**: Python style analysis - 9 iterations across 174 files, file inventory, living document to python_style.md, two-mode collaboration proved highly efficient

**Don't force structure upfront**: Let it emerge based on discoveries. Mixed/hybrid structures are valid. The checkpoint pattern applies regardless of structure choice.

**Documentation depth at each checkpoint:**
- **Outcomes over actions** - "What was accomplished" not just "did step 3"
- **Rationale for decisions** - "Why we chose X over Y"
- **Concrete specifics** - File paths, line counts, test results, metrics
- **Lessons learned** - Gotchas, friction points, things harder than expected
- **"Resume from Here" section** - Update at major milestones with current state summary, key context, next priorities, and open questions (enables 10min cold resume vs 30-45min)

**Composability with specialized skills:**

For specialized tasks, invoke the relevant skill for detailed workflow:
- Architecture extraction → `extract-architecture` skill
- Deep codebase investigation → `codebase-researcher` subagent

Specialized skills build on tag-team's checkpoint and progress tracking framework. The progress file remains the state document regardless of workflow.

**Implementation workflow:**
1. Read the approved plan from `~/.claude/workspace/<workspace>/tasks/<task_name>_plan.md`
2. Create progress file using `assets/templates/progress_template.md` as starting point
3. For each step in the plan:
   - Execute the step
   - Document in progress file (detailed notes, not just checkboxes)
   - Write artifacts to `~/.claude/workspace/<workspace>/output/<task_name>/` if applicable
   - Pause and present progress to human
   - Wait for approval to continue
4. At completion: mark status as "completed", update all sections, capture lessons learned

**File reference requirements:**
- Use paths **relative to project root** in all plan and progress files
- Example: `ruby_worker/app/workflows/workflow.rb:15-30`
- NOT: `/Users/chris.helma/workspace/personal/...`
- Enables portability across machines and sessions

## Assets

This skill includes template files used for creating plans and tracking progress:

- `assets/templates/plan_template.md` - Template structure for planning documents
- `assets/templates/progress_template.md` - Template structure for tracking implementation progress

These templates are read directly from the skill assets directory when creating new plans. Working files (plans, progress, outputs) are stored in `~/.claude/workspace/<workspace>/`.
