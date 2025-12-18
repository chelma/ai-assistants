# Plan: Centralize Protobuf Type Generation

**Workspace**: time-cop
**Project Root**: ~/workspace/personal/time-cop
**Status**: draft
**GitHub Issue**: [#15](https://github.com/scriptdash/time-cop/issues/15)
**Created**: 2025-10-22

## Problem Statement

Currently, each consumer (Python Worker, Ruby Worker, Dispatcher) defines its own protobuf compilation logic, leading to:
- Duplicated validation and generation code across consumers
- Inconsistent build processes
- New consumers (like the HTTP Dispatcher in PR #14) must copy/paste build logic
- Long-term maintainability issues around consistency

## Acceptance Criteria

- [ ] Consumers do not need to define their own compilation behavior from scratch
- [ ] Consumers can rely on and invoke centralized compilation behavior
- [ ] Consumers can determine at build-time whether generated interface types are compatible with their runtime libraries
- [ ] All existing workers (Python, Ruby, Dispatcher) successfully build using centralized generation
- [ ] Containerfiles use centralized generation
- [ ] Documentation updated to reflect new approach

---

## Current State Analysis

**Python Worker:**
- Has `scripts/validate_protoc.py` that validates protoc/protobuf version compatibility
- Uses Poetry task `poe protos` to generate types into `time_cop_worker/protos/`
- Validates that protoc major version matches Python protobuf minor version
- Containerfile installs protoc 29.5 and runs generation during build

**Ruby Worker:**
- Has `ProtosHelper` module in Rakefile with validation logic
- Uses Rake task `rake protos:generate` to generate Ruby classes and Sorbet RBI files
- Validates protoc major version matches Ruby gem minor version
- Containerfile installs protoc 29.5, Go, and protoc-gen-rbi, then runs generation

**Dispatcher:**
- Currently has generated protobuf files checked into git (`dispatcher/dispatcher/protos/`)
- No generation mechanism (the gap that PR #14 addressed)
- Containerfile does NOT install protoc or generate files
- Uses Python 3.10 and protobuf 5.29.*

**Version Management:**
- protoc version 29.5 is hardcoded in Python and Ruby Containerfiles
- Also defined in `helm-chart/time-cop-stack/values.yaml`
- Each consumer has its own validation logic

## Proposed Solution

### 1. Create Centralized Build System in `./protos/`

Create new directory structure:
```
protos/
├── Makefile              # Main build orchestration
├── config/
│   └── versions.yaml     # Single source of truth for versions
├── scripts/
│   ├── validate.py       # Validates system protoc only
│   ├── generate_python.sh
│   └── generate_ruby.sh
└── generated/            # Output directory (gitignored)
    ├── python/
    ├── ruby/
    └── rbi/
```

**config/versions.yaml** structure:
```yaml
protoc:
  required_version: "29.5"

python:
  protobuf_library: "5.29.*"

ruby:
  google_protobuf_gem: ">= 4.29.0, < 4.30"
```

This is the **single source of truth** for all version requirements across the project.

**Validation Architecture** (separation of concerns):

*Central Validation* (`protos/scripts/validate.py`):
- Reads `config/versions.yaml`
- Checks **only** system protoc version against requirements
- Invoked by `protos/Makefile` before generation
- Does NOT check consumer library versions (Python protobuf, Ruby gem, etc.)
- Purpose: Ensure system protoc can generate compatible code for all consumers
- Fast check suitable as Makefile prerequisite

*Consumer Validation* (each worker validates independently):
- **Python Worker**: `python_worker/scripts/validate_protoc.py`
- **Ruby Worker**: `ruby_worker/Rakefile` (ProtosHelper module)
- **Dispatcher**: `dispatcher/scripts/validate_protoc.py` (to be created)
- Each reads `../protos/config/versions.yaml` for version requirements
- Each checks its own installed library version (Python protobuf package, Ruby google-protobuf gem)
- Each validates compatibility between system protoc and its specific library
- Purpose: Ensure consumer runtime can use the generated code
- Invoked as part of consumer build process (poe task, rake task, etc.)

This architecture maintains clear separation of concerns: central generation validates protoc tooling is correct, while consumers validate they can consume the generated code with their runtime libraries.

**generate_python.sh** will:
- Use system `protoc` with `--python_out` and `--pyi_out` plugins
- Recursively find all `.proto` files using `find . -name "*.proto"`
- Set `--proto_path=.` to ensure imports (including subdirectory protos) resolve correctly
- Output to `generated/python/`

**generate_ruby.sh** will:
- Use system `protoc` with `--ruby_out` plugin
- Use `protoc-gen-rbi` plugin for Sorbet RBI generation
- **Assumes `protoc-gen-rbi` is already installed on the system** (not installed by the script)
- Recursively find all `.proto` files using `find . -name "*.proto"`
- Set `--proto_path=.` to ensure imports (including subdirectory protos) resolve correctly
- Generate both Ruby classes (to `generated/ruby/`) and Sorbet RBI files (to `generated/rbi/`)

**Makefile targets**:
- `make python` - Generate Python types
- `make ruby` - Generate Ruby types + RBI files
- `make all` - Generate all languages
- `make clean` - Remove generated files
- `make validate` - Run validation only

### 2. Update Consumers

**Output Strategy**: Copy generated files from `protos/generated/` to consumer directories during build (safer for distributed builds than symlinking)

**Python Worker:**
- **Keep** `scripts/validate_protoc.py` but update it to read from `../protos/config/versions.yaml`
- Update validation logic to check Python protobuf library against central config
- Update `pyproject.toml` poe task to invoke `make -C ../protos python` then copy files
- Update Containerfile to hardcode protoc version (matching versions.yaml) and invoke centralized generation

**Ruby Worker:**
- **Keep** `ProtosHelper` module validation logic in Rakefile
- Update it to read from `../protos/config/versions.yaml` instead of hardcoded version checks
- Update validation to check Ruby google-protobuf gem against central config
- Update Rake task to invoke `make -C ../protos ruby` then copy files
- Update Containerfile to hardcode protoc version (matching versions.yaml) and invoke centralized generation

**Dispatcher:**
- **Create** `scripts/validate_protoc.py` that reads from `../protos/config/versions.yaml`
- Add validation to check Python protobuf library against central config (similar to Python Worker)
- Add poe task for protobuf generation (similar to python_worker)
- Remove checked-in protobuf files from git
- Update Containerfile to hardcode protoc version (matching versions.yaml) and invoke centralized generation

### 3. Update .gitignore

- Add `protos/generated/` to ignore centrally generated files
- Remove dispatcher's checked-in protobuf files
- Keep consumer-local copies ignored as they are now

### 4. Update Documentation

- Update CLAUDE.md with centralized protobuf generation approach
- Update README protobuf section
- Document Makefile targets

## Implementation Steps

1. Create `protos/` infrastructure:
   - Create `protos/config/versions.yaml` with version requirements from Helm values
   - Create `protos/scripts/validate.py` (validates system protoc only, not libraries)
   - Create `protos/scripts/generate_python.sh` (using find for recursive proto discovery)
   - Create `protos/scripts/generate_ruby.sh` (using find, assumes protoc-gen-rbi installed)
   - Create `protos/Makefile` with targets (validate, python, ruby, all, clean)

2. Test centralized generation in isolation:
   - Run `make validate` to verify protoc version check works
   - Run `make python` and `make ruby` to verify generation works
   - Verify output structure in `protos/generated/{python,ruby,rbi}/`

3. Update Python Worker:
   - Update `scripts/validate_protoc.py` to read from `../protos/config/versions.yaml`
   - Keep existing library validation logic (Python protobuf compatibility check)
   - Update `pyproject.toml` poe task to invoke `make -C ../protos python` then copy files
   - Test locally: `cd python_worker && poetry run poe protos`
   - Update Containerfile to hardcode protoc version matching versions.yaml
   - Convert Containerfile to multi-stage approach separating build and runtime, reducing final image size
   - Remove checked-in protos from git
   - Test container build

4. Update Ruby Worker:
   - Update `ProtosHelper` in Rakefile to read from `../protos/config/versions.yaml`
   - Keep existing gem validation logic (Ruby google-protobuf compatibility check)
   - Update Rake task to invoke `make -C ../protos ruby` then copy files
   - Test locally: `cd ruby_worker && bundle exec rake protos:generate`
   - Update Containerfile to hardcode protoc version matching versions.yaml
   - Remove checked-in protos from git
   - Test container build

5. Update Dispatcher:
   - Create `scripts/validate_protoc.py` reading from `../protos/config/versions.yaml`
   - Implement Python protobuf library validation (similar to Python Worker)
   - Add poe task for protobuf generation invoking centralized Makefile
   - Update Containerfile to hardcode protoc version and generate
   - Convert Containerfile to multi-stage approach separating build and runtime, reducing final image size
   - Remove checked-in protos from git
   - Test locally and container build

6. Update .gitignore and documentation:
   - Add `protos/generated/` to .gitignore
   - Update CLAUDE.md to reflect centralized generation and config/versions.yaml architecture
   - Update README.md to document config/versions.yaml as single source of truth
   - Document validation architecture (central vs. consumer)

7. End-to-end testing:
   - Run `make deploy` to verify full stack builds
   - Run `make expose-services` and test workflows
   - Verify all workers function correctly

## Risks and Considerations

**Version Drift**: If consumers update their protobuf library versions independently, validation will catch incompatibility but could block builds. Solution: Update config/versions.yaml as part of any library version changes.

**Build Dependencies**: Consumers now depend on the centralized Makefile. If someone tries to build a consumer in isolation without the protos/ directory, it will fail. This is acceptable as the repo structure requires protos/ to exist.

**Containerfile Complexity**: Dispatcher Containerfile currently doesn't install protoc. Will need to add that step, increasing image build time and size slightly.

**Migration Path**: Existing checked-in dispatcher protobuf files must be removed from git. Git history will preserve them if needed.

**Backward Compatibility**: This is a build-time change only; generated code interfaces remain identical, so no runtime impact.

**Ruby Sorbet Dependency**: Ruby generation requires `protoc-gen-rbi` to be installed on the system via Go (`go install github.com/sorbet/protoc-gen-rbi@v0.2.0`). The generation script assumes this prerequisite is met and will not install it. This is already documented in README.md for developer setup and installed in ruby_worker/Containerfile for container builds.

**Proto File Organization**: The centralized generation scripts handle proto files in subdirectories (e.g., `types/`, `ruby_worker/activities/`) and imports between proto files. Using `--proto_path=.` with recursive file discovery ensures that imports like `types/patient_event_summary.proto` resolve correctly.

**Separation of Concerns**: The centralized validation (`protos/scripts/validate.py`) only checks system protoc version to ensure generation can proceed. Each consumer (Python Worker, Ruby Worker, Dispatcher) independently validates their library versions are compatible by reading `protos/config/versions.yaml`. This maintains clear separation: generation (central) validates tooling, consumption (per-worker) validates runtime compatibility.

**Containerfile Protoc Versions**: Protoc versions in Containerfiles will be hardcoded to match `config/versions.yaml` requirements. While this creates a potential source of drift if versions.yaml is updated without updating Containerfiles, it keeps Containerfiles simple and readable. Developers must manually sync Containerfile protoc installation commands when updating config/versions.yaml.

## Testing Strategy

1. **Unit Testing**: Verify validation script correctly detects version mismatches
2. **Local Builds**: Test each consumer's build process locally after migration
3. **Container Builds**: Build all three Containerfiles successfully
4. **Integration Testing**: Cleanup the the full stack with `make cleanup` then deploy with `make deploy` to run demo workflows
5. **Verify Workflows**: Run Python, Ruby, and Mixed workflows to confirm functionality unchanged
