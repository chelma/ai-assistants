# Plan: 2025-11-07-extract-temporal-workflow-pattern

**Workspace**: time-cop
**Project Root**: /Users/chris.helma/workspace/personal/time-cop
**Status**: draft
**GitHub Issue**: N/A
**Created**: 2025-11-07

## Problem Statement

Time Cop needs a reusable architectural reference that enables AI coding assistants to add new Temporal workflows following the established cross-language patterns demonstrated by WorkflowDemoMixed. Currently, the pattern knowledge is implicit in the implementation, making it difficult for AI assistants to replicate the pattern consistently without comprehensive guidance.

## Acceptance Criteria

- [ ] Complete reconnaissance of WorkflowDemoMixed implementation (all involved files mapped)
- [ ] Pattern extraction covering Ruby workflows, cross-language activities, protobuf schemas, testing, and deployment
- [ ] Prescriptive guide with step-by-step workflow creation process
- [ ] Reference to WorkflowDemoMixed as the canonical example
- [ ] Documentation includes dispatcher integration, Helm testing, and load generation patterns
- [ ] Output formatted as shared reference in `.agents/` directory
- [ ] Guide enables creating a "Hello World" workflow with one Python and one Ruby activity

---

## Current State Analysis

### WorkflowDemoMixed - Complete Implementation Map

The WorkflowDemoMixed workflow demonstrates the complete pattern for cross-language workflow orchestration in Time Cop. Reconnaissance reveals **37+ files** involved across the full lifecycle:

#### **Core Workflow Components** (5 files)
- `ruby_worker/app/workflows/workflow_demo_mixed.rb` - Main workflow definition (Ruby)
- `ruby_worker/app/workflows/workflow_list.rb` - Workflow registration
- `ruby_worker/app/workflows/workflow_definition.rb` - Base class with task queue config
- `ruby_worker/app/activities/activity_say_hello_ruby.rb` - Ruby activity implementation
- `python_worker/time_cop_worker/activities/activity_say_hello_python.py` - Python activity implementation

#### **Protobuf Schema Layer** (6+ files)
- `protos/workflow_demo_mixed.proto` - Workflow request/response messages
- `protos/activity_say_hello.proto` - Activity request/response messages
- `protos/config/versions.yaml` - Single source of truth for protoc and library versions
- `protos/Makefile` - Centralized generation with validation
- `protos/scripts/validate.py` - Version enforcement
- `protos/scripts/generate_{python,ruby}.sh` - Language-specific generation

#### **Dispatcher Integration** (5 files)
- `dispatcher/dispatcher/main.py` - FastAPI application
- `dispatcher/dispatcher/api/ruby_worker.py` - Exposes `/ruby/demo-mixed` endpoint
- `dispatcher/dispatcher/temporal_client.py` - Temporal client management
- `dispatcher/dispatcher/env_vars.py` - Environment variable configuration
- Generated protobuf classes in `dispatcher/dispatcher/protos/`

#### **Worker Registration** (4 files)
- `ruby_worker/app/start_worker.rb` - Ruby worker initialization with workflow/activity registration
- `ruby_worker/bin/run.rb` - Ruby worker entry point
- `python_worker/time_cop_worker/main.py` - Python worker with activity registration
- Activity list modules in both workers

#### **Build & Containerization** (3 files)
- `ruby_worker/Containerfile` - Multi-stage build with protoc installation
- `python_worker/Containerfile` - Poetry-based build with protoc
- `dispatcher/Containerfile` - FastAPI dispatcher container

#### **Kubernetes Deployment** (5 files)
- `helm-chart/time-cop-stack/templates/ruby-worker.yaml` - Worker deployment
- `helm-chart/time-cop-stack/templates/dispatcher.yaml` - Dispatcher deployment
- `helm-chart/time-cop-stack/templates/dispatcher-service.yaml` - Service exposure
- `helm-chart/time-cop-stack/templates/ruby-worker-service.yaml` - Metrics service
- `helm-chart/time-cop-stack/values.yaml` - Configuration (task queues, protoc version)

#### **Testing** (2 files)
- `helm-chart/time-cop-stack/templates/tests/test-mixed-workflow-executes.yaml` - End-to-end Helm test
- `helm-chart/time-cop-stack/templates/tests/test-dispatcher-running.yaml` - Dispatcher health check

#### **Load Generation** (2 files)
- `bin/sample-load.sh` - Continuous workflow execution script
- `bin/print-functions.sh` - Logging utilities

