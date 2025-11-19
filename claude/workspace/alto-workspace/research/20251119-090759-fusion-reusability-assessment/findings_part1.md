# Investigation Findings - Part 1
## Core Architecture & Dependency Management

This file contains detailed analysis of alto-workspace's core architecture, configuration system, dependency management, and repository orchestration.

---

## Question 1: Core Architecture & Philosophy

### Fundamental Architecture

**alto-workspace is a CLI-based developer productivity tool for managing a multi-repository monorepo ecosystem.**

**Core components:**

1. **Configuration System** (`lib/alto/config.rb`, 624 lines)
   - Central registry of all repositories in YAML files
   - Typed structs using Sorbet for configuration objects
   - Supports Ruby, Python, and JavaScript repositories
   - Each repo config defines: URL, dependencies, CI workflows, owners, gems

2. **CLI Framework** (Thor-based)
   - Main commands: `alto up`, `alto generate`, `alto start`, `alto bump`, `alto dir`
   - Subcommands organized under `lib/alto/commands/`
   - Base command mixin provides common functionality
   - Generator pattern for code/config generation

3. **Multi-Repo Management**
   - Git wrapper (`lib/alto/shell/git.rb`, 151 lines) for repo operations
   - Async operations using concurrent-ruby Promises
   - Custom logging system for progress visualization

4. **Template System**
   - ERB templates for generating standardized files
   - Templates for: Gemfiles, CI configs, Dockerfiles, etc.
   - Context objects provide data to templates

### Problems It Solves

**1. Multi-Repository Dependency Management**
- **Problem**: Alto has 50+ repositories with interdependencies (gems, engines, apps)
- **Solution**: Centralized configuration declares dependencies, `alto generate deps` generates dependency files
- **Example**: `scriptdash` depends on 25+ Alto gems; config lists them with versions, tool generates Gemfile

**2. Local Development Linking**
- **Problem**: Testing changes across multiple repos requires publishing gems
- **Solution**: `alto generate deps --local <gem>` creates path-based dependencies
- **Example**: Working on `devtools` gem? Link it locally to `scriptdash` for immediate testing
- **Code reference**: `lib/alto/templates/gemfiles/alto.rb.erb:12-18`

**3. Repository Synchronization**
- **Problem**: Developers need latest code from many repos
- **Solution**: `alto up` clones missing repos, rebases existing ones in parallel
- **Example**: Updates 50+ repos in seconds using async operations
- **Code reference**: `lib/alto/commands/up.rb`

**4. Standardization Across Repos**
- **Problem**: CI configs, rubocop rules, etc. diverge across repos
- **Solution**: Templates ensure consistency; `alto generate circleci` updates all repos
- **Example**: Change rubocop rule once, regenerate across all repos

### Design Philosophy: Host-Based Development

**CRITICAL FINDING: alto-workspace is fundamentally designed for host-based development.**

**Evidence:**

1. **Directory Structure Assumption** (`lib/alto/directory.rb:16-22`)
   ```ruby
   if Config.instance.use_gopath?
     return File.join(Config.instance.repo_root, config.url)
   end
   repo_folder_name = config.url.split('/').last
   File.join(Config.instance.repo_root, repo_folder_name)
   ```
   - Default: `$GOPATH/src/github.com/scriptdash/scriptdash`
   - Alternative: `$ALTO_WORKSPACE_REPO_ROOT/scriptdash` (flat sibling structure)
   - **Both assume repos cloned to local filesystem**

2. **Local Dependency Linking** (`lib/alto/templates/gemfiles/alto.rb.erb:12-18`)
   ```erb
   <%- if dep[:local] -%>
   gem '<%= dep[:name] %>', {
     path: '<%= dep[:path] %>',
   }
   ```
   - Uses Bundler's `path:` directive to link local checkouts
   - Assumes all repos are on host filesystem, accessible by path
   - **No concept of containerized services or image building**

3. **Service Starters Run on Host**
   - Kafka starter: Uses docker-compose but for infrastructure only
   - Boxcar starter: Runs `bundle exec rails server` directly on host
   - **No container orchestration for application services**

