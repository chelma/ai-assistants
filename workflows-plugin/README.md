# Collaborative Workflows Plugin

A collection of Claude Code skills and agents designed to enhance collaborative AI-assisted development workflows.

## What's Included

### Skills

#### `tag-team`
Collaborative pair programming workflow using a checkpoint-driven pattern (DO WORK → DOCUMENT → PAUSE → CONTINUE). Enables multi-session tasks with portable progress tracking.

**Use when**: Working on substantive, multi-session tasks that benefit from structured planning and progress documentation.

#### `extract-architecture`
Extract architectural patterns and design decisions from existing codebases to create AI-consumable reference guides. Builds on tag-team for progress tracking and composes with codebase-researcher for large-scale investigations.

**Use when**: Documenting architecture, creating pattern catalogs, building reference implementations, or producing prescriptive guides for AI coding assistants.

### Agents

#### `codebase-researcher`
Performs extensive codebase investigations with structured findings while maintaining context health. Loads relevant skills based on task, uses Explore agent for reconnaissance, applies research methodologies (chunked reading ~1500 lines), saves findings to disk for resumability.

**Use when**: GitHub issue creation requiring code trawl, architecture exploration, understanding unfamiliar code patterns, investigating bugs/quirks, or any research task requiring deep codebase understanding without polluting main session context.

## Installation

```bash
# Add the marketplace
/plugin marketplace add chelma/ai-assistants

# Install the plugin
/plugin install collaborative-workflows@chelma-ai-tools
```

## Usage

Once installed, the skills and agents are automatically available:

- **tag-team skill**: Invoked when you explicitly say "tag-team" (user-initiated workflow)
- **extract-architecture skill**: Invoked when working on architecture documentation tasks
- **codebase-researcher agent**: Available via the Task tool with `subagent_type=codebase-researcher`

## Integration

These tools are designed to work together:
- **tag-team** provides the checkpoint pattern for multi-session work
- **extract-architecture** uses tag-team for progress tracking during extraction tasks
- **codebase-researcher** can be invoked from within tag-team or extract-architecture workflows for deep investigations

## Source

This plugin is maintained at [github.com/chelma/ai-assistants](https://github.com/chelma/ai-assistants).

The plugin uses symlinks to the main repository, ensuring updates to skills and agents are automatically reflected in the plugin.