#### **Key Patterns Observed**
1. **Cross-language orchestration**: Ruby workflow calls both Ruby (class reference) and Python (string name) activities
2. **Task queue routing**: Activities specify their target worker's task queue
3. **Protobuf type safety**: All inputs/outputs use generated protobuf classes
4. **Centralized proto generation**: Single `protos/` directory with version enforcement
5. **Worker-consumer split**: Centralized generation, consumer-level validation and copying
6. **End-to-end testing**: Helm chart tests validate full workflow execution post-deployment
7. **HTTP exposure**: Dispatcher provides REST API for workflow triggering
8. **Containerized builds**: Protoc installation and generation in container build process

### Architecture Analysis

The pattern demonstrates a **highly structured, type-safe, polyglot workflow orchestration system** with these architectural characteristics:

- **Separation of Concerns**: Workflows (orchestration) vs Activities (execution) vs Dispatcher (HTTP interface)
- **Cross-Language Communication**: Protobuf ensures type safety across Ruby/Python boundaries
- **Version Management**: Strict enforcement via `config/versions.yaml` prevents API mismatches
- **Deployment Integration**: Containerfiles include proto generation; Helm tests validate deployment
- **Developer Ergonomics**: Simple `make` commands, centralized generation, clear registration patterns

## Proposed Solution

Create a comprehensive architectural reference documenting the WorkflowDemoMixed pattern for AI assistant consumption. Following extract-architecture methodology, work in `~/.claude/workspace/time-cop/output/` during extraction, then transform to `.agents/references/` format at completion.

### Working Directory (During Extraction)

All deliverables created in: `~/.claude/workspace/time-cop/output/2025-11-07-extract-temporal-workflow-pattern/`

### Deliverables Created During Extraction

1. **patterns.md** - Comprehensive pattern catalog
   - Cross-language activity invocation patterns
   - Protobuf schema design patterns
   - Testing and deployment patterns
   - File references to WorkflowDemoMixed implementation
   - Priority classifications (CRITICAL/PREFERRED/OBSERVED)

2. **guide_draft.md** - Prescriptive guide content
   - "Building Your First Temporal Workflow" step-by-step walkthrough
   - Core concepts explanation (workflows, activities, task queues, protobuf)
   - Decision points with rationale
   - Cross-references to WorkflowDemoMixed as canonical example

### Final Output Format (After Transformation)

At completion (Step 10), transform deliverables to Shared Reference format per `.agents/FORMAT.md`:

```
.agents/references/temporal-workflow-pattern/
├── README.md                    # Main guide (transformed from guide_draft.md)
│                                # Includes: Overview, Quick Start, Core Concepts,
│                                # Step-by-Step Workflow, Key Design Decisions
└── references/
    └── patterns.md              # Detailed pattern catalog (moved from working dir)
```

**Metadata (README.md frontmatter)**:
```yaml
name: temporal-workflow-pattern
description: >
  Add new Temporal workflows to Time Cop following the WorkflowDemoMixed pattern.
  Use when implementing cross-language workflow orchestration with Ruby workflows
  calling Python and Ruby activities via protobuf. Covers workflow definition,
  dispatcher integration, Helm testing, and load generation.
tags: [temporal, workflow, ruby, python, protobuf, kubernetes, helm]
languages: [ruby, python]
frameworks: [temporal, fastapi]
domains: [workflow-orchestration, polyglot-systems]
```

### Analysis Strategy

Given the comprehensive file inventory (37+ files), use **iterative analysis** approach:

**Iteration 1: Core Workflow & Activities** (~15 files, ~800 lines estimated)
- Focus: Workflow definition, activity implementations, base classes
- Files: workflow_demo_mixed.rb, activity files, workflow_list.rb, activities_list.rb, registration files
- Patterns: Cross-language orchestration, task queue routing, activity invocation

**Iteration 2: Protobuf & Type Safety** (~8 files, ~600 lines estimated)
- Focus: Proto definitions, generation scripts, version management
- Files: Proto files, Makefile, validation scripts, generation scripts
- Patterns: Schema design, centralized generation, version enforcement

**Iteration 3: Dispatcher & HTTP Integration** (~5 files, ~400 lines estimated)
- Focus: FastAPI endpoints, Temporal client, environment configuration
- Files: dispatcher files, API routers, client management
- Patterns: HTTP exposure, workflow triggering, error handling

