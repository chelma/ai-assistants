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
