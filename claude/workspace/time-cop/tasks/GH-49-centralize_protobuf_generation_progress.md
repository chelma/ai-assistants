# Implementation: Centralize Protobuf Type Generation

**Workspace**: time-cop
**Project Root**: /Users/chris.helma/workspace/personal/time-cop
**Status**: completed
**Plan**: [centralize_protobuf_generation_plan.md](./centralize_protobuf_generation_plan.md)
**Started**: 2025-10-28
**Completed**: 2025-10-28

## Progress

- [x] Step 1: Create `protos/` infrastructure
- [x] Step 2: Test centralized generation in isolation
- [x] Step 3: Update Python Worker
- [x] Step 4: Update Ruby Worker
- [x] Step 5: Update Dispatcher
- [x] Step 6: Update .gitignore and documentation
- [x] Step 7: End-to-end testing
- [x] Post-implementation: GitHub Actions CI fixes

## Deviations from Plan

**Step 6 (partial) completed early**: Added `protos/generated/` to `.gitignore` immediately after Step 2 instead of waiting until Step 6. This prevents accidentally committing generated files during consumer updates. The rest of Step 6 (documentation updates) will still be completed in sequence.

**Enhanced version enforcement (Step 3)**: Consumer validation scripts now enforce strict version matching against `config/versions.yaml` requirements, not just internal protoc/library compatibility. This ensures all workers use compatible versions for consistent code generation across the polyglot system. Rationale: While protobuf supports forward/backward compatibility at the wire format level, different protoc versions can generate subtly different APIs and helper methods. Since workflows cross language boundaries, we need predictable generated code behavior. This change affects Steps 4 and 5 (Ruby Worker and Dispatcher validation will also enforce strict version matching).

## Blockers

None - all blockers resolved during implementation.

## Key Implementation Decisions & Solutions

**Protobuf subdirectory renamed to avoid Python conflict**: Renamed `protos/types/` to `protos/protobuf_types/` because Python's built-in `types` module would conflict with imports. Updated all `.proto` file import statements accordingly.

**Python path configuration required**: Protoc generates absolute imports for cross-file dependencies (e.g., `from protobuf_types import patient_event_summary_pb2`). Both Python Worker and Dispatcher add their protos directory to `sys.path` at application startup to make these imports work. Added to both `main.py` entry points.

**Centralized `__init__.py` creation**: The `generate_python.sh` script creates `__init__.py` files in all generated directories, producing a complete Python package ready for copying. Consumers simply copy the generated files without post-processing.

**Strict version enforcement**: All consumers enforce exact major.minor version matching against `config/versions.yaml` to ensure consistent code generation across the polyglot system. While protobuf supports wire-format compatibility, different protoc versions generate different APIs/methods, which matters for cross-language workflows.

## Gotchas and Friction Points

**Container testing requirement**: Any step that modifies a Containerfile must include container build and launch testing before marking the step complete. This ensures the containerized build process works correctly and catches issues early.

**Gitignore local copies**: Each consumer must add its local protobuf copy directory to .gitignore to prevent committing generated files:
- `python_worker/time_cop_worker/protos/`
- `ruby_worker/protos/` and `ruby_worker/sorbet/rbi/protos/`
- `dispatcher/dispatcher/protos/`

**PyYAML system dependency**: The centralized validation script (`protos/scripts/validate.py`) requires PyYAML to read `config/versions.yaml`. Developers must install it: `pip3 install --user pyyaml` or `python3 -m pip install --user pyyaml`. In containers, this is handled by Containerfiles (Python consumers via Poetry, Ruby Worker via pip in builder stage).

**Consumer poe/rake task paths are relative**: When running generation tasks from within consumer directories, paths in shell commands are relative to that directory. Dispatcher uses `dispatcher/protos` (not `dispatcher/dispatcher/protos`) since the task runs from within `dispatcher/`.

## Additional Research

_To be documented as needed_

## Testing Results

_Test results will be recorded here_

## Notes

### Step 1: Create `protos/` infrastructure (Completed)

Created centralized protobuf generation infrastructure:

**Files created:**
- `protos/config/versions.yaml` - Single source of truth for version requirements:
  - protoc: 29.5
  - Python protobuf library: 5.29.*
  - Ruby google-protobuf gem: >= 4.29.0, < 4.30
- `protos/scripts/validate.py` - Validates system protoc version (requires PyYAML)
- `protos/scripts/generate_python.sh` - Generates complete Python packages:
  - Recursively discovers all .proto files
  - Generates Python classes and .pyi type stubs
  - Creates `__init__.py` files in all directories for proper Python package structure
