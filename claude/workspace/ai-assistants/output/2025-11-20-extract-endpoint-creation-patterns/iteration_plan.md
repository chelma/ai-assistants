# Iteration Plan: FetchAll + FetchOne Pattern Extraction

**Created**: 2025-11-20
**Scope**: FetchAll and FetchOne endpoint patterns for Scriptdash and Rails Engines
**Deliverable**: Claude Skill for endpoint creation

---

## Content Inventory

### Available Documentation

**From reconnaissance (already created):**
1. `reconnaissance_summary.md` - 19k tokens, architectural overview
2. `pr_analysis.md` - 5k tokens, detailed PR comparison

**From codebase exploration (new):**

**Scriptdash (6 comprehensive documents, 5,380 lines):**
- INDEX.md - Navigation guide
- FINDINGS_SUMMARY.txt - Executive summary
- ENDPOINT_INVENTORY.md (1,092 lines) - Complete endpoint reference
- QUICK_REFERENCE.md - Developer cheat sheet
- RECONNAISSANCE_SUMMARY.md (2,645 lines) - Deep architecture analysis
- PR_ANALYSIS.md - Design review guidelines

**Actions Engine (comprehensive inventory):**
- 13 endpoints analyzed in detail
- Pattern variations documented
- Edge cases identified

### Total Content Estimate
- Reconnaissance docs: ~24k tokens
- Scriptdash Explore output: ~5,380 lines (~40k tokens estimated)
- Actions Engine Explore output: ~2,000 lines (~15k tokens estimated)
- **Total**: ~79k tokens of content

---

## Investigation Approach Decision

**Threshold**: 3,000 lines → Use delegated investigation (codebase-researcher)

**Actual**: ~7,380 lines of documentation + source files to analyze

**Decision**: **Hybrid Approach**
- **Direct reading** of Explore agent outputs (already synthesized)
- **Supplemental file reads** for specific pattern examples
- **No delegation needed** - Explore agents already did the heavy lifting

**Rationale**:
- Explore agents already synthesized patterns from source code
- Reading their outputs is more efficient than re-analyzing source files
- We can read specific source files as needed for clarification

---

## Pattern Organization (By Layer)

### Layer 1: Proto System
- Proto type definitions (`.proto` files for types)
- Proto endpoint definitions (`.proto` files for services)
- Service V2.0 patterns
- Request/Response message patterns
- Field annotations and conventions

### Layer 2: Code Generation
- Generated interface modules
- Generated client modules
- Generated controller modules
- Generated routes modules
- Generated RPC client modules (Engine only)
- Type structs and enums

### Layer 3: Implementation Layer
- Endpoint implementations (business logic)
- Adapter pattern usage
- Database access patterns
- Error handling
- Type mapping (ActiveRecord → Proto structs)

### Layer 4: Controller Layer
- Controller structure (include mixin + endpoint accessor)
- Base controller inheritance
- Sorbet type annotations

### Layer 5: Routing Layer
- Routes extension pattern
- URL patterns (RESTful mapping)
- HTTP verb mapping

### Layer 6: Core API Integration (Scriptdash only)
- Core API module structure
- `add_api` pattern
- Endpoint configuration (local vs RPC)
- Dotted accessor pattern

### Layer 7: Permissions Layer (Scriptdash only)
- Ability class patterns
- WunderbarAbility patterns
- Authorization checks in endpoints
- Permission types (read, create, update, destroy)

### Layer 8: Testing Layer
- Engine test patterns (RPC client with `:rpc_client_requests`)
- Scriptdash test patterns (controller specs with mocking)
- Factory usage
- Test data setup

---

## Iteration Plan (8 Iterations)

### Iteration 1: Proto System Patterns (FetchAll + FetchOne)
**Files to analyze:**
- Scriptdash ENDPOINT_INVENTORY.md (proto sections)
- Actions Engine inventory (proto definitions)
- Sample proto files for both FetchAll and FetchOne

**Focus:**
- Proto message structure (Request/Response patterns)
- Service definition patterns
- Field annotations (`opts.field`, required vs optional)
- Variations: empty request, optional IDs, required IDs
- Naming conventions

**Expected patterns:** 5-8 patterns (CRITICAL/PREFERRED/OBSERVED)

**Estimated effort:** Read ~500 lines of docs + 2-3 proto files

---

### Iteration 2: Generated Code Patterns
**Files to analyze:**
- Actions Engine inventory (Generated Code Pattern section)
- Sample generated files: interface.rb, client.rb, controller.rb

**Focus:**
- Interface module structure (Request/Response structs, Abstract class)
- Client module structure (local/RPC switching)
- Controller module structure (action methods, parameter extraction)
- Routes module structure
- RPC client structure (Engine only)
- Sorbet type annotations in generated code

**Expected patterns:** 6-10 patterns

**Estimated effort:** Read ~800 lines

---

### Iteration 3: Endpoint Implementation Patterns (FetchAll)
**Files to analyze:**
- Scriptdash ENDPOINT_INVENTORY.md (FetchAll implementations)
- Actions Engine inventory (FetchAll implementations)
- Sample endpoint files

**Focus:**
- Three implementation styles:
  - Delegation to Core API (Scriptdash)
  - Direct Model Query (Engine)
  - Custom Service Logic
- Adapter pattern usage
- Database query patterns (includes, joins, ordering)
- Empty request vs IDs parameter variations
- Optional IDs patterns
- Filter-based patterns

**Expected patterns:** 8-12 patterns

**Estimated effort:** Read ~1,000 lines

---

### Iteration 4: Endpoint Implementation Patterns (FetchOne)
**Files to analyze:**
- Scriptdash ENDPOINT_INVENTORY.md (FetchOne implementations)
- Actions Engine inventory (FetchOne implementations)
- Sample endpoint files

