# Endpoint Creation - Reference Implementations

This directory contains complete, working examples demonstrating FetchAll and FetchOne endpoint patterns.

## Purpose

These are **instructive** reference implementations for AI coding assistants. They demonstrate:

1. **Proto-first architecture**: .proto → bin/protos → Generated code → Implementation
2. **Two-layer pattern**: Engine (business logic) + Scriptdash (permissions/frontend)
3. **Service V2.0**: Automated controller, routes, and client generation
4. **Testing patterns**: Full-stack tests using RPC clients

## Choose Your Example

### Engine Examples (Business Logic Layer)

**[action_partnerships_fetch_all/](engine/action_partnerships_fetch_all/)** - Empty Request Pattern
- **When to use**: Small datasets, dropdown lists, reference data (< 1000 records)
- **Demonstrates**: FetchAll with no parameters, simple Model.all query
- **HTTP**: `GET /v2/action_partnerships/fetch_all`

**[action_types_fetch_one/](engine/action_types_fetch_one/)** - Single ID Pattern
- **When to use**: Fetching specific record by ID
- **Demonstrates**: FetchOne with required ID parameter, Model.find(id)
- **HTTP**: `GET /v2/action_types/:id`

### Scriptdash Example (Frontend/Permissions Layer)

**[action_partnerships_fetch_all/](scriptdash/action_partnerships_fetch_all/)** - Two-Layer with Permissions
- **When to use**: Frontend needs permissions, gateway pattern
- **Demonstrates**: Scriptdash wraps Engine API, adds CanCanCan authorization
- **HTTP**: `GET /actions/v1/action_partnerships` (Scriptdash) → Engine via Core::API

## Structure

Each example includes:

```
example_name/
├── README.md                    # What this example demonstrates
├── protos/                      # Proto definitions (.proto files)
│   ├── types/v2/*.proto        # Type definitions
│   └── v2/*_endpoint.proto     # Service definitions
├── generated/                   # Generated code (show structure only)
│   └── *.rb                    # Interface, Client, Controller, Routes modules
├── impl/                        # Your implementation
│   ├── endpoint.rb             # Business logic
│   └── controller.rb           # Rails controller
└── spec/                        # Tests
    └── *_spec.rb               # RSpec request tests
```

## How to Use These Examples

1. **Copy the structure**: Use the file organization as a template
2. **Read the patterns**: Each file has inline comments explaining WHAT and WHY
3. **Adapt for your domain**: Replace ActionPartnership with your resource
4. **Follow the annotations**: Look for `# PATTERN:`, `# KEY CONCEPT:`, `# TODO:` comments

## Pattern Annotations

Files use these annotations to highlight teaching moments:

- `# PATTERN DEMONSTRATED:` - What architectural pattern this shows
- `# KEY CONCEPT:` - Important concept to understand
- `# CRITICAL:` - Must do this (required for functionality)
- `# PREFERRED:` - Best practice (recommended approach)
- `# TODO:` - Fill in with your domain-specific logic
- `# ← annotation` - Inline explanation for specific line

## Complete Workflows

See each example's README for step-by-step workflows from proto → tests.
