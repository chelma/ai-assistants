# Alto-Workspace Quick Reference

**Purpose**: Quick lookup for endpoint-creation skill development
**Token Cost**: ~1k (use full reference for detailed context)
**Location**: `~/workspace/alto/alto-workspace/`

## Key Commands

### Proto Generation
```bash
# Generate proto files from database table
alto generate protos REPO_NAME TABLE_NAME PACKAGE_NAME \
  --endpoint_methods=fetch_one,fetch_all,create,update,delete

# Example
alto generate protos billing prescriptions billing.prescriptions
```

### Dependency Management
```bash
# Generate dependency files
alto generate deps REPO_NAME

# Update dependencies to latest
alto bump REPO_NAME [DEPENDENCY_NAMES]

# Example
alto bump billing core analytics
```

### Proto Infrastructure
```bash
# Initialize complete proto setup
alto generate init_protos REPO_NAME
```

## Configuration Schema

**File**: `config/repositories/{repo_name}.yml`

```yaml
url: scriptdash/engine-name
default_branch: main
gems:
  - engine_name
  - api_name

alto_ruby_deps:
  - name: core
    version: '~> 1.0'
    gems:
      - core_api  # Optional: specific gems only

protos:
  name: api_name
  targets:
    - type: typescript
    - type: ruby
      out: ./custom_path
  deps:
    - core
```

## SQL to Proto Type Mapping

| SQL Type | Proto Type |
|----------|-----------|
| `text`, `varchar` | `string` |
| `integer`, `smallint` | `int64` |
| `boolean` | `bool` |
| `date` | `core.types.v1.Date` |
| `numeric`, `double` | `core.types.v1.Decimal` |
| `timestamp`, `time` | `google.protobuf.Timestamp` |
| `json`, `jsonb` | `google.protobuf.Struct` |

## Standard RPC Methods

Alto generates 6 CRUD methods per proto:

1. **FetchOne** - Get single by ID
2. **FetchAll** - Get multiple by IDs array
3. **Search** - Query by indexed fields (_id fields)
4. **Create** - Create new (excludes: id, created_at, updated_at, deleted_at)
5. **Update** - Update existing by ID
6. **Delete** - Delete by ID

## Workflow: Adding Endpoint

```bash
# 1. Generate proto boilerplate
alto generate protos actions prescriptions actions.prescriptions

# 2. Update repo config if adding new dependencies
# Edit: config/repositories/actions.yml

# 3. Regenerate dependency files
alto generate deps actions

# 4. Generate language-specific bindings
cd {repo}/protos && make generate

# 5. Implement handlers and tests
```

## Key Files

| File | Purpose |
|------|---------|
| `bin/alto` | CLI entry point |
| `lib/alto/config.rb` | Configuration system (623 lines) |
| `lib/alto/protos.rb` | Proto data structures (286 lines) |
| `lib/alto/deps.rb` | Dependency resolution (116 lines) |
| `lib/alto/commands/bump.rb` | Dependency updates (238 lines) |
| `lib/alto/commands/generators/protos.rb` | Proto generation (127 lines) |
| `config/repositories/*.yml` | Repository definitions (58 repos) |
| `lib/alto/templates/protos/*.tt` | Proto templates (ERB) |

## Version Constraints

- `'~> 1.0'` - >= 1.0.0, < 2.0.0
- `'~> 1.5'` - >= 1.5.0, < 2.0.0
- `'latest'` - Fetches latest git tag
- `'>= 1.0'` - Greater than or equal
- `'= 1.0.0'` - Exact version

## Important Concepts

**Repository**: Managed by YAML config in `config/repositories/`  
**AltoDep**: Alto repository dependency with version or branch  
**ProtoTarget**: Code generation target (typescript, python, ruby)  
**MethodConfig**: RPC method configuration with request/response messages  
**EndpointConfig**: Service definition for a resource

## Common Patterns

### Add Dependency
```yaml
alto_ruby_deps:
  - name: new_service
    version: '~> 1.0'
    gems:
      - new_service_api
```

### Add Proto Target
```yaml
protos:
  targets:
    - type: typescript
    - type: ruby
      out: ./custom_location
```

### Local Development
```bash
alto generate deps --local core,actions
```

## Token-Efficient Usage

- **Quick lookup**: This file (~1k tokens)
- **Implementation details**: Full reference (~5-6k tokens)
- **Deep dive on config system**: Read `lib/alto/config.rb` directly
- **Proto generation logic**: Read `lib/alto/protos.rb` directly