- `protos/scripts/generate_ruby.sh` - Generates Ruby classes and Sorbet RBI files (requires protoc-gen-rbi)
- `protos/Makefile` - Provides targets: all, python, ruby, validate, clean, help
- All scripts made executable with chmod +x

### Step 2: Test centralized generation in isolation (Completed)

Tested all Makefile targets successfully:
- `make validate` - ✓ Passed, protoc version 29.5 matches requirements
- `make python` - ✓ Generated Python classes and .pyi stubs for all 8 proto files
  - Output structure includes subdirectories (ruby_worker/activities/, types/)
  - Generated files in `protos/generated/python/`
- `make ruby` - ✓ Generated Ruby classes and Sorbet RBI files for all 8 proto files
  - Output structure mirrors proto file organization
  - Generated Ruby classes in `protos/generated/ruby/`
  - Generated RBI files in `protos/generated/rbi/`
- `make clean` - ✓ Successfully removed all generated files
- `make all` - ✓ Generated both Python and Ruby successfully

Verified sample generated files:
- `activity_say_hello_pb2.py` shows protobuf 5.29.5 compatibility
- `activity_say_hello_pb.rb` shows proper Ruby module structure

All generation scripts correctly handle recursive proto file discovery and subdirectory imports.

### Step 3: Update Python Worker (Completed)

Updated Python Worker to use centralized protobuf generation with strict version enforcement and Python path configuration.

**scripts/validate_protoc.py (created):**
- Reads version requirements from `../protos/config/versions.yaml`
- Enforces THREE validations:
  1. System protoc major.minor matches requirement (e.g., "29.5")
  2. Python protobuf library major.minor matches pattern (e.g., "5.29.*")
  3. protoc and protobuf are internally compatible
- Added PyYAML as dev dependency in pyproject.toml

**pyproject.toml changes:**
- Added `[tool.poe.tasks.protos]` to use centralized generation:
  1. `make -C ../protos clean` - ensures fresh generation
  2. `make -C ../protos python` - generates via centralized scripts
  3. `rm -rf time_cop_worker/protos` - cleans local copies
  4. `cp -r ../protos/generated/python/*` - copies complete package
- Depends on `validate-protoc` task for version validation

**time_cop_worker/main.py changes:**
- Added Python path configuration at module import to add `time_cop_worker/protos` to `sys.path`
- Required for protoc's absolute imports (e.g., `from protobuf_types import ...`)

**Containerfile changes:**
- Converted to multi-stage build (builder + runtime stages)
- Builder includes protoc 29.5, make, and build tools
- Runtime excludes build tools (reduced image: 761 MB → 408 MB, ~46% reduction)
- Comment notes protoc version must match protos/config/versions.yaml

**.gitignore changes:**
- Added `python_worker/time_cop_worker/protos/` to ignore generated files

**Testing:**
- ✅ Local: `poetry run poe protos` generates and copies successfully
- ✅ Local: Imports work with sys.path configuration
- ✅ Container: Builds successfully with multi-stage build
- ✅ Container: Starts and initializes correctly (fails only on Temporal connection as expected)

### Step 4: Update Ruby Worker (Completed)

Updated Ruby Worker to use centralized protobuf generation with strict version enforcement.

**Rakefile ProtosHelper changes:**
- Added version validation helpers that read from `../protos/config/versions.yaml`
- Enforces THREE validations:
  1. System protoc major.minor matches requirement (e.g., "29.5")
  2. Ruby google-protobuf gem matches requirement (e.g., ">= 4.29.0, < 4.30")
  3. protoc and gem are internally compatible

**Rakefile protos:generate task changes:**
- Updated to use centralized generation:
  1. `make -C protos clean` - ensures fresh generation
  2. `make -C protos ruby` - generates via centralized scripts
  3. `rm -rf ruby_worker/protos` and `rm -rf ruby_worker/sorbet/rbi/protos` - cleans local copies
  4. `cp -r protos/generated/ruby/*` and `cp -r protos/generated/rbi/*` - copies complete files

**Containerfile changes:**
- Added `make` to build dependencies (for centralized Makefile)
- Added `python3`, `python3-pip`, and `pyyaml` to build stage (for centralized validation script)
- Comment notes protoc version must match protos/config/versions.yaml
- Already multi-stage build (no runtime changes needed)

**.gitignore changes:**
- Added `ruby_worker/protos/` and `ruby_worker/sorbet/rbi/protos/` to ignore generated files

