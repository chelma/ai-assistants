# Investigation Findings - Part 1: Patterns and Analysis

## 1. Files Using :nocov: Directives

### Finding: Only 2 files in the codebase use :nocov:

#### File 1: lib/global_collector.rb (SUCCESSFUL PATTERN)
**Location**: `lib/global_collector.rb` lines 3-10

**Structure**:
```ruby
# typed: false

# @owners { team: dev-sec-ops, domain: internal }

unless defined?(ENGINE_ROOT)
  # :nocov:
  ENGINE_ROOT = File.expand_path('..', __dir__)
  ENGINE_PATH = File.expand_path('../lib/partnerships_engine/engine', __dir__)
  # :nocov:
end
```

**Key observations**:
- `@owners` tag is at line 3, BEFORE any `:nocov:` directive
- `:nocov:` only wraps specific constant definitions (lines 6-9)
- `:nocov:` is INSIDE the conditional block, not wrapping the entire file
- Yardowners successfully parses the `@owners` tag
- SimpleCov successfully excludes the constant definitions from coverage

**Why it works**:
- The `@owners` tag is not wrapped by `:nocov:`, so YARD's parser can see it
- Only non-testable constant definitions are excluded from coverage
- The `:nocov:` scope is minimized to exactly what needs exclusion

**Commit history**: Added in commit 7644b16b (Apr 26, 2024) to "exclude const defs from coverage requirement"

#### File 2: app/services/partnerships_engine/labels.rb (PROBLEMATIC)
**Location**: `app/services/partnerships_engine/labels.rb`

**Current structure** (as of commit aae7667a):
```ruby
# typed: strict

# :nocov:
module PartnershipsEngine
  # @owners { team: care, domain: partnerships }
  module Labels
    include Core::API

    # Add labels_api RPC client
    # Will use ENV['LABELS_API_BASE_URL'] for remote calls
    add_api LabelsAPI::V1::LabelsEndpoint::Client

    # No local endpoint - PartnershipsEngine is deployed separately (Boxcar)
    # and accesses LabelsEngine via RPC HTTP calls
  end
end
# :nocov:
```

**Evolution through 3 commits**:

1. **Commit b9954b40** (Dec 10, 08:34) - "fix: resolve CI failures for labels integration"
   - ADDED `:nocov:` outside module (lines 3 and 18)
   - Fixed SimpleCov coverage failure
   - **Problem**: This placement breaks yardowners parsing

2. **Commit b5791858** (Dec 10, 08:42) - "fix: resolve yardowners lint failures for labels integration"
   - MOVED `:nocov:` inside module, after `@owners` tag (lines 5 and 16)
   - Attempted to fix yardowners by keeping `@owners` visible
   - **Problem**: SimpleCov per-file coverage still failed

3. **Commit aae7667a** (Dec 10, 08:56) - "fix: extend :nocov: coverage to entire labels.rb file"
   - MOVED `:nocov:` back outside module (lines 3 and 18)
   - Prioritized SimpleCov fix over yardowners
   - **Current problem**: Yardowners fails with "missing team owner for PartnershipsEngine"

**Why yardowners fails**:
- When `:nocov:` wraps the module definition line, YARD's parser sees it as a comment on the module
- This interferes with YARD's ability to associate the `@owners` tag (inside the module) with the module itself
- Yardowners looks for `@owners` tags in the AST parsed by YARD
- The `:nocov:` comment positioning breaks the AST association

**Why SimpleCov requires this placement**:
- SimpleCov counts the `module PartnershipsEngine` and `module Labels` lines as executable code
- Without wrapping these lines, SimpleCov reports 83.33% coverage (5 out of 6 lines)
- The per-file threshold is 90%, causing CI failure

## 2. Similar API Wrapper Modules

### Pattern Analysis: Declaration-Only vs Namespace Modules

#### Type A: Pure Declaration-Only (3 files - all use `add_api`)
These modules ONLY contain `include Core::API` and `add_api` - no executable methods:

