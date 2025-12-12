# Summary: SimpleCov :nocov: and Yardowners @owners Interaction

## Executive Summary

The conflict between SimpleCov's `:nocov:` directive and yardowners' `@owners` tag parsing in `labels.rb` stems from a fundamental incompatibility:

- **SimpleCov requires** `:nocov:` to wrap the module definition lines to exclude them from per-file coverage metrics
- **Yardowners requires** `@owners` tags to be visible in YARD's AST, which breaks when `:nocov:` wraps module definitions
- **No positioning** of `:nocov:` can satisfy both tools simultaneously for declaration-only modules

## Research Questions Answered

### 1. Other files using :nocov: directives

**Finding**: Only 2 files use `:nocov:` in the codebase:

1. **`lib/global_collector.rb`** (SUCCESSFUL):
   - `@owners` tag at line 3 (outside `:nocov:`)
   - `:nocov:` wraps only constant definitions (lines 6-9)
   - Does NOT wrap module definitions
   - Both SimpleCov and yardowners work correctly

2. **`app/services/partnerships_engine/labels.rb`** (PROBLEMATIC):
   - `:nocov:` wraps entire module definition (current state)
   - Fixed SimpleCov but broke yardowners
   - Three commit attempts show no viable `:nocov:` positioning

**Key insight**: `global_collector.rb` shows `:nocov:` and `@owners` CAN coexist, but only when `:nocov:` wraps specific statements (constants), not module definitions.

### 2. Declaration-only API wrapper modules

**Finding**: 4 files use the `include Core::API` + `add_api` pattern:

| File | add_api? | Accessor Methods? | Spec File? | Coverage Issue? | Solution? |
|------|----------|-------------------|------------|-----------------|-----------|
| facilities.rb | ✅ | ❌ | ❌ | ❌ | N/A - not measured |
| scheduling.rb | ✅ | ❌ | ❌ | ❌ | N/A - not measured |
| labels.rb | ✅ | ❌ | ✅ | ✅ | Needs fix |
| patients.rb | ✅ | ✅ (4 methods) | Partial | ❌ | Methods provide coverage |

**Critical finding**: `labels.rb` is the ONLY declaration-only module with a spec file. This is why it triggers coverage measurement while facilities.rb and scheduling.rb don't.

**Timeline**:
- Dec 9, 2025 (5db34341): `labels_spec.rb` added (248 lines of tests)
- Dec 10, 2025 (b9954b40): SimpleCov failure → `:nocov:` added
- Dec 10, 2025 (b5791858): Yardowners failure → `:nocov:` repositioned (failed)
- Dec 10, 2025 (aae7667a): `:nocov:` moved back → yardowners still fails

### 3. Yardowners configuration and special cases

**Finding**: No special yardowners configuration for handling `:nocov:`

`.yardowners.yml` configuration:
- Scans paths: `app/`, `lib/`, `db/seeds/domains/`
- Ignores: `app/types/`, `lib/sandbox/seeds/`
- No file-specific exclusions available
- Uses YARD's AST parser to find `@owners` tags

**SimpleCov-yardowners integration** (spec_helper.rb lines 51-65):
```ruby
teams.each do |team|
  add_group team.to_s do |src_file|
    src_file.src.each do |line|
      if line.include? "# @owners { team: #{team}"
        file_includes_team = true
      end
    end
  end
end
```
- SimpleCov scans for `@owners` tags to group coverage by team
- This REQUIRES `@owners` to be readable in source
- Further evidence that `@owners` must not be hidden by `:nocov:`

### 4. Similar CI failures in git history

**Finding**: Precedent exists for filtering namespace modules from SimpleCov

**Commit d1fd823e** (Dec 9, 2024) - "test: fix test coverage":
```ruby
add_filter 'app/services/partnerships_engine/comms.rb'
```
- Added filter for `comms.rb` (namespace-only module)
- Same reason: declaration-only file with no testable logic
- Solved coverage problem without using `:nocov:`

**Current filters** (spec_helper.rb lines 40-42):
```ruby
add_filter 'app/services/partnerships_engine/comms.rb'
add_filter 'app/services/partnerships_engine/consumers.rb'
add_filter 'app/services/partnerships_engine/harrow/consumers.rb'
```

### 5. Alternative patterns

**Finding**: SimpleCov `add_filter` is the established pattern for declaration-only modules

**Comparison of approaches**:

| Approach | SimpleCov OK? | Yardowners OK? | Precedent? | Recommended? |
|----------|---------------|----------------|------------|--------------|
| `:nocov:` outside module | ✅ | ❌ | Current state | ❌ |
| `:nocov:` inside module | ❌ | ✅ | Tried in b5791858 | ❌ |
| SimpleCov filter | ✅ | ✅ | comms.rb, consumers.rb | ✅ |
| Remove spec file | ✅ | ✅ | facilities.rb | ❌ |
| Add executable code | ✅ | ✅ | None | ❌ |

