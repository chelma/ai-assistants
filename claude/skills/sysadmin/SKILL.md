---
name: sysadmin
description: System administration assistance for personal devices (macOS, Linux). Only use when the user explicitly requests system administration help or invokes this skill directly. Do not auto-trigger based on context.
---

# System Administration

## Initialization (Required)

Upon loading this skill, **immediately** run system detection before any other work:

```bash
uname -s && uname -r && uname -m
```

Then gather OS-specific details:

**If macOS:**
```bash
sw_vers
```

**If Linux:**
```bash
cat /etc/os-release 2>/dev/null || cat /etc/*-release 2>/dev/null | head -5
```

## Report Format

After detection, provide a brief summary:

```
System detected:
- OS: [macOS/Linux distro name]
- Version: [version number]
- Platform: [architecture, e.g., x86_64, arm64]
```

Then ask how to proceed.

## Risk Assessment Framework

Before any operation, assess risk based on **blast radius** and **reversibility**.

### Risk Tiers

| Tier | Characteristics | Examples |
|------|-----------------|----------|
| **Low** | User-space, easily reversible, read-only | Reading any file, listing processes, checking disk space, viewing logs |
| **Medium** | Reversible with effort, affects running state or user configs | Editing dotfiles, installing packages, restarting services, modifying `~/.config/` |
| **High** | Difficult/impossible to reverse, system-critical, requires sudo | Modifying `/etc/fstab`, firewall rules, disk partitions, boot config, deleting data |

### Reversibility Questions

When uncertain about risk tier, ask:
1. Can I undo this with a simple command or restore?
2. Does this affect only the user or the whole system?
3. Could this prevent the system from booting or networking?
4. Am I deleting anything?

## Workflow Patterns by Risk

### Low Risk
Proceed and briefly note what you're doing.

### Medium Risk
1. **Propose**: State what you intend to do and why
2. **Backup**: Copy files before modifying (`cp file file.bak.$(date +%Y%m%d-%H%M%S)`)
3. **Execute**: Make the change
4. **Verify**: Confirm the change worked as expected

### High Risk
1. **Propose**: Clearly state the operation and its risks
2. **Confirm**: Wait for explicit user approval before proceeding
3. **Backup**: Create backups of affected files/configs
4. **Execute**: Make the change
5. **Verify**: Test that the system still functions correctly
6. **Document**: Note what was changed for future reference

## Context Management

Some commands produce verbose output that bloats the context window. Delegate these to a Haiku subagent using the Task tool.

### When to Delegate

Delegate **low-risk, read-only** operations with potentially verbose output:
- Log queries (`journalctl`, `dmesg`, `/var/log/*`)
- Process listings (`ps aux`, `top -b -n1`)
- Recursive finds (`find / -name ...`)
- Package listings (`apt list --installed`, `brew list`)
- Disk usage scans (`du -h --max-depth=N`)

### How It Works

The main session acts as a **risk-aware gatekeeper**:

1. Assess the operation using the risk framework above
2. Confirm it's low-risk and read-only
3. Delegate with a specific, bounded instruction
4. Subagent executes in its own context and returns a summary
5. Main session continues with condensed findings

### Delegation Pattern

```
Task(
  subagent_type: "general-purpose",
  model: "haiku",
  prompt: "Run [specific command] and summarize [what to extract]"
)
```

**Key principle**: The subagent receives a narrow, pre-approved operation. It executes and summarizes—no risk decisions needed. Risk intelligence stays in the main session.

### When NOT to Delegate

- Medium or high-risk operations (keep risk assessment in main context)
- Operations requiring follow-up decisions based on output
- When you need the full output for documentation

## Sudo Operations

Claude Code runs without an interactive terminal (no TTY), so `sudo` cannot prompt for passwords.

### Default Approach

1. **Prefer non-sudo alternatives** when possible:
   - Many read operations work without root (`cat`, `ls`, `ps`, `df`)
   - User-space package managers (`brew`, `pipx`, `nvm`) avoid system-level installs
   - Check if the operation truly requires elevated privileges

2. **Defer to user execution** when sudo is required:
   - Clearly state the command that needs to be run
   - Explain what it does and why it's needed
   - Let the user run it in their own terminal
   - Ask the user to report the result so work can continue

### Example Handoff

```
I need to check the nginx configuration, but it requires root access.

Please run in your terminal:
  sudo nginx -t

This tests the nginx configuration for syntax errors. Let me know
if it reports "syntax is ok" or shows any errors.
```

### Future Option: Automated Sudo

For frequently-used, trusted commands, a two-layer defense can enable automation:

1. **OS layer**: Configure NOPASSWD in `/etc/sudoers.d/` for specific commands
2. **Claude Code layer**: Allowlist those same commands in `.claude/settings.json`

This is not configured by default. When the need arises, we can set this up for specific commands.

## Backup Convention

When backing up files before modification:
```bash
cp /path/to/file /path/to/file.bak.$(date +%Y%m%d-%H%M%S)
```

This creates timestamped backups that don't collide.

## Notes

- Claude Code's permission system provides an additional safety layer
- When in doubt, ask before acting
- Prefer dry-run flags when available (e.g., `rsync --dry-run`, `apt --simulate`)
