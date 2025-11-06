# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This repository manages personal AI assistant configuration, primarily for Claude Code. It uses symlinks to version-control the `~/.claude/` directory, enabling Git-tracked configuration that syncs automatically between the repository and the active Claude Code installation.

## Setup and Installation

Run the installation script to set up symlinks:

```bash
./claude/install.sh
```

This creates bidirectional symlinks between `~/.claude/` and the repository's `claude/` directory. Changes in either location automatically reflect in the other, enabling version control of Claude Code configuration.

## Directory Structure

- **claude/** - Claude Code configuration (symlinked to `~/.claude/`)
  - **skills/** - Custom Claude Code skills (see below)
  - **commands/** - Custom slash commands
  - **memories/** - Custom memories
  - **agents/** - Custom subagent definitions
  - **settings.json** - Global user settings (permissions, environment variables)
  - **CLAUDE.md** - User-level instructions for all sessions
  - **.mcp.json** - MCP server configuration
  - **install.sh** - Symlinking installation script

- **.agents/** - Shared architecture references (version-controlled)
  - **FORMAT.md** - Canonical format specification for architecture references
  - **README.md** - Overview and usage guide
  - **references/** - Architecture references extracted from codebases
    - Each reference documents patterns, design decisions, and reusable abstractions
    - AI-agnostic format works across coding assistants (Claude, Copilot, Cursor, etc.)
    - Can be converted to assistant-specific formats (e.g., Claude Skills)

- **.claude/agents/** - Engineer-specific task planning and research artifacts (git-ignored)
  - **tasks/** - Planning and progress documents for multi-session work
  - **output/** - Task deliverables and intermediate artifacts
  - **research/** - Codebase investigation findings from codebase-researcher sub-agent

## Claude Skills and Sub-agents

This repository contains 6 custom Claude Code skills and 1 custom sub-agent. For detailed documentation including usage patterns, key philosophies, and what each provides, see `claude/README.md`.

**Skills**:
- **aws-interface-builder** - AWS SDK interface patterns with Factory + Dependency Injection
- **extract-architecture** - Extract architectural patterns from codebases; outputs to shared references (`.agents/references/`) or Claude Skills format
- **langchain-expert-builder** - LangChain multi-expert system builder using Expert-Task-Tool pattern
- **python-style** - Comprehensive Python coding guidelines with priority-based patterns
- **task-planning** - Structured planning workflow for multi-session feature work
- **tech-writing** - Technical documentation guidelines (READMEs, issues, PRs)

**Sub-agents**:
- **codebase-researcher** - Deep codebase investigation with context health management, composes with skills ecosystem

Read `claude/README.md` for comprehensive documentation on each skill and sub-agent, including when to use them, what they provide, and how they integrate with each other.

## Working with This Repository

### Modifying Skills
Skills are located in `claude/skills/*/SKILL.md`. Each skill uses YAML frontmatter for metadata and contains detailed instructions. Reference materials are stored in `references/` subdirectories within each skill.

### Committing Configuration Changes
Since `~/.claude/` is symlinked, changes made by Claude Code appear as modifications in this repository:

```bash
git status
git add claude/
git commit -m "Update Claude configuration"
git push
```

### Skill Development
When creating or modifying skills, follow the structure observed in existing skills:
- YAML frontmatter with name and description
- Overview section explaining purpose
- Loading strategy (if applicable)
- Detailed implementation guidance
- Reference materials in `references/` subdirectory

### Architecture References
Architecture references in `.agents/references/` document reusable patterns extracted from codebases:

**Creating references:**
- Use `extract-architecture` skill to extract patterns from codebases
- Skill offers choice: shared reference (`.agents/references/`) or Claude Skill format
- Shared references are AI-agnostic and version-controlled for team use
- Can be converted to assistant-specific formats later

**Working with references:**
- Read `.agents/FORMAT.md` for detailed format specification
- Read `.agents/README.md` for overview and usage guidance
- References use progressive disclosure (README.md → references/ → assets/)
- Optimized for token efficiency (2-10k tokens loaded vs 50k+ available)

**Key distinction:**
- `.agents/references/` - Shared, version-controlled architecture references (team resource)
- `.claude/agents/` - Engineer-specific working files, git-ignored (personal workspace)

## Key Patterns

- **Symlink Architecture**: All Claude Code configuration is symlinked, not copied. Changes are immediately reflected in both locations.
- **Git Workflow**: Commit configuration changes like any other code changes. The repository acts as backup and version control for AI assistant configuration.
- **Skill Organization**: Skills use progressive disclosure - load core guidance always, load additional references conditionally based on task context.
- **Priority Levels**: python-style skill demonstrates priority-based pattern application (CRITICAL > PREFERRED > OBSERVED).
