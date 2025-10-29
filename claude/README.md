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
├── README.md           # This file
├── install.sh          # Installation script for symlinking
├── settings.json       # Global user settings (permissions, env vars)
├── CLAUDE.md           # User-level instructions loaded at session start
├── .mcp.json           # MCP server configuration
├── skills/             # Custom Claude Code skills
│   └── task-planning/  # Task planning workflow skill
├── commands/           # Custom slash commands
├── memories/           # Custom memories
└── agents/             # Custom subagent definitions
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

### task-planning

Structured workflow for planning and implementing features across multiple Claude Code sessions.

**Usage**: Explicitly invoke when planning tasks:
- "Help me plan this feature"
- "Use task planning skill"
- "Create a plan for X"

**What it does**:
- Sets up `.agents/` directory structure in git repositories
- Reconciles local templates with canonical versions
- Guides interactive plan creation
- Separates planning from implementation sessions

See `skills/task-planning/SKILL.md` for full documentation.

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
