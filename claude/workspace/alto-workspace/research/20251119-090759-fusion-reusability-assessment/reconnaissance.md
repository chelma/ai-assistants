# Reconnaissance Findings

## Repository Context

**Technology stack:**
- Ruby (primary language)
- Thor CLI framework for commands
- Sorbet for static typing
- Concurrent-ruby for async operations
- Zeitwerk for autoloading
- ERB templating for code generation
- Docker Compose (limited use - just Kafka starter)

**Architecture style:**
- CLI tool / developer productivity tool
- Host-based development environment
- Configuration-driven repository management
- Template-based code generation

**Key modules relevant to investigation:**
- `/lib/alto/` - Core module
- `/lib/alto/config.rb` - Configuration system
- `/lib/alto/commands/` - CLI commands
- `/lib/alto/templates/` - ERB templates
- `/config/repositories/` - Repository definitions (YAML)

## Files Identified

### Configuration System (1162 lines total)
- `lib/alto/config.rb` (624 lines) - Complex configuration loader with typed structs, repository/application definitions, dependency management
- `config/repositories/*.yml` (50+ files) - Individual repository configurations
- `config/apps/apps.yaml` - Application definitions

### Repository Management (146 lines total)
- `lib/alto/commands/up.rb` (116 lines) - Multi-repo sync with async operations using Concurrent::Promises
- `lib/alto/directory.rb` (30 lines) - Directory path resolution (GOPATH-based by default)
- `lib/alto/shell/git.rb` (not yet examined) - Git operations wrapper

### Dependency Generation System (126+ lines examined)
- `lib/alto/commands/generators/deps.rb` (126 lines) - Main deps generator command
- `lib/alto/commands/generators/deps_generator/ruby_context.rb` (not examined) - Ruby-specific dependency generation
- `lib/alto/commands/generators/deps_generator/python_context.rb` (not examined) - Python-specific dependency generation

### Code Generation & Templates (~150 lines examined, many templates not examined)
- `lib/alto/commands/generators/gem.rb` (150 lines) - Scaffold new Ruby gems
- `lib/alto/commands/generators/kubernetes.rb` (52 lines) - Kubernetes config setup (kubectl + kubeconfig, NOT Helm charts)
- `lib/alto/templates/` - Extensive ERB templates (gemfiles, CI configs, etc.)

### Service Starter System (46 lines examined)
- `lib/alto/commands/start.rb` (28 lines) - Command registry for starters
- `lib/alto/commands/starters/kafka_starter.rb` (18 lines) - Docker Compose wrapper for Kafka
- `lib/alto/commands/starters/boxcar_starter.rb` (not examined)
- `lib/alto/commands/starters/scanner_client_starter.rb` (not examined)

### Logging & UI (~300+ lines based on file count)
- `lib/alto/logs/` - Custom async logging for multi-repo operations

## Initial Observations

### 1. Host-Based Philosophy
- **GOPATH assumption**: Default directory structure assumes `$GOPATH/src/github.com/<org>/<repo>`
- **Alternative**: Can override with `ALTO_WORKSPACE_REPO_ROOT` for non-GOPATH layouts
- **Local dependency linking**: `alto generate deps --local` creates path-based dependencies for local development
- **No containerization**: Services run directly on host (except Kafka starter which uses docker-compose)

### 2. Configuration-Driven System
- **Central registry**: All repositories defined in `config/repositories/*.yml`
- **Rich metadata**: Each repo config includes URL, dependencies (Ruby/Python/JS), CI workflows, owners, etc.
- **Typed structs**: Heavy use of Sorbet-typed configuration classes
- **Multi-language support**: Handles Ruby, Python, and JavaScript dependencies

### 3. Repository Orchestration
- **Multi-repo sync**: `alto up` clones/updates all configured repositories in parallel
- **Dependency resolution**: `alto generate deps` generates dependency files (Gemfile, pyproject.toml) from config
- **Local linking**: Supports local development versions of dependencies via path-based requires

### 4. Template-Based Generation
- **ERB templates**: Extensive use of ERB for generating CI configs, Gemfiles, etc.
- **Standardization**: Templates ensure consistency across repositories
- **Generator commands**: Thor-based generators for gems, engines, CircleCI, GitHub Actions, etc.

### 5. Limited Container Support
- **Kafka starter only**: Single docker-compose file for local Kafka broker
- **No Kubernetes orchestration**: `alto generate kubernetes` only sets up kubectl config, doesn't generate Helm charts
- **No image building**: No concept of building container images from local directories
- **No service orchestration**: No ability to start/stop multiple containerized services

### 6. Async Operation Support
- **Concurrent-ruby**: Uses Promises API for parallel operations
- **Custom logging**: Sophisticated logging system for showing progress across multiple async tasks
- **Pattern established**: Clear pattern for async multi-repo operations

## Investigation Strategy

Based on reconnaissance, plan to investigate:

### Deep Dive 1: Configuration & Dependency System
- Read `lib/alto/commands/generators/deps_generator/ruby_context.rb`
- Read `lib/alto/commands/generators/deps_generator/python_context.rb`
- Understand how local vs. remote dependencies work
- Examine how dependency versions are resolved
- Assess if this system could work with container images

### Deep Dive 2: Repository Management & Directory Structure
- Read `lib/alto/shell/git.rb`
- Understand GOPATH vs. custom root directory handling
- Examine how multi-repo layouts are enforced
- Assess compatibility with fusion's "all repos must be siblings" requirement

### Deep Dive 3: Code Generation System
- Examine template structure under `lib/alto/templates/`
- Understand ERB context and available helpers
- Look at examples of CI/CD generation
- Assess if template system could generate Helm charts

### Deep Dive 4: Service Starter Analysis
- Read other starter implementations (boxcar, scanner_client)
- Understand how services are currently started
- Look for any abstraction patterns that could be extended
- Assess gap between current starters and Kubernetes orchestration

### Deep Dive 5: Extensibility Assessment
- Examine base command structure
- Look at how new commands are registered
- Understand coupling between components
- Identify extension points

## Context Health Checkpoint
**Files read directly**: 11 files, ~2100 lines
**Explore agent calls**: 0
**Risk assessment**: 🟢 Green - Reconnaissance complete, ready for deep investigation
