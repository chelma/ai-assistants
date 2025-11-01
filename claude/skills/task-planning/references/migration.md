# Migration Guide: Upgrading .agents/ Directory Structure

This guide provides detailed instructions for migrating older `.agents/` directory structures to the current standard.

**Current Skill Version:** 2

## When to Use This Guide

Load this reference when:
- Local `.agents/.version` is less than skill version (2)
- `.agents/.version` file is missing (treat as v0)
- User requests migration to latest standards

## Version Detection

1. **Check for `.agents/.version` file:**
   - If exists: Read the integer version number
   - If missing: Treat as **v0** (legacy, pre-versioning)

2. **Compare with skill version:**
   - Skill version: **2**
   - If `local_version < 2`: Migration needed
   - If `local_version == 2`: No migration needed
   - If `local_version > 2`: Unexpected (user is ahead of skill)

## Version History

**v0 (Legacy - pre-versioning):**
- No `.agents/.version` file
- Task files without prefixes: `add_auth_plan.md`
- Files named `*_implement.md`
- Template named `implementation_template.md`
- May be missing `output/` directory
- No `Output Directory` field in template

**v1 (Partial updates):**
- Has `.agents/.version` containing `1`
- May have some task prefixes OR progress naming (not both)
- Inconsistent structure from partial manual updates

**v2 (Current standard):**
- Has `.agents/.version` containing `2`
- All task files have prefixes: `GH-123-feature_plan.md` or `2025-10-31-feature_plan.md`
- All files use `*_progress.md` naming
- Template named `progress_template.md`
- Template has `Output Directory` field
- `output/` directory exists

## Migration Workflow

### Step 1: Present Migration Option

When detecting old version, inform the user:

```
I found a .agents/ directory at version [X] (current skill version: 2).

[If v0:]
This appears to be a legacy structure from before versioning was introduced.

[If v1:]
This appears to be partially updated.

Changes needed to upgrade to v2:
- [List specific changes based on version - see migration paths below]

Would you like me to migrate to v2?

Migration will:
- Rename files to match current conventions
- Update template files to v2 standard
- Add/update .version file
- NOT modify the contents of plan or progress files
- Create a backup at .agents.backup.[timestamp] before making changes

Migrate now? (yes/no)
```

### Step 2: Create Backup

If user confirms, always create a backup first:

```bash
cp -r .agents .agents.backup.$(date +%Y%m%d_%H%M%S)
```

Inform user of backup location.

### Step 3: Perform Version-Specific Migrations

Execute migrations based on version gap. See **Migration Paths** section below for version-specific steps.

#### Migration A: *_implement.md → *_progress.md

**What to do:**
1. Find all files matching `*_implement.md` pattern in `.agents/tasks/`
2. For each file:
   - Rename: `<name>_implement.md` → `<name>_progress.md`
   - Update any plan files that reference this implement file (change links)
3. DO NOT modify file contents (only rename)

**Example:**
```bash
# Find and rename
mv .agents/tasks/add_auth_implement.md .agents/tasks/add_auth_progress.md

# Update references in plan file
# In add_auth_plan.md, change any mention of add_auth_implement.md → add_auth_progress.md
```

#### Migration B: Add Task Name Prefixes

**What to do:**
1. Find all task files without prefixes in `.agents/tasks/`
2. For each unprefixed task:
   - Ask user: "What prefix should I use for <task_name>? (issue/ticket ID, or I'll use YYYY-MM-DD)"
   - Wait for response
   - Rename both plan and progress files with prefix:
     - `<name>_plan.md` → `<PREFIX>-<name>_plan.md`
     - `<name>_progress.md` → `<PREFIX>-<name>_progress.md`
   - Update cross-references between plan and progress files
   - Update any `Output Directory` references to use new prefixed name

**Example:**
```bash
# User provides prefix GH-123
mv .agents/tasks/add_auth_plan.md .agents/tasks/GH-123-add_auth_plan.md
mv .agents/tasks/add_auth_progress.md .agents/tasks/GH-123-add_auth_progress.md

# Update internal cross-references
# In plan file: update any self-references
# In progress file: update Plan field and Output Directory field
```

#### Migration C: Update Progress Template

**What to do:**
1. Check for old template name:
   - If `.agents/templates/implementation_template.md` exists, rename to `progress_template.md`
2. Read `.agents/templates/progress_template.md`
3. Check if `Output Directory` field exists in header
4. If missing:
   - Add after `Plan` field: `**Output Directory**: ../output/[task_name]/`
   - Preserve all other user customizations
   - Only add this single field, don't replace entire template

**Example of header after migration:**
```markdown
# Implementation: [Task Name]

**Status**: in_progress
**Plan**: [Link to corresponding _plan.md file]
**Output Directory**: `../output/[task_name]/`
**Started**: [Date]
```

#### Migration D: Ensure Output Directory Exists