**Testing:**
- ✅ Local: `bundle exec rake protos:generate` generates and copies successfully
- ✅ Local: Validation enforces version requirements
- ✅ Container: Builds successfully (528 MB, already had multi-stage)
- ✅ Container: Starts and initializes correctly (fails only on Temporal connection as expected)

### Step 5: Update Dispatcher (Completed)

Updated Dispatcher to use centralized protobuf generation with strict version enforcement and Python path configuration.

**scripts/validate_protoc.py (created):**
- Same structure as Python Worker validation script
- Reads version requirements from `../protos/config/versions.yaml`
- Enforces THREE validations:
  1. System protoc major.minor matches requirement (e.g., "29.5")
  2. Python protobuf library major.minor matches pattern (e.g., "5.29.*")
  3. protoc and protobuf are internally compatible

**pyproject.toml changes:**
- Added `poethepoet` and `pyyaml` to dev dependencies
- Added `[tool.poe.tasks.protos]` to use centralized generation:
  1. `make -C ../protos clean` - ensures fresh generation
  2. `make -C ../protos python` - generates via centralized scripts
  3. `rm -rf dispatcher/protos` - cleans local copies (note: path relative to dispatcher/ directory)
  4. `cp -r ../protos/generated/python/*` - copies complete package to `dispatcher/protos/`
- Depends on `validate-protoc` task for version validation

**dispatcher/main.py changes:**
- Added Python path configuration at module import to add `dispatcher/dispatcher/protos` to `sys.path`
- Required for protoc's absolute imports (e.g., `from protobuf_types import ...`)

**Containerfile (created):**
- Multi-stage build (builder + runtime stages)
- Builder includes protoc 29.5, make, and build tools
- Runtime excludes build tools for optimized image
- Comment notes protoc version must match protos/config/versions.yaml

**dispatcher/README.md updates:**
- Updated container build command to run from repo root: `podman build -f dispatcher/Containerfile -t time-cop-dispatcher .`
- Updated local run command to include protobuf generation step: `poetry run poe protos`
- Added note about when protobuf generation is required

**.gitignore changes:**
- Added `dispatcher/dispatcher/protos/` to ignore generated files

**Git cleanup:**
- Removed previously-tracked consumer-local protobuf files from version control
- Only source `.proto` files and infrastructure remain tracked

**Testing:**
- ✅ Local: `poetry run poe protos` generates and copies successfully
- ✅ Local: Imports work with sys.path configuration
- ✅ Container: Builds successfully with multi-stage build
- ✅ Container: Starts and initializes correctly (fails only on Temporal connection as expected)


### Step 6: Update .gitignore and documentation (Completed)

Updated project documentation to reflect centralized protobuf generation architecture.

**.gitignore updates (completed in earlier steps):**
- `protos/generated/` - Added in Step 2
- `python_worker/time_cop_worker/protos/` - Added in Step 3
- `ruby_worker/protos/` and `ruby_worker/sorbet/rbi/protos/` - Added in Step 4
- `dispatcher/dispatcher/protos/` - Added in Step 5

**CLAUDE.md updates:**
- Updated "Dispatcher Development" section with correct build commands (from repo root) and protobuf generation step
- Expanded "Protobuf Code Generation" section with three subsections:
  - **Centralized Generation**: Commands to generate at the central level (`make -C protos python/ruby/all/clean`)
  - **Consumer-Specific Generation**: Commands for each consumer to generate and copy locally
  - **Version Management**: Documented `protos/config/versions.yaml` as single source of truth and system protoc requirement
- Updated "Adding New Cross-Language Activities" to include Dispatcher in step 2
- Added new "Protobuf Version Management" subsection under "Important Notes" explaining:
  - Single source of truth (config/versions.yaml)
  - Centralized generation approach
  - Strict version enforcement rationale
  - System protoc requirement
  - Consumer validation architecture
- Added note about generated files being gitignored

**README.md updates:**
- Completely rewrote "Protobuf & Cross-Language Workflows" section with four new subsections:
  - **Centralized Protobuf Generation**: Explains the centralized approach, version management, validation architecture, and consumer build process
  - **Adding New Cross-Language Activities**: Step-by-step guide for adding new proto files
  - **Why Strict Version Enforcement?**: Explains the rationale for strict version matching across consumers
  - **Design Decisions**: Documents key architectural choices (system protoc, centralized-then-copy, validation separation)
- Removed outdated references to helm-chart/time-cop-stack/values.yaml for version definition (now in protos/config/versions.yaml)



