# Plan: 2025-12-15-port-skills-to-agentic-toolbox

**Workspace**: agentic-toolbox
**Project Root**: ~/workspace/alto/agentic-toolbox
**Status**: approved
**GitHub Issue**: N/A
**Created**: 2025-12-15

## Problem Statement

Port Claude Code configuration (tag-team, extract-architecture, better-boundaries skills and codebase-researcher subagent) from the personal ai-assistants repo to a new Alto-specific repo (agentic-toolbox). The skills need to be made portable by removing dependencies on external skills not being ported and updating internal references to only reference skills within the package.

## Acceptance Criteria

- [ ] All four components (tag-team, extract-architecture, better-boundaries, codebase-researcher) copied to agentic-toolbox with proper plugin structure
- [ ] codebase-researcher: External skill references removed, internal skill references (tag-team, extract-architecture) retained
- [ ] extract-architecture: Output format choice updated to default to Claude Skill with custom format option
- [ ] extract-architecture: skill-creator dependency documented in README
- [ ] tag-team: Template paths converted to relative paths (./assets/templates/)
- [ ] tag-team: Composability section updated to only reference internal skills
- [ ] Plugin marketplace structure created with workflows-plugin and reference-plugin
- [ ] README documentation complete with dependency notes

---

## Current State Analysis

### Source Files (ai-assistants repo)

**Skills**:
| Skill | Location | Size | References |
|-------|----------|------|------------|
| tag-team | `claude/skills/tag-team/SKILL.md` | ~338 lines | + 2 templates in assets/ |
| extract-architecture | `claude/skills/extract-architecture/SKILL.md` | ~470 lines | + 3 references/ files |
| better-boundaries | `claude/skills/better-boundaries/SKILL.md` | ~560 lines | + 11 references/ + assets/ |

**Subagent**:
| Agent | Location | Size |
|-------|----------|------|
| codebase-researcher | `claude/agents/codebase-researcher.md` | ~806 lines |

### Existing Plugin Structure (ai-assistants repo)

```
.claude-plugin/marketplace.json          # Marketplace definition
workflows-plugin/
├── .claude-plugin/plugin.json
├── skills/ (symlinks)
├── agents/ (symlinks)
└── README.md
reference-plugin/
├── .claude-plugin/plugin.json
├── skills/ (symlinks)
└── README.md
```

### Cross-References to Address

**codebase-researcher references these external skills (to REMOVE)**:
- python-style
- langchain-expert-builder
- tech-writing
- aws-interface-builder

**codebase-researcher references these internal skills (to KEEP)**:
- extract-architecture
- tag-team

**extract-architecture references**:
- tag-team (internal - KEEP)
- codebase-researcher (internal - KEEP)
- skill-creator (external - KEEP but document dependency)

**tag-team references**:
- extract-architecture (internal - KEEP)
- tech-writing (external - REMOVE)
- codebase-researcher (internal - KEEP)

### Target Repository

`~/workspace/alto/agentic-toolbox` - currently empty (just .git)

## Proposed Solution

**Phased approach with iterative review:**

1. **Phase 1: Scaffold** - Copy all files as-is to establish baseline
2. **Phase 2-N: Theme-based modifications** - Work through each change theme to completion, with human review after each theme

**Target structure**:
```
agentic-toolbox/
├── .claude-plugin/
│   └── marketplace.json
├── workflows-plugin/
│   ├── .claude-plugin/plugin.json
│   ├── skills/
│   │   ├── tag-team/
│   │   │   ├── SKILL.md
│   │   │   └── assets/templates/
│   │   └── extract-architecture/
│   │       ├── SKILL.md
│   │       └── references/
│   ├── agents/
│   │   └── codebase-researcher.md
│   └── README.md
├── reference-plugin/
│   ├── .claude-plugin/plugin.json
│   ├── skills/
│   │   └── better-boundaries/
│   │       ├── SKILL.md
│   │       ├── references/
│   │       └── assets/
│   └── README.md
└── README.md
```

## Implementation Steps

### Phase 1: Scaffold (copy as-is)

1. Create directory structure in agentic-toolbox
2. Copy marketplace.json (update metadata)
3. Copy workflows-plugin structure with real files (not symlinks)
4. Copy reference-plugin structure with real files (not symlinks)
5. Create root README.md

**Checkpoint**: Review scaffold before modifications

### Phase 2: Theme - codebase-researcher skill cleanup

6. Remove "Skill Integration" section (lines 43-59) - trim to internal skills only
7. Remove "1.3 Load Relevant Skills" section (lines 87-119) - trim to internal skills only
8. Remove "Skills Loading Guidance" section (lines 587-616) entirely

**Checkpoint**: Review codebase-researcher changes

### Phase 3: Theme - extract-architecture output format

9. Modify Phase 4.3 to offer Claude Skill (default) + Custom format option
10. Update Phase 6.2 to handle custom format path
11. Add note about skill-creator dependency

**Checkpoint**: Review extract-architecture changes

### Phase 4: Theme - tag-team portability

12. Convert template paths to relative (./assets/templates/)
13. Update composability section to only reference internal skills (remove tech-writing)

**Checkpoint**: Review tag-team changes

### Phase 5: Theme - Documentation

14. Update workflows-plugin README with dependency notes (skill-creator)
15. Update reference-plugin README
16. Create root README for agentic-toolbox repo

**Checkpoint**: Final review

## Risks and Considerations

1. **skill-creator dependency**: Users need example-skills plugin for full extract-architecture functionality. Mitigated by documenting clearly in README.

2. **Template path resolution**: Relative paths from SKILL.md need to work when skill is installed via plugin. Test after implementation.

3. **Internal skill references**: codebase-researcher loading extract-architecture assumes both are installed. Since they're in the same plugin, this should work, but worth verifying.

4. **better-boundaries assets**: This skill has significant assets/ content (reference implementations). Ensure all copied correctly.

## Testing Strategy

1. **Structure validation**: Verify all files copied to correct locations
2. **Plugin installation**: Test installing the plugin locally via `/plugin marketplace add`
3. **Skill invocation**: Test each skill can be invoked
4. **Cross-skill composition**: Test codebase-researcher → extract-architecture composition
5. **Template loading**: Test tag-team can read its templates via relative paths
