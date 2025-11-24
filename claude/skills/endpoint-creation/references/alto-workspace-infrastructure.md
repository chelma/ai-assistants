# Alto Workspace: Infrastructure Reference for Endpoint Creation

**Document Version**: 1.0
**Created**: 2025-11-24
**Purpose**: Comprehensive reference for alto-workspace architecture, CLI commands, and YAML configuration patterns to support endpoint-creation skill development
**Token Cost**: ~5-6k tokens covering repository structure, commands, configuration schemas, and integration patterns

---

## Table of Contents

1. [Repository Overview](#repository-overview)
2. [CLI Architecture](#cli-architecture)
3. [Configuration System](#configuration-system)
4. [Proto Generation Pipeline](#proto-generation-pipeline)
5. [Dependency Management](#dependency-management)
6. [Integration with Endpoint Workflow](#integration-with-endpoint-workflow)
7. [Common Patterns & Examples](#common-patterns--examples)

---

## Repository Overview

### High-Level Purpose

Alto-workspace is the central orchestration layer for the Alto engineering environment. It:
- Manages configuration for 58+ repositories across multiple domains
- Provides CLI tools for generating code from templates (dependencies, CI/CD, protos, engines)
- Coordinates dependency resolution across Ruby, Python, and JavaScript ecosystems
- Integrates with proto3/buf for API endpoint generation
- Manages CI/CD workflow configuration (GitHub Actions, CircleCI, Concourse)

### Directory Structure

```
alto-workspace/
├── bin/alto                          # CLI entry point (Thor-based)
├── lib/alto/
│   ├── alto.rb                       # Main module loader (Zeitwerk)
│   ├── config.rb                     # Configuration system (20.9k lines)
│   ├── directory.rb                  # Directory resolution utilities
│   ├── deps.rb                       # Dependency resolution logic
│   ├── protos.rb                     # Proto message/endpoint config (286 lines)
│   ├── shell.rb                      # Shell command execution
│   ├── commands/                     # CLI command implementations
│   │   ├── base_command.rb           # Common command utilities
│   │   ├── generate.rb               # Generate command router
│   │   ├── bump.rb                   # Dependency bumping (238 lines)
│   │   ├── up.rb                     # Repository sync
│   │   ├── vendor_protos.rb          # Proto vendoring
│   │   └── generators/               # 30+ generator implementations
│   │       ├── protos.rb             # Proto generation from DB tables
│   │       ├── init_protos.rb        # Initialize proto structure
│   │       ├── deps.rb               # Dependency file generation
│   │       ├── engine.rb             # Rails engine scaffolding
│   │       └── deps_generator/
│   │           ├── ruby_context.rb   # Ruby-specific dep generation
│   │           └── python_context.rb # Python-specific dep generation
│   └── templates/                    # 23 template directories
│       ├── protos/
│       │   ├── message.proto.tt      # Proto message template
│       │   ├── endpoint.proto.tt     # Proto service template
│       │   └── gen/                  # Language-specific gen targets
│       └── [other templates]         # Engine, gem, JS library, etc.
└── config/
    ├── repositories/                 # 58 YAML repo definitions
    │   ├── actions.yml
    │   ├── core.yml
    │   ├── api.yml
    │   └── [others]
    ├── apps/apps.yaml                # Application definitions
    └── ml-apps/ml-apps.yaml          # ML application definitions
```

### Key Technologies

- **Language**: Ruby 3.x with Sorbet type checking
- **CLI Framework**: Thor (command-line scripting)
- **Configuration**: PSYCH (YAML parsing), Zeitwerk (autoloading)
- **Type System**: Sorbet (strict typing with T::Struct)
- **Templates**: ERB (.tt files)
- **Proto Tooling**: buf.build, proto3
- **Package Management**: Bundler (Ruby), yarn (JS), pip (Python)

---

## CLI Architecture

### Entry Point

**File**: `/Users/chris.helma/workspace/alto/alto-workspace/bin/alto`

```ruby
#!/usr/bin/env ruby
# frozen_string_literal: true

require "pathname"
original_bundle_gemfile = ENV["BUNDLE_GEMFILE"]
ENV["BUNDLE_GEMFILE"] ||= File.expand_path("../../Gemfile", Pathname.new(__FILE__).realpath)
require "bundler/setup"

require 'thor'
require_relative '../lib/alto'

ENV["BUNDLE_GEMFILE"] = original_bundle_gemfile

class AltoCommand < Thor
  def self.exit_on_failure?
    true
  end

  desc 'up', 'Pull the latest updates from Alto repositories'
  subcommand :up, Alto::Commands::Up

  desc 'dir', 'Return common alto directories.'
  subcommand :dir, Alto::Commands::Dir

  desc 'generate', 'Generate code from templates'
  subcommand :generate, Alto::Commands::Generate

  desc 'mv', 'Refactor a ruby file to a new destination'
  subcommand :mv, Alto::Commands::Mv

  desc 'analyze_refs', 'Analyze reference graph of ruby library'
  subcommand :analyze_refs, Alto::Commands::AnalyzeRefs

  desc 'install', 'Install or set up specific dependencies'
  subcommand :install, Alto::Commands::Install

  desc 'start', 'Start up a local development server or servers'
  subcommand :start, Alto::Commands::Start

  desc 'bump', 'Bump dependencies for a repo'
  subcommand :bump, Alto::Commands::Bump

  desc 'vendor_protos', 'Set up vendored proto dependencies for a repository'
  subcommand :vendor_protos, Alto::Commands::VendorProtos

  desc 'engines', 'A collection of commands for working with engines'
  subcommand :engines, Alto::Commands::Engines
end

AltoCommand.start
```

### Core Commands for Endpoint Creation

#### 1. `alto generate protos` - Proto Generation

**Command Structure**:
```
alto generate protos REPO_NAME TABLE_NAME PACKAGE_NAME [OPTIONS]
```

**Arguments**:
- `REPO_NAME`: Repository identifier from config (e.g., "actions", "billing")
- `TABLE_NAME`: PostgreSQL table name to generate protos from
- `PACKAGE_NAME`: Package namespace (e.g., "actions.v1")

**Options**:
- `--dbname`: Database name (default: `rxapp_development`)
- `--version`: Package version (default: `v1`)
- `--endpoint_methods`: RPC methods to generate (default: `['fetch_all', 'fetch_one', 'create', 'update', 'delete']`)
  - Valid options: `fetch_all`, `fetch_one`, `search`, `create`, `update`, `delete`

**Implementation** (`lib/alto/commands/generators/protos.rb`):
- Reads PostgreSQL table schema using `psql` command
- Maps SQL types to proto types (see mapping below)
- Generates two proto files:
  1. **message.proto** - Data model definition
  2. **endpoint.proto** - RPC service definition

**Type Mapping** (from `lib/alto/protos.rb`):
```ruby
'character varying', 'text'     → 'string'
'boolean'                       → 'bool'
'integer', 'smallint'          → 'int64'
'date'                         → 'core.types.v1.Date'
'numeric', 'double precision'  → 'core.types.v1.Decimal'
'*time*'                       → 'google.protobuf.Timestamp'
'*json*'                       → 'google.protobuf.Struct'
other                          → 'google.protobuf.Any'
```

**Example Command**:
```bash
alto generate protos actions prescriptions actions.prescriptions \
  --dbname=scriptdash_development \
  --version=v1 \
  --endpoint_methods=fetch_one,fetch_all,create,update,delete
```

**Generated Files**:
- `protos/src/actions/prescriptions/types/v1/prescription.proto`
- `protos/src/actions/prescriptions/v1/prescriptions_endpoint.proto`

#### 2. `alto generate deps` - Dependency Configuration

**Command Structure**:
```
alto generate deps [REPO_NAMES...] [OPTIONS]
```

**Arguments**:
- `REPO_NAMES`: One or more repository names (optional - generates for all if omitted)

**Options**:
- `--local`: Treat specified dependencies as local development versions
- `--alto_only`: Only generate Alto repository dependencies for Rails engines

**Purpose**: Generates language-specific dependency files:
- **Ruby**: `gemfiles/alto.rb` with evaluated Alto dependencies
- **Python**: `requirements*.txt` files with pinned versions
- Updates main Gemfile/Pipfile with `eval_gemfile` directives

**Implementation** (`lib/alto/commands/generators/deps.rb`):
- Routes to language-specific contexts (RubyContext, PythonContext)
- RubyContext generates `gemfiles/alto.rb` and inserts `eval_gemfile` statements
- Handles local vs. version-pinned dependencies based on config
- Runs `bundle install` after generation

#### 3. `alto bump` - Dependency Updates

**Command Structure**:
```
alto bump REPO_NAME [DEPENDENCY_NAMES...] [OPTIONS]
```

**Purpose**: Updates Alto dependencies to latest versions and regenerates type information

**Process**:
1. Validates repo and dependencies exist in config
2. `bundle install` to fetch uninstalled gems
3. `bundle update --conservative` for specified gems
4. Syncs Rails engine migrations (scriptdash-specific)
5. Runs `bundle exec tapioca gem` to update Sorbet RBI files

**Key Workflow**:
```ruby
def bump
  deps = select_deps                    # Validate deps
  gems = deps.flat_map { |d| d.gems }  # Resolve gem names
  
  Bundler.with_unbundled_env do
    inside(dir) do
      install_gems                      # bundle install
      update_gems(gems, repo)          # bundle update --conservative
      sync_engine_migrations(gems)     # for scriptdash only
      update_gem_types(gems)           # tapioca gem
    end
  end
end
```

#### 4. `alto generate init_protos` - Proto Infrastructure Setup

**Command Structure**:
```
alto generate init_protos REPO_NAME
```

**Purpose**: Initialize complete proto infrastructure in a repository

**Setup Steps**:
1. Creates `.gitignore` for proto artifacts
2. Initializes buf configuration
3. Generates language-specific proto packages:
   - **TypeScript**: npm package in `protos/gen/typescript/`
   - **Python**: Python package in `protos/gen/python/`
   - **Ruby**: Skipped (handled separately as published gem)
4. Sets up CI workflows (GitHub Actions or CircleCI)
5. Configures semantic-release

#### 5. `alto generate` - Full Generator Registry

**Available Subcommands**:
```
Commands:
  alto generate agents REPO                    # Configure agents
  alto generate alerts NAME                    # Alert YAML files
  alto generate circleci NAME                  # CircleCI config
  alto generate dashboards NAME                # Dashboard files
  alto generate deps NAME                      # Dependencies
  alto generate engine NAME                    # New Rails engine
  alto generate gem NAME                       # New Ruby gem
  alto generate github_actions NAME            # GitHub Actions config
  alto generate js_library NAME                # JS library scaffolding
  alto generate kubernetes                     # K8s config
  alto generate mlmodule NAME                  # Python ML module
  alto generate mlpipeline NAME                # ML Concourse pipeline
  alto generate pipeline NAME                  # Concourse pipeline
  alto generate protos TABLE PACKAGE VERSION   # Proto from DB table
  alto generate prpipeline NAME                # PR Concourse pipeline
  alto generate proto_target_typescript REPO NAME     # TypeScript proto package
  alto generate proto_target_python REPO NAME         # Python proto package
  alto generate proto_target_ruby REPO NAME           # Ruby proto package
  alto generate buf REPO_NAME                  # buf.build config
  alto generate init_protos REPO_NAME          # Full proto setup
  alto generate rubocop NAME                   # Rubocop config
  alto generate semantic_release NAME          # Semantic-release setup
  alto generate yard NAME                      # YARD doc config
```

---

## Configuration System

### Architecture

The configuration system is defined in `lib/alto/config.rb` (623 lines) using Sorbet structs with strict typing. It parses YAML files from `config/repositories/*.yml` and `config/apps/` directories.

### Repository Configuration Schema

**File Format**: `config/repositories/{repo_name}.yml`

```yaml
# Core repository metadata
url: scriptdash/{repo-name}              # GitHub repository URL
default_branch: main                     # Default git branch (main or master)

# Ruby Dependencies
shared_ruby_deps:                        # External Ruby gems (non-Alto)
  - core                                 # Gem name(s)
  - rails_core
  - sidekiq

alto_ruby_deps:                          # Alto repository dependencies
  - name: core                           # Repo name (must exist in config)
    version: '~> 1.0'                    # Version constraint OR branch
    gems:                                # Optional: specific gems to pull
      - core_api
  - name: analytics
    version: '~> 1.0'
    gems:
      - analytics_api

# Python Dependencies
shared_py_deps:                          # External Python packages
  - requests
  - pandas

alto_py_deps:                            # Alto Python dependencies
  - name: core
    version: '~> 1.0'

# JavaScript Dependencies
shared_js_deps:                          # External npm packages
  - react
  - lodash

alto_js_deps:                            # Alto npm packages
  - name: core
    version: '~> 1.0'

# Gems this repo publishes
gems:                                    # Ruby gems provided by this repo
  - billing_engine
  - billing_api

# Rubocop Configuration
rubocop_includes:                        # Additional rubocop config files
  - '.rubocop_todo.yml'

# CI/CD Configuration
github_actions:                          # GitHub Actions workflow collections
  workflows:
    - build_and_test_ruby_engine         # Workflow collection names
    - publish_proto_package_typescript   # See Config::GithubActionsWorkflowCollection
  test_ruby_environment:                 # Environment variables for Ruby tests
    RAILS_ENV: test

circle_ci:                               # CircleCI configuration
  workflows:
    - BuildAndTestRubyEngine
  test_ruby_parallelism: 4               # Parallel test runners
  test_ruby_environment:
    CUSTOM_VAR: value

# Ownership & Organization
owner: unified-workflow                  # Team owner (from .yardowners.yml)
domain: actions                          # Domain/business area
reviewers:                               # PR reviewers (github teams)
  - team-name

# Proto Configuration
protos:
  name: actions_api                      # Package name for published protos
  targets:                               # Code generation targets
    - type: typescript                   # Target language: typescript|python|ruby
    - type: ruby
      out: ./actions_api                 # Optional: custom output directory
  deps:                                  # Proto package dependencies
    - core

# Optional
git_host: github.com                     # Custom git host (default: github.com)
description: "Repository description"    # For documentation
```

### Complete Configuration Examples

**Minimal Repository** (`config/repositories/api.yml`):
```yaml
---
url: scriptdash/alto-api
default_branch: master
```

**Simple Engine** (`config/repositories/actions.yml`):
```yaml
---
url: scriptdash/engine-actions
default_branch: main
gems:
  - actions_engine
  - actions_api
shared_ruby_deps:
  - core
  - rails_core
  - rails_app
  - sidekiq
alto_ruby_deps:
  - name: core
    version: '~> 1.0'
  - name: analytics
    version: '~> 1.0'
    gems:
      - analytics_api
  - name: experimentation
    version: '~> 1.0'
  - name: operations
    version: '~> 1.0'
    gems:
      - operations_api
  - name: boxcar
    version: '~> 2.0'
github_actions:
  workflows:
    - build_and_test_ruby_engine
    - publish_proto_package_typescript
    - tapioca_gem
owner: unified-workflow
domain: actions
protos:
  name: actions_api
  targets:
    - type: typescript
    - type: ruby
      out: ./actions_api
  deps:
    - core
```

**Complex Engine** (`config/repositories/billing.yml`):
```yaml
---
url: scriptdash/engine-billing
default_branch: main
gems:
  - billing_engine
  - billing_api
shared_ruby_deps:
  - core
  - rails_core
  - sidekiq
alto_ruby_deps:
  - name: core
    version: '~> 1.0'
  - name: boxcar
    version: '~> 1.0'
  - name: experimentation
    version: '~> 1.0'
  - name: patients
    version: '~> 1.0'
    gems:
      - patients_api
  - name: prescriptions
    version: '~> 1.0'
    gems:
      - prescriptions_api
  - name: voice-agents
    version: '~> 1.0'
    gems:
      - voice_agents_api
github_actions:
  workflows:
    - build_and_test_ruby_engine
    - publish_proto_package_typescript
    - tapioca_gem
owner: care
domain: billing
protos:
  name: billing_api
  targets:
    - type: typescript
    - type: ruby
      out: ./billing_api
  deps:
    - core
```

### Configuration Classes (Sorbet T::Struct)

```ruby
# Dependency specification
class AltoDep < T::Struct
  prop :name, String              # Repo name
  prop :version, T.nilable(String) # Version constraint (e.g., '~> 1.0')
  prop :branch, T.nilable(String) # Git branch (alternative to version)
  prop :local, T::Boolean         # Use local development version
  prop :gems, T.nilable(T::Array[String]) # Specific gems to use
end

# Proto code generation target
class ProtoGenerationTarget < T::Struct
  prop :type, ProtoGenerationTargetType # :typescript, :python, :ruby
  prop :out, T.nilable(String) # Custom output directory

  def package_root
    out || "protos/gen/#{type.serialize}"
  end
end

# Proto package configuration
class ProtosConfig < T::Struct
  prop :name, String # Package name
  prop :targets, T::Array[ProtoGenerationTarget] # Code gen targets
  prop :deps, T::Array[String] # Proto dependencies
end

# Main repository configuration
class Repo < T::Struct
  prop :name, String
  prop :url, String
  prop :default_branch, String
  prop :description, String
  prop :gems, T::Array[String]
  prop :shared_ruby_deps, T::Array[String]
  prop :alto_ruby_deps, T::Array[AltoDep]
  prop :shared_py_deps, T::Array[String]
  prop :alto_py_deps, T::Array[AltoDep]
  prop :shared_js_deps, T::Array[String]
  prop :alto_js_deps, T::Array[AltoDep]
  prop :circle_ci, T.nilable(CircleCI)
  prop :github_actions, T.nilable(GithubActions)
  prop :owner, T.nilable(String)
  prop :domain, T.nilable(String)
  prop :protos, ProtosConfig
  prop :git_host, T.nilable(String)

  # Helper methods
  def ruby_repo?
    !alto_ruby_deps.empty? || !shared_ruby_deps.empty?
  end

  def python_repo?
    !alto_py_deps.empty? || !shared_py_deps.empty?
  end

  def rails_engine?
    gems.any? { |g| g.end_with?('_engine') }
  end
end
```

### Configuration Loading Process

```ruby
# 1. Load all YAML files from config/repositories/*.yml
repository_files = Dir.glob('config/repositories/*.yml')

# 2. For each YAML:
Config::Loader.new(
  repository_files: repository_files,
  apps_file: 'config/apps/apps.yaml',
  ml_apps_file: 'config/ml-apps/ml-apps.yaml'
).load

# 3. Create Config instance with:
Config.new(
  gopath: ENV['GOPATH'] || File.join(Dir.home, 'go'),
  repositories: { action: Repo(...), billing: Repo(...), ... },
  applications: { app_name: Application(...), ... },
  ml_applications: { ml_app: MLApplication(...), ... }
)
```

---

## Proto Generation Pipeline

### Proto Message Structure

**File**: `lib/alto/protos.rb` (286 lines)

```ruby
# Represents a field in a proto message
class FieldConfig < T::Struct
  prop :name, String           # Field name
  prop :type, String           # Proto type (string, int64, etc.)
  prop :nullable, T::Boolean   # Optional or required
  prop :comment, T.nilable(String) # Documentation
  prop :repeated, T::Boolean   # Array/repeated field
end

# Represents a proto message type
class MessageConfig < T::Struct
  prop :package, String        # Package namespace
  prop :name, String           # Message name
  prop :version, String        # Version (default: 'v1')
  prop :fields, T::Array[FieldConfig] # Fields

  def package_name          # "package.v1"
  def types_package_name    # "package.types.v1"
  def fully_qualified_name  # "package.types.v1.MessageName"
  def message_file_path     # "package/types/v1/message_name.proto"
  def endpoint_file_path    # "package/v1/messages_endpoint.proto"
end

# Represents an RPC method
class MethodConfig < T::Struct
  prop :name, String                        # Method name (Create, Update, etc.)
  prop :params_message, T.nilable(MessageConfig) # Params message
  prop :request_message, MessageConfig      # Request message
  prop :response_message, MessageConfig     # Response message
end

# Represents a resourceful endpoint
class EndpointConfig < T::Struct
  prop :name, String           # Endpoint name (MessagesEndpoint)
  prop :resource, MessageConfig # The resource being exposed
  prop :api_methods, T::Array[MethodConfig] # RPC methods

  # Factory method to generate endpoint with standard methods
  def self.for_resource(message, include_methods)
    # include_methods: ['fetch_all', 'fetch_one', 'create', 'update', 'delete']
    # Generates appropriate MethodConfig objects
  end
end
```

### Proto Template Generation

**Message Template** (`lib/alto/templates/protos/message.proto.tt`):
```protobuf
syntax = "proto3";

package <%= resource.types_package_name %>;

<%- resource.imports.each do |import| -%>
import "<%= import %>";
<%- end -%>

message <%= resource.name %> {
  <%- resource.fields.each_with_index do |field, i| -%>
  <%- if field.comment -%>
  // <%= field.comment %>
  <%- end -%>
  <%= field.declaration(i + 1) %>
  <%- end -%>
}
```

**Endpoint Template** (`lib/alto/templates/protos/endpoint.proto.tt`):
```protobuf
syntax = "proto3";

package <%= endpoint.resource.package_name %>;

<%- endpoint.imports.each do |import| -%>
import "<%= import %>";
<%- end -%>

<%- endpoint.api_methods.each do |method| -%>
<%- method.messages.each do |message| -%>
message <%= message.name %> {
  <%- message.fields.each_with_index do |field, i| -%>
  <%- if field.comment -%>
  // <%= field.comment %>
  <%- end -%>
  <%= field.declaration(i + 1) %>
  <%- end -%>
}

<%- end -%>
<%- end -%>

service <%= endpoint.name %> {
  option (opts.service_value) = {version: "v2.0"};
  <%- endpoint.api_methods.each do |method| -%>

  rpc <%= method.name %>(<%= method.request_message.name %>) returns (<%= method.response_message.name %>);
  <%- end -%>
}
```

### Standard RPC Methods

Alto generates six standard CRUD methods from a message:

#### 1. **FetchOne** - Get single record
```proto
rpc FetchOne(MessagesEndpointFetchOneRequest) returns (MessagesEndpointFetchOneResponse);

message MessagesEndpointFetchOneRequest {
  int64 id = 1;  # ID field from resource
}

message MessagesEndpointFetchOneResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  Message data = 2;  # Nullable response data
}
```

#### 2. **FetchAll** - Get multiple records by IDs
```proto
rpc FetchAll(MessagesEndpointFetchAllRequest) returns (MessagesEndpointFetchAllResponse);

message MessagesEndpointFetchAllRequest {
  repeated int64 ids = 1;  # Multiple IDs
}

message MessagesEndpointFetchAllResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  repeated Message data = 2;  # Array response
}
```

#### 3. **Search** - Query by indexed fields
```proto
rpc Search(MessagesEndpointSearchRequest) returns (MessagesEndpointSearchResponse);

message MessagesEndpointSearchRequest {
  # All fields ending with _id from the resource
  int64 category_id = 1;
  int64 user_id = 2;
}

message MessagesEndpointSearchResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  repeated Message data = 2;
}
```

#### 4. **Create** - Create new record
```proto
rpc Create(MessagesEndpointCreateRequest) returns (MessagesEndpointCreateResponse);

message MessagesEndpointCreateParams {
  # All fields except: id, created_at, updated_at, deleted_at
  string title = 1;
  string description = 2;
}

message MessagesEndpointCreateRequest {
  MessagesEndpointCreateParams params = 1;
}

message MessagesEndpointCreateResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  Message data = 2;
}
```

#### 5. **Update** - Update existing record
```proto
rpc Update(MessagesEndpointUpdateRequest) returns (MessagesEndpointUpdateResponse);

message MessagesEndpointUpdateParams {
  # Same as Create (mutable fields)
}

message MessagesEndpointUpdateRequest {
  int64 id = 1;  # Resource ID to update
  MessagesEndpointUpdateParams params = 2;
}

message MessagesEndpointUpdateResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  Message data = 2;
}
```

#### 6. **Delete** - Delete record
```proto
rpc Delete(MessagesEndpointDeleteRequest) returns (MessagesEndpointDeleteResponse);

message MessagesEndpointDeleteRequest {
  int64 id = 1;
}

message MessagesEndpointDeleteResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  Message data = 2;
}
```

---

## Dependency Management

### Dependency Resolution System

**File**: `lib/alto/deps.rb` (116 lines)

```ruby
module Deps
  # Core resolution function
  def self.resolve_deps(alto_deps, local:, pipeline: false, pull_request: false)
    # Input: Array of AltoDep objects
    # Output: Array of hashes with name, repo_name, url, version, path, local
    alto_deps.map do |dep|
      resolve_dependency_data(dep, local: local, pipeline: pipeline, pull_request: pull_request)
    end.flatten
  end

  # Single dependency resolution
  def self.resolve_dependency_data(dep, local:, pipeline: false, pull_request: false)
    dep_repo = Config.instance.repositories[dep.name.to_sym]
    git = Shell::Git.new(dep_repo)
    is_local = dep.local || local.include?(dep.name)

    version = version(git, dep, is_local, pipeline, pull_request)

    # Filter gems if specific subset requested
    gems = dep_repo.gems
    gems = gems.select { |name| dep.gems.include?(name) } if dep.gems

    # Return resolved dependency for each gem
    gems.map do |name|
      {
        name: name,
        repo_name: dep_repo.name,
        url: dep_repo.url,
        branch: dep.branch,
        version: version,
        path: git.repo_root,
        local: is_local,
        git_host: dep_repo.git_host,
      }
    end
  end

  # Version resolution logic
  def self.version(git, dep, local, pipeline, pull_request)
    return nil if local  # Local versions don't need version pins

    if dep.version == 'latest'
      git.fetch_origin_default unless pipeline
      version = git.current_tag[1..]  # Strip 'v' prefix
      if pull_request
        version = "#{version}.pre.#{git.local_commit_sha[0, 7]}"
      end
      version
    else
      dep.version  # Use specified constraint
    end
  end
end
```

### Gemfile Generation

**Ruby Context** (`lib/alto/commands/generators/deps_generator/ruby_context.rb`):

```ruby
def generate_deps
  generate_shared_deps unless @alto_only
  generate_alto_deps
  install if changed
end

private

def generate_shared_deps
  repo.shared_ruby_deps.each do |dep_name|
    copy_gemfile(dep_name)        # Copy gemfiles/{dep_name}.rb
    insert_eval_gemfile(dep_name) # Add to Gemfile
  end
end

def generate_alto_deps
  return if repo.alto_ruby_deps.empty?

  mark_changed
  copy_template('gemfiles/alto.rb.erb', 'gemfiles/alto.rb')

  if repo.rails_engine?
    copy_template('github/dependabot.yml.erb', '.github/dependabot.yml')
  end

  insert_eval_gemfile('alto')
end

def insert_eval_gemfile(dep_name)
  flag = "# alto-workspace dependencies\n"
  new_str = "eval_gemfile './gemfiles/#{dep_name}.rb'\n"

  # Insert into Gemfile if not already present
  File.read(gemfile_path).include?(new_str) ? true : insert_into_file(gemfile_path, new_str, { before: flag })
end
```

### Version Constraints

Alto uses standard Ruby version constraint syntax:

- `'~> 1.0'` - Compatible: >= 1.0.0, < 2.0.0 (minor version bump allowed)
- `'~> 1.5'` - Compatible: >= 1.5.0, < 2.0.0
- `'>= 1.0'` - Greater than or equal
- `'= 1.0.0'` - Exact version
- `'latest'` - Fetches latest git tag

### Local Development

During development, use `local: true` in config or pass `--local` to commands:

```bash
alto generate deps --local core,actions
```

This:
1. Uses local repository paths instead of published gem versions
2. Points Bundler to local checkout for immediate testing
3. Bypasses version constraints

---

## Integration with Endpoint Workflow

### Files Modified When Creating Endpoints

When adding a new endpoint to a repository, these files typically need updates:

#### 1. **Repository Configuration** (`config/repositories/{repo}.yml`)

**When to update**: When adding new dependencies or proto targets

```yaml
# Add new proto dependencies if needed
protos:
  name: my_api
  targets:
    - type: typescript
    - type: ruby
      out: ./my_api
  deps:
    - core      # Add new dependency
    - billing   # Add new dependency
```

#### 2. **Proto Configuration** (in repository)

**Files**: 
- `protos/src/{package}/types/v1/{message}.proto` - Generated message definitions
- `protos/src/{package}/v1/{message}_endpoint.proto` - Generated service definitions
- `protos/buf.yaml` - buf tool configuration

**Workflow**:
```bash
# Generate protos from database table
alto generate protos {repo_name} {table_name} {package.name}

# Or manually create/edit proto files
# Then regenerate language-specific bindings
cd protos && make generate
```

#### 3. **Dependency Updates**

When new proto packages are added:

```bash
# Update Gemfile for Ruby proto dependencies
alto generate deps {repo_name}

# Update package.json for TypeScript bindings
# Update pyproject.toml for Python bindings
# These happen automatically via protos/Makefile
```

#### 4. **Repository Configuration YAML**

**When required**:
- Adding new Alto repository dependency
- Enabling new CI workflow
- Changing proto targets

```yaml
# Example: Adding new dependency
alto_ruby_deps:
  - name: new_service
    version: '~> 1.0'
    gems:
      - new_service_api
```

Then run:
```bash
alto generate deps {repo_name}
```

### Workflow: Adding a New Endpoint

**Complete workflow for adding an endpoint to an existing repository**:

```bash
# 1. Create or identify target database table
# 2. Generate proto boilerplate from table schema
alto generate protos actions prescriptions actions.prescriptions \
  --endpoint_methods=fetch_one,fetch_all,create,update,delete

# 3. Manually edit generated protos if needed
# - Adjust field types
# - Add validation rules
# - Customize method signatures

# 4. Update repository config if adding new dependencies
# Edit: config/repositories/actions.yml
# Then regenerate deps
alto generate deps actions

# 5. Generate language-specific bindings
cd {repo}/protos && make generate

# 6. Implement service handlers (Ruby/Python/TypeScript)
# 7. Add tests
# 8. Commit and deploy
```

### Dependency Resolution During Endpoint Creation

When an endpoint depends on other services:

```yaml
# config/repositories/billing.yml
alto_ruby_deps:
  - name: patients
    version: '~> 1.0'
    gems:
      - patients_api  # Specific gem for patient endpoints
  - name: prescriptions
    version: '~> 1.0'
    gems:
      - prescriptions_api
```

The `bump` command ensures all dependent gems are synchronized:

```bash
alto bump billing

# This:
# 1. Updates all alto_ruby_deps to latest
# 2. Syncs engine migrations
# 3. Regenerates Sorbet RBI files
# 4. Updates TypeScript proto bindings if applicable
```

---

## Common Patterns & Examples

### Pattern 1: Proto Generation from Database Table

**Scenario**: Adding prescription endpoints to billing engine

```bash
# Step 1: Identify table schema
psql rxapp_development -c '\d+ prescriptions'

# Step 2: Generate proto files
alto generate protos billing prescriptions billing.prescriptions \
  --dbname=rxapp_development \
  --version=v1 \
  --endpoint_methods=fetch_one,fetch_all,create,update,delete

# Output:
# ✔ protos/src/billing/prescriptions/types/v1/prescription.proto
# ✔ protos/src/billing/prescriptions/v1/prescriptions_endpoint.proto
```

**Generated Files**:

`protos/src/billing/prescriptions/types/v1/prescription.proto`:
```proto
syntax = "proto3";
package billing.prescriptions.types.v1;

import "core/types/v1/date.proto";
import "opts/opts.proto";

message Prescription {
  int64 id = 1 [(opts.field) = {required: true}];
  int64 patient_id = 2 [(opts.field) = {required: true}];
  string medication = 3 [(opts.field) = {required: true}];
  core.types.v1.Date filled_date = 4;
  string notes = 5;
  google.protobuf.Timestamp created_at = 6;
  google.protobuf.Timestamp updated_at = 7;
}
```

`protos/src/billing/prescriptions/v1/prescriptions_endpoint.proto`:
```proto
syntax = "proto3";
package billing.prescriptions.v1;

import "billing/prescriptions/types/v1/prescription.proto";
import "core/types/v1/error_object.proto";

message PrescriptionsEndpointFetchOneRequest {
  int64 id = 1;
}

message PrescriptionsEndpointFetchOneResponse {
  repeated core.types.v1.ErrorObject errors = 1;
  billing.prescriptions.types.v1.Prescription data = 2;
}

// ... other method messages ...

service PrescriptionsEndpoint {
  option (opts.service_value) = {version: "v2.0"};

  rpc FetchOne(PrescriptionsEndpointFetchOneRequest) 
    returns (PrescriptionsEndpointFetchOneResponse);
  rpc FetchAll(PrescriptionsEndpointFetchAllRequest) 
    returns (PrescriptionsEndpointFetchAllResponse);
  rpc Create(PrescriptionsEndpointCreateRequest) 
    returns (PrescriptionsEndpointCreateResponse);
  rpc Update(PrescriptionsEndpointUpdateRequest) 
    returns (PrescriptionsEndpointUpdateResponse);
  rpc Delete(PrescriptionsEndpointDeleteRequest) 
    returns (PrescriptionsEndpointDeleteResponse);
}
```

### Pattern 2: Dependency Graph with Multiple Services

**Scenario**: Billing depends on Patients, Prescriptions, and Core

```yaml
# config/repositories/billing.yml
alto_ruby_deps:
  - name: core
    version: '~> 1.0'
    
  - name: patients
    version: '~> 2.0'
    gems:
      - patients_api
      
  - name: prescriptions
    version: '~> 1.0'
    gems:
      - prescriptions_api
      
  - name: operations
    version: '~> 1.0'
```

**Dependency Resolution**:
```bash
alto generate deps billing

# Generates gemfiles/alto.rb with:
gem 'core', '~> 1.0', path: '../core'
gem 'patients_api', '~> 2.0', path: '../patients'
gem 'prescriptions_api', '~> 1.0', path: '../prescriptions'
gem 'operations_api', '~> 1.0', path: '../operations'

# Then in Gemfile:
eval_gemfile './gemfiles/alto.rb'
```

### Pattern 3: Proto with Multiple Targets

**Scenario**: Publishing TypeScript and Ruby bindings

```yaml
# config/repositories/actions.yml
protos:
  name: actions_api
  targets:
    - type: typescript  # Generate TS npm package
    - type: ruby        # Generate Ruby gem (at ./actions_api)
      out: ./actions_api
  deps:
    - core
```

**Generation Process**:
```bash
# 1. Initialize proto infrastructure
alto generate init_protos actions

# 2. Create proto files (manually or via alto generate protos)
# 3. Generate language-specific bindings
cd protos
make generate

# Output structure:
# protos/gen/typescript/
#   package.json        # npm package metadata
#   src/
#     generated/        # Generated TS files
#
# protos/actions_api/
#   lib/
#     actions_api.rb    # Ruby gem entry point
#   actions_api.gemspec # Gem metadata
#   generated/          # Generated Ruby files
```

### Pattern 4: Bumping Dependencies Across Repositories

**Scenario**: Core package updated, need to bump all dependent engines

```bash
# 1. Core published new version
# 2. Update all engines that depend on core
alto bump actions
alto bump billing
alto bump comms

# Process for each repo:
# 1. bundle install
# 2. bundle update core --conservative
# 3. Sync engine migrations (scriptdash only)
# 4. bundle exec tapioca gem core  # Update RBI files
```

### Pattern 5: Validation & Error Handling

**Configuration Validation**:
```ruby
# From Config::Loader
def create_alto_dep(dep)
  if dep['branch'].nil? && dep['version'].nil?
    raise ArgumentError, 'Alto dep must contain a version or a branch'
  end
  if dep['branch'] && dep['version']
    raise ArgumentError, 'Alto dep cannot contain a version and a branch'
  end
  # ... create AltoDep
end

# Repository validation
def select_repository
  ruby_repositories = Config.instance.repositories.filter { |_name, repository| 
    repository.ruby_repo? 
  }

  selected_repository = ruby_repositories[repo.to_sym]

  return selected_repository if selected_repository.present?

  # Error handling - list available repos
  configured_repositories = ruby_repositories.keys.sort.map { |name| "\n• #{name}" }
  say set_color("\n⚠️  Could not find the provided repository", :yellow, :bold)
  say set_color("Please enter one of the following: #{configured_repositories}", :yellow)
  nil
end
```

---

## Summary

This reference provides comprehensive coverage of:

1. **Repository Architecture**: Structure, technologies, and organization
2. **CLI Commands**: All major commands with syntax, options, and examples
3. **Configuration Schema**: Complete YAML structure with validation
4. **Proto Pipeline**: Message generation, templates, and RPC methods
5. **Dependency Management**: Resolution, versioning, and generation
6. **Endpoint Workflow**: Integration points and common patterns

**Key Files for Endpoint-Creation Skill**:
- `config/repositories/*.yml` - Examples and schema
- `lib/alto/protos.rb` - Proto configuration logic (286 lines)
- `lib/alto/commands/generators/protos.rb` - Proto generation (127 lines)
- `lib/alto/config.rb` - Configuration system (623 lines)
- `lib/alto/deps.rb` - Dependency resolution (116 lines)
- `lib/alto/commands/bump.rb` - Dependency updates (238 lines)

