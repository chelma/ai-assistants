# Claude Code Configuration

This directory contains version-controlled configuration for Claude Code, including skills, commands, and memories.

## Setup

Run the install script to symlink this configuration to `~/.claude/`:

```bash
./install.sh
```

The script will:
- Create necessary directories if they don't exist
- Create template files (settings.json, CLAUDE.md, .mcp.json) if they don't exist
- Symlink directories: `skills/`, `commands/`, `memories/`, `agents/`
- Symlink files: `settings.json`, `CLAUDE.md`, `.mcp.json`
- Handle existing files/directories gracefully with backup options
- Can be run multiple times safely (idempotent)

## Directory Structure

```
claude/
├── README.md                    # This file
├── install.sh                   # Installation script for symlinking
├── settings.json                # Global user settings (permissions, env vars)
├── CLAUDE.md                    # User-level instructions loaded at session start
├── .mcp.json                    # MCP server configuration
├── skills/                      # Custom Claude Code skills
│   ├── aws-interface-builder/   # AWS SDK interface patterns with Factory + DI
│   ├── extract-architecture/    # Extract patterns from codebases for AI consumption
│   ├── langchain-expert-builder/  # LangChain multi-expert system builder
│   ├── python-style/            # Python coding style guidelines
│   ├── task-planning/           # Task planning workflow skill
│   └── tech-writing/            # Technical documentation guidelines
├── commands/                    # Custom slash commands (empty)
├── memories/                    # Custom memories (empty)
└── agents/                      # Custom subagent definitions
    └── codebase-researcher.md   # Deep codebase investigation with context health management
```

## How It Works

After running `install.sh`, configuration in `~/.claude/` becomes symlinks:

**Directories:**
```
~/.claude/skills -> /path/to/ai-assistants/claude/skills
~/.claude/commands -> /path/to/ai-assistants/claude/commands
~/.claude/memories -> /path/to/ai-assistants/claude/memories
~/.claude/agents -> /path/to/ai-assistants/claude/agents
```

**Files:**
```
~/.claude/settings.json -> /path/to/ai-assistants/claude/settings.json
~/.claude/CLAUDE.md -> /path/to/ai-assistants/claude/CLAUDE.md
~/.claude/.mcp.json -> /path/to/ai-assistants/claude/.mcp.json
```

This means:
- ✅ Changes in `~/.claude/` automatically appear in this git repo
- ✅ Changes in this git repo automatically appear in `~/.claude/`
- ✅ You can version control your Claude Code configuration
- ✅ Easy backup and sync across machines

## Workflow

1. **Make changes** to skills/commands/memories (either via Claude Code or directly)
2. **Check status**: `git status`
3. **Stage changes**: `git add .`
4. **Commit**: `git commit -m "Update Claude configuration"`
5. **Push**: `git push`

## Skills

### aws-interface-builder

Build production-ready Python interfaces for AWS SDK (boto3) using the Factory + Dependency Injection pattern.

**Usage**: Use when implementing AWS SDK interactions:
- Creating testable AWS service wrappers
- Multi-account AWS access with centralized credential management
- Structured interfaces to S3, EC2, Lambda, or other AWS services
- Migrating from scattered boto3 calls to structured patterns

**What it provides**:
- Complete AwsClientProvider factory class (handles credentials, sessions, regions, role assumption)
- S3 service wrapper reference implementation
- Testing patterns (mock the provider, not boto3)
- Domain exception mapping (ClientError → custom exceptions)
- 10 CRITICAL patterns for implementation and testing

**Key philosophy**: Single point of credential configuration, testable without real AWS calls, business logic separated from SDK details.

See `skills/aws-interface-builder/SKILL.md` for full documentation.

### extract-architecture

Extract architectural patterns and design decisions from existing codebases to create AI-consumable reference guides.

**Usage**: Use when tasked with documenting architecture:
- Creating pattern catalogs for specific architectural approaches
- Building reference implementations from proven production code
- Producing prescriptive "how to build" guides for AI assistants
- Extracting reusable abstractions for frameworks/libraries

**What it provides**:
- Structured workflow (reconnaissance → iterative analysis → refinement)
- Context health management (direct reading or delegated investigation via codebase-researcher)
- Flexible deliverables (pattern catalog, prescriptive guide, reference implementation)
- Builds on task-planning for progress tracking
- Optional skill conversion for distribution

**Key characteristics**: Supports both small extractions (<3k lines, direct reading) and large extractions (>3k lines, delegated to codebase-researcher). Optimizes for AI consumption with file references and progressive disclosure.

See `skills/extract-architecture/SKILL.md` for full documentation.

### langchain-expert-builder

Build LangChain-based multi-expert systems using the Expert-Task-Tool pattern. Provides production-ready Python abstractions and complete reference implementation.

**Usage**: Use when implementing LLM workflows:
- Structured output requirements (validated, type-safe LLM responses)
- Multi-turn conversations with validation retry loops
- Task-specific AI agents (code generation, analysis, classification)
- Multi-phase expert pipelines

**What it provides**:
- Copy-paste ready `core/` abstractions (Expert, Task, Tool, ValidationReport)
- Complete reference implementation (JSON transformer with two-phase workflow)
- Progressive detail loading pattern (70% token reduction in multi-phase workflows)
- Multi-stage validation with observability
- Contrasting LLM configuration examples (creative vs deterministic)

