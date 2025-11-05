---
name: task-planning
description: This skill should ONLY be invoked when the user explicitly mentions "task planning" or "task-planning" in their request (e.g., "use task planning", "help me with task-planning", "set up task planning workflow"). Do NOT use this skill for general planning requests like "help me plan this feature" or "create a plan for X" - those should use Claude's built-in planning mode. This skill establishes the .agents/ directory workflow for structured planning across sessions.
---

# Task Planning

## Overview

This skill helps establish and maintain a structured planning workflow in git repositories. It creates a `.agents/` directory structure that separates planning from implementation, enabling efficient context management across multiple Claude Code sessions.

**When to use this skill:** Only when the user explicitly mentions "task planning" or "task-planning" in their request. Do NOT use for general planning requests - those should use Claude's built-in planning mode.

**Current Version:** 3

**Version History:**
- **v0**: Legacy (pre-versioning) - no task prefixes, `*_implement.md` files
- **v1**: Partial updates (some prefixes or progress naming adopted)
- **v2**: Task prefixes, `*_progress.md` files, output directory, `progress_template.md`
- **v3**: Added resumability guidance, skill improvement tracking, phase outcome patterns (README sections + template comments)

## Workflow Decision Tree

When this skill is invoked, follow this decision tree:

1. **Check if `.agents/` directory exists**
   - If NO → Go to "First-Time Setup"
   - If YES → Go to "Check Version"