**Iteration 4: Testing & Deployment** (~9 files, ~700 lines estimated)
- Focus: Helm tests, Containerfiles, Kubernetes resources, load generation
- Files: Helm templates, Containerfiles, sample-load script
- Patterns: End-to-end testing, container builds, deployment configuration

**Total**: ~2,500 lines across 4 iterations

## Implementation Steps

### Phase 1: Reconnaissance (COMPLETE)
1. ✅ Launch Explore agent to survey WorkflowDemoMixed implementation
2. ✅ Create comprehensive file inventory organized by category
3. ✅ Identify all cross-file dependencies and data flows
4. ✅ Document architecture overview and key patterns

### Phase 2: Setup & Planning
1. Create `~/.claude/workspace/time-cop/tasks/2025-11-07-extract-temporal-workflow-pattern_progress.md` file
2. Initialize progress tracking sections (file inventory, iteration plan, phase tracking)
3. Set up `~/.claude/workspace/time-cop/output/2025-11-07-extract-temporal-workflow-pattern/` directory
4. Read progress template additions from extract-architecture skill

### Phase 3: Iterative Pattern Extraction
1. **Iteration 1**: Analyze core workflow and activity files
   - Read workflow_demo_mixed.rb, activity implementations, registration files
   - Document cross-language orchestration patterns
   - Extract task queue routing patterns
   - Document activity invocation (class vs string reference)
   - Create initial `patterns.md` with findings

2. **Iteration 2**: Analyze protobuf and type safety layer
   - Read proto definitions, Makefile, validation/generation scripts
   - Document schema design patterns
   - Extract centralized generation workflow
   - Document version enforcement mechanisms
   - Append findings to `patterns.md`

3. **Iteration 3**: Analyze dispatcher and HTTP integration
   - Read dispatcher main.py, routers, temporal client
   - Document HTTP endpoint patterns
   - Extract workflow triggering patterns
   - Document environment configuration
   - Append findings to `patterns.md`

4. **Iteration 4**: Analyze testing and deployment
   - Read Helm tests, Containerfiles, Kubernetes resources
   - Document end-to-end testing patterns
   - Extract container build patterns
   - Document deployment configuration
   - Append findings to `patterns.md`

5. After each iteration:
   - Update progress file with analyzed files (✅ checkmarks)
   - Document key insights and pattern discoveries
   - Note any deviations from plan

### Phase 4: Critical Review & Priority Classification
1. Review complete `patterns.md` for pattern coverage
2. Classify patterns as CRITICAL/PREFERRED/OBSERVED based on:
   - CRITICAL: Core abstractions, cross-cutting concerns, define the architecture
   - PREFERRED: Stylistic improvements, recommended practices
   - OBSERVED: Implementation details, domain-specific choices
3. Present pattern classifications to user for validation
4. Adjust priorities based on user feedback
5. Determine deliverables scope based on validated priorities

### Phase 5: Prescriptive Guide Creation
1. Create `guide_draft.md` in `~/.claude/workspace/time-cop/output/2025-11-07-extract-temporal-workflow-pattern/` following prescriptive guide structure:
   - Overview section (what this reference provides, when to use it)
   - Quick Start section
   - Core Concepts (workflows, activities, task queues, protobuf)
   - Step-by-step: "Building Your First Temporal Workflow" (7-10 steps)
   - Key Design Decisions with rationale
   - Advanced Patterns (cross-language invocation)
   - Resources section pointing to patterns.md and WorkflowDemoMixed

2. Focus guide on CRITICAL patterns with light coverage of PREFERRED patterns
3. Use file references instead of inline code (e.g., `See ruby_worker/app/workflows/workflow_demo_mixed.rb:15-30`)
4. Mark ambiguities with `[TODO: WHY?]` for human collaboration phase
5. Keep guide lean (400-650 lines) via progressive disclosure

### Phase 6: Human Collaboration - Design Rationale
1. Present guide with `[TODO: WHY?]` markers to user
2. Gather human insight on:
   - Why this cross-language pattern over alternatives
   - Why centralized proto generation vs per-worker
   - What production experience motivated design decisions
   - What trade-offs were considered
   - Guiding principles behind the architecture
3. Incorporate feedback, replacing TODO markers with rationale
4. Add "Design Principles" or "Guiding Philosophy" section if patterns emerge
5. Verify completeness with user

