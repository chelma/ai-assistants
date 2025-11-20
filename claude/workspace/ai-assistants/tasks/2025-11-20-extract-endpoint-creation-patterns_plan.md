# Plan: Extract Endpoint Creation Patterns

**Workspace**: ai-assistants
**Project Root**: /Users/chris.helma/workspace/personal/ai-assistants
**Status**: Ready for implementation
**GitHub Issue**: N/A
**Created**: 2025-11-20

## Problem Statement

Currently, creating endpoints across Scriptdash and Rails Engines requires deep knowledge of the multi-layer architecture, proto definitions, and service coordination patterns. This makes it difficult for new engineers and AI assistants to implement endpoint creation tasks autonomously.

## Acceptance Criteria

- [ ] Reference documentation gathered and reviewed (Notion docs on proto system, architecture, patterns)
- [ ] Reconnaissance complete: understand codebase structure, proto system, layering patterns
- [ ] Patterns extracted with priorities (CRITICAL/PREFERRED/OBSERVED)
- [ ] Reference guide created that enables AI to autonomously implement endpoint creation tasks
- [ ] Guide covers: task description → proto definitions → service implementation → coordination patterns
- [ ] Process and learnings documented

---

## Current State Analysis

### Available Resources

**Concrete implementation examples:**
- Scriptdash PR #48986: FetchAll Action Partnerships endpoint (308 additions, 16 files)
  - Controller → Service → Type definitions → Proto → Tests
  - Includes permissions layer (Ability classes)
- Actions Engine PR #535: FetchAll Action Partnerships endpoint (298 additions, 17 files)
  - Nearly identical structure to Scriptdash
  - Controller → Endpoint → API type definitions → Proto → Tests

**Documentation to review:**
- Notion documentation on proto system, architecture patterns, conventions
- Will be provided at start of reconnaissance phase

### Initial Pattern Observations

From PR analysis, the endpoint creation pattern appears to involve:

**Multi-layer architecture:**
1. **Proto layer**: Protocol Buffer definitions (.proto files)
2. **Type generation**: Auto-generated TypeScript types from protos
3. **API type layer**: Client, Controller, Interface, Routes (Ruby)
4. **Service/Endpoint layer**: Business logic implementation
5. **Controller layer**: Request handling and response formatting
6. **Permissions layer**: Authorization rules (Scriptdash-specific via Ability classes)
7. **Routing**: Registration in config/routes.rb
8. **Testing**: Controller specs

**Service coordination:**
- Pattern appears consistent between Scriptdash and Rails Engines
- Some engines may be consumed by Scriptdash (Actions Engine → Scriptdash)
- Suggests a client-server relationship that needs coordination

**Key unknowns:**
- Full proto system workflow (definition → generation → integration)
- When to create endpoints in one service vs multiple services
- Naming conventions and directory structure patterns
- CODEOWNERS and team ownership patterns
- Testing patterns and quality criteria
- Error handling and validation patterns

## Proposed Solution

Follow the extract-architecture workflow to create a comprehensive, AI-consumable reference guide:

**Phase 1: Reconnaissance** (estimated 2-3 iterations)
- Gather and review Notion reference documentation
- Analyze concrete implementation examples (PRs #48986, #535)
- Explore codebase structure in both Scriptdash and Actions Engine repos
- Create file inventory organized by layer/concern
- Plan analysis iterations (~1500 lines per batch)

**Phase 2: Iterative Analysis** (estimated 5-8 iterations)
- Extract patterns incrementally by layer:
  - Proto system and type generation workflow
  - API type layer conventions (Client, Controller, Interface, Routes)
  - Service/Endpoint implementation patterns
  - Controller and routing patterns
  - Permissions and authorization layer
  - Testing conventions
  - Cross-service coordination patterns
- Document patterns with priorities (CRITICAL/PREFERRED/OBSERVED)
- Update progress file after each iteration

**Phase 3: Critical Review**
- Human priority review of extracted patterns
- Determine deliverables: Prescriptive guide + pattern catalog
- Choose output format: Shared Reference (.agents/) or Claude Skill

**Phase 4: Refinement**
- Create prescriptive "How to Create Endpoints" guide
- Structure: Quick Start → Core Concepts → Step-by-Step Workflow → Design Decisions
- Focus on CRITICAL patterns with deep coverage
- Mark ambiguities for human collaboration (design rationale)

**Phase 5: Human Collaboration**
- Gather design rationale for marked ambiguities
- Answer: "Why this approach?" "What trade-offs?" "When to deviate?"
- Incorporate feedback into guide

**Phase 6: Finalize & Deliver**
- Document process learnings
- Format deliverables per chosen output format
- Present completed reference guide

**Deliverable structure (anticipated):**
- Prescriptive guide: "How to Create Endpoints in Scriptdash and Rails Engines"
- Pattern catalog: Detailed patterns by layer with priorities
- Reference implementation: If reusable abstractions are identified

## Implementation Steps

### Phase 1: Reconnaissance & Planning

1. **Gather reference documentation**
   - User provides Notion docs on proto system, architecture, patterns
   - Review and document key architectural concepts
   - Identify terminology and conventions

2. **Clone/locate target repositories**
   - Locate Scriptdash repository (may need to clone to ~/workspace/claude/)
   - Locate Actions Engine repository (may need to clone to ~/workspace/claude/)
   - Document repository structure and key directories

3. **Analyze concrete implementation examples**
   - Review PR #48986 (Scriptdash) in detail
   - Review PR #535 (Actions Engine) in detail
   - Document file-by-file changes and patterns observed

4. **Explore codebase structure**
   - Use Explore agent (very thorough) to survey both repositories
   - Identify files related to endpoint creation patterns
   - Map directory structure by layer (proto, types, controllers, services, etc.)

5. **Create file inventory**
   - Organize files by layer/domain/concern with line counts
   - Add checkboxes for tracking analysis progress
   - Group into iteration batches (~1500 lines each)

6. **Choose investigation approach**
   - Calculate total lines from inventory
   - If ≤3,000 lines: Direct reading approach
   - If >3,000 lines: Delegated investigation (codebase-researcher per iteration)
   - Document choice and rationale

7. **Present reconnaissance plan for approval**
   - Total iterations planned
   - Analysis approach (direct vs delegated)
   - Files per iteration with grouping rationale
   - Expected deliverables

### Phase 2: Iterative Analysis

8. **Execute planned iterations**
   - For each iteration batch:
     - Read files (or delegate to codebase-researcher)
     - Extract patterns with format: Purpose → Implementation → When to use → Trade-offs
     - Add priority tags: [PRIORITY: CRITICAL/PREFERRED/OBSERVED]
     - Document in patterns.md with file references (relative to project root)
     - Update progress file immediately
     - Mark files analyzed in inventory

9. **Pattern organization**
   - Group patterns by layer/concern:
     - Proto system and type generation
     - API type layer (Client, Controller, Interface, Routes)
     - Service/Endpoint layer
     - Controller layer
     - Permissions and authorization
     - Routing configuration
     - Testing patterns
     - Cross-service coordination

10. **Human priority review checkpoint**
    - Present pattern breakdown (CRITICAL/PREFERRED/OBSERVED counts)
    - Human reviews and adjusts priority tags
    - Document priority breakdown in progress file

### Phase 3: Critical Review & Deliverable Scoping

11. **Review pattern documentation**
    - Is output descriptive ("what exists") or prescriptive ("how to build")?
    - Can someone use this to implement endpoints autonomously?
    - Are reusable abstractions clearly identified?
    - What is the distribution of CRITICAL vs PREFERRED vs OBSERVED patterns?

12. **Determine deliverables**
    - Pattern Catalog (already created)
    - Prescriptive Guide: "How to Create Endpoints" (anticipated primary deliverable)
    - Reference Implementation: If reusable abstractions identified
    - Quick reference guide: Optional

13. **Choose output format checkpoint**
    - Option 1: Shared Reference (AI-agnostic format in .agents/)
    - Option 2: Claude Skill (Claude Code-specific format)
    - Document choice in progress file

### Phase 4: Refinement

14. **Create prescriptive guide**
    - Structure: Quick Start → Core Concepts → Step-by-Step Workflow → Design Decisions
    - Use imperative/infinitive form (not second person)
    - Use file references instead of inline code: `See path/to/file.py:line-range`
    - Include "why" and "when" for design decisions
    - Document anti-patterns and trade-offs
    - Mark ambiguities: `[TODO: WHY?]` for unclear rationale (focus on CRITICAL decisions)

15. **Create reference implementation (if applicable)**
    - Extract reusable abstractions
    - Make domain-agnostic
    - Enhance docstrings with pattern explanations
    - Create minimal but complete example
    - Mark ambiguities: `# TODO: Why this approach?`

16. **Token optimization**
    - Apply file references (replace inline code)
    - Enhance docstrings (make reference implementation self-teaching)
    - Trim READMEs (structure tree + key patterns)
    - Progressive disclosure (lean main documents, detailed info in references/)

### Phase 5: Human Collaboration

17. **Design rationale gathering checkpoint**
    - Present marked deliverables (guide/implementation with TODO markers)
    - Human provides context for each marker:
      - Design rationale (why X over Y)
      - Trade-offs (what was gained/sacrificed)
      - Guiding principles
      - Production experience
      - When to deviate
    - Incorporate feedback (replace TODOs, add design principles)
    - Verify completeness

### Phase 6: Finalize & Deliver

18. **Process documentation**
    - Add "Phase Completion Summary" sections to progress file
    - Deliverables created (list with locations)
    - Process documentation (what worked well, key decisions)
    - Artifacts for future extractions (reusable patterns, principles)
    - Lessons learned (what worked better/harder than expected)

19. **Format & deliver based on Phase 3 choice**
    - If Shared Reference: Transform to .agents/ format per FORMAT.md
    - If Claude Skill: Invoke skill-creator skill for formatting
    - Organize deliverables in appropriate directory

20. **Final review**
    - Present all deliverables created
    - Output directory structure
    - Key insights (core patterns, reusable abstractions, design principles)
    - Suggested next steps

## Risks and Considerations

**Codebase access:**
- May need to clone Scriptdash and Actions Engine repositories
- Use ~/workspace/claude/ as working directory for external repos
- Ensure proper GitHub authentication via gh CLI

**Scope management:**
- Pattern may vary across different Rails Engines (not just Actions Engine)
- May need to expand scope to cover multiple engines if patterns differ significantly
- Could start with Actions Engine, then validate/expand to other engines if needed

**Documentation completeness:**
- Notion docs may have gaps that require codebase investigation
- May need to infer patterns from code when documentation unclear
- Balance between documentation and code analysis

**Pattern complexity:**
- Proto system may be complex and require dedicated extraction focus
- Type generation workflow may involve tooling/build steps not visible in code
- May need to understand build/deployment pipeline for complete picture

**Cross-service coordination:**
- Understanding when to create endpoints in one vs multiple services
- Client-server relationship patterns between Scriptdash and engines
- May require understanding request flow and service boundaries

**Domain specificity:**
- Need to extract general patterns while using domain-specific examples
- Risk of being too specific to Action Partnerships
- Should validate patterns apply to other endpoint types (FetchOne, Create, Update, Delete)

**Token budget:**
- Large codebase exploration may consume significant context
- May need to use codebase-researcher for delegation if >3k lines
- Progressive disclosure and file references critical for token efficiency

## Testing Strategy

**Validation approach:**

1. **Pattern validation during extraction**
   - Cross-reference patterns across both PRs
   - Verify patterns apply to different endpoint types (FetchAll, FetchOne, etc.)
   - Check consistency between Scriptdash and Actions Engine implementations

2. **Guide completeness check**
   - Can the guide answer: "How do I create a FetchAll endpoint for X?"
   - Are all layers covered (proto → types → controller → service → tests)?
   - Are decision points clear (when to use which patterns)?

3. **AI consumption test**
   - After guide creation, test with a fresh Claude session
   - Provide guide + a new endpoint task description
   - Validate AI can generate implementation plan without additional context

4. **Human review**
   - Chris reviews guide for accuracy and completeness
   - Validates design rationale and trade-offs captured correctly
   - Confirms patterns match production experience and conventions

**Success criteria:**
- Guide enables AI to autonomously plan endpoint creation tasks
- All CRITICAL patterns documented with rationale
- File references are accurate and resolvable
- Output is token-efficient (file refs, progressive disclosure)
- Process is resumable across multiple sessions