**Focus:**
- FetchOne signature patterns
- Database access (single find vs includes)
- Adapter usage
- Error handling (RecordNotFound)
- Type mapping

**Expected patterns:** 4-6 patterns

**Estimated effort:** Read ~500 lines

---

### Iteration 5: Controller, Routes, and HTTP Integration
**Files to analyze:**
- Scriptdash QUICK_REFERENCE.md (controller patterns)
- Actions Engine inventory (controller section)
- Sample controller files

**Focus:**
- Controller structure (include + endpoint accessor)
- Memoization pattern
- Sorbet type annotations
- Routes extension pattern
- HTTP verb mapping (show → FetchOne, index → FetchAll)
- URL patterns

**Expected patterns:** 6-8 patterns

**Estimated effort:** Read ~600 lines

---

### Iteration 6: Core API and Permissions (Scriptdash)
**Files to analyze:**
- Scriptdash RECONNAISSANCE_SUMMARY.md (Core API section)
- Scriptdash PR_ANALYSIS.md (permissions section)
- pr_analysis.md (permissions patterns)

**Focus:**
- Core API module structure
- `include Core::API` pattern
- `add_api` pattern
- Endpoint configuration (local vs RPC)
- Dotted accessor pattern
- Ability class patterns
- Authorization checks
- Permission types

**Expected patterns:** 8-10 patterns

**Estimated effort:** Read ~800 lines

---

### Iteration 7: Testing Patterns
**Files to analyze:**
- Scriptdash ENDPOINT_INVENTORY.md (testing section)
- Actions Engine inventory (testing patterns)
- pr_analysis.md (test examples)

**Focus:**
- Engine test patterns (`:rpc_client_requests`, RPC client usage)
- Scriptdash test patterns (controller specs, mocking)
- Factory usage
- Permission testing
- Test structure

**Expected patterns:** 6-8 patterns

**Estimated effort:** Read ~700 lines

---

### Iteration 8: Edge Cases, Variations, and Anti-Patterns
**Files to analyze:**
- Scriptdash FINDINGS_SUMMARY.txt
- Actions Engine inventory (Edge Cases section)
- reconnaissance_summary.md (Troubleshooting section)

**Focus:**
- Empty request patterns
- Optional vs required IDs
- Filter-based FetchAll
- Scoped vs unscoped
- Version-specific implementations (v1 vs v2)
- Common gotchas
- Troubleshooting patterns
- Anti-patterns to avoid

**Expected patterns:** 6-10 patterns

**Estimated effort:** Read ~800 lines

---

## Total Iteration Summary

- **Total iterations**: 8
- **Estimated total reading**: ~5,700 lines of documentation + selective source file reads
- **Expected patterns**: 50-70 total patterns
- **Priority distribution estimate**:
  - CRITICAL: 20-25 patterns (core abstractions, must-haves)
  - PREFERRED: 15-20 patterns (strong recommendations)
  - OBSERVED: 15-25 patterns (conventions, nice-to-haves)

---

## Pattern Documentation Format

For each pattern, document:

```markdown
### Pattern Name

**Priority**: [CRITICAL | PREFERRED | OBSERVED]

**Purpose**: What problem does this solve? Why does this pattern exist?

**Implementation**:
- File reference: `path/to/file.rb:line-range`
- Key code snippet (if inline needed)
- Step-by-step description

**When to use**:
- Scenarios where this pattern applies
- Decision criteria

**Trade-offs**:
- What do you gain?
- What do you sacrifice?
- When NOT to use this pattern

**Related patterns**: Links to other patterns that work together

**Examples**: File references to concrete implementations
```

---

## Output Organization

Patterns will be written to: `patterns.md` (living document)

**Structure:**
```markdown
# FetchAll + FetchOne Endpoint Patterns

## Table of Contents
[Auto-generated based on layers]

## Layer 1: Proto System
### [Pattern Name] - [PRIORITY]
...

## Layer 2: Code Generation
...

[etc.]
```

**Living document approach**:
- Write patterns to `patterns.md` immediately after each iteration
- Keep progress file lean (just tracking and outcomes)
- Enables high iteration count without context bloat

---

## Next Steps

1. **Present this plan for approval** ✓ (you're reading it!)
2. **Execute iterations 1-8** (mark progress in todo list)
3. **Human priority review** (after all iterations)
4. **Create Claude Skill deliverable** (Phase 4)
5. **Gather design rationale** (Phase 5)
6. **Finalize and package** (Phase 6)

---

## Decisions Made

1. **Scope**: Focused approach - PRs + Actions Engine + minimal Scriptdash spot-checking (NOT exhaustive survey)
2. **Code examples**: INLINE code snippets for portability (no external file references)
3. **Troubleshooting**: YES - include common errors and fixes
4. **Philosophy**: Prescriptive ("do it THIS way") not descriptive ("here are 10 ways")

## Revised Iteration Plan (Focused)

### Phase 2A: Extract from North Star (4 iterations)

**Iteration 1**: Proto patterns from PRs + Actions Engine
**Iteration 2**: Implementation patterns from PRs + Actions Engine
**Iteration 3**: Controller/Routes/Testing patterns from PRs + Actions Engine
**Iteration 4**: Core API + Permissions patterns from PRs

### Phase 2B: Validation (1 iteration)

**Iteration 5**: Spot-check 3-5 recent Scriptdash endpoints to validate patterns

### Phase 2C: Edge Cases (1 iteration)

**Iteration 6**: Document edge cases, variations, common errors, troubleshooting

**Total**: 6 focused iterations instead of 8 broad ones
**Expected output**: 20-30 CRITICAL patterns, all current best practices
