# Workspace Setup Guide

This guide provides detailed instructions for setting up and verifying the Alto workspace for Better Boundaries development.

## Overview

The Alto workspace consists of 55+ repositories managed by the `alto-workspace` CLI tool. Before implementing endpoints, verify that both the workspace and target repositories are properly configured.

## Quick Start

```bash
# 1. Initialize workspace (one-time setup)
scripts/init_workspace.sh

# 2. Initialize target repository
scripts/init_repo.sh engine-partnerships

# 3. Verify repository is ready
scripts/verify_repo.sh engine-partnerships --all
```

## Detailed Setup Process

### Step 1: Workspace Initialization

The workspace initialization script verifies that the Alto workspace environment is properly configured.

**Command:**
```bash
scripts/init_workspace.sh [--sync]
```

**What it checks:**
- ✅ `$ALTO_WORKSPACE_REPO_ROOT` environment variable is set
- ✅ `alto-workspace` repository exists at that location
- ✅ `alto-workspace/bin` is in `$PATH`
- ✅ `alto` command is accessible

**Optional sync:**
- Use `--sync` flag to run `alto up` (syncs all repos to latest)
- ⚠️ **Warning**: `alto up` will rebase any branches that are behind origin/master
- Default behavior: Skip sync for safety

**Common issues:**

**`ALTO_WORKSPACE_REPO_ROOT` not set:**
```bash
# Add to ~/.zshrc or ~/.bashrc:
export ALTO_WORKSPACE_REPO_ROOT=~/workspace/alto
```

**`alto` command not found:**
```bash
# Add to ~/.zshrc or ~/.bashrc:
export PATH="$ALTO_WORKSPACE_REPO_ROOT/alto-workspace/bin:$PATH"

# Then reload:
source ~/.zshrc  # or source ~/.bashrc
```

### Step 2: Repository Initialization

Initialize a specific repository for development (installs dependencies, generates protos, sets up database).

**Command:**
```bash
scripts/init_repo.sh <repo-name>
```

**Examples:**
```bash
scripts/init_repo.sh engine-partnerships
scripts/init_repo.sh scriptdash
scripts/init_repo.sh engine-actions
```

**What it does:**
1. **Navigates to repository** at `$ALTO_WORKSPACE_REPO_ROOT/<repo-name>`
2. **Installs dependencies** via `bundle install`
3. **Generates protos** via `bin/protos` (if exists)
   - For engines, automatically restores the API file after generation
4. **Creates test database** via `RAILS_ENV=test bin/rails db:create`
5. **Runs migrations** via `bundle exec rails db:migrate RAILS_ENV=test`

**Requirements:**
- PostgreSQL must be running
- Ruby version specified in `.ruby-version` must be installed

**Common issues:**

**PostgreSQL not running:**
```bash
# macOS with Homebrew:
brew services start postgresql

# Check if running:
pg_isready
```

**Wrong Ruby version:**
```bash
# Check required version:
cat .ruby-version

# Install if needed:
rbenv install <version>

# Verify:
ruby --version
```

### Step 3: Repository Verification

Verify that a repository is working correctly by running type checks and tests.

**Command:**
```bash
scripts/verify_repo.sh <repo-name> [--sorbet|--tests|--all]
```

**Options:**
- `--sorbet`: Run Sorbet type checking only (fast, ~30 seconds)
- `--tests`: Run RSpec test suite only (slow, 5-60+ minutes depending on repo)
- `--all`: Run both (default if no option specified)

**Examples:**
```bash
# Quick type check before making changes:
scripts/verify_repo.sh engine-partnerships --sorbet

# Full verification (includes tests):
scripts/verify_repo.sh engine-partnerships --all

# Tests only:
scripts/verify_repo.sh scriptdash --tests
```

**What it checks:**
- **Sorbet** (`bundle exec srb tc`): Type correctness
- **RSpec** (`bundle exec rspec`): Test suite passes

**Expected results:**

**Engine repositories** (e.g., engine-partnerships):
- Tests: ~1200 examples, <5 failures, >95% coverage
- Duration: 5-10 minutes
- Sorbet: No errors

**Scriptdash** (monolith):
- Tests: Thousands of examples, may take 30-60+ minutes
- Sorbet: No errors
- Consider running `--sorbet` only for quick verification

**Interpreting failures:**

**Sorbet errors:**
- Indicates type inconsistencies in the codebase
- Should be clean before making changes
- Fix errors or investigate if they're expected

**Test failures:**
- Small number of failures may be environment-specific (e.g., AWS mocks)
- Large number of failures indicates setup issues
- Check that migrations ran successfully and database is accessible

## Ruby Version Management

Repositories may require different Ruby versions. Use `rbenv` to manage multiple versions.

**Check required version:**
```bash
cd $ALTO_WORKSPACE_REPO_ROOT/<repo-name>
cat .ruby-version
```

**Install if needed:**
```bash
rbenv install <version>
```

**Verify:**
```bash
cd $ALTO_WORKSPACE_REPO_ROOT/<repo-name>
ruby --version  # Should match .ruby-version
```

**Common Ruby versions:**
- engine-partnerships: 3.2.2
- scriptdash: 3.2.3

## Database Setup

### PostgreSQL Installation