**How Deeply Embedded Is "Run on Host"?**

**Very deeply.** The assumption permeates:
- Directory resolution logic
- Dependency generation (path-based linking)
- Service starters (direct process execution)
- Template context (expects filesystem paths)
- Git operations (expects repos on local FS)

**No abstraction layer exists for "where code runs" - it's always assumed to be the host.**

---

## Question 2: Dependency Management System

### How Dependency Generation Works

**Overview:** `alto generate deps <repo>` generates dependency files (Gemfile, pyproject.toml) from centralized configuration.

**Architecture:**

1. **Configuration Layer** (`config/repositories/*.yml`)
   - Each repo declares dependencies: `alto_ruby_deps`, `shared_ruby_deps`, `alto_py_deps`, etc.
   - Example from `scriptdash.yml`:
     ```yaml
     shared_ruby_deps:
       - core
       - rails_core
     alto_ruby_deps:
       - name: devtools
         version: '~> 1.0'
       - name: actions
         version: '~> 1.0'
         local: true  # Optional: use local checkout
     ```

2. **Generation Command** (`lib/alto/commands/generators/deps.rb`, 126 lines)
   - Entry point: `alto generate deps [repo_names]`
   - Options: `--local <deps>` to override config and link local checkouts
   - Creates language-specific contexts (RubyContext, PythonContext)

3. **Language-Specific Contexts**
   - **RubyContext** (`lib/alto/commands/generators/deps_generator/ruby_context.rb`, 134 lines)
     - Copies shared gemfiles from templates (e.g., `gemfiles/core.rb`)
     - Generates `gemfiles/alto.rb` from ERB template with Alto dependencies
     - Inserts `eval_gemfile './gemfiles/alto.rb'` into main Gemfile
     - Runs `bundle install` after generation

   - **PythonContext** (`lib/alto/commands/generators/deps_generator/python_context.rb`, 186 lines)
     - Parses existing `pyproject.toml`
     - Generates new `[tool.poetry.dependencies]` section
     - Handles local vs. remote dependencies

### Local vs. Remote Dependencies

**Remote Dependencies (Default):**
```ruby
# Generated in gemfiles/alto.rb
gem 'devtools', '~> 1.0'
```
- Uses version specified in config
- Bundler fetches from GitHub or RubyGems
- Standard production behavior

**Local Dependencies:**
```ruby
# Generated when `local: true` or `--local devtools`
gem 'devtools', {
  # FIXME: This gem has been linked to your local checkout for development.
  path: '../devtools',
}
```
- Uses `path:` directive to link local checkout
- Assumes repo exists at `../devtools` (sibling directory)
- **Requires all repos to be on host filesystem**

**Branch-Based Dependencies:**
```ruby
gem 'devtools', {
  git: 'https://github.com/scriptdash/devtools.git',
  branch: 'feature-branch',
}
```
- For testing unreleased branches
- Still fetches from GitHub

### Mechanism for Linking Alto Repos Together

**1. Configuration Registry** (`config/repositories/*.yml`)
- All Alto repos registered in central config
- Each declares its dependencies on other Alto repos
- Example: `scriptdash` depends on `actions`, `billing`, `devtools`, etc.

**2. Dependency Resolution**
- `alto generate deps` reads config
- For each Alto dependency:
  - Looks up repo in registry
  - Determines path (local) or version (remote)
  - Generates appropriate dependency declaration

**3. Path Calculation for Local Deps** (`lib/alto/commands/generators/deps_generator/language_context.rb`)
```ruby
def local_dep_path(dep_name)
  dep_dir = Directory.repository(dep_name)
  Pathname.new(dep_dir).relative_path_from(Pathname.new(dir)).to_s
end
```
- Calculates relative path between dependent repo and dependency
- Example: `scriptdash` → `../devtools`
- **Assumes both repos are on local filesystem**