**What to do:**
1. Check if `.agents/output/` directory exists
2. If not, create it:
   ```bash
   mkdir -p .agents/output
   ```
3. DO NOT move or modify any existing files in output locations
4. DO NOT create subdirectories (they'll be created during implementation)

### Step 4: Update Version File

After successful migration:

1. Write new version to `.agents/.version`:
   ```bash
   echo "2" > .agents/.version
   ```

2. Report completion:
   ```
   Migration to v2 complete! Changes made:
   - [List all specific changes made]
   - Updated .version file (v[X] → v2)

   Backup created at: .agents.backup.[timestamp]

   All task file contents preserved unchanged.

   Ready to proceed with task planning.
   ```

### Step 5: Handle Migration Decline

If user declines migration:

```
No problem! I'll continue with your existing structure.

Note: New plans created will follow current conventions (prefixed names, *_progress.md files).
You can migrate existing tasks manually or ask me to migrate specific files later.

Ready to proceed with task planning.
```

## Migration Paths

This section documents specific steps for each migration path.

**Strategy:** Document incremental paths only (v1→v2, v2→v3, etc.), with one exception for the legacy bootstrap (v0→v2). Multi-hop migrations (e.g., v1→v4) are handled by chaining incremental paths sequentially.

### Migration Path: v0 → v2

**Applies to:** Legacy structures with no `.version` file (pre-versioning)

**This is the bootstrap migration** that establishes versioning. Most users will be on v0 (legacy) or v2 (current).

**Required changes:**
1. Execute Migration A: `*_implement.md` → `*_progress.md`
2. Execute Migration B: Add task name prefixes
3. Execute Migration C: Update progress template (rename + add Output Directory field)
4. Execute Migration D: Ensure output directory exists
5. Create `.agents/.version` file containing `2`

**Example scenario:**
```
Before (v0):
- tasks/add_auth_plan.md
- tasks/add_auth_implement.md
- templates/implementation_template.md (no Output Directory field)

After (v2):
- tasks/GH-123-add_auth_plan.md
- tasks/GH-123-add_auth_progress.md
- templates/progress_template.md (with Output Directory field)
- output/ (created)
- .version (contains: 2)
```

### Migration Path: v1 → v2

**Applies to:** Partially updated structures with `.version` containing `1`

**Note:** v1 is transitional and rare. Users likely have some but not all v2 features.

**Required changes depend on current state:**

**Detect what's missing:**
1. Check for `*_implement.md` files → If found, needs Migration A
2. Check for unprefixed task files → If found, needs Migration B
3. Check template name and Output Directory field → If missing, needs Migration C
4. Check for `output/` directory → If missing, needs Migration D

**Execute only the needed migrations:**
- If missing progress naming: Execute Migration A
- If missing prefixes: Execute Migration B
- If template needs updates: Execute Migration C
- If missing output directory: Execute Migration D
- Update `.agents/.version` to `2`

**Example scenario:**
```
Before (v1 - has prefixes but not progress naming):
- tasks/GH-123-add_auth_plan.md
- tasks/GH-123-add_auth_implement.md ← needs rename
- templates/implementation_template.md ← needs rename + field
- .version (contains: 1)

After (v2):
- tasks/GH-123-add_auth_plan.md
- tasks/GH-123-add_auth_progress.md
- templates/progress_template.md (with Output Directory field)
- output/ (created)
- .version (contains: 2)
```

### Future Migration Paths

When the skill is updated to v3 or beyond, document **incremental paths only**:

**v2 → v3:** (Not yet defined)
- [When v3 is created, document what changes and how to migrate from v2]

**v3 → v4:** (Not yet defined)
- [When v4 is created, document what changes and how to migrate from v3]

**Multi-hop migrations (e.g., v1 → v4):**
- Apply incremental paths sequentially: v1→v2, then v2→v3, then v3→v4
- Each step updates `.version` file and creates timestamped backup
- Claude handles chaining automatically

## Important Principles

### What NOT to Modify

**NEVER modify these during migration:**
- Contents of any `*_plan.md` files (except cross-reference links)
- Contents of any `*_progress.md` files (except cross-reference links)
- Any files in `.agents/output/` or subdirectories
- User's custom sections in template files

### What IS Safe to Modify

**ONLY modify these:**
- File names (renaming for new conventions)
- Cross-reference links between plan and progress files
- Template files (adding missing fields, updating to canonical structure)
- Directory structure (creating missing directories)

### Always Create Backups

Before ANY migration:
- Create timestamped backup of entire `.agents/` directory
- Inform user of backup location
- Never destructive without backup safety net

## Future Migrations

When the user requests changes to the task-planning skill structure:

1. **Update this migration guide** with new version detection logic
2. **Add new migration path** (Migration E, F, etc.) following the pattern above
3. **Document what changes** and what stays the same
4. **Test the migration** logic before committing
5. **Keep old migration paths** for users on very old versions

This ensures the skill can always upgrade from any previous version to the latest.