**File**: `app/services/partnerships_engine/facilities.rb` (14 lines)
```ruby
# typed: strict

module PartnershipsEngine
  # The Facilities API is served from Wunderbar.
  # It provides access to Alto facilities and their details.
  # @owners { team: care, domain: partnerships }
  module Facilities
    include Core::API
    extend T::Sig

    add_api OperationsAPI::V1::FacilitiesEndpoint::Client
  end
end
```
- **No :nocov:**: Not needed
- **No spec file**: No `spec/services/partnerships_engine/facilities_spec.rb`
- **Coverage status**: Never measured by SimpleCov (file not loaded during testing)

**File**: `app/services/partnerships_engine/scheduling.rb` (11 lines)
```ruby
# typed: strict

module PartnershipsEngine
  # @owners { team: care, domain: partnerships }
  module Scheduling
    include Core::API

    add_api OrdersAPI::V1::SchedulingEndpoint::Client
  end
end
```
- **No :nocov:**: Not needed
- **No spec file**: No `spec/services/partnerships_engine/scheduling_spec.rb`
- **Coverage status**: Never measured by SimpleCov

**File**: `app/services/partnerships_engine/labels.rb` (18 lines)
```ruby
# Current state with :nocov:
```
- **HAS :nocov:**: Required to avoid coverage failure
- **HAS spec file**: `spec/services/partnerships_engine/labels_spec.rb` (248 lines)
- **Coverage status**: Measured by SimpleCov because spec loads the module
- **KEY DIFFERENCE**: This is the ONLY declaration-only module with a spec file!

#### Type B: API Wrapper with Accessors (2 files)
These modules use `add_api` PLUS define accessor methods:

**File**: `app/services/partnerships_engine/patients.rb` (32 lines)
```ruby
module PartnershipsEngine
  # @owners { team: care, domain: partnerships }
  module Patients
    extend T::Sig
    include Core::API

    add_api PatientsAPI::V1::PatientsEndpoint::Client

    sig { returns(T.class_of(Addresses)) }
    def self.addresses
      Addresses
    end
    # ... 3 more accessor methods
  end
end
```
- **No :nocov:**: Has executable code (accessor methods)
- **Coverage status**: Accessor methods provide coverage
- **No coverage problem**: Methods are testable and provide sufficient coverage

**File**: `app/services/partnerships_engine/billing.rb` (56 lines)
```ruby
module PartnershipsEngine
  # @owners { team: care, domain: partnerships }
  module Billing
    extend T::Sig
    include Core::API

    sig { returns(T.class_of(Prices)) }
    def self.prices
      Prices
    end
    # ... 8 more accessor methods
  end
end
```
- **No :nocov:**: Has executable code (9 accessor methods)
- **Coverage status**: Accessor methods provide coverage

#### Type C: Namespace-Only Modules (8 files)
These modules serve as namespaces but have NO `add_api` calls:

**File**: `app/services/partnerships_engine/comms.rb` (29 lines)
```ruby
module PartnershipsEngine
  # @owners { team: care, domain: partnerships }
  module Comms
    extend T::Sig

    sig { returns(T.class_of(CommsResources)) }
    def self.comms_resources
      CommsResources
    end
    # ... 3 more accessor methods
  end
end
```
- **SimpleCov filter**: Line 40 in spec_helper.rb: `add_filter 'app/services/partnerships_engine/comms.rb'`
- **Reason**: Namespace-only module with just accessors
- **Added**: Commit d1fd823e (Dec 9, 2024) "test: fix test coverage"

**File**: `app/services/partnerships_engine/consumers.rb` (26 lines)
- **SimpleCov filter**: Line 41 in spec_helper.rb: `add_filter 'app/services/partnerships_engine/consumers.rb'`
- **Reason**: Namespace-only module

**Other namespace modules** (not in filters):
- `prescriptions.rb` (30 lines) - 4 accessor methods
- `deliver.rb` (14 lines) - 1 accessor method
- `providers.rb` (13 lines) - 1 accessor method
- `experimentation.rb` (62 lines) - actual business logic methods
- `pdf_utils.rb` (58 lines) - actual utility methods
- `analytics.rb` (22 lines) - delegator methods

### Critical Finding: The Spec File is the Root Cause

