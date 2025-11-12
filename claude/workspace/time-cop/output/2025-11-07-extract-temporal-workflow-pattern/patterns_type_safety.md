# Type Safety Patterns

**Project Root**: /Users/chris.helma/workspace/personal/time-cop

**Pattern Coverage**: Patterns 9-15 from WorkflowDemoMixed extraction

**Focus**: Protobuf version management, centralized generation, validation, and consumer integration

---

## Pattern 9: Single Source of Truth for Versions [PRIORITY: CRITICAL]

**Purpose**: Centralize all protobuf-related version requirements in one YAML file to ensure consistency across all consumers.

**Problem Solved**: In polyglot systems, protoc version and language-specific protobuf library versions must be compatible. Without centralized management, consumers can drift out of sync, leading to incompatible generated code and runtime errors.

**Implementation**:

**Version Configuration File** (protos/config/versions.yaml:1-12):
```yaml
# Single source of truth for protobuf tooling and library versions
# Used by centralized generation scripts and consumer validation scripts

protoc:
  required_version: "29.5"

python:
  protobuf_library: "5.29.*"

ruby:
  google_protobuf_gem: ">= 4.29.0, < 4.30"
```

**Key Principles**:
1. **One file defines all requirements** - protoc compiler + all language library versions
2. **Loaded by all validation scripts** - both centralized (protos/scripts/validate.py) and consumer-level (python_worker/scripts/validate_protoc.py, ruby_worker/Rakefile)
3. **Version alignment enforced** - protoc major version matches language library minor version (protobuf compatibility matrix)

**Usage Pattern**:
- **Centralized validation**: protos/scripts/validate.py reads this file before generation
- **Consumer validation**: Each worker validates its library version matches before copying generated files
- **Version updates**: Change one file, all consumers and generators adapt

**When to use**:
- All polyglot systems using protobuf for cross-language communication
- Systems with multiple deployment environments that need version consistency
- Teams where different engineers work on different language workers

**When NOT to use**:
- Single-language systems (library version can be in dependency file)
- Protobuf not used for cross-language serialization