**4. Gemfile Evaluation**
```ruby
# In scriptdash/Gemfile
eval_gemfile './gemfiles/alto.rb'
```
- Main Gemfile includes generated Alto dependencies
- Bundler resolves all dependencies together
- Local path deps override remote versions

### Could This System Work With Containerized Services?

**SHORT ANSWER: Not without fundamental redesign.**

**Incompatibilities:**

1. **Path-Based Linking**
   - System assumes `gem 'foo', path: '../foo'` works
   - In containers: Repos aren't on shared filesystem
   - Would need: Volume mounts, multi-stage builds, or private registry

2. **Dependency Generation Context**
   - Generated files assume host filesystem layout
   - Templates use relative paths (`../other-repo`)
   - Would need: Container-aware path resolution

3. **Installation Process**
   - `bundle install` runs on host after generation
   - In containers: Would need to rebuild image after dep changes
   - Current system has no concept of image building

**Potential Adaptations:**

1. **Container Registry Approach**
   - Publish all Alto gems to private registry (Artifactory)
   - Use versioned dependencies instead of path-based
   - Loses "test uncommitted changes" capability

2. **Volume Mount Approach**
   - Mount all repos into container at known paths
   - Preserve path-based dependencies
   - Complex volume configuration, slow on macOS

3. **Monorepo Approach**
   - Abandon multi-repo, consolidate into monorepo
   - All code in single container
   - **Major architectural shift**

**VERDICT:** Dependency system is tightly coupled to host-based filesystem. Containerization would require either:
- Abandoning local development linking (use published gems only)
- Complex volume mounting (preserve linking but add complexity)
- Architectural shift to monorepo or micro-frontends

---

## Question 3: Repository Management

### How `alto up` Works

**Purpose:** Clone missing repositories and update existing ones to latest default branch.

**Implementation:** (`lib/alto/commands/up.rb`, 116 lines)

**Architecture:**

1. **Async Orchestration**
   ```ruby
   Config.instance.repositories.each do |name, conf|
     results << Up.sync_repo(command_logs, name, conf)
   end

   Concurrent::Promises
     .zip(*results)
     .then { command_logs.set_succeeded.stop }
     .wait
   ```
   - Creates promise for each repository
   - All repos processed in parallel (thread pool)
   - Waits for all to complete

2. **Promise Chain for Each Repo**
   ```ruby
   Concurrent::Promises
     .future(context, &Up.ensure_repo)
     .then(&Up.update_repo)
     .then { |ctx| ctx.task_logs.set_succeeded }
     .rescue(context, &Up.handle_failure)
   ```
   - **Step 1**: Ensure repo exists (clone if missing)
   - **Step 2**: Update repo (rebase if needed)
   - **Step 3**: Log success
   - **Error handling**: Catch failures without blocking other repos

3. **Repo Existence Check** (`lib/alto/commands/up.rb:56-76`)
   ```ruby
   if ctx.repo.exists?
     logs.set_succeeded.title('Looking for repo ... Found!')
     return ctx
   end

   logs.title('Looking for repo...Cloning!')
   result = ctx.repo.clone
   ```
   - Checks if directory exists at expected path
   - If missing: Clones from GitHub
   - **Assumes filesystem-based repo storage**

4. **Update Logic** (`lib/alto/commands/up.rb:78-103`)
   ```ruby
   ctx.repo.fetch_origin_default
   if ctx.repo.uncommitted_changes?
     logs.set_succeeded.title('There are uncommitted changes. Skipped.')
     return ctx
   end
   unless ctx.repo.needs_rebase?
     logs.set_succeeded.title('Already up to date!')
     return ctx
   end

   result = ctx.repo.rebase
   ```
   - Fetches latest from origin
   - Skips if uncommitted changes present
   - Rebases if behind default branch
   - **Direct git operations on local filesystem**

### Multi-Repo Directory Layout

**Default Layout (GOPATH-based):**
```
$GOPATH/src/github.com/
├── scriptdash/
│   ├── scriptdash/       # Main app
│   ├── devtools/         # Gem
│   ├── actions/          # Engine
│   └── alto-workspace/   # This repo
```

