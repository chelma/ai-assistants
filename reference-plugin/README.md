# Reference Guides Plugin

Knowledge-based reference skills providing domain-specific patterns, best practices, and implementation guides.

## What's Included

### Skills

#### `endpoint-creation`
Create FetchAll and FetchOne endpoints across Scriptdash and Rails Engines using proto-first architecture. Provides complete reference implementations with pattern annotations and step-by-step workflows.

**Version**: v1.0 (FetchAll + FetchOne read operations)

**Use when**:
- Creating new API endpoints in Scriptdash or Rails Engines
- Implementing proto-first patterns
- Working with Better Boundaries architecture
- Setting up two-layer patterns (Engine + Scriptdash with permissions)

**What you get**:
- 10-step autonomous creation workflow
- 3 complete reference implementations (Engine FetchAll, Engine FetchOne, Scriptdash FetchAll)
- 37 patterns across 8 layers (proto, implementation, controllers, routes, testing, permissions)
- Better Boundaries architectural context
- Troubleshooting guide

## Installation

```bash
# Add the marketplace (if not already added)
/plugin marketplace add chelma/ai-assistants

# Install the plugin
/plugin install reference-guides@ai-assistants
```

## Usage

Once installed, the `endpoint-creation` skill is automatically available when working on endpoint-related tasks. The skill uses progressive disclosure - the workflow loads by default (~4k tokens), with detailed pattern documentation and reference implementations loaded only as needed.

## Integration with Collaborative Workflows

This plugin complements the `collaborative-workflows` plugin:
- Use `tag-team` skill for multi-session endpoint development
- Use `extract-architecture` skill to extract patterns from other codebases
- Use `endpoint-creation` skill to implement endpoints following established patterns

## Future Additions

Additional reference skills will be added to this plugin as they're developed.

## Source

This plugin is maintained at [github.com/chelma/ai-assistants](https://github.com/chelma/ai-assistants).

The plugin uses symlinks to the main repository, ensuring updates to skills are automatically reflected in the plugin.
