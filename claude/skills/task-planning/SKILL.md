---
name: task-planning
description: This skill should ONLY be invoked when the user explicitly mentions "task planning" or "task-planning" in their request (e.g., "use task planning", "help me with task-planning", "set up task planning workflow"). Do NOT use this skill for general planning requests like "help me plan this feature" or "create a plan for X" - those should use Claude's built-in planning mode. This skill establishes the .claude/agents/ directory workflow for structured planning across sessions.
---

# Task Planning

## Overview

This skill helps establish and maintain a structured planning workflow in git repositories. It creates a `.claude/agents/` directory structure that separates planning from implementation, enabling efficient context management across multiple Claude Code sessions.

**When to use this skill:** Only when the user explicitly mentions "task planning" or "task-planning" in their request. Do NOT use for general planning requests - those should use Claude's built-in planning mode.

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
  - .claude/agents/tasks/GH-123-add_authentication_plan.md
  - .claude/agents/tasks/GH-123-add_authentication_progress.md (during implementation)
  - .claude/agents/output/GH-123-add_authentication/ (for deliverables)

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

1. **Ensure directory structure exists:**
   - Create `.claude/agents/tasks/` if it doesn't exist
   - Create `.claude/agents/output/` if it doesn't exist

2. **Read the plan template from skill assets:**
   - Read `claude/skills/task-planning/assets/templates/plan_template.md` from the repository

3. **Fill in the template** with:
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

4. **Write the plan file:**
   - Write to `.claude/agents/tasks/<task_name>_plan.md`

5. **Inform the user:**
   ```
   Created draft plan at: .claude/agents/tasks/<task_name>_plan.md

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
2. Reference the plan file: .claude/agents/tasks/<task_name>_plan.md
3. Ask Claude to begin implementation following the plan

Claude will create a <task_name>_progress.md file to track progress and will pause after each implementation step for your review.
```

## Key Principles

When using this skill, follow these principles:

### For Plan Creation:
- **Always prompt for GitHub/JIRA issue** if not provided initially
- **Thoroughly explore codebase** before suggesting implementation approach
- **Be specific in implementation steps** - actionable, ordered, clear
- **Consider risks and edge cases** - better to identify issues during planning
- **Create draft plans** - user should review and approve before implementation

### For Implementation (Not handled by this skill):
This skill only handles planning. Implementation follows in a separate session where:
- User references the approved plan
- Claude creates `.claude/agents/tasks/<task_name>_progress.md` to track progress
- Claude follows the plan steps, stopping after each for human review
- Implementation details are documented in the progress file
- Task deliverables and artifacts are written to `.claude/agents/output/<task_name>/` directory

## Assets

This skill includes template files used for creating plans and tracking progress:

- `assets/templates/plan_template.md` - Template structure for planning documents
- `assets/templates/progress_template.md` - Template structure for tracking implementation progress

These templates are read directly from the skill assets directory when creating new plans. Working files (plans, progress, outputs) are stored in `.claude/agents/` which is git-ignored and engineer-specific.
