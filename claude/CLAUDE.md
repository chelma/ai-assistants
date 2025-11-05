# Claude Code User-Level Instructions

---

## Persistent Guidance

Long-term preferences and instructions that should apply across all projects indefinitely.

### Token Efficiency

**IMPORTANT** Any additions to this global CLAUDE.md file should be carefully considered for token efficiency, as this content is loaded into context for every Claude Code session. Keep entries concise and remove outdated guidance regularly.

### Git Repository Workspace

When needing to clone or examine external Git repositories, use `/Users/chris.helma/workspace/claude` as the working directory. Never clone repositories into the current working directory unless explicitly instructed.

### GitHub Access

When needing to interact with GitHub, use the locally installed GitHub CLI (`gh`) to ensure you have acess to the human's credentials GitHub credentials.

---

## Temporary Context

Short-term guidance relevant for current work (weeks/months). Review and prune regularly.

### Claude Skills Documentation

When discussing Claude Skills or Claude Code Skills, fetch these reference docs if not already loaded:
- https://www.anthropic.com/news/skills
- https://anthropic.mintlify.app/en/docs/claude-code/skills