**macOS (Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**Verify:**
```bash
pg_isready
# Output: /tmp:5432 - accepting connections
```

### Database Creation and Migration

The `init_repo.sh` script handles this automatically, but you can run manually if needed:

```bash
cd $ALTO_WORKSPACE_REPO_ROOT/<repo-name>

# Create test database
RAILS_ENV=test bin/rails db:create

# Run migrations
bundle exec rails db:migrate RAILS_ENV=test
```

**Common database names:**
- engine-partnerships: `partnerships_test`
- scriptdash: `rxapp_test`, `metadata_test`, `scriptdash_providers_test`, etc.

### Database Issues

**Database already exists:**
- Not an error, skip to migrations

**Connection refused:**
- PostgreSQL not running: `brew services start postgresql`
- Wrong port: Check `config/database.yml` for port configuration

**Migration failures:**
- Check for conflicting migrations
- Ensure database user has proper permissions
- Review migration error messages for schema issues

## Proto Generation

For repositories with proto definitions (engines), the `bin/protos` script generates code from `.proto` files.

**What it generates:**
- Ruby types (T::Struct)
- Interface modules (AbstractEndpoint)
- Controller mixins
- Route definitions
- RPC clients
- TypeScript definitions

**Important:**
After running `bin/protos`, the API file must be restored from git:
```bash
# Example for partnerships:
git checkout partnerships_api/lib/partnerships_api.rb
```

The `init_repo.sh` script handles this automatically.

**Proto generation issues:**

**Warnings about missing dependencies:**
- Usually safe to ignore during initialization
- Dependencies may not be published yet

**Import errors:**
- Ensure all proto dependencies are available
- Check `alto-workspace/config/repositories/*.yml` for proto dependencies

## Test Execution Strategies

### Small Repositories (Engines)

Run full test suite:
```bash
bundle exec rspec
```

Expected: 5-10 minutes, ~1200 examples

### Large Repositories (Scriptdash)

**Option 1: Sorbet only (fast)**
```bash
scripts/verify_repo.sh scriptdash --sorbet
```

**Option 2: Targeted tests**
```bash
# Run specific spec file:
bundle exec rspec spec/requests/partnerships/delivery_labels_spec.rb

# Run directory:
bundle exec rspec spec/services/partnerships/
```

**Option 3: Full suite (slow)**
```bash
scripts/verify_repo.sh scriptdash --tests
# Or: bundle exec rspec
```

Expected: 30-60+ minutes, thousands of examples

**Background execution:**
For very long test suites, consider running in background or terminal multiplexer.

## Workflow Recommendations

### Before Starting Implementation

1. **Verify workspace** (one-time):
   ```bash
   scripts/init_workspace.sh
   ```

2. **Initialize target repos**:
   ```bash
   scripts/init_repo.sh engine-partnerships
   scripts/init_repo.sh scriptdash
   ```

3. **Quick verification** (Sorbet only):
   ```bash
   scripts/verify_repo.sh engine-partnerships --sorbet
   scripts/verify_repo.sh scriptdash --sorbet
   ```

4. **Optional: Full test verification**:
   ```bash
   scripts/verify_repo.sh engine-partnerships --tests
   # Skip scriptdash full tests (too slow)
   ```

### During Development

1. **Type check frequently**:
   ```bash
   bundle exec srb tc
   ```

2. **Run targeted tests**:
   ```bash
   bundle exec rspec spec/requests/path/to/new_spec.rb
   ```

3. **Before committing**:
   ```bash
   scripts/verify_repo.sh <repo> --all
   ```

## Troubleshooting

### Scripts fail with "command not found"

Ensure scripts are executable:
```bash
chmod +x scripts/*.sh
```

### `alto up` rebases my feature branch

This is expected behavior. `alto up` rebases any branch that is behind origin/master.

**Workarounds:**
- Use `scripts/init_workspace.sh` without `--sync` flag
- Manually run `alto up` when on master branch
- Stash changes before running `alto up`

### Tests hang or timeout

**Large test suites** (scriptdash) can take 30-60+ minutes.

**Solutions:**
- Use `--sorbet` for quick verification
- Run targeted tests instead of full suite
- Increase timeout for background execution

### Sorbet shows errors on fresh checkout

This indicates:
- Codebase has type errors (investigate if expected)
- Missing RBI files (run `bin/tapioca gem` and `bin/tapioca dsl`)
- Wrong Sorbet version (check `Gemfile.lock`)

### Database migrations fail

**Common causes:**
- PostgreSQL not running
- Database user lacks permissions
- Conflicting migrations
- Schema mismatches

**Solutions:**
- Verify PostgreSQL is running: `pg_isready`
- Check database user permissions
- Drop and recreate database: `RAILS_ENV=test bin/rails db:drop db:create db:migrate`

## Summary

**One-time setup:**
1. Set `$ALTO_WORKSPACE_REPO_ROOT` environment variable
2. Add `alto-workspace/bin` to `$PATH`
3. Install PostgreSQL
4. Install required Ruby versions

**Per-repository setup:**
1. `scripts/init_repo.sh <repo-name>`
2. `scripts/verify_repo.sh <repo-name> --sorbet`

**Before making changes:**
- Verify Sorbet is clean
- Optionally verify tests pass (engines only, skip scriptdash)

**This ensures a clean baseline before implementing new features.**