**Trade-offs**:
- ✅ Single source of truth prevents version drift
- ✅ Easy to update versions (one file change)
- ✅ Clear documentation of compatibility requirements
- ✅ Enables validation automation across all consumers
- ❌ Requires all consumers to coordinate upgrades (can't upgrade independently)
- ❌ Additional file to maintain beyond language dependency files

**Related patterns**: Centralized Proto Generation, Two-Level Validation

---

## Pattern 10: Centralized Proto Generation [PRIORITY: CRITICAL]

**Purpose**: Generate protobuf code for all languages from a single location using a unified workflow, then distribute to consumers.

**Problem Solved**: Without centralized generation, each consumer generates independently, leading to:
- Inconsistent protoc versions
- Duplicate generation logic
- No guarantee all consumers regenerate after schema changes
- Difficult to enforce generation best practices

**Implementation**:

**Centralized Makefile** (protos/Makefile:1-43):
```makefile
# Centralized protobuf generation Makefile

.PHONY: all python ruby validate clean help

# Default target
all: python ruby

# Validate protoc version
validate:
	@echo "Validating protoc version..."
	@python3 scripts/validate.py

# Generate Python protobuf interfaces
python: validate
	@bash scripts/generate_python.sh

# Generate Ruby protobuf interfaces and Sorbet RBI files
ruby: validate
	@bash scripts/generate_ruby.sh

# Clean all generated files
clean:
	@echo "Cleaning generated files..."
	@rm -rf generated/python generated/ruby generated/rbi
	@echo "✓ Clean complete"
```

**Generation Scripts**:

**Python Generation** (protos/scripts/generate_python.sh:19-46):
```bash
# Find all .proto files and generate Python code
cd "${PROTOS_DIR}"
proto_files=$(find . -name "*.proto" -type f)

# Generate for each proto file
for proto_file in $proto_files; do
    echo "  Processing: $proto_file"
    protoc \
        --proto_path=. \
        --python_out="${OUTPUT_DIR}" \
        --pyi_out="${OUTPUT_DIR}" \
        "$proto_file"
done

# Create __init__.py files in all directories
find "${OUTPUT_DIR}" -type d -exec touch {}/__init__.py \;
```

**Ruby Generation** (protos/scripts/generate_ruby.sh:44-52):
```bash
# Generate for each proto file
for proto_file in $proto_files; do
    echo "  Processing: $proto_file"
    protoc \
        --proto_path=. \
        --ruby_out="${RUBY_OUTPUT_DIR}" \
        --rbi_out="${RBI_OUTPUT_DIR}" \
        "$proto_file"
done
```

**Output Structure**:
```
protos/
├── generated/
│   ├── python/        # Python _pb2.py and _pb2.pyi files
│   ├── ruby/          # Ruby _pb.rb files
│   └── rbi/           # Sorbet .rbi type annotations for Ruby
```

**When to use**:
- Polyglot systems with multiple language consumers
- Systems where schema evolution needs careful coordination
- Teams that want to enforce generation best practices centrally

**When NOT to use**:
- Single consumer of protobufs (can generate inline)
- Tight coupling between schema and single consumer acceptable

**Trade-offs**:
- ✅ Consistent protoc version across all consumers
- ✅ DRY principle - generation logic defined once
- ✅ Easy to add new languages (one new script)
- ✅ Validation happens before any generation
- ✅ Output can be inspected before distribution to consumers
- ❌ Two-step workflow: generate centrally, then copy to consumers
- ❌ Requires build coordination (must run `make` before consumer builds)
- ❌ Generated files not directly in consumer source trees

**Related patterns**: Single Source of Truth, Consumer Copy Pattern

---

## Pattern 11: Two-Level Validation Pattern [PRIORITY: CRITICAL]

**Purpose**: Validate protobuf version compatibility at two levels: centralized (protoc only) and consumer-level (protoc + language library).

**Problem Solved**: Different stakeholders need different validation:
- **Centralized generation**: Only needs protoc validation (libraries aren't installed)
- **Consumers**: Need to validate protoc + their specific language library compatibility

**Implementation**:

**Level 1: Centralized Protoc Validation** (protos/scripts/validate.py:73-87):
```python
def main() -> int:
    """Main validation logic."""
    config = load_version_config()
    required_version = config['protoc']['required_version']
    installed_version = get_protoc_version()

    if validate_protoc_version(installed_version, required_version):
        print(f"✓ protoc version {installed_version} meets requirements ({required_version})")
        return 0
    else:
        return 1
```

**Validates**: System protoc version matches config/versions.yaml

**Level 2: Consumer-Level Validation**

**Python Consumer** (python_worker/scripts/validate_protoc.py:111-172):
```python
def main() -> int:
    """Main validation function."""
    # Load centralized version requirements
    config = load_version_config()
    required_protoc = config['protoc']['required_version']
    required_protobuf = config['python']['protobuf_library']

    # Check system protoc
    protoc_version = get_system_protoc_version()

    # Check Python protobuf library
    protobuf_version = get_python_protobuf_version()

    # Validate against requirements
    errors = []

    if not validate_protoc_requirement(protoc_version, required_protoc):
        errors.append(f"❌ protoc version mismatch...")

    if not validate_protobuf_requirement(protobuf_version, required_protobuf):
        errors.append(f"❌ Python protobuf version mismatch...")

    # Also validate internal compatibility (protoc major == protobuf minor)
    if not validate_compatibility(protoc_version, protobuf_version):
        errors.append(f"❌ protoc/protobuf internal incompatibility...")

    return 0 if not errors else 1
```

**Ruby Consumer** (ruby_worker/Rakefile:17-42):
```ruby
def validate_system_protoc
  puts '🔍 Validating protoc/protobuf compatibility for Ruby Worker...'

  config = load_version_config
  required_protoc = config['protoc']['required_version']
  required_gem = config['ruby']['google_protobuf_gem']

  protoc_version = installed_protoc_version
  gem_version = protobuf_gem_version

  errors = collect_validation_errors(
    protoc_version,
    required_protoc,
    gem_version,
    required_gem,
  )

  raise_errors_if_present(errors)
  puts '✅ All version checks passed!'
end
```

**Validation Hierarchy**:
```
Centralized (protos/scripts/validate.py)
├─ Protoc version only
└─ Runs before: make python, make ruby

Consumer Level (run before copying generated files)
├─ Python (python_worker/scripts/validate_protoc.py)
│  ├─ Protoc version
│  ├─ Python protobuf library version
│  └─ Compatibility: protoc.major == protobuf.minor
│
└─ Ruby (ruby_worker/Rakefile ProtosHelper)
   ├─ Protoc version
   ├─ Ruby google-protobuf gem version
   └─ Compatibility: protoc.major == gem.minor
```

**When to use**:
- Polyglot systems with multiple language consumers
- Systems where version mismatches cause subtle bugs
- CI/CD pipelines that need to fail fast on version issues

**When NOT to use**:
- Single-language systems (one validation sufficient)
- When protobuf library versions are tightly controlled (e.g., Docker with pinned versions)

**Trade-offs**:
- ✅ Fail fast at both generation and consumption time
- ✅ Clear error messages with resolution steps
- ✅ Catches incompatibilities before runtime
- ✅ Each consumer validates only what it needs
- ❌ Validation logic duplicated across languages (Ruby, Python, Shell)
- ❌ Must maintain validation scripts in sync with compatibility matrix

**Related patterns**: Single Source of Truth, Protoc Compatibility Rules

---

## Pattern 12: Consumer Copy Pattern [PRIORITY: CRITICAL]

**Purpose**: Consumers copy centrally-generated protobuf files to their local directories after validation, ensuring generated code is co-located with consumer code.

**Problem Solved**: Generated files need to be:
1. In consumer source tree for import resolution
2. Gitignored (not checked in, regenerated on build)
3. Validated before copying (ensure compatibility)

**Implementation**:

**Python Consumer** (python_worker/pyproject.toml:56-80):
```toml
[tool.poe.tasks.validate-protoc]
# Validate protoc/protobuf compatibility before generation
script = "scripts.validate_protoc:main"

[tool.poe.tasks.protos]
# Generate Python protobuf interfaces using centralized generation, then copy to local directory
deps = ["validate-protoc"]
shell = """
# Clean centralized generated files to ensure fresh start
make -C ../protos clean

# Generate using centralized Makefile
make -C ../protos python

# Clean out any existing local protobuf files
rm -rf time_cop_worker/protos
mkdir -p time_cop_worker/protos

# Copy generated files to local directory
cp -r ../protos/generated/python/* time_cop_worker/protos/

echo "✅ Python protobuf files copied to time_cop_worker/protos/"
"""
```

**Ruby Consumer** (ruby_worker/Rakefile:189-215):
```ruby
desc 'Generate Ruby classes from protobuf definitions using centralized generation'
task :generate do
  validate_system_protoc

  chdir '..' do
    # Clean centralized generated files to ensure fresh start
    sh 'make -C protos clean'

    # Generate using centralized Makefile
    sh 'make -C protos ruby'

    # Clean out any existing local protobuf files
    FileUtils.rm_rf('ruby_worker/protos')
    FileUtils.rm_rf('ruby_worker/sorbet/rbi/protos')
    FileUtils.mkdir_p('ruby_worker/protos')
    FileUtils.mkdir_p('ruby_worker/sorbet/rbi/protos')

    # Copy generated files to local directories
    FileUtils.cp_r(Dir.glob('protos/generated/ruby/*'), 'ruby_worker/protos/')
    FileUtils.cp_r(Dir.glob('protos/generated/rbi/*'), 'ruby_worker/sorbet/rbi/protos/')

    puts '✅ Ruby protobuf files copied to ruby_worker/protos/ and ruby_worker/sorbet/rbi/protos/'
  end
end
```

**Workflow**:
1. **Validate** consumer library compatibility
2. **Clean** centralized generated/ directory (fresh start)
3. **Generate** via centralized `make` target
4. **Clean** local consumer proto directories
5. **Copy** generated files to consumer-local paths
6. **Import** protobuf classes using relative imports

**Consumer Directory Structure**:
```
python_worker/
├── time_cop_worker/
│   ├── protos/                    # Gitignored - copied from ../protos/generated/python/
│   │   ├── __init__.py
│   │   ├── workflow_demo_mixed_pb2.py
│   │   ├── workflow_demo_mixed_pb2.pyi
│   │   └── ...
│   └── activities/
│       └── activity_say_hello_python.py  # Imports: from ..protos.activity_say_hello_pb2 import ...

ruby_worker/
├── protos/                         # Gitignored - copied from ../protos/generated/ruby/
│   ├── workflow_demo_mixed_pb.rb
│   └── ...
├── sorbet/rbi/protos/              # Gitignored - copied from ../protos/generated/rbi/
│   ├── workflow_demo_mixed_pb.rbi
│   └── ...
└── app/
    └── workflows/
        └── workflow_demo_mixed.rb  # Requires: require 'workflow_demo_mixed_pb'
```

**When to use**:
- Centralized generation pattern (Pattern 10)
- Generated files should be co-located with consumer source code
- Generated files should not be checked into version control

**When NOT to use**:
- Single consumer (can generate directly into source tree)
- Generated files are checked in (copy not needed, generate once)

**Trade-offs**:
- ✅ Generated files co-located with consumer code (easy imports)
- ✅ Gitignored files don't pollute version control
- ✅ Clean separation: centralized generation vs consumer consumption
- ✅ Validation happens before copying (fail early)
- ❌ Two-step process (generate, then copy)
- ❌ Must remember to run consumer task after schema changes
- ❌ Build tool dependency (poe, rake, make)

**Related patterns**: Centralized Proto Generation, Fresh Start Pattern

---

## Pattern 13: Protoc Compatibility Rules [PRIORITY: CRITICAL]

**Purpose**: Enforce protobuf's version compatibility matrix to prevent runtime serialization/deserialization errors.

**Problem Solved**: Protobuf has strict compatibility rules between protoc compiler version and language library versions. Mismatches cause:
- Different message encoding/decoding behavior
- Missing features in generated code
- Subtle runtime bugs in cross-language communication

**Official Compatibility Matrix**:
- **Python**: `protobuf_library.minor == protoc.major`
  - Example: protoc 29.5 requires Python protobuf 5.29.x
  - See: https://protobuf.dev/support/version-support/#python-support

- **Ruby**: `google_protobuf_gem.minor == protoc.major`
  - Example: protoc 29.5 requires Ruby google-protobuf 4.29.x
  - See: https://protobuf.dev/support/version-support/#ruby-support

**Implementation**:

**Python Compatibility Check** (python_worker/scripts/validate_protoc.py:98-109):
```python
def validate_compatibility(protoc_version: Tuple[int, int, int],
                          protobuf_version: Tuple[int, int, int]) -> bool:
    """
    Validate protoc/protobuf compatibility based on official support matrix.
    According to the matrix, the Python protobuf minor version should align
    with the protoc major version.  For example, if protoc is 29.x, then
    Python protobuf version should be 5.29.x.

    See: https://protobuf.dev/support/version-support/#python-support
    """
    protoc_major, _, _ = protoc_version
    _, protobuf_minor, _ = protobuf_version

    return protobuf_minor == protoc_major
```

**Ruby Compatibility Check** (ruby_worker/Rakefile:170-183):
```ruby
def compatible_versions?(protoc_version, protobuf_version)
  # Extract major versions
  protoc_match = protoc_version.match(/(\d+)\./)
  protoc_major = protoc_match[1].to_i
  protobuf_minor = protobuf_version.split('.')[1].to_i

  # The Ruby Protobuf gem minor version should match the protoc major version
  # See - https://protobuf.dev/support/version-support/#ruby-support
  protobuf_minor == protoc_major
end
```

**Version Configuration Example** (protos/config/versions.yaml):
```yaml
protoc:
  required_version: "29.5"    # Major = 29

python:
  protobuf_library: "5.29.*"  # Minor = 29 (matches protoc major)

ruby:
  google_protobuf_gem: ">= 4.29.0, < 4.30"  # Minor = 29 (matches protoc major)
```

**When to use**:
- All protobuf-based cross-language systems
- When upgrading protoc or language library versions
- CI/CD pipelines to prevent incompatible deployments

**When NOT to use**:
- N/A - this is a hard requirement from protobuf project

**Trade-offs**:
- ✅ Prevents subtle cross-language serialization bugs
- ✅ Catches incompatibilities before runtime
- ✅ Documents compatibility requirements explicitly
- ❌ Restricts version upgrades (all languages must upgrade together)
- ❌ Requires understanding of protobuf compatibility matrix

**Related patterns**: Two-Level Validation, Single Source of Truth

---

## Pattern 14: Multi-Output Generation (Ruby + RBI) [PRIORITY: PREFERRED]

**Purpose**: Generate both runtime Ruby code and Sorbet type annotations (.rbi files) from protobuf schemas to enable static type checking.

**Problem Solved**: Ruby is dynamically typed, but Sorbet enables gradual typing. Generated protobuf classes need type annotations so Sorbet can type-check code using protobuf messages.

**Implementation**:

**Ruby Generation with RBI** (protos/scripts/generate_ruby.sh:21-56):
```bash
# Check for protoc-gen-rbi
if ! command -v protoc-gen-rbi &> /dev/null; then
    echo "Error: protoc-gen-rbi is not installed" >&2
    echo "Install with: go install github.com/sorbet/protoc-gen-rbi@v0.2.0" >&2
    exit 1
fi

# Create output directories
mkdir -p "${RUBY_OUTPUT_DIR}"
mkdir -p "${RBI_OUTPUT_DIR}"

# Generate for each proto file
for proto_file in $proto_files; do
    echo "  Processing: $proto_file"
    protoc \
        --proto_path=. \
        --ruby_out="${RUBY_OUTPUT_DIR}" \
        --rbi_out="${RBI_OUTPUT_DIR}" \   # Sorbet type annotations
        "$proto_file"
done

echo "✓ Ruby protobuf generation complete:"
echo "  Ruby classes: ${RUBY_OUTPUT_DIR}"
echo "  Sorbet RBI files: ${RBI_OUTPUT_DIR}"
```

**Dual Output Structure**:
```
protos/generated/
├── ruby/                              # Runtime Ruby code
│   ├── workflow_demo_mixed_pb.rb
│   └── activity_say_hello_pb.rb
└── rbi/                               # Sorbet type annotations
    ├── workflow_demo_mixed_pb.rbi
    └── activity_say_hello_pb.rbi
```

**Consumer Integration** (ruby_worker/Rakefile:203-211):
```ruby
# Copy generated files to local directories
FileUtils.cp_r(Dir.glob('protos/generated/ruby/*'), 'ruby_worker/protos/')
FileUtils.cp_r(Dir.glob('protos/generated/rbi/*'), 'ruby_worker/sorbet/rbi/protos/')
```

**Sorbet Type Checking**:
Ruby workflows with `# typed: strict` can use protobuf messages with full type safety:
```ruby
# See: ruby_worker/app/workflows/workflow_demo_mixed.rb:23-24
sig { params(request: Timecop::Workflows::WorkflowDemoMixedRequest)
        .returns(Timecop::Workflows::WorkflowDemoMixedResponse) }
def execute(request)
  # Sorbet knows the types from .rbi files
end
```

**When to use**:
- Ruby codebases using Sorbet for gradual typing
- Teams that want static type checking for protobuf messages in Ruby
- Systems where type safety across language boundaries is critical

**When NOT to use**:
- Ruby codebases not using Sorbet (RBI files won't be used)
- Python (has built-in .pyi stub generation, not RBI)

**Trade-offs**:
- ✅ Static type checking for protobuf messages in Ruby
- ✅ Editor autocomplete and type hints
- ✅ Catch type errors at compile time (via Sorbet)
- ✅ Generated RBI files don't pollute runtime code
- ❌ Requires protoc-gen-rbi installation (Go-based tool)
- ❌ Additional output directory to manage
- ❌ Ruby-specific (other languages have different type annotation mechanisms)

**Related patterns**: Activity Definition Patterns (Ruby), Centralized Proto Generation

---

## Pattern 15: Fresh Start Pattern [PRIORITY: PREFERRED]

**Purpose**: Clean both centralized and local generated directories before regeneration to ensure stale files don't persist after schema changes.

**Problem Solved**: Without cleaning:
- Renamed/deleted .proto files leave orphaned generated files
- Schema changes can leave outdated code
- Hard to debug issues from stale generated files

**Implementation**:

**Python Consumer** (python_worker/pyproject.toml:65-79):
```toml
shell = """
# Clean centralized generated files to ensure fresh start
make -C ../protos clean

# Generate using centralized Makefile
make -C ../protos python

# Clean out any existing local protobuf files
rm -rf time_cop_worker/protos
mkdir -p time_cop_worker/protos

# Copy generated files to local directory
cp -r ../protos/generated/python/* time_cop_worker/protos/
```

**Ruby Consumer** (ruby_worker/Rakefile:193-211):
```ruby
chdir '..' do
  # Clean centralized generated files to ensure fresh start
  puts 'Cleaning centralized generated files...'
  sh 'make -C protos clean'

  # Generate using centralized Makefile
  puts 'Generating via centralized Makefile...'
  sh 'make -C protos ruby'

  # Clean out any existing local protobuf files
  FileUtils.rm_rf('ruby_worker/protos')
  FileUtils.rm_rf('ruby_worker/sorbet/rbi/protos')
  FileUtils.mkdir_p('ruby_worker/protos')
  FileUtils.mkdir_p('ruby_worker/sorbet/rbi/protos')

  # Copy generated files to local directories
  FileUtils.cp_r(Dir.glob('protos/generated/ruby/*'), 'ruby_worker/protos/')
end
```

**Centralized Clean** (protos/Makefile:24-28):
```makefile
clean:
	@echo "Cleaning generated files..."
	@rm -rf generated/python generated/ruby generated/rbi
	@echo "✓ Clean complete"
```

**Clean Stages**:
1. **Centralized clean** (`make -C protos clean`) - removes protos/generated/
2. **Centralized generate** (`make -C protos python|ruby`) - regenerates from scratch
3. **Local clean** (`rm -rf consumer/protos`) - removes consumer's local copy
4. **Local copy** (`cp -r ...`) - copies fresh generated files

**When to use**:
- All protobuf generation workflows
- When .proto files are renamed, moved, or deleted
- CI/CD pipelines (ensure reproducible builds)

**When NOT to use**:
- Incremental development where full regeneration is slow (though this pattern is usually fast enough)

**Trade-offs**:
- ✅ No stale generated files after schema changes
- ✅ Reproducible builds (always fresh generation)
- ✅ Easier debugging (know all files are current)
- ✅ Catch schema deletion issues immediately
- ❌ Slightly slower than incremental generation
- ❌ More disk I/O (delete, regenerate, copy)

**Related patterns**: Consumer Copy Pattern, Centralized Proto Generation

---

## Summary: Iteration 2 Patterns

**Files Analyzed**: 8 files, ~600 lines

**Pattern Categories**:
1. **Version management** (Patterns 9, 11, 13)
2. **Centralized generation** (Patterns 10, 12, 15)
3. **Language-specific concerns** (Pattern 14)

**Priority Breakdown**:
- **CRITICAL**: 5 patterns (single source of truth, centralized generation, two-level validation, consumer copy, compatibility rules)
- **PREFERRED**: 2 patterns (multi-output Ruby+RBI, fresh start)

**Key Insights**:
- Version management is sophisticated: single source of truth + two-level validation + compatibility matrix enforcement
- Centralized generation with consumer copy enables both consistency and co-located imports
- Ruby's Sorbet integration requires dual output (runtime .rb + type annotations .rbi)
- Fresh start pattern prevents subtle bugs from stale generated files
- Pattern enforces protobuf compatibility matrix as code (not just documentation)

**Architectural Significance**:
The protobuf pattern is CRITICAL for cross-language reliability. Version mismatches cause subtle serialization bugs that are hard to debug. This pattern treats version management as a first-class concern with validation at multiple levels.

**Next Iteration**: Dispatcher & HTTP Integration patterns (FastAPI endpoints, Temporal client management, workflow triggering).

