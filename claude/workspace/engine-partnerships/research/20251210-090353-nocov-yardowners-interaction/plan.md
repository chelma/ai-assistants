# Research Plan: SimpleCov :nocov: and Yardowners @owners Interaction Patterns

**Workspace**: engine-partnerships
**Project Root**: ~/workspace/alto/engine-partnerships
**Started**: 2025-12-10 09:03:53

## Research Objective

Understand how SimpleCov `:nocov:` directives and yardowners `@owners` tags interact in the codebase, specifically for declaration-only API wrapper files that need to be excluded from coverage but still require ownership tracking.

## Key Questions

1. **:nocov: Usage Patterns**
   - Where are `:nocov:` directives currently used in the codebase?
   - How are they structured (file-level vs block-level)?
   - Do any files successfully combine `:nocov:` with `@owners` tags?

2. **API Wrapper Module Patterns**
   - How do other `app/services/partnerships_engine/*.rb` files handle coverage?
   - Do similar declaration-only modules (facilities.rb, patients.rb, scheduling.rb) use `:nocov:`?
   - What ownership patterns exist in these files?

3. **Configuration and Rules**
   - What SimpleCov configuration exists in spec/spec_helper.rb?
   - Are there SimpleCov filters or exclusions configured?
   - What's in .yardowners.yml - any special rules or patterns?
   - Does .simplecov file exist with additional configuration?

4. **Historical Context**
   - Have similar issues been addressed before?
   - Git history of changes involving "yardowners", "nocov", or coverage
   - How were conflicts between coverage and ownership resolved?

5. **Alternative Approaches**
   - Are there other ways to exclude files from SimpleCov besides `:nocov:`?
   - SimpleCov filters by path pattern?
   - Can YARD parse `@owners` through `:nocov:` blocks with different positioning?

## Investigation Scope

### Priority Files to Examine
- `app/services/partnerships_engine/labels.rb` (the problem file)
- `app/services/partnerships_engine/facilities.rb`
- `app/services/partnerships_engine/patients.rb`
- `app/services/partnerships_engine/scheduling.rb`
- `app/services/partnerships_engine/*.rb` (all root-level service files)
- `spec/spec_helper.rb` (SimpleCov configuration)
- `.yardowners.yml` (yardowners configuration)
- `.simplecov` (if exists)

### Search Patterns
- Files containing `:nocov:`
- Files containing `@owners` tags
- Files with both `:nocov:` AND `@owners`
- Declaration-only modules using `include Core::API` pattern

## Expected Deliverables

1. **findings_part1.md** - :nocov: usage patterns and API wrapper analysis
2. **findings_part2.md** - Configuration analysis and historical context
3. **summary.md** - Synthesis with recommended approach based on codebase patterns

## Skills Loaded
None initially - will load as needed during investigation