**Alternative Layout (Custom Root):**
```
$ALTO_WORKSPACE_REPO_ROOT/
├── scriptdash/           # Main app
├── devtools/             # Gem
├── actions/              # Engine
└── alto-workspace/       # This repo
```

**Directory Resolution** (`lib/alto/directory.rb:12-23`)
```ruby
def self.repository(name)
  _, config = Config.instance.repositories.find { |current, _| name == current.to_s }

  if Config.instance.use_gopath?
    return File.join(Config.instance.repo_root, config.url)
    # Returns: $GOPATH/src/github.com/scriptdash/scriptdash
  end

  repo_folder_name = config.url.split('/').last
  File.join(Config.instance.repo_root, repo_folder_name)
  # Returns: $ALTO_WORKSPACE_REPO_ROOT/scriptdash
end
```

**Key Characteristics:**
- All repos must be on local filesystem
- GOPATH mode: Nested directory structure (matches GitHub URL)
- Custom root mode: Flat sibling structure (fusion-compatible!)
- No support for repos in different locations

### Overlap With Fusion's Multi-Repo Needs

**Fusion Requirement:** "All repositories must be siblings in same parent directory"
```
~/code/
├── fuzerx-local-dev/    # Orchestration repo
├── core-api/            # Truepill service
├── partners-engine/     # Alto service
└── scriptdash/          # Alto service
```

**alto-workspace With Custom Root:**
```
$ALTO_WORKSPACE_REPO_ROOT/
├── alto-workspace/      # This repo
├── scriptdash/          # Repo
├── devtools/            # Repo
└── actions/             # Repo
```

**OVERLAP: High! The custom root mode matches fusion's layout.**

**Reusable Components:**

1. **Repository Registry Concept**
   - Fusion needs service catalog (`config/service-catalog.yaml`)
   - alto-workspace has repository registry (`config/repositories/*.yml`)
   - **Similar purpose: Declare all managed repos**

2. **Multi-Repo Operations**
   - Fusion needs `deploy-all.sh` (deploy all services)
   - alto-workspace has `alto up` (update all repos)
   - **Similar pattern: Iterate over all registered repos**

3. **Directory Structure Enforcement**
   - Fusion requires sibling layout for predictability
   - alto-workspace supports sibling layout via custom root
   - **Compatible directory conventions**

**Incompatibilities:**

1. **Git-Centric vs. Container-Centric**
   - alto-workspace: Git clone/rebase on local filesystem
   - Fusion: Build container images from local directories
   - **Different operations, but both need repo paths**

2. **Host Operations vs. Kubernetes Deployment**
   - alto-workspace: Run `bundle install`, `rails server` on host
   - Fusion: Deploy to Minikube with Helm
   - **Different execution environments**

**VERDICT:** Repository management concepts are highly reusable (registry, multi-repo operations, directory layout), but implementation is host-centric and would need container-aware adaptations.

---

## Summary: Part 1 Key Findings

### Core Architecture
- **CLI tool for multi-repo monorepo management**
- **Host-based development is fundamental design assumption**
- **No abstraction for "where code runs" - always assumes local filesystem**

### Dependency Management
- **Configuration-driven: Central registry declares dependencies**
- **Local linking: Path-based dependencies for cross-repo development**
- **Incompatible with containers without major redesign**
- **Would need: Private registry, volume mounts, or monorepo shift**

### Repository Management
- **Multi-repo sync: Parallel clone/update operations**
- **Flexible directory layouts: GOPATH or custom root (sibling structure)**
- **HIGH OVERLAP with fusion's multi-repo needs**
- **Registry concept and directory conventions are reusable**
- **Implementation is git/host-centric, needs container adaptation**

### Reusability Assessment (Preliminary)
**Reusable Concepts:**
- Repository registry pattern
- Multi-repo parallel operations
- Sibling directory structure
- Async orchestration with logging

**Incompatible Implementation:**
- Host-based dependency linking
- Direct git operations (vs. container builds)
- No container/Kubernetes awareness
- No Helm chart generation