**Why labels.rb has the :nocov: problem**:
1. `labels_spec.rb` was added in commit 5db34341 (Dec 9, 2025)
2. This caused SimpleCov to track `labels.rb` during test runs
3. `labels.rb` is declaration-only - only module definitions, no executable methods
4. SimpleCov counts module definition lines as "code" but marks them as uncovered
5. Per-file threshold (90%) fails because 5 of 6 lines are "uncovered declarations"
6. `:nocov:` was added to exclude the file from per-file metrics

**Why facilities.rb and scheduling.rb don't have the problem**:
1. No spec files for these modules
2. SimpleCov never tracks them (not loaded during testing)
3. No coverage metrics = no coverage failure
4. They're functionally identical to labels.rb but never measured

**Implication**: Adding a spec file to ANY declaration-only module will trigger this same coverage problem.

## 3. Configuration Findings

### SimpleCov Configuration (spec/spec_helper.rb)

**Key configuration lines**:
```ruby
# Line 22-43: SimpleCov.start 'rails' do
add_filter '/app/types/'
add_filter '/bin/'
# ... directory-level filters ...
add_filter 'app/services/partnerships_engine/comms.rb'           # Line 40
add_filter 'app/services/partnerships_engine/consumers.rb'       # Line 41
add_filter 'app/services/partnerships_engine/harrow/consumers.rb' # Line 42
add_filter '/lib/script/'

minimum_coverage JSON.parse(File.read('.coverage-config.json'))['threshold']
minimum_coverage_by_file(
  JSON.parse(File.read('.coverage-config.json'))['file_threshold'] ||
  JSON.parse(File.read('.coverage-config.json'))['threshold'],
)
```

**Key observations**:
1. **Per-file threshold enforced**: Line 46-49 enforce minimum_coverage_by_file
2. **File-specific filters exist**: Lines 31-42 show 12 file-specific filters
3. **Namespace modules filtered**: `comms.rb` and `consumers.rb` are filtered
4. **Precedent established**: commit d1fd823e added comms.rb filter for same reason
5. **No .simplecov file**: Configuration is entirely in spec_helper.rb

**SimpleCov filter patterns**:
- Directory patterns: `/app/types/`, `/bin/`, `/db/`, `/config/`, `/spec/`, `/vendor/`
- File name patterns: `/version.rb`, `/constants.rb`, `/partnerships_api/`
- Specific file paths: Full paths for special cases

**Team-based grouping** (Lines 51-65):
```ruby
yard_owners = Psych.load_file('.yardowners.yml')
teams = yard_owners['teams'].keys

teams.each do |team|
  add_group team.to_s do |src_file|
    file_includes_team = false
    src_file.src.each do |line|
      if line.include? "# @owners { team: #{team}"
        file_includes_team = true
        break
      end
    end
    file_includes_team
  end
end
```
- SimpleCov scans source files for `@owners` tags
- This REQUIRES `@owners` to be parseable (not wrapped by `:nocov:`)
- Groups files by team for coverage reporting

### Yardowners Configuration (.yardowners.yml)

**Key sections**:
```yaml
owners:
  partnerships:
    team: care
    domain: partnerships

path:
  - app
  - db/seeds/domains
  - lib

ignore:
  - app/types
  - lib/sandbox/seeds

teams:
  care:
    github: care-team
    slack_channel: '#care-eng-team'
```

**Key observations**:
1. **Path scanning**: Yardowners scans `app/`, `lib/`, and `db/seeds/domains/`
2. **Ignore patterns**: Excludes `app/types` and `lib/sandbox/seeds`
3. **No specific file ignores**: No way to exclude individual files
4. **Team definitions**: 14 teams defined with GitHub and Slack info
5. **Domain definitions**: 40+ domains with ownership

**Yardowners behavior**:
- Scans all `.rb` files in configured paths
- Uses YARD's AST parser to find modules/classes
- Looks for `@owners` tags in YARD documentation
- Validates every module has an owner
- Cannot parse `@owners` if wrapped by comment blocks that break AST

## 4. Alternative Approaches Identified

### Option 1: Add to SimpleCov Filter (RECOMMENDED)
**Pattern**: Add `labels.rb` to SimpleCov filters like `comms.rb`

