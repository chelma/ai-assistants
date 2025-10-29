---
name: task-planning
description: This skill should ONLY be invoked when the user explicitly mentions "task planning" or "task-planning" in their request (e.g., "use task planning", "help me with task-planning", "set up task planning workflow"). Do NOT use this skill for general planning requests like "help me plan this feature" or "create a plan for X" - those should use Claude's built-in planning mode. This skill establishes the .agents/ directory workflow for structured planning across sessions.
---

# Task Planning

## Overview

This skill helps establish and maintain a structured planning workflow in git repositories. It creates a `.agents/` directory structure that separates planning from implementation, enabling efficient context management across multiple Claude Code sessions.

**When to use this skill:** Only when the user explicitly mentions "task planning" or "task-planning" in their request. Do NOT use for general planning requests - those should use Claude's built-in planning mode.

## Workflow Decision Tree

When this skill is invoked, follow this decision tree:

1. **Check if `.agents/` directory exists**
   - If NO → Go to "First-Time Setup"
   - If YES → Go to "Validate Structure"

2. **Validate Structure**
   - Check for: `.agents/README.md`, `.agents/templates/`, `.agents/tasks/`
   - If structure matches expected pattern → Go to "Reconcile Templates"
   - If structure is wildly different → Go to "Handle Unexpected Structure"

3. **Reconcile Templates**
   - Compare local files with canonical versions
   - If differences exist → Go to "Template Reconciliation"
   - If no differences → Go to "Create New Plan"

4. **Create New Plan**
   - Interactive plan creation workflow

## First-Time Setup

When no `.agents/` directory exists, create the complete structure:

1. **Create directory structure:**
   ```
   .agents/
   ├── README.md
   ├── tasks/
   └── templates/
       ├── plan_template.md
       └── implementation_template.md
   ```

2. **Copy canonical files from skill assets:**
   - Copy `assets/README.md` to `.agents/README.md`
   - Copy `assets/templates/plan_template.md` to `.agents/templates/plan_template.md`
   - Copy `assets/templates/implementation_template.md` to `.agents/templates/implementation_template.md`

3. **Inform the user:**
   ```
   Created .agents/ directory structure for task planning:
   - README.md: Explains the planning workflow
   - templates/: Contains plan and implementation templates
   - tasks/: Will contain your plan and implementation tracking files

   Ready to create your first plan!
   ```

4. **Proceed to "Create New Plan"**

## Handle Unexpected Structure

If `.agents/` exists but doesn't match the expected pattern:

1. **Stop and explain the situation:**
   ```
   I found a .agents/ directory, but it doesn't match the expected structure for this task planning workflow.

   Expected structure:
   - .agents/README.md
   - .agents/templates/plan_template.md
   - .agents/templates/implementation_template.md
   - .agents/tasks/

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

1. **Read local files:**
   - `.agents/README.md`
   - `.agents/templates/plan_template.md`
   - `.agents/templates/implementation_template.md`

2. **Compare with canonical versions** (from skill assets)

3. **For each file with differences:**

   a. **Summarize the differences** (don't show full diffs unless requested):
   ```
   Your local README.md differs from the canonical version:
   - Local version has a "Dependencies" section not in canonical
   - Canonical version has updated language in "Key Principles"
   - Formatting differences in "Workflow" section
   ```

   b. **Offer reconciliation options:**
   ```
   How would you like to handle these differences?
   1. Keep local version (no changes)
   2. Use canonical version (replace local)
   3. Show me the full diff
   4. Help me merge (I'll guide you through sections that differ)
   ```

   c. **If user chooses "Show me the full diff":**
   - Display both versions side-by-side or in a clear comparison format
   - Then re-offer the reconciliation options

   d. **If user chooses "Help me merge":**
   - Identify specific sections that differ
   - For each section, show both versions and ask which to keep
   - Create merged version based on user choices
   - Write the merged version to the local file

4. **After reconciliation is complete,** proceed to "Create New Plan"

## Create New Plan

Interactive workflow to create a new plan file:

### Step 1: Gather Information

Ask the user these questions one at a time (don't overwhelm with all at once):

1. **Task description:**
   ```
   What task or feature would you like to plan?
   ```

2. **GitHub/JIRA issue:**
   ```
   Is there a GitHub or JIRA issue for this task? (Paste the link or say "N/A")
   ```

3. **Problem statement:**
   ```
   What problem does this task address? (1-2 sentences)
   ```

4. **Acceptance criteria:**
   ```
   What are the key acceptance criteria? (I'll format these as checkboxes)
   ```

### Step 2: Suggest Task Name

Based on the user's task description, suggest a file name:

```
Based on your description, I suggest naming this plan:
  tasks/add_authentication_plan.md

Does this work, or would you prefer a different name?
```

Wait for confirmation or alternative name.

### Step 3: Explore Codebase (if applicable)

If the task involves code changes:

```
Let me explore the codebase to understand the current state...
```

Use Task tool with subagent_type=Explore or appropriate search tools to gather context about:
- Existing patterns and architecture
- Related files and components
- Dependencies and integration points

Document findings for the "Current State Analysis" section.

### Step 4: Create Draft Plan

1. **Read the plan template:**
   - Read `.agents/templates/plan_template.md`

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

### Step 5: Iterative Refinement

Remain available for iterative refinement of the plan:

- Answer questions about the proposed approach
- Explore additional codebase areas as needed
- Revise implementation steps based on user feedback
- Add more detail to specific sections
- Consider alternative approaches

Update the plan file as the conversation progresses using the Edit tool.

### Step 6: Finalization

When the user is satisfied:

```
Your plan is ready! When you're ready to mark it as "approved", edit the Status field in the plan file.

To implement this plan:
1. Start a fresh Claude Code session (optimizes context)
2. Reference the plan file: .agents/tasks/<task_name>_plan.md
3. Ask Claude to begin implementation following the plan

Claude will create a <task_name>_implement.md file to track progress and will pause after each implementation step for your review.
```

## Key Principles

When using this skill, follow these principles:

### For File Reconciliation:
- **Never modify files under `.agents/tasks/`** - these contain user's work-in-progress
- **Only reconcile** README.md and template files
- **Always get user input** before replacing local files with canonical versions
- **Preserve user customizations** when merging

### For Plan Creation:
- **Always prompt for GitHub/JIRA issue** if not provided initially
- **Thoroughly explore codebase** before suggesting implementation approach
- **Be specific in implementation steps** - actionable, ordered, clear
- **Consider risks and edge cases** - better to identify issues during planning
- **Create draft plans** - user should review and approve before implementation

### For Implementation (Not handled by this skill):
This skill only handles planning. Implementation follows in a separate session where:
- User references the approved plan
- Claude creates `tasks/<task_name>_implement.md` to track progress
- Claude follows the plan steps, stopping after each for human review
- Implementation details are documented in the implement file

## Assets

This skill includes canonical versions of the planning workflow files:

- `assets/README.md` - Explains the .agents/ workflow to users and future Claude sessions
- `assets/templates/plan_template.md` - Template structure for planning documents
- `assets/templates/implementation_template.md` - Template structure for tracking implementation progress

These files are copied to new `.agents/` directories and used for reconciliation when local versions differ.