2. **Check Version**
   - Read `.agents/.version` file (if missing, treat as v0 - legacy)
   - Compare local version with skill version (currently v3)
   - If `local_version < skill_version` → Go to "Offer Migration"
   - If `local_version == skill_version` → Go to "Validate Structure"
   - If `local_version > skill_version` → Warn user (they're ahead, unexpected)

3. **Validate Structure**
   - Check for: `.agents/README.md`, `.agents/templates/`, `.agents/tasks/`
   - If structure matches expected pattern → Go to "Reconcile Templates"
   - If structure is wildly different → Go to "Handle Unexpected Structure"

4. **Reconcile Templates**
   - Compare local files with canonical versions
   - If differences exist → Go to "Template Reconciliation"
   - If no differences → Go to "Create New Plan"

5. **Create New Plan**
   - Interactive plan creation workflow

## First-Time Setup

When no `.agents/` directory exists, create the complete structure:

1. **Create directory structure:**
   ```
   .agents/
   ├── .version
   ├── README.md
   ├── tasks/
   ├── templates/
   │   ├── plan_template.md
   │   └── progress_template.md
   └── output/
   ```

2. **Copy canonical files from skill assets:**
   - Copy `assets/.version` to `.agents/.version` (contains: 2)
   - Copy `assets/README.md` to `.agents/README.md`
   - Copy `assets/templates/plan_template.md` to `.agents/templates/plan_template.md`
   - Copy `assets/templates/progress_template.md` to `.agents/templates/progress_template.md`

3. **Inform the user:**
   ```
   Created .agents/ directory structure for task planning (v2):
   - .version: Tracks structure version
   - README.md: Explains the planning workflow
   - templates/: Contains plan and progress templates
   - tasks/: Will contain your plan and progress tracking files
   - output/: Will contain task deliverables and artifacts

   Ready to create your first plan!
   ```

4. **Proceed to "Create New Plan"**

## Offer Migration

When local version is older than skill version:

1. **Determine version gap:**
   - Read local version from `.agents/.version` (or 0 if missing)
   - Current skill version: 2
   - Calculate migration path needed (e.g., v0→v2, v1→v2)

2. **Load migration guidance:**
   - Load detailed guidance: `references/migration.md`
   - Follow version-specific migration workflow
   - Migration guide contains paths for each version jump

3. **Key principles** (details in migration.md):
   - Always create backup before changes
   - Never modify file contents (only rename/restructure)
   - Offer migration but allow user to decline
   - Update `.version` file after successful migration
   - Report all changes made

## Handle Unexpected Structure

If `.agents/` exists but doesn't match the expected pattern:

1. **Stop and explain the situation:**
   ```
   I found a .agents/ directory, but it doesn't match the expected structure for this task planning workflow.

   Expected structure:
   - .agents/.version
   - .agents/README.md
   - .agents/templates/plan_template.md
   - .agents/templates/progress_template.md
   - .agents/tasks/
   - .agents/output/

   Current structure:
   [List what actually exists]

   How would you like to proceed?
   1. Rename existing .agents/ to .agents.backup/ and create new structure
   2. Merge the structures (I'll help adapt the canonical templates)
   3. Skip setup and just create a plan file in the existing structure
   4. Cancel and investigate manually
   ```

2. **Wait for user decision** and follow their guidance.

## Template Reconciliation

When local templates differ from canonical versions:

1. **Identify files to reconcile:**
   - `.agents/README.md`
   - `.agents/templates/plan_template.md`
   - `.agents/templates/implementation_template.md`

2. **Compare with canonical versions** from skill assets

3. **If differences exist:**
   - Load detailed guidance: `references/reconciliation.md`
   - Follow the workflow documented there for summarizing differences, offering options, and performing merges

4. **After reconciliation is complete,** proceed to "Create New Plan"

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

### Step 3: Confirm Task Name

Based on the user's task description and prefix, suggest a task name:

```
Based on your description, I'll name this task:
  <PREFIX>-<descriptive_name>

For example:
  - GH-123-add_authentication (if GitHub issue #123)
  - PROJ-456-refactor_api (if JIRA ticket PROJ-456)
  - 2025-10-31-optimize_queries (if no tracking ID)

This will create:
  - tasks/GH-123-add_authentication_plan.md
  - tasks/GH-123-add_authentication_progress.md (during implementation)
  - output/GH-123-add_authentication/ (for deliverables)

Does this naming work for you, or would you prefer a different name?
```

**Important:** The task name includes the prefix - it's not a separate entity. Use the full task name everywhere (files, output directory, references).

Wait for confirmation or alternative name before proceeding.

### Step 4: Explore Codebase (if applicable)

If the task involves code changes:

```
Let me explore the codebase to understand the current state...
```

**Code/Documentation Scanning Guidance:**
When scanning large amounts of code or documentation to extract patterns, architecture, or context:
- **Default chunk size:** Target ~1500 lines of code/text per chunk
- **Confirm with user:** Before proceeding with chunked scanning, confirm this chunk size works for their needs
- **Scope limitation:** This guidance applies ONLY to pulling content into the context window of THIS session (the one running task-planning skill), NOT to sub-agents like the Explore agent which manage their own context

Use Task tool with subagent_type=Explore or appropriate search tools to gather context about:
- Existing patterns and architecture
- Related files and components
- Dependencies and integration points

Document findings for the "Current State Analysis" section.

**If reconnaissance reveals extensive investigation needed** (multiple complex modules, >3k lines to understand, architectural patterns to extract), consider using the codebase-researcher subagent for deeper investigation before finalizing plan. This prevents planning based on incomplete understanding and keeps main session context healthy.

### Step 5: Create Draft Plan

1. **Read the templates:**
   - Read `.agents/templates/plan_template.md`
   - Read `.agents/templates/progress_template.md` (for reference)

2. **Fill in the template** with:
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

3. **Write the plan file:**
   - Write to `.agents/tasks/<task_name>_plan.md`

4. **Inform the user:**
   ```
   Created draft plan at: .agents/tasks/<task_name>_plan.md

   The plan includes:
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

### Step 6: Iterative Refinement

Remain available for iterative refinement of the plan:

- Answer questions about the proposed approach
- Explore additional codebase areas as needed
- Revise implementation steps based on user feedback
- Add more detail to specific sections
- Consider alternative approaches

Update the plan file as the conversation progresses using the Edit tool.

### Step 7: Finalization

When the user is satisfied:

```
Your plan is ready! When you're ready to mark it as "approved", edit the Status field in the plan file.

To implement this plan:
1. Start a fresh Claude Code session (optimizes context)
2. Reference the plan file: .agents/tasks/<task_name>_plan.md
3. Ask Claude to begin implementation following the plan

Claude will create a <task_name>_progress.md file to track progress and will pause after each implementation step for your review.
```

## Key Principles

When using this skill, follow these principles:

### For File Reconciliation and Migration:
- **Never modify files under `.agents/tasks/`** - these contain user's work-in-progress
- **Only reconcile** README.md and template files
- **Always get user input** before replacing local files with canonical versions
- **Preserve user customizations** when merging
- **Detect and offer migration** when encountering previous versions of `.agents/` structure
- **Future-proof migrations**: When the user requests changes to artifact structure:
  - Update this skill's guidance with new migration path
  - Add detection logic for the old convention
  - Document what NOT to modify (typically file contents, only structure/naming)
  - Always create backups before performing migrations

### For Plan Creation:
- **Always prompt for GitHub/JIRA issue** if not provided initially
- **Thoroughly explore codebase** before suggesting implementation approach
- **Be specific in implementation steps** - actionable, ordered, clear
- **Consider risks and edge cases** - better to identify issues during planning
- **Create draft plans** - user should review and approve before implementation

### For Implementation (Not handled by this skill):
This skill only handles planning. Implementation follows in a separate session where:
- User references the approved plan
- Claude creates `tasks/<task_name>_progress.md` to track progress
- Claude follows the plan steps, stopping after each for human review
- Implementation details are documented in the progress file
- Task deliverables and artifacts are written to `output/<task_name>/` directory

## Assets

This skill includes canonical versions of the planning workflow files:

- `assets/README.md` - Explains the .agents/ workflow to users and future Claude sessions
- `assets/templates/plan_template.md` - Template structure for planning documents
- `assets/templates/progress_template.md` - Template structure for tracking implementation progress

These files are copied to new `.agents/` directories and used for reconciliation when local versions differ.

## References

Detailed guidance loaded on-demand for specific scenarios:

- `references/migration.md` - **Load when:** Detecting old `.agents/` structure that needs migration. Provides step-by-step migration workflows for each version upgrade path.
- `references/reconciliation.md` - **Load when:** Local template files differ from canonical versions. Provides interactive reconciliation workflow with multiple merge strategies.

**Progressive loading pattern:** The main SKILL.md contains workflow logic and decision points. References contain detailed "how-to" guidance loaded only when needed, keeping context efficient.

## Versioning Philosophy

Version increments signal substantive changes to skill capability, guidance, or structure. Changes warranting version bumps include:
- New sections in README or templates
- Structural changes to `.agents/` layout
- Workflow or philosophical shifts
- Coordinated improvements that evolve skill capability

Typo fixes, minor clarifications, and single-example additions typically don't warrant version bumps.

**When in doubt:** If users should review the changes, bump the version.
