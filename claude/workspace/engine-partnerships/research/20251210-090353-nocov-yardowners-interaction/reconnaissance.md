# Reconnaissance Findings

## Repository Context
- **Technology stack**: Ruby on Rails, Sorbet (typed: strict), RSpec, SimpleCov, YARD
- **Architecture style**: Rails Engine (PartnershipsEngine) with Boxcar deployment
- **Coverage tools**: SimpleCov with per-file threshold (90%), yardowners for ownership tracking
- **Key modules relevant to investigation**:
  - API wrapper modules in `app/services/partnerships_engine/*.rb`
  - SimpleCov configuration in `spec/spec_helper.rb`
  - Yardowners configuration in `.yardowners.yml`

## Files Identified

### Category 1: The Problem File (1 file, 18 lines)
- `app/services/partnerships_engine/labels.rb` (18 lines) - Declaration-only API wrapper with `:nocov:` and `@owners` conflict

### Category 2: Similar API Wrapper Files Without :nocov: (13 files, ~700 lines estimated)
These files follow the same pattern but DON'T use `:nocov:`:
- `app/services/partnerships_engine/facilities.rb` (14 lines) - Simple `include Core::API` + `add_api` pattern
- `app/services/partnerships_engine/patients.rb` (32 lines) - API wrapper with accessor methods
- `app/services/partnerships_engine/scheduling.rb` (11 lines) - Minimal API wrapper
- `app/services/partnerships_engine/prescriptions.rb` (30 lines) - Namespace with accessor methods
- `app/services/partnerships_engine/comms.rb` (29 lines) - Namespace with accessor methods
- `app/services/partnerships_engine/billing.rb` (56 lines) - Namespace with many accessors
- `app/services/partnerships_engine/deliver.rb` (14 lines) - Namespace with accessor method
- `app/services/partnerships_engine/analytics.rb` (not examined yet)
- `app/services/partnerships_engine/bot_worker.rb` (not examined yet)
- `app/services/partnerships_engine/consumers.rb` (not examined yet)
- `app/services/partnerships_engine/experimentation.rb` (not examined yet)
- `app/services/partnerships_engine/pdf_utils.rb` (not examined yet)
- `app/services/partnerships_engine/providers.rb` (not examined yet)

### Category 3: Files Using :nocov: (2 files)
Only 2 files in the codebase use `:nocov:` directives:
- `app/services/partnerships_engine/labels.rb` (18 lines) - **HAS CONFLICT**: `:nocov:` outside module prevents yardowners parsing
- `lib/global_collector.rb` (35 lines) - **SUCCESSFUL COEXISTENCE**: `@owners` at line 3, `:nocov:` wraps only constant definitions (lines 6-9)

### Category 4: Configuration Files (2 files)
- `spec/spec_helper.rb` (149 lines) - SimpleCov configuration with per-file threshold enforcement
- `.yardowners.yml` (216 lines) - Team/domain ownership configuration

## Initial Observations

1. **Very limited :nocov: usage**: Only 2 files use `:nocov:` in the entire codebase
2. **Successful pattern exists**: `lib/global_collector.rb` shows `@owners` and `:nocov:` CAN coexist
3. **Key difference**: In `global_collector.rb`, `@owners` is OUTSIDE the `:nocov:` block
4. **Recent history**: Three commits (b9954b40, b5791858, aae7667a) show evolution of the problem:
   - First attempt: `:nocov:` outside module (b9954b40) - fixed SimpleCov, broke yardowners
   - Second attempt: `:nocov:` inside module after `@owners` (b5791858) - tried to fix yardowners
   - Third attempt: `:nocov:` back outside (aae7667a) - reverted to fix SimpleCov again
5. **SimpleCov configuration**: Uses 90% per-file threshold via `minimum_coverage_by_file`
6. **SimpleCov filters**: Many files explicitly filtered via `add_filter` (31-42), but NOT labels.rb

## Investigation Strategy

Based on reconnaissance, need to:

1. **Analyze the successful pattern** in `global_collector.rb`:
   - How is `@owners` positioned relative to `:nocov:`?
   - Why does yardowners parse it successfully?
   - Can this pattern apply to `labels.rb`?

2. **Understand SimpleCov's :nocov: semantics**:
   - Does `:nocov:` need to wrap the module definition?
   - Can it wrap only the contents?
   - How does SimpleCov determine what to exclude?

3. **Understand yardowners parsing**:
   - Where does yardowners look for `@owners` tags?
   - Does `:nocov:` comment interfere with YARD parsing?
   - Can `@owners` be outside the module declaration?

4. **Evaluate alternative approaches**:
   - Can `labels.rb` be added to SimpleCov filters instead?
   - Pattern: `add_filter 'app/services/partnerships_engine/labels.rb'`
   - Would this avoid `:nocov:` entirely?

5. **Compare with other API wrappers**:
   - Why don't other simple wrappers (facilities.rb, scheduling.rb) need `:nocov:`?
   - What makes labels.rb different?
   - Is there additional code that gets executed that needs coverage?
