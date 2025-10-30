# Claude Code Collaboration System

The `.agents/` directory enables structured collaboration between humans and Claude Code by separating planning from implementation and maintaining context across sessions.

## Directory Structure

```
.agents/
├── README.md                      # This file
├── tasks/
│   ├── <task_name>_plan.md        # Where Human and Claude store their implementation plan for the task
│   └── <task_name>_implement.md   # Where Claude carefully tracks its progress after each step of the implementation plan
├── templates/
│   ├── plan_template.md
│   └── implementation_template.md
└── output/
    └── <task_name>/                # Task-specific output directory for deliverables and artifacts
        └── <artifact_files>        # Outputs produced during implementation (final and intermediate)
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
- **Claude**: Creates a `tasks/<task_name>_implement.md` file to track progress using the `templates/implementation_template.md` as a starting point
- **Claude**: Implements following the plan, carefully documenting its progress in the file `tasks/<task_name>_implement.md`.
- **Claude**: Stops after each stage of the implementation plan laid out in `tasks/<task_name>_plan.md`.
- **Human**: Reviews work of the current stage, then asks Claude to continue with the next stage when comfortable.

## File Naming Convention

Files are named `tasks/<task_name>_plan.md` and `tasks/<task_name>_implement.md` so they appear adjacent when sorted.

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
├── python_coding_style_analysis/
│   └── python_style.md              # Generated style guide (later split into skill)
└── authentication_feature/
    ├── auth_module.py               # Generated authentication module
    └── migration_script.sql         # Database migration script
```

## Key Principles

**For Humans:**
- Drive the plan creation process with assistance from Claude
- Use separate sessions for planning vs. implementation (optimizes context)
- Always reference GitHub issues when they exist

**For Claude:**
- Always prompt for GitHub issue if not provided
- Analyze codebase thoroughly before creating plan
- Read `templates/implementation_template.md` and use it as the structure for the implementation file you create (`tasks/<task_name>_implement.md`)
- Carefully document the work performed in implementation file `tasks/<task_name>_implement.md` after each step of the implementation plan
- Write task deliverables and artifacts to `output/<task_name>/` directory during implementation
- Stop implementation and ask for human review after you've updated the implementation file at the end of each step of the implementation plan
- NEVER automatically proceed from one step of an implementation plan to the next step without Human approval
