# Claude Code Collaboration System

The `.agents/` directory enables structured collaboration between humans and Claude Code by separating planning from implementation and maintaining context across sessions.

## Directory Structure

```
.agents/
├── .version                       # Tracks structure version
├── README.md                      # This file
├── tasks/
│   ├── <task_name>_plan.md        # Where Human and Claude store their implementation plan for the task
│   └── <task_name>_progress.md   # Where Claude carefully tracks its progress after each step of the implementation plan
├── templates/
│   ├── plan_template.md
│   └── progress_template.md
└── output/
    └── <task_name>/               # Task-specific output directory for deliverables and artifacts
        └── <artifact_files>       # Outputs produced during implementation (final and intermediate)
```

## Workflow

### 1. Planning (Session 1)
- **Human**: Specifies the overall task to be performed to Claude, including any GitHub or JIRA issue numbers, current state, reason for perform the task, and acceptance criteria.
- **Human**: Asks Claude to create detailed plan from the task description
- **Claude**: If no GitHub or Jira issue referenced, prompts for one
- **Claude**: Explores codebase and writes comprehensive plan to file `tasks/<task_name>_plan.md` using the `templates/plan_template.md` as a starting point
- **Human**: Reviews and edits plan file directly and/or collaborates with Claude to refine the plan
- **Human**: Marks plan status as `approved`

### 2. Implementation (Session 2)
- **Human**: Starts fresh Claude session, references approved plan file, asks Claude to begin implementation
- **Claude**: Creates a `tasks/<task_name>_progress.md` file to track progress using the `templates/progress_template.md` as a starting point
- **Claude**: Implements following the plan, carefully documenting its progress in the file `tasks/<task_name>_progress.md`.
- **Claude**: Stops after each stage of the implementation plan laid out in `tasks/<task_name>_plan.md`.
- **Human**: Reviews work of the current stage, then asks Claude to continue with the next stage when comfortable.

## File Naming Convention

Files are named: `tasks/<task_name>_plan.md` and `tasks/<task_name>_progress.md`.

**Task name format:**
The task name includes a prefix for uniqueness and sorting:
- If GitHub issue or JIRA ticket exists: `<ISSUE-ID>-<description>` (e.g., `GH-123-add_authentication`)
- Otherwise: `<YYYY-MM-DD>-<description>` (e.g., `2024-10-30-refactor_api`)

This ensures files appear adjacent when sorted and scales across many tasks in repositories with multiple contributors.

**Examples:**
- `tasks/GH-456-user_dashboard_plan.md` and `tasks/GH-456-user_dashboard_progress.md`
- `tasks/2024-10-30-optimize_queries_plan.md` and `tasks/2024-10-30-optimize_queries_progress.md`

## Output Directory

The `output/` directory stores artifacts and deliverables produced during task implementation:

**Purpose:**
- Separate task metadata (plans/tracking) from actual deliverables (code, documentation, configs)
- Preserve historical artifacts even after outputs are moved to their final locations
- Organize multiple outputs per task in dedicated subdirectories

**Organization:**
- One subdirectory per task: `output/<task_name>/`
- All artifacts for that task live in its subdirectory
- Can include final deliverables, intermediate outputs, generated files, etc.

**When to use:**
- During implementation, write deliverables to `output/<task_name>/`
- After task completion, deliverables may be moved to their final project locations
- Original files remain in `output/` as historical reference

**Example:**
```
output/
├── 2024-10-30-python_coding_style_analysis/
│   └── python_style.md              # Generated style guide (later split into skill)
└── GH-789-authentication_feature/
    ├── auth_module.py               # Generated authentication module
    └── migration_script.sql         # Database migration script
```

## Key Principles

**For Humans:**
- Drive the plan creation process with assistance from Claude
- Use separate sessions for planning vs. implementation (optimizes context)
- Always reference GitHub issues when they exist

**For Claude:**
- Always prompt for GitHub issue or tracking ID if not provided (use timestamp if none exists)
- Construct full task name with prefix: `<ISSUE-ID>-<description>` or `<YYYY-MM-DD>-<description>`
- Analyze codebase thoroughly before creating plan
- Read `templates/progress_template.md` and use it as the structure for the progress file you create (`tasks/<task_name>_progress.md`)
- Carefully document the work performed in progress file `tasks/<task_name>_progress.md` after each step of the implementation plan
- Write task deliverables and artifacts to `output/<task_name>/` directory during implementation (task_name includes prefix)
- Stop implementation and ask for human review after you've updated the progress file at the end of each step of the implementation plan
- NEVER automatically proceed from one step of an implementation plan to the next step without Human approval

## Resumability: Progress Files as State Documents

The progress file (`tasks/<task_name>_progress.md`) serves as the **authoritative state document** for resuming work across sessions. This is critical because:

- Claude Code sessions restart frequently (/compact every 2-3 hours, new sessions daily)
- Conversation history is not preserved between sessions
- The progress file + plan file + output artifacts = complete resumable state

**What makes a progress file resumable:**

When starting a fresh Claude Code session, Claude should be able to read only the plan and progress files to understand:
1. **What's been completed** - Checked boxes, phase outcomes, delivered artifacts
2. **Current state** - What's in progress, what's blocked, what's next
3. **Key decisions made** - Important choices with rationale documented
4. **Deviations from plan** - Why the actual path differs from the original plan
5. **Context for continuation** - Enough detail to pick up work without conversation history

**Best practices for maintaining resumability:**

- Update progress file after completing each implementation step
- Document outcomes clearly (what was accomplished, not just "step done")
- Note key decisions and their rationale as they're made
- Keep "Deviations from Plan" and "Blockers" sections current
- For multi-day work, ensure each session ends with clear "where to pick up next"

**Philosophy:** Could a fresh Claude session pick up from here? If not, document more detail.

## Documenting Phase Outcomes

For complex, multi-phase tasks, consider organizing progress by phase and documenting clear phase outcomes. This provides natural checkpoints for resumability and knowledge capture.

**When to use phase-based organization:**

- Multi-day or multi-week tasks with distinct stages
- Tasks requiring different types of work (research → design → implementation → validation)
- Complex workflows where progress tracking benefits from higher-level structure
- Tasks following a specific methodology (e.g., architectural extraction, system design)

**Phase outcome pattern:**

When completing a phase, document:
1. **What was accomplished** - Deliverables created, work completed (concrete, specific)
2. **Key decisions made** - Important choices with rationale
3. **Metrics** (if applicable) - Lines analyzed, files created, reductions achieved, questions answered
4. **What's next** - State for next phase, dependencies, prerequisites

**Example phase structure:**

```markdown
### Phase 2: Reconnaissance ✅
- ✅ Create progress file
- ✅ Launch Explore agent for codebase survey
- ✅ Document repository statistics
- ✅ Create iteration plan

**Outcome**: Comprehensive reconnaissance completed. Identified 1,575 lines of
AWS SDK interaction code across 11 service wrappers. Created 2-iteration plan:
Iteration 1 analyzes ALL implementation code (1,203 lines), Iteration 2 analyzes
ALL test code (1,687 lines). This validates the incremental artifact building workflow.
```

**Benefits:**
- Clear checkpoints for resuming work after breaks
- Documents architectural decisions and rationale
- Provides process documentation for future similar tasks
- Enables easier handoff between sessions or team members

**Note:** Simple tasks don't need this level of structure. Use phase-based organization when it adds value, not as a default.

## Documenting Skill Improvements

As you work on tasks, you may discover improvements to the skills you're using (task-planning, extract-architecture, or custom skills). Documenting these insights ensures they feed back into skill evolution.

**When to document skill improvements:**

- You discover a gap in skill guidance (missing step, unclear instruction)
- You identify a workflow improvement through real-world use
- You find a better way to structure templates or organize work
- You encounter a problem that reveals a missing capability

**Where to document:**

In the progress file, add a section (typically near the end):

```markdown
## Skill Improvements Discovered

### Improvements for [skill-name] Skill

**1. [Improvement Title]**
- **Problem**: What gap or issue did you encounter?
- **Root cause**: Why did this happen? What's missing from current skill?
- **Solution**: What should be added/changed?
- **Where to add**: Which file(s) or section(s) of the skill?
- **Why it matters**: Impact on skill usability or effectiveness
- **Status**: discovered / validated / implemented
```

**Structure elements:**
- **Which skill** - Name of the skill being improved
- **What improvement** - Specific change to guidance, templates, or workflow
- **Where to add** - File paths and sections for implementation
- **Why it matters** - Rationale and impact
- **Status** - Track from discovery through validation to implementation

**Example:**

```markdown
**1. File Size Constraints for Pattern Documentation**
- **Problem**: Created 2,474-line patterns.md file that couldn't be fully
  read back into context during refinement phase
- **Root cause**: No guidance on maximum file size for pattern documentation
- **Solution**: Add explicit file size constraints (~1,500 lines) and splitting
  guidance to Step 3 (Iterative Analysis Phase)
- **Where to add**: Step 3.2 "Document Patterns" section in extract-architecture SKILL.md
- **Why it matters**: Pattern catalog is primary input for refinement; if it
  can't be fully read, deliverables will have critical gaps
- **Status**: validated (tested in AWS SDK extraction task)
```

**Benefits:**
- Captures learnings in structured, actionable format
- Provides clear implementation guidance for skill updates
- Ensures improvements discovered during one task benefit future work
- Creates feedback loop for continuous skill evolution

**Note:** Most tasks won't discover skill improvements - that's normal. This section is optional and should only be used when genuine insights emerge.
