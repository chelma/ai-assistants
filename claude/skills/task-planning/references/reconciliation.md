# Template Reconciliation Guide

This guide provides detailed instructions for reconciling local template files with canonical versions.

## When to Use This Guide

Load this reference when:
- Local `.agents/` templates differ from canonical versions in skill assets
- User wants to understand differences between their customizations and defaults
- Merging updates from skill while preserving user customizations

## Files Subject to Reconciliation

These files can be reconciled:
- `.agents/README.md`
- `.agents/templates/plan_template.md`
- `.agents/templates/progress_template.md`

**NEVER reconcile files in `.agents/tasks/`** - those contain user's work-in-progress.

## Reconciliation Workflow

### Step 1: Read Local Files

Read all reconcilable files from the local `.agents/` directory:
- `.agents/README.md`
- `.agents/templates/plan_template.md`
- `.agents/templates/progress_template.md`

### Step 2: Compare with Canonical Versions

Compare each local file with its canonical version from skill assets:
- `skills/task-planning/assets/README.md`
- `skills/task-planning/assets/templates/plan_template.md`
- `skills/task-planning/assets/templates/progress_template.md`

For each file, identify:
- Sections present in canonical but missing in local
- Sections present in local but missing in canonical (user additions)
- Sections present in both but with different content
- Formatting differences

### Step 3: Summarize Differences

For each file with differences, create a high-level summary (don't show full diffs unless requested):

```
Your local README.md differs from the canonical version:
- Local version has a "Dependencies" section not in canonical (custom addition)
- Canonical version has updated language in "Key Principles" section
- Canonical version has new "Migration" section
- Minor formatting differences in "Workflow" section
```

**Keep summaries concise** - users don't need line-by-line diffs initially.

### Step 4: Offer Reconciliation Options

For each file with differences, present options:

```
How would you like to handle these differences for README.md?
1. Keep local version (no changes)
2. Use canonical version (replace local, lose customizations)
3. Show me the full diff
4. Help me merge (I'll guide you through conflicting sections)
```

Wait for user response before proceeding.

### Step 5: Handle User Choice

#### Option 1: Keep Local Version

```
Keeping your local README.md unchanged.
```

No action needed. Move to next file.

#### Option 2: Use Canonical Version

```
Replacing local README.md with canonical version.

Note: Your custom "Dependencies" section will be lost.
Consider saving it separately if you want to reference it later.
```

Copy canonical file to local location, overwriting existing.

#### Option 3: Show Full Diff

Display both versions in a clear comparison format:

```
=== LOCAL VERSION (.agents/README.md) ===
[Show full local content]

=== CANONICAL VERSION (skill assets) ===
[Show full canonical content]

=== DIFFERENCES ===
Sections only in local:
- Dependencies

Sections only in canonical:
- Migration

Sections with different content:
- Key Principles
- Workflow
```

Then re-offer options 1, 2, or 4.

#### Option 4: Help Me Merge

Enter interactive merge mode:

1. **Identify conflicting sections:**
   - List all sections that differ between versions

2. **For each conflicting section:**
   ```
   Section: "Key Principles"

   --- Your local version ---
   [Show local section content]

   --- Canonical version ---
   [Show canonical section content]

   Which version would you like to keep?
   1. Keep local version
   2. Use canonical version
   3. Keep both (I'll append canonical after local)
   4. Let me edit manually (skip for now)
   ```

3. **For sections only in local:**
   ```
   Your local version has a "Dependencies" section not in canonical.

   Would you like to:
   1. Keep it (preserve your addition)
   2. Remove it (match canonical exactly)
   ```

4. **For sections only in canonical:**
   ```
   Canonical version has a new "Migration" section.

   Would you like to:
   1. Add it to your local version
   2. Skip it (don't add)
   ```

5. **Build merged version:**
   - Collect all user choices
   - Construct final merged content
   - Show preview: "Here's the merged version: [preview]"
   - Confirm: "Apply this merged version? (yes/no)"

6. **Write merged version:**
   - Write to local file
   - Confirm completion

### Step 6: Repeat for All Files

Process each file that has differences:
- README.md
- plan_template.md
- progress_template.md

Allow user to make different choices for each file (keep one, replace another, merge a third).

## Advanced Reconciliation Scenarios

### Handling Format-Only Differences

If files are semantically identical but have formatting differences (whitespace, line endings):

```
Your local README.md has only formatting differences from canonical (whitespace, line breaks).
Content is identical.

Would you like to:
1. Keep local formatting
2. Adopt canonical formatting
3. Ignore (they're functionally the same)
```

### Handling Version Metadata

Some template files may have version comments or metadata. When reconciling:
- Preserve version metadata if present locally
- Don't treat version differences as content conflicts
- Focus on actual functional content

### Preserving User Comments

If local files have user-added comments (e.g., `<!-- Custom note: ... -->`):
- Always preserve these during reconciliation
- Point them out: "Note: Your local file has custom comments which I'll preserve"
- Include them in merged versions automatically

## Best Practices

### When to Recommend Each Option

**Keep Local (Option 1):**
- User has extensive customizations
- Canonical changes are minor
- Local version is working well for user

**Use Canonical (Option 2):**
- User hasn't customized templates
- Canonical has important updates
- User explicitly wants "latest defaults"

**Show Diff (Option 3):**
- User wants to understand changes before deciding
- Differences are significant
- User is technical and wants full context

**Merge (Option 4):**
- User has customizations AND wants canonical updates
- Both versions have valuable content
- User wants best of both worlds

### Minimizing User Burden

- Start with high-level summaries, not full diffs
- Only dive into details when user requests
- Batch similar decisions when possible
- Remember user's preference pattern (if they keep local twice, suggest that for third)

### Handling Edge Cases

**Empty local file:**
- Just copy canonical version
- Don't bother with reconciliation options

**Empty canonical file (shouldn't happen):**
- Warn: "Canonical version is missing/empty - keeping your local version"
- File an internal note that skill assets may be corrupted

**Identical files:**
- Silent success - no reconciliation needed
- Don't bother user with "no differences" message unless they asked