**Key philosophy**: LLMs perform best with narrow scope and deep specialization.

See `skills/langchain-expert-builder/SKILL.md` for full documentation.

### python-style

Comprehensive Python coding style guidelines extracted from Chris's production codebases.

**Usage**: Automatically invoked when working with Python code:
- Writing new Python code
- Reviewing existing Python code
- Refactoring Python modules
- Discussing Python architecture

**What it provides**:
- Core style patterns (code organization, type hints, documentation, error handling, design patterns)
- Testing patterns (loaded when writing/reviewing tests)
- Async patterns (loaded when working with async/await code)
- Priority-based guidance (CRITICAL, PREFERRED, OBSERVED)
- Context-aware pattern application with project conflict handling

**Structure**:
- `references/core.md` - Always-loaded core patterns (~850 lines)
- `references/testing.md` - Conditionally loaded testing patterns (~285 lines)
- `references/async.md` - Conditionally loaded async patterns (~25 lines)

See `skills/python-style/SKILL.md` for full documentation.

### task-planning

Structured workflow for planning and implementing features across multiple Claude Code sessions.

**Usage**: Explicitly invoke when the user mentions "task planning":
- "Use task planning skill"
- "Help me with task-planning"
- "Set up task planning workflow"

**Note**: Do NOT use for general planning requests like "help me plan this feature" - use Claude's built-in planning mode for those.

**What it does**:
- Sets up `.agents/` directory structure in git repositories
- Reconciles local templates with canonical versions
- Guides interactive plan creation
- Separates planning from implementation sessions

See `skills/task-planning/SKILL.md` for full documentation.

### tech-writing

Technical documentation guidelines for README files, GitHub issues, pull requests, and proposals.

**Usage**: Automatically invoked when creating technical documentation:
- Writing or updating README files
- Creating GitHub issues with acceptance criteria
- Drafting pull request descriptions
- Technical proposals or RFCs

**What it provides**:
- README preferences (context before instructions, third-person objective tone, pragmatic completeness)
- GitHub issue structure (title conventions, situation/request format, acceptance criteria)
- PR description guidelines (testing evidence, change summary)
- Code formatting standards (no shell prompts, complete examples, language tags)
- Visual element strategy (Mermaid diagrams, labeled screenshots)

**Structure**:
- `references/readme-guide.md` - Comprehensive README preferences
- `references/issue-guide.md` - GitHub issue and PR guidelines
- `references/exemplars/` - Reference examples of excellent documentation

**Key philosophy**: Third-person objective tone, context before instructions, pragmatic completeness.

See `skills/tech-writing/SKILL.md` for full documentation.

## Sub-agents

### codebase-researcher

Specialized research sub-agent that performs extensive codebase investigations while maintaining context health. Runs in separate context window from main session.

**Usage**: Invoked automatically or explicitly for:
- GitHub issue creation requiring code trawl
- Architecture exploration across many files
- Understanding unfamiliar code patterns
- Investigating bugs/quirks with structured findings
- Any research task requiring deep codebase understanding

**What it does**:
- Loads relevant skills based on task (python-style, langchain-expert-builder, tech-writing, extract-architecture)
- Uses Explore agent for reconnaissance
- Chunks file reading (~1500 lines max per batch)
- Monitors context health with resumability checkpoints
- Saves structured findings to disk
- Returns concise summary + file paths to main session

**Key characteristics**: Separate context window prevents pollution of main session. Designed to compose with skills ecosystem (invoked by extract-architecture for iteration-level investigations, can be invoked during task-planning for extensive reconnaissance).

**File structure**: Creates `.agents/research/<timestamp>-<task-name>/` with plan.md, progress.md, findings.md, and deliverables.

See `agents/codebase-researcher.md` for full documentation.

## Configuration Files

### settings.json
Global user-level settings including:
- **permissions**: Tool access rules (allow/deny/ask patterns)
- **env**: Environment variables applied to all sessions
- **model**: Override default AI models
- **sandbox**: Filesystem and network isolation settings

### CLAUDE.md
User-level instructions loaded at the start of every Claude Code session. Use for:
- Global coding style preferences
- Common terminology or abbreviations
- Default behaviors across all projects
- Links to personal documentation

### .mcp.json
Configuration for MCP (Model Context Protocol) servers that extend Claude's capabilities with external integrations.

## Uninstalling

To remove the symlinks and restore normal files/directories:

```bash
# Remove directory symlinks
rm ~/.claude/skills ~/.claude/commands ~/.claude/memories ~/.claude/agents

# Remove file symlinks
rm ~/.claude/settings.json ~/.claude/CLAUDE.md ~/.claude/.mcp.json

# If you had backups, restore them:
mv ~/.claude/settings.json.backup.YYYYMMDD_HHMMSS ~/.claude/settings.json
# (repeat for other files/directories if needed)
```

## Notes

- The install script creates directories in this repo if they don't exist
- Existing `~/.claude/` directories are backed up before symlinking
- The script is idempotent - safe to run multiple times
- Add unwanted files to `.gitignore` in this directory if Claude Code creates them