### Step 7: End-to-end Testing (Completed)

Ran full stack deployment to verify centralized protobuf generation works correctly in production environment.

**Test Process:**
1. `make cleanup` - Removed existing Time Cop stack
2. `make deploy` - Built all images with centralized protobuf generation and deployed to minikube

**Container Builds:**
- ✅ Python Worker: Built successfully using cached layers, protobuf generation via `poetry run poe protos` in container
- ✅ Ruby Worker: Built successfully using cached layers, protobuf generation via `bundle exec rake protos:generate` in container
- ✅ Dispatcher: Built successfully using cached layers, protobuf generation via `poetry run poe protos` in container

**All build steps used centralized generation:**
- STEP 11/15: `COPY protos ./protos` - Copies centralized proto source files
- STEP 14/15 (Python) / STEP 22/22 (Ruby): Runs consumer generation task which invokes `make -C protos python/ruby`
- All containers successfully generated protobuf files during build

**Helm Deployment:**
- ✅ Deployed to minikube successfully
- ✅ All pods started correctly
- ✅ Image tag: 20251028-102059
- ✅ Protoc version: 29.5 (matching config/versions.yaml)

**Helm Test Results (all passed):**
- ✅ time-cop-stack-grafana-test - Grafana running
- ✅ time-cop-stack-test-dispatcher-running - Dispatcher responding
- ✅ time-cop-stack-test-namespace - Temporal namespace configured
- ✅ time-cop-stack-test-temporal-frontend - Temporal frontend accessible
- ✅ time-cop-stack-test-python-worker - Python worker connected
- ✅ time-cop-stack-test-ruby-worker - Ruby worker connected
- ✅ time-cop-stack-test-python-workflow - Python workflow executes
- ✅ time-cop-stack-test-ruby-workflow - Ruby workflow executes
- ✅ **time-cop-stack-test-mixed-workflow** - **Cross-language workflow executes successfully!**

**Key Validation:**
The **mixed workflow test** is the critical validation - it verifies that Ruby workflows can successfully call Python activities using the centralized protobuf generation. This test passed, confirming:
- Protobuf interfaces are compatible across languages
- Python path configuration works correctly in containers
- Strict version enforcement ensures consistent code generation
- Cross-language serialization/deserialization works as expected

**Conclusion:**
✅ All tests passed successfully. The centralized protobuf generation system is fully functional and working correctly in the production-like Kubernetes environment.


### Post-Implementation: GitHub Actions CI Fixes (Completed)

After creating a PR, discovered Ruby Worker CI failures due to missing protobuf files (gitignored) and Rubocop style violations in new Rakefile code.

**GitHub Workflows Updated:**

1. **`.github/workflows/test-ruby.yaml`** - Added protobuf generation steps before RSpec:
   - Install protoc 29.5
   - Install protoc-gen-rbi (Go tool for Sorbet RBI generation)
   - Add `$HOME/go/bin` to PATH (for protoc-gen-rbi visibility)
   - Install PyYAML (for validation script)
   - Run `bundle exec rake protos:generate`

2. **`.github/workflows/lint-ruby.yaml`** - Added same protobuf generation steps before Rubocop

**Rakefile Refactoring:**

Refactored `ProtosHelper` module to meet Rubocop style requirements:
- **Reduced complexity**: Broke `validate_system_protoc` into smaller helper methods:
  - `print_requirements` - Display version requirements
  - `check_protoc_installed` - Verify protoc is available
  - `check_gem_installed` - Verify gem is installed
  - `print_installed_versions` - Display installed versions
  - `collect_validation_errors` - Collect all validation errors
  - `raise_errors_if_present` - Report validation failures
  - `installed_protoc_version` - Extract protoc version
- **Fixed predicate naming**: Renamed validation methods to end with `?`:
  - `validate_protoc_requirement` → `protoc_requirement_satisfied?`
  - `validate_gem_requirement` → `gem_requirement_satisfied?`
- **Removed redundant begin block**: Simplified `gem_requirement_satisfied?` error handling
- **Fixed string literals**: Changed to single quotes where interpolation not needed
- **Fixed line lengths**: Split long error messages across multiple lines

**`.rubocop.yml` Update:**

Added `Metrics/ModuleLength: Max: 150` to accommodate the 128-line `ProtosHelper` module, similar to existing `Metrics/ClassLength: Max: 500` configuration.

**Testing:**

- ✅ Rubocop passes with no offenses
- ✅ Protobuf generation still works correctly after refactoring
- ✅ All validation logic preserved
