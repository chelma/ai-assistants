---
name: code-reviewer
description: >
  Guidance for assisting with code reviews. This skill should be used when
  explicitly requested to help review code or pull requests. Provides workflow
  for checking out code locally and principles for collaborative review.
---

# Code Reviewer

This skill provides guidance for assisting the user with code reviews in a collaborative, context-efficient manner.

## When to Use This Skill

Use this skill only when explicitly requested:
- "Help me review PR #123"
- "Can you assist with this code review?"
- "I need help reviewing this pull request"
- "Help me understand what changed in this branch"

Do NOT trigger this skill automatically. Wait for explicit request from the user.

## Collaborative Review Principles

**Claude's role**: Assist the user in reaching their own conclusions about the code, not perform a formal review independently.

**Context efficiency**: Keep responses brief unless detail is specifically requested. This preserves context window and allows the user to dig deeper where they choose.

**Token-heavy investigations**: Use sub-agents (like `codebase-researcher`) for questions likely to consume many tokens, such as:
- Understanding how a feature works across many files
- Tracing data flow through the codebase
- Identifying all usages of a pattern or API
- Architecture exploration

## Workflow

### 1. Check Out Code Locally

When asked to help review a pull request:

1. Check `~/.claude/CLAUDE.md` for guidance on where to clone repositories
2. If not specified there, use `~/workspace/claude` as the working directory
3. Use GitHub CLI (`gh`) to ensure proper authentication:
   ```bash
   gh pr checkout <PR-number> --repo <owner>/<repo>
   ```
   or
   ```bash
   gh pr view <PR-number> --repo <owner>/<repo> --json headRefName
   # then git checkout <branch>
   ```

### 2. Understand the Changes

- Use `gh pr view` and `gh pr diff` to understand the scope
- Read relevant files to build context
- For large changes, consider delegating to `codebase-researcher` sub-agent

### 3. Assist with Analysis

Respond to the user's questions and observations:
- Keep answers concise unless detail is requested
- Ask clarifying questions when the user's concern is unclear
- Point out what you notice, but let the user draw conclusions
- Suggest areas to investigate further rather than making definitive judgments

### 4. Expand as Needed

The user will add additional preferences to this skill over time based on their code review workflow.

## Resources

- User's global instructions: `~/.claude/CLAUDE.md`
- Sub-agents: `codebase-researcher` for deep investigations
- Tools: GitHub CLI (`gh`) for PR interaction
