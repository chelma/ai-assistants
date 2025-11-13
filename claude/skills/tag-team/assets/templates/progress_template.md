# Implementation: [Task Name]

<!--
RESUMABILITY: This file is the authoritative state document. When starting a fresh
Claude Code session (/compact, new day, etc.), Claude will read this file to understand:
- What's been completed (checked boxes, phase outcomes)
- Current blockers and decisions made
- Where to pick up next

CRITICAL: Update this file IMMEDIATELY after EACH phase/step completion (not in batches).
Batched updates cause context strain and reduce resumability effectiveness.

For complex multi-phase work, consider grouping progress by phase and documenting
outcomes: what was accomplished, key decisions, metrics, what's next.

See .agents/README.md sections "Resumability" and "Documenting Phase Outcomes" for details.
-->

**Workspace**: [workspace-name]
**Project Root**: [/absolute/path/to/project/root]
**Status**: in_progress
**Plan**: [Link to corresponding _plan.md file]
**Output Directory**: `~/.claude/workspace/[workspace-name]/output/[task_name]/`
**Started**: [Date]

## Progress

<!--
STRUCTURE: Adapt this section to match your task type.

Examples:
- Linear work: Simple checklist with detailed Notes per step
- Multi-phase work: Organize by phase with outcome summaries
- High-iteration work: Lean Progress + write findings to deliverables

Don't force structure upfront - let it emerge based on work.
See tag-team SKILL.md "Task-Type Patterns" for detailed guidance.

For multi-phase work, consider organizing by phase:

### Phase 1: [Name] ✅/⏳/[ ]
- [✅] Step 1
- [✅] Step 2

**Outcome**: What was accomplished, key decisions, what's next

### Phase 2: [Name] ⏳
- [ ] Step 3
-->

- [ ] [Step 1 from plan]
- [ ] [Step 2 from plan]
- [ ] [Step 3 from plan]

## Resume from Here

<!--
This section helps with cold resumption after /compact or new Claude session.
Update this section after major milestones or when pausing for extended periods.
-->

**Current State**: [2-3 sentence summary of where things stand]

**Key Context**:
- [Critical decision/discovery that affects remaining work]
- [Important constraint or architectural choice]
- [Any non-obvious state that needs to be understood]

**Next Priorities**:
1. [What should be done next]
2. [Then what]
3. [Any dependent work]

**Open Questions**:
- [Question requiring human input or decision]
- [Uncertainty that may affect approach]

## Evolution and Adaptations

<!--
Document plan changes and discoveries. These are often improvements discovered
during execution, not problems. Use positive framing.

Format: "Phase X: Expanded/Modified to include Y. Rationale: [reason]. Impact: [what changed]."

If no adaptations needed by task completion, you can remove this section.
-->

[Document any changes from the approved plan and reasoning]

## Blockers

<!--
Track any blockers or questions that need human input.
If still empty ("None" or "No blockers") at task completion, you can remove this section.
-->

[Note any blockers or questions that need human input, or "None" if no blockers]

## Gotchas and Friction Points

<!--
Document unexpected issues, edge cases, or things that were harder than expected.
Consider: What surprised you? What would you do differently? What took longer than expected?

If no significant friction points by task completion, you can remove this section.
-->

[Document friction points, or remove section if none encountered]

## Additional Research

<!--
Summarize any web searches, documentation lookups, or external research needed.
If no external research required by task completion, you can remove this section.
-->

[Summarize research, or remove section if none needed]

## Testing Results

[Record test results and verification steps completed]

## Notes

[Any additional context or decisions made during implementation]