## Recommended Approach

### Use SimpleCov Filter (Matches Codebase Pattern)

**Change required**:
```ruby
# In spec/spec_helper.rb, add after line 42:
add_filter 'app/services/partnerships_engine/labels.rb'
```

**Rationale**:
1. ✅ **Precedent exists**: `comms.rb` and `consumers.rb` use this exact approach
2. ✅ **Preserves tests**: Keeps valuable 248-line test suite
3. ✅ **Preserves @owners**: No changes to labels.rb needed
4. ✅ **Simple**: One-line addition to spec_helper.rb
5. ✅ **Clear intent**: Filtered files are explicitly documented
6. ✅ **Both tools happy**: SimpleCov ignores file, yardowners sees `@owners`

**Trade-off**: File won't appear in coverage reports, but this accurately reflects reality - declaration-only modules have no testable logic.

### Implementation Steps

1. **Remove `:nocov:` from labels.rb**:
   ```ruby
   # typed: strict

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
   ```

2. **Add SimpleCov filter** (spec/spec_helper.rb after line 42):
   ```ruby
   add_filter 'app/services/partnerships_engine/harrow/consumers.rb'
   add_filter 'app/services/partnerships_engine/labels.rb'  # <-- ADD THIS
   add_filter '/lib/script/'
   ```

3. **Verify both checks pass**:
   ```bash
   bundle exec rspec spec/services/partnerships_engine/labels_spec.rb
   bundle exec rake yardowners
   ```

4. **Commit with clear message**:
   ```
   fix: exclude labels.rb from SimpleCov using filter pattern

   Labels module is declaration-only (Core::API + add_api) with no
   executable logic. Following established pattern from comms.rb and
   consumers.rb, use SimpleCov filter instead of :nocov: directive.

   This resolves conflict where :nocov: positioning satisfied SimpleCov
   but broke yardowners parsing of @owners tags.

   Refs: commits d1fd823e (comms.rb filter), aae7667a (nocov attempt)
   ```

## Supporting Evidence

### File References

**Research outputs**:
- `plan.md` - Research objectives and questions
- `reconnaissance.md` - Initial survey and file inventory
- `findings_part1.md` - Detailed analysis of all patterns
- `progress.md` - Investigation checkpoint

**Key codebase files examined**:
- `app/services/partnerships_engine/labels.rb` - Problem file
- `app/services/partnerships_engine/{facilities,scheduling,patients}.rb` - Similar patterns
- `app/services/partnerships_engine/comms.rb` - Filtered namespace module (precedent)
- `lib/global_collector.rb` - Successful :nocov: + @owners coexistence
- `spec/spec_helper.rb` - SimpleCov configuration
- `.yardowners.yml` - Yardowners configuration

**Relevant commits**:
- `5db34341` - Added labels_spec.rb (triggered coverage measurement)
- `b9954b40` - First :nocov: attempt (fixed SimpleCov, broke yardowners)
- `b5791858` - :nocov: repositioning attempt (broke SimpleCov)
- `aae7667a` - Current state (SimpleCov OK, yardowners broken)
- `d1fd823e` - Precedent: added comms.rb filter for same reason

## Next Steps

1. **Implement filter approach** (recommended)
2. **Consider documenting pattern**: Add comment explaining why declaration-only modules are filtered
3. **Future consideration**: If facilities.rb or scheduling.rb get spec files, they'll need the same filter

## Technical Details

### Why :nocov: Cannot Work for This Case

**SimpleCov's behavior**:
- Counts `module PartnershipsEngine` as line 1 of executable code
- Counts `module Labels` as line 2 of executable code
- Counts `include Core::API` as line 3
- Counts `add_api ...` as line 4
- Total: 6 lines of "code", 5 uncovered (83.33%)
- Per-file threshold: 90% required → FAILS

**To pass SimpleCov**: Must wrap lines 1-2 (module definitions) with `:nocov:`

**Yardowners' behavior**:
- Uses YARD to parse Ruby AST
- Looks for `@owners` tag in module documentation
- When `:nocov:` wraps `module PartnershipsEngine`, YARD sees:
  ```ruby
  # :nocov:
  module PartnershipsEngine
  ```
- The comment association breaks AST parsing
- `@owners` inside the module can't be associated with the outer module
- Error: "missing team owner for PartnershipsEngine"

**The incompatibility**: No `:nocov:` positioning can:
1. Exclude module definition lines from SimpleCov (requires wrapping)
2. Keep module definition clear for YARD parsing (requires NOT wrapping)

### Why SimpleCov Filter Works

**Filter behavior**:
- Completely excludes file from coverage tracking
- File never appears in coverage metrics
- No per-file threshold check
- File can still be loaded and tested

**Yardowners behavior unchanged**:
- Still scans file normally
- Parses `@owners` tag successfully
- No SimpleCov directives to interfere with parsing

**Result**: Both tools operate independently without conflict.