### Phase 7: Token Optimization
1. Review for duplication between guide and pattern catalog
2. Replace inline code examples with file references
3. Ensure pattern catalog stays in references/ for on-demand loading
4. Trim README to minimal quick reference
5. Verify guide is 400-650 lines, patterns.md is reasonable size

### Phase 8: Process Documentation
1. Complete phase summaries in progress file
2. Document lessons learned
3. Capture process improvements for future extractions
4. Note skill conversion option (don't auto-invoke)

### Phase 9: Transform to Shared Reference Format
1. Read `.agents/FORMAT.md` to understand format requirements
2. Transform `guide_draft.md` to `README.md` with YAML frontmatter:
   - Add frontmatter with: name, description, tags, languages, frameworks, domains
   - Structure content: Overview, Quick Start, Core Concepts, Step-by-Step Workflow, Key Design Decisions, Resources
   - Ensure file references are accurate
   - Verify 400-700 line target
3. Move `patterns.md` to `references/` subdirectory
4. Organize final structure in `.agents/references/temporal-workflow-pattern/`:
   ```
   .agents/references/temporal-workflow-pattern/
   ├── README.md
   └── references/
       └── patterns.md
   ```
5. Verify format compliance:
   - [ ] README.md has YAML frontmatter with name and description
   - [ ] Name matches directory name
   - [ ] Uses file references instead of inline code
   - [ ] Includes trade-offs and design rationale

### Phase 10: Final Review
1. Present complete deliverables to user
2. Summarize key insights and patterns extracted
3. Highlight final output structure and location: `.agents/references/temporal-workflow-pattern/`
4. Note that reference is ready for:
   - Git commit and team sharing
   - Conversion to Claude Skill (if desired later)
   - Use by any AI coding assistant

## Risks and Considerations

### Extraction Risks
1. **Pattern completeness**: WorkflowDemoMixed is a demo - may not cover all production patterns
   - Mitigation: Focus on what's demonstrated, note limitations in guide
   - Mark areas where production usage may differ

2. **Context size**: 37+ files could strain context window
   - Mitigation: Use 4 iteration approach (~600-800 lines each)
   - Delegate to codebase-researcher if context becomes strained

3. **Over-documentation**: Risk of capturing too much detail vs actionable patterns
   - Mitigation: Priority classification (CRITICAL/PREFERRED/OBSERVED)
   - Keep guide focused on CRITICAL patterns, details in references/

### Pattern Applicability Risks
1. **Workflow complexity**: Real workflows may need error handling, retries, sagas not shown in demo
   - Mitigation: Document "Advanced Patterns" section for future expansion
   - Note guide covers basic pattern, not production hardening

2. **Protobuf evolution**: Version changes could invalidate patterns
   - Mitigation: Document current versions explicitly (protoc 29.5)
   - Note version management as CRITICAL pattern

3. **Deployment variations**: Pattern assumes minikube/Podman, may differ in production
   - Mitigation: Document as "local development pattern"
   - Note where production deployments may differ

### AI Consumption Risks
1. **File reference rot**: Line numbers may become stale as code evolves
   - Mitigation: Use line ranges, not single lines
   - Include enough context to find code even if lines shift

2. **Missing "why" rationale**: Claude can observe "what" but not "why"
   - Mitigation: Phase 6 human collaboration to capture design rationale
   - Mark all ambiguities during guide creation

## Testing Strategy

### Validation During Extraction
1. **Pattern accuracy**: Cross-reference patterns against actual WorkflowDemoMixed code
2. **File reference validation**: Verify all file paths and line ranges are accurate
3. **Completeness check**: Ensure all 37+ files are accounted for in analysis

### Post-Extraction Validation
1. **Human review**: User reviews reference for:
   - Accuracy of technical details
   - Clarity of step-by-step instructions
   - Completeness of design rationale
   - Usefulness for onboarding new developers or AI assistants

2. **Format compliance**: Verify deliverables match `.agents/FORMAT.md` requirements:
   - README.md has proper YAML frontmatter
   - File structure matches specification
   - Uses file references instead of inline code
   - Progressive disclosure maintained

3. **Independent workflow test**: User will independently test the guide by creating a new workflow following the documented pattern

### Success Criteria
- Guide enables creating a basic workflow without referring to external docs
- All CRITICAL patterns are documented with rationale
- File references are accurate and helpful
- Token-efficient (no unnecessary duplication)
- Format compliant with `.agents/FORMAT.md`
- Ready for git commit and team sharing
