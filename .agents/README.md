# AI Architecture References

This directory contains architecture references designed for AI coding assistant consumption.

## Purpose

Architecture references document patterns, design decisions, and reusable abstractions extracted from codebases. They enable AI assistants to understand and replicate architectural approaches consistently across projects.

## Directory Structure

```
.agents/
├── README.md          # This file (overview)
├── FORMAT.md          # Detailed format specification
└── references/        # Architecture references
    └── <reference-name>/
        ├── README.md      # Main guide
        ├── references/    # Detailed patterns (on-demand)
        └── assets/        # Reference implementations
```

## Using References

**For AI Assistants:**
1. Read `FORMAT.md` to understand the reference format
2. Browse `references/` directory to find relevant references
3. Read reference `README.md` for essential patterns and workflows
4. Load reference `references/` files when need detailed pattern documentation
5. Copy code from `assets/` to user projects (not loaded to context)

**For Engineers:**
- Create new references using the `extract-architecture` skill
- Convert references to assistant-specific formats (e.g., Claude Skills)
- Version control references via git for team sharing

## Key Principles

**Progressive Disclosure**: References use layered information structure to optimize token usage. README.md (~2-3k tokens) provides essential info; references/ (~5-8k tokens each) provide details on-demand; assets/ contain copy-paste code not loaded to context.

**Assistant-Agnostic**: Core format works across AI coding assistants (Claude Code, Copilot, Cursor, Windsurf, etc.). Assistant-specific metadata is optional.

**Token-Efficient**: File references instead of inline code, minimal duplication, self-documenting implementations. Typical reference produces 50k+ tokens of content but AI only loads 2-10k tokens for normal usage.

## Format Details

See `FORMAT.md` for comprehensive format specification including:
- YAML frontmatter structure
- Content organization patterns
- Token optimization strategies
- Reference type examples
- Writing conventions

## Creating References

Use the `extract-architecture` skill to extract patterns from codebases. The skill will:
1. Guide you through extraction workflow
2. Offer output format choice (shared reference or Claude Skill)
3. Generate references in this directory structure automatically

See `FORMAT.md` for manual reference creation guidance.
