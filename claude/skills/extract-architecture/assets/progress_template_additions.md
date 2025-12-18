# Progress Template Additions for Architecture Extraction

## Overview

These sections should be added to the standard tag-team progress template when performing architecture extraction tasks. They provide structure for documenting reconnaissance findings, iteration plans, and phase-by-phase progress.

**Usage**: When tag-team creates `<task_name>_progress.md`, add these sections after the standard template sections (Evolution and Adaptations, Blockers, Gotchas, Additional Research).

**CRITICAL - Incremental Updates**:
- **UPDATE THIS FILE IMMEDIATELY AFTER EACH PHASE/ITERATION COMPLETION** (not in batches)
- Batched updates cause context strain and reduce resumability
- Update progress file BEFORE moving to next phase/iteration
- This ensures state is preserved if context needs to be compacted

**File Reference Requirements**:
- The standard progress template (from tag-team) includes Workspace and Project Root fields
- All file paths in these architecture extraction sections should be **relative to project root**
- Example: `ruby_worker/app/workflows/workflow_demo_mixed.rb:15-30`
- NOT: `~/workspace/personal/time-cop/ruby_worker/...`
- This ensures portability across machines and Claude sessions

---

## Reconnaissance Summary

### Repository Statistics
- **Total Files**: [Number] files related to [domain/pattern being extracted]
- **Total Lines**: [Number] lines of code
- **Key Technologies**: [Framework/library versions, languages, dependencies]
- **Architecture Style**: [e.g., Multi-expert LLM system, Microservices, Event-driven, etc.]

### Architecture Overview
[2-3 paragraph summary of the architecture being extracted]

Key components:
1. **[Component 1]**: [Purpose and role]
2. **[Component 2]**: [Purpose and role]
3. **[Component 3]**: [Purpose and role]

**Key Patterns Identified** (initial survey):
- [Pattern 1 description]
- [Pattern 2 description]
- [Pattern 3 description]
- [etc.]

### Complete File Inventory

Organize files by architectural layer, concern, or domain. For each layer:
- List all relevant files
- Include line counts
- Add checkmarks (✅ or [ ]) to track analysis progress
- Group by vertical slices or horizontal layers

**Example structure:**

#### Layer 1: Core Abstractions ([X] files, [Y] lines)
- ✅ `path/to/file1.py` (50 lines) - Brief description
- [ ] `path/to/file2.py` (75 lines) - Brief description

#### Layer 2: [Domain] Implementations ([X] files, [Y] lines)

**[Implementation Group 1]** (X files, Y lines)
- [ ] `path/to/file3.py` (40 lines) - Brief description
- [ ] `path/to/file4.py` (60 lines) - Brief description

**[Implementation Group 2]** (X files, Y lines)
- [ ] `path/to/file5.py` (55 lines) - Brief description

#### Layer 3: [Supporting Concerns] ([X] files, [Y] lines)
- [ ] `path/to/file6.py` (100 lines) - Brief description
- [ ] `path/to/file7.py` (200 lines) - Brief description

---

## Iteration Plan

### Iteration Strategy
- **Target**: ~[1500] lines per iteration (adjust based on complexity and context limits)
- **Estimated Iterations**: [N] iterations to cover all key files
- **Approach**: [Vertical slices by complete subsystem OR horizontal layers OR domain groupings]
- **Priority**: [Order rationale - e.g., "Core abstractions → implementations → utilities"]

### Iteration [N]: [Title/Focus] (~[X] lines, [Y] files) ⭐ [KEY INSIGHT/GOAL]

**Focus**: [What this iteration aims to understand]

**Files to analyze** ([Y] files, [X] lines):
- ✅/[ ] `path/to/file.py` ([Z] lines) - [What to extract]
- ✅/[ ] `path/to/file2.py` ([Z] lines) - [What to extract]
- [etc.]

**Key Patterns to Extract**:
- **[Pattern Category 1]**: [Specific patterns expected in these files]
- **[Pattern Category 2]**: [Specific patterns expected in these files]
- [etc.]

**Rationale**: [Why these files are grouped together and analyzed in this iteration]

---

### Iteration [N+1]: [Title/Focus] (~[X] lines, [Y] files) ⭐ [KEY INSIGHT/GOAL]

[Repeat structure for each planned iteration]

---

## Phase Progress Tracking

**REMEMBER**: Update this file immediately after EACH phase completion (not in batches).

### Phase 1: Plan with Tag-Team ✅/⏳/[ ]
- ✅/[ ] Invoke tag-team skill
- ✅/[ ] Create plan file with extraction goals and acceptance criteria

**Outcome**: [Summary of plan created]

---

### Phase 2: Reconnaissance & Iteration Planning ✅/⏳/[ ]
- ✅/[ ] Launch Explore agent for [repository] repository
- ✅/[ ] Review reconnaissance report
- ✅/[ ] Create complete file inventory organized by [layer/concern/domain]
- ✅/[ ] Plan iterations (~1500 lines each)
- ✅/[ ] Choose investigation approach (direct / delegated)
- ✅/[ ] Present iteration plan for approval (CHECKPOINT)

**Outcome**: [Summary of what was learned and strategy approved]

---

### Phase 3: Iterative Analysis ✅/⏳/[ ]
- ✅/[ ] Iteration 1: [Title] ([X] files, [Y] lines)
- ✅/[ ] Iteration 2: [Title] ([X] files, [Y] lines)
- ✅/[ ] Iteration 3: [Title] ([X] files, [Y] lines)
- ✅/[ ] [Additional iterations as needed]
- ✅/[ ] Human priority review (CHECKPOINT)

**Outcome**: [Summary of patterns extracted with priority breakdown - X CRITICAL, Y PREFERRED, Z OBSERVED]

