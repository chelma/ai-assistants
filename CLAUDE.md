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

- **.agents/** - Task planning artifacts (when using task-planning skill)
  - **tasks/** - Planning and progress documents for multi-session work

## Claude Skills

This repository contains six custom Claude Code skills:

### python-style
Comprehensive Python coding guidelines extracted from production codebases. Automatically applies when working with Python code. Uses priority-based patterns (CRITICAL, PREFERRED, OBSERVED) with conditional loading for testing and async patterns.

### langchain-expert-builder
Reference implementation and abstractions for building LangChain-based multi-expert systems using the Expert-Task-Tool pattern. Provides copy-paste ready core abstractions and complete reference implementation demonstrating structured output, validation pipelines, and progressive detail loading.

### aws-interface-builder
Production-ready patterns for building testable AWS SDK (boto3) interfaces using Factory + Dependency Injection. Includes reference implementation demonstrating 10 critical patterns for implementation and testing with complete S3 wrapper examples.

### tech-writing
Style guidelines for README files, GitHub issues, and pull requests. Emphasizes third-person objective tone, context-before-instructions structure, complete code examples, and pragmatic completeness. Includes exemplar READMEs and evolution of patterns from 2023-2025.

### task-planning
Structured workflow for planning and implementing features across multiple sessions. Establishes `.agents/` directory workflow. Only invoke when user explicitly mentions "task planning" - do NOT use for general planning requests.

### extract-architecture
Extract architectural patterns from existing codebases to create AI-consumable reference guides. Use when tasked with documenting architecture, creating pattern catalogs, or producing prescriptive guides for AI assistants.

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

## Key Patterns

- **Symlink Architecture**: All Claude Code configuration is symlinked, not copied. Changes are immediately reflected in both locations.
- **Git Workflow**: Commit configuration changes like any other code changes. The repository acts as backup and version control for AI assistant configuration.
- **Skill Organization**: Skills use progressive disclosure - load core guidance always, load additional references conditionally based on task context.
- **Priority Levels**: python-style skill demonstrates priority-based pattern application (CRITICAL > PREFERRED > OBSERVED).