**Implementation**:
```ruby
# In spec/spec_helper.rb, add after line 42:
add_filter 'app/services/partnerships_engine/labels.rb'
```

**Pros**:
- ✅ Completely excludes file from coverage metrics (both overall and per-file)
- ✅ No conflict with yardowners - `@owners` tag remains visible
- ✅ Precedent exists: `comms.rb` and `consumers.rb` use this approach
- ✅ Simple one-line change
- ✅ No changes to labels.rb file needed
- ✅ Consistent with codebase patterns

**Cons**:
- ❌ File won't appear in coverage reports at all
- ❌ If executable code is added later, it won't be covered

**When to use**: Declaration-only modules that serve as API wrappers with no testable logic

### Option 2: Position :nocov: to Preserve @owners Visibility
**Pattern**: Keep `@owners` outside `:nocov:` block

**Implementation**:
```ruby
# typed: strict

module PartnershipsEngine
  # @owners { team: care, domain: partnerships }

  # :nocov:
  module Labels
    include Core::API
    add_api LabelsAPI::V1::LabelsEndpoint::Client
  end
  # :nocov:
end
```

**Pros**:
- ✅ Keeps coverage exclusion in the file itself
- ✅ Makes intent explicit (this code is not testable)
- ✅ `@owners` tag visible to YARD parser

**Cons**:
- ❌ Doesn't work - SimpleCov still measures outer module line
- ❌ Per-file coverage still fails (83.33%)
- ❌ Attempted in commit b5791858, failed

**Status**: NOT VIABLE - SimpleCov counts outer module definition

### Option 3: Remove labels_spec.rb
**Pattern**: Delete the spec file so SimpleCov doesn't track the module

**Implementation**:
```bash
rm spec/services/partnerships_engine/labels_spec.rb
```

**Pros**:
- ✅ Matches pattern of facilities.rb and scheduling.rb
- ✅ No coverage metrics = no coverage failure
- ✅ No :nocov: needed

**Cons**:
- ❌ Loses test coverage for RPC delegation behavior
- ❌ Regression risk if Labels API changes
- ❌ 248 lines of tests deleted
- ❌ Goes against testing best practices

**Status**: NOT RECOMMENDED - tests are valuable

### Option 4: Add Executable Code to labels.rb
**Pattern**: Add accessor methods or helper methods to increase coverage

**Implementation**:
```ruby
module Labels
  include Core::API
  add_api LabelsAPI::V1::LabelsEndpoint::Client

  def self.api_client
    LabelsAPI::V1::LabelsEndpoint::Client
  end
end
```

**Pros**:
- ✅ Provides executable code that can be tested
- ✅ No :nocov: needed
- ✅ Coverage naturally meets threshold

**Cons**:
- ❌ Adds unnecessary code just for coverage metrics
- ❌ Violates YAGNI principle
- ❌ Doesn't match the Core::API pattern used elsewhere

**Status**: NOT RECOMMENDED - artificial complexity

## 5. Root Cause Summary

**The fundamental conflict**:
1. **SimpleCov's perspective**: Module definition lines are "code" that should be covered
2. **Reality**: Declaration-only modules have no executable logic to test
3. **SimpleCov's :nocov:**: Must wrap module definition to exclude it from per-file metrics
4. **Yardowners' requirement**: `@owners` tag must be visible in YARD's AST
5. **YARD's parsing**: Comments on module lines interfere with tag association

**Why global_collector.rb works**:
- `@owners` is outside the `:nocov:` block (line 3)
- `:nocov:` only wraps constant assignments (lines 6-9), not module definitions
- YARD can see the `@owners` tag in normal context
- SimpleCov excludes only the constants, not the entire file

**Why labels.rb fails**:
- Must wrap module definition lines to meet per-file coverage threshold
- Wrapping module definition breaks YARD's ability to associate `@owners` with the module
- Cannot position `:nocov:` to satisfy both SimpleCov and yardowners simultaneously

**The real issue**: SimpleCov's per-file threshold doesn't distinguish between "untestable declarations" and "untested code"