---

### Phase 4: Critical Review & Deliverable Scoping ✅/⏳/[ ]
- ✅/[ ] Review pattern documentation (descriptive vs prescriptive)
- ✅/[ ] Determine deliverables needed (catalog / guide / reference impl)
- ✅/[ ] Choose output format: Shared Reference OR Claude Skill (CHECKPOINT)

**Outcome**: [Deliverables scoped, format chosen]

---

### Phase 5: Refinement ✅/⏳/[ ]
- ✅/[ ] Create prescriptive guide (if applicable) with TODO markers
- ✅/[ ] Create reference implementation (if applicable) with TODO markers
- ✅/[ ] Human collaboration - design rationale (CHECKPOINT)
- ✅/[ ] Token optimization (file references, enhanced docstrings)

**Outcome**: [Deliverables created with human rationale incorporated]

---

### Phase 6: Finalize & Deliver ✅/⏳/[ ]
- ✅/[ ] Process documentation (phase summaries, lessons learned)
- ✅/[ ] Format deliverables per Phase 4 choice
- ✅/[ ] Final review and presentation to user

**Outcome**: [Complete deliverable set delivered]

---

### [Optional Additional Phases]

**Note**: Additional phases may emerge from human reviews. Document them here using positive framing in "Evolution and Adaptations" section (not as deviations/failures).

---

## Phase [N] Completion Summary

### Deliverables Created

#### [Deliverable 1 Name]
**Location**: [Path to file or directory]

[Description of deliverable]:
- [Key feature 1]
- [Key feature 2]
- [Key feature 3]

**Key improvements over [baseline/previous version]**:
- [Improvement 1]
- [Improvement 2]

#### [Deliverable 2 Name]
**Location**: [Path to file or directory]

[Repeat structure for each deliverable]

---

### Process Documentation

#### What Worked Well
1. **[Approach/decision 1]**: [Why it worked]
2. **[Approach/decision 2]**: [Why it worked]
3. [etc.]

#### Key Decisions Made
1. **[Decision 1]**: [What was decided and why]
2. **[Decision 2]**: [What was decided and why]
3. [etc.]

#### Artifacts for Future [Type] Extractions

**Process Pattern**:
1. **[Step 1]**: [Description]
2. **[Step 2]**: [Description]
3. [etc.]

**Key Principles**:
- [Principle 1]
- [Principle 2]
- [etc.]

---

### Files Created/Modified

**Total**: [X] new files ([Y] documentation, [Z] code) + [N] modified files

**Structure**:
```
[output_directory]/
├── [file1]                    # [Description]
├── [file2]                    # [Description]
└── [directory]/
    ├── [file3]
    └── [file4]
```

**Total Lines**: ~[X] lines of [code/documentation]

---

### Next Steps (For Future Sessions)

1. **[Next step 1]**: [Description]
2. **[Next step 2]**: [Description]
3. [etc.]

---

### Lessons Learned

1. **[Lesson 1]**: [What was learned and why it matters]
2. **[Lesson 2]**: [What was learned and why it matters]
3. [etc.]

---

## Notes on Using These Sections

### When to Add Sections

- **Reconnaissance Summary**: Add immediately after initial codebase exploration
- **Iteration Plan**: Add after file inventory is complete, before starting analysis
- **Phase Progress Tracking**: Add at start of extraction, update after each phase
- **Phase Completion Summaries**: Add after each major phase completes

### Customization Guidance

**File Inventory Organization:**
- Choose structure that matches the codebase (layers, domains, concerns, technologies)
- Include line counts to plan iteration batches (~1500 lines per iteration)
- Use checkmarks to track analysis progress

**Iteration Planning:**
- Target ~1500 lines per iteration (adjust for complexity)
- Group by vertical slices (complete subsystems) when possible for context preservation
- Document rationale for grouping decisions

**Phase Tracking:**
- Use ✅ for completed, ⏳ for in-progress, [ ] for pending
- Add custom phases as needed (beyond the common 4-5 phases)
- Document outcomes after each phase completion

**Process Documentation:**
- Focus on what's reusable for future extractions
- Capture decision rationale (why X approach over Y)
- Document friction points and solutions

### Integration with Standard Template

These sections integrate with tag-team's progress template as follows:

**Standard template sections** (from tag-team):
- Status
- Plan reference
- Started date
- Progress overview

**Add these architecture extraction sections**:
- Reconnaissance Summary
- Iteration Plan
- Phase Progress Tracking

**Standard template sections** (from tag-team):
- Deviations from Plan
- Blockers
- Gotchas and Friction Points
- Additional Research

**Add these phase completion sections as needed**:
- Phase [N] Completion Summary (repeat for each phase)

**Standard template section** (from tag-team):
- Notes

### Example Integration

```markdown
# Implementation: [Task Name]

**Status**: in_progress
**Plan**: [task_name_plan.md](./task_name_plan.md)
**Started**: 2025-11-01

## Progress

[High-level progress summary from tag-team template]

---

## Reconnaissance Summary

[Add Reconnaissance Summary section here]

---

## Iteration Plan

[Add Iteration Plan section here]

---

## Phase Progress Tracking

[Add Phase tracking sections here]

---

## Deviations from Plan

[Standard tag-team section]

---

## Blockers

[Standard tag-team section]

---

## Gotchas and Friction Points

[Standard tag-team section]

---

## Additional Research

[Standard tag-team section]

---

## Phase 1 Completion Summary

[Add after Phase 1 completes]

---

## Phase 2 Completion Summary

[Add after Phase 2 completes]

---

## Notes

[Standard tag-team section]
```

This structure enables comprehensive progress tracking while maintaining compatibility with tag-team's established workflow.
