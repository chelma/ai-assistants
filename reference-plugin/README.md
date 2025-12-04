# Reference Guides Plugin

Knowledge-based reference skills providing domain-specific patterns, best practices, and implementation guides.

## What's Included

### Skills

#### `better-boundaries`
Understand and apply Better Boundaries architecture through hands-on endpoint creation using proto-first development. Provides complete reference implementations, comprehensive patterns, and architectural context for building scalable Rails applications.

**Version**: v1.0 (FetchAll + FetchOne read operations)

**Use when**:
- Creating new API endpoints in Scriptdash or Rails Engines
- Understanding Module→Engine→Boxcar migration philosophy
- Learning proto-first architecture patterns and code generation
- Working with alto-workspace tooling
- Investigating Core::API design patterns for service boundaries

**What you get**:
- 9-step autonomous endpoint creation workflow
- 3 deployment patterns (Engine-only, Intermediate, Two-layer)
- Complete reference implementations with tests and pattern annotations
- Comprehensive pattern documentation by layer (proto, implementation, controllers, testing)
- Better Boundaries architectural philosophy and migration strategies
- alto-workspace integration guide
- Troubleshooting reference

## Installation

```bash
# Add the marketplace (if not already added)
/plugin marketplace add chelma/ai-assistants

# Install the plugin
/plugin install reference-guides@chelma-ai-tools
```

## Usage

Once installed, the `better-boundaries` skill is automatically available when working on Better Boundaries architecture or endpoint-related tasks. The skill uses progressive disclosure - the core workflow and philosophy load by default, with detailed pattern documentation and reference implementations loaded only as needed.

## Integration with Collaborative Workflows

This plugin complements the `collaborative-workflows` plugin:
- Use `tag-team` skill for multi-session endpoint development
- Use `extract-architecture` skill to extract patterns from other codebases
- Use `better-boundaries` skill to implement endpoints and learn architectural patterns

## Future Additions

Additional reference skills will be added to this plugin as they're developed.

## Source

This plugin is maintained at [github.com/chelma/ai-assistants](https://github.com/chelma/ai-assistants).

The plugin uses symlinks to the main repository, ensuring updates to skills are automatically reflected in the plugin.
