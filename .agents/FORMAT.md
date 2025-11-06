# Architecture Reference Format

**Last Updated**: 2025-11-06
**Purpose**: Canonical format definition for AI-consumable architecture references

## Overview

Architecture references are structured guides that document patterns, design decisions, and reusable abstractions from codebases. They are designed for consumption by AI coding assistants (Claude Code, GitHub Copilot, Cursor, Windsurf, etc.) and human engineers.

**Key Characteristics**:
- **AI-first design**: Optimized for AI assistant consumption with progressive disclosure, file references, and semantic structure
- **Assistant-agnostic**: Core format works across different AI coding assistants
- **Portable**: Can be converted to assistant-specific formats (Claude Skills, Cursor Rules, etc.)
- **Composable**: References can build on or reference other references

**When to create references**:
- Extracted architectural patterns from existing codebases
- Documented design decisions for complex systems
- Created reusable abstractions or frameworks
- Established team coding standards or conventions
- Built reference implementations for common patterns

## Directory Structure

Each reference lives in its own directory under `.agents/references/`:

```
.agents/
├── FORMAT.md                          # This file (format definition)
└── references/
    └── <reference-name>/
        ├── README.md                      # Main guide (REQUIRED)
        ├── references/                    # Detailed documentation (OPTIONAL)
        │   ├── patterns.md
        │   ├── case_studies.md
        │   └── decisions.md
        └── assets/                        # Code, templates, examples (OPTIONAL)
            ├── reference_implementation/
            ├── templates/
            └── examples/
```

### Naming Conventions

**Reference names** (directory names):
- Use lowercase letters, numbers, and hyphens only
- Maximum 64 characters
- Descriptive and specific (e.g., `langchain-expert-builder`, not `llm-guide`)
- Examples: `multi-expert-llm-patterns`, `aws-client-factory`, `temporal-workflow-orchestration`

**File names**:
- README.md is always named exactly `README.md` (not `GUIDE.md`, `REFERENCE.md`, etc.)
- Files in `references/` use descriptive names: `patterns.md`, `case_studies.md`, `api_documentation.md`
- Files in `assets/` follow target language conventions (Python: snake_case, Java: PascalCase, etc.)

## README.md Structure

The README.md is the primary entry point for each reference. It contains YAML frontmatter for metadata and markdown content for the guide.

### YAML Frontmatter (Required)

```yaml
---
name: reference-name                    # REQUIRED: Must match directory name
description: >                          # REQUIRED: 1-3 sentences, AI discoverability
  Brief description of what this reference provides and when to use it.
  Should be specific enough for AI assistants to determine relevance.
tags: [tag1, tag2, tag3]                # OPTIONAL: For discovery and organization
languages: [python, typescript]         # OPTIONAL: Primary languages
frameworks: [langchain, django, react]  # OPTIONAL: Key frameworks/libraries
domains: [llm, web, infrastructure]     # OPTIONAL: Problem domains
created: 2025-11-06                     # OPTIONAL: Creation date
updated: 2025-11-06                     # OPTIONAL: Last update date
authors: [author1, author2]             # OPTIONAL: Contributors
# AI Assistant-specific metadata (optional)
claude:
  loading_strategy: |                   # When to load references/ files
    Load references/patterns.md when need detailed pattern documentation.
    Assets are for copying to projects, not loading to context.
---
```

**Field Descriptions**:

- **name** (required): Lowercase-with-hyphens identifier, must match directory name
- **description** (required): Clear description including what the reference does AND when to use it (critical for AI discoverability)
- **tags** (optional): Keywords for searching and categorization
- **languages** (optional): Programming languages covered
- **frameworks** (optional): Frameworks or libraries this reference addresses
- **domains** (optional): Problem domains (e.g., llm, web, infrastructure, testing)
- **created/updated** (optional): Timestamp tracking (git provides full history)
- **authors** (optional): Contributors for attribution
- **AI-specific sections** (optional): Assistant-specific configuration (claude, copilot, cursor, etc.)

### Content Structure

After the YAML frontmatter, README.md should follow this structure:

```markdown
# [Reference Title]

## Overview

High-level introduction (2-4 paragraphs):
- What this reference provides
- When to use it
- Key characteristics or benefits
- Prerequisites or assumptions

## Quick Start [or Quick Reference]

Minimal path to first success:
- Copy these files
- Follow this structure
- Try this example

Keep this section lean (<50 lines). Goal is rapid orientation.

## Core Concepts [or Key Patterns]

Foundational knowledge needed to use this reference:
- Core abstractions with "why" explanations
- Architectural decisions with rationale
- Trade-offs and alternatives
- Design principles

Use file references, not inline code:
- "See `assets/reference_implementation/core/experts.py:40-51`"
- NOT: Large code blocks duplicating assets/

## Step-by-Step Workflow [if applicable]

Prescriptive guidance for building/implementing:
- Numbered steps (typically 5-10)
- Each step has clear outcome
- Points to relevant files in assets/ or references/
- Explains "why" at decision points

## Key Design Decisions [if applicable]

Document significant architectural choices:
- What was decided
- Why this approach over alternatives
- When to deviate
- Trade-offs

## Advanced Patterns [if applicable]

Beyond basics:
- Multi-phase workflows
- Composition strategies
- Optimization techniques
- Edge cases and solutions

## Resources [or See Also]

Pointers to:
- Related references in this repo
- Files in references/ directory
- External documentation
- Further reading
```

**Section Guidelines**:
- **Required sections**: Overview, Core Concepts (or equivalent)
- **Optional sections**: Add based on reference type (patterns catalog vs prescriptive guide vs framework reference)
- **Ordering**: Most important information first (progressive disclosure)
- **Length**: Aim for 400-700 lines for README.md; move detailed content to references/

### Writing Conventions

**Voice and Tone**:
- Use **imperative/infinitive form** (verb-first instructions): "Define task classes with domain-specific fields"
- NOT second person: ~~"You should define task classes"~~
- Use **third-person objective** when describing: "This reference provides..."
- Avoid marketing language: "powerful", "easy", "simply"

**Progressive Disclosure**:
- Essential information in README.md
- Detailed documentation in references/
- Code in assets/ (not loaded to context unless needed)

**File References**:
- Use explicit file paths with line ranges: `See assets/core/experts.py:40-51`
- Enables AI to locate and read relevant code quickly
- Reduces token usage (no inline code duplication)

**Priority Classifications**:
When documenting patterns, use priority tags to indicate importance:
- `[CRITICAL]` - Core abstractions, essential patterns, architectural foundations
- `[PREFERRED]` - Recommended approaches, stylistic improvements
- `[OBSERVED]` - Implementation details, context-dependent choices

**Code Examples**:
- Minimal inline examples (prefer file references)
- When inline code necessary, keep under 20 lines
- Always include language tags in code blocks
- Use TODO/FIXME comments for project-specific parts

**Rationale Documentation**:
- Always explain **why** for design decisions
- Document **when to use** and **when NOT to use**
- Include **trade-offs** (benefits and limitations)
- Note **alternatives** considered

## References Directory (Optional)

The `references/` directory contains detailed documentation loaded on-demand by AI assistants.

**Purpose**:
- Keep README.md lean while providing depth
- Detailed pattern catalogs
- Case studies and examples
- API documentation
- Decision records

**When to use**:
- README.md would exceed 700 lines
- Content is relevant only for specific scenarios
- Need comprehensive pattern documentation
- Maintaining decision history (ADRs)

**Organization Patterns**:

```
references/
├── patterns.md              # Comprehensive pattern catalog
├── case_studies.md          # Real-world examples and outcomes
├── decisions.md             # Architecture decision records
├── api_documentation.md     # Detailed API references
├── migration_guides.md      # Version migration instructions
└── troubleshooting.md       # Common issues and solutions
```

**File Size Considerations**:
- Target ~1500 lines maximum per file
- If larger, split by topic or concern
- AI assistants should be able to load full files into context

**Content Style**:
- More detailed than README.md
- Can include longer examples
- Comprehensive trade-off analysis
- Historical context and evolution

## Assets Directory (Optional)

The `assets/` directory contains files that will be used in implementation, not loaded into AI context.

**Purpose**:
- Reference implementations (copy-paste ready code)
- Templates (boilerplate to customize)
- Examples (instructive demonstrations)
- Supporting files (configs, schemas, diagrams)

**When to use**:
- Have reusable code abstractions
- Provide starting templates
- Include working examples
- Need supporting resources

**Organization Patterns**:

```
assets/
├── reference_implementation/     # Production-ready abstractions
│   ├── core/                     # Generic, reusable components
│   │   ├── README.md             # Minimal overview
│   │   └── *.py / *.ts / *.java
│   └── examples/                 # Complete example implementations
│       └── example_domain/
│           ├── README.md
│           └── *.py / *.ts / *.java
├── templates/                    # Boilerplate for customization
│   ├── project_template/
│   └── config_template.yaml
└── diagrams/                     # Architecture diagrams
    └── system_architecture.mermaid
```

**Portability Requirements**:

Assets should be **portable** across projects:
- No hardcoded absolute paths
- No project-specific imports (unless clearly marked as examples)
- Environment-agnostic (use TODO comments for configuration)
- Self-documenting (comprehensive docstrings)

**Code Documentation**:

Code in assets/ should be self-teaching:
- Module-level docstrings explaining purpose
- Class/function docstrings with examples
- Comments explaining "why", not just "what"
- Pattern annotations (e.g., "PATTERN DEMONSTRATED: Factory pattern")

**README Requirements**:

Each subdirectory in assets/ should have a minimal README.md:
- Purpose (1-2 sentences)
- Directory structure tree
- Key patterns demonstrated (bullets with file references)
- NO usage examples (those belong in main README.md)

**Examples**:

Keep examples:
- **Minimal but complete**: Full workflow, but TODO comments for details
- **Instructive**: Demonstrates patterns, not production complexity
- **Domain-generic**: Use placeholder domain names (avoid project-specific jargon)

## Metadata Field Usage Guide

### Required Fields

These fields must be present in every reference:

**name**: Must match directory name exactly
```yaml
name: langchain-expert-builder  # Directory: .agents/references/langchain-expert-builder/
```

**description**: Critical for AI assistant discoverability. Should include:
- What the reference provides (capabilities)
- When to use it (triggers/scenarios)
- Key characteristics (2-3 distinctive features)

Good examples:
```yaml
description: >
  Build LangChain multi-expert systems using the Expert-Task-Tool pattern.
  Use when implementing LLM workflows with structured output, multi-turn
  conversations, validation pipelines, or task-specific AI agents. Provides
  production-ready Python abstractions and complete reference implementation.
```

Bad examples:
```yaml
description: LangChain patterns  # Too vague
description: Useful LangChain utilities  # Not specific about when to use
```

### Optional but Recommended

**tags**: Keywords for discovery and filtering
```yaml
tags: [langchain, llm, structured-output, validation, multi-expert]
```

Use tags for:
- Technologies (langchain, django, react, aws)
- Patterns (factory, dependency-injection, observer)
- Use cases (testing, validation, error-handling)
- Domains (web, infrastructure, data-pipeline)

**languages**: Primary languages covered
```yaml
languages: [python, typescript]
```

**frameworks**: Key frameworks or libraries
```yaml
frameworks: [langchain, fastapi, pytest]
```

**domains**: Problem domains addressed
```yaml
domains: [llm, web-api, testing]
```

### Optional Advanced

**created/updated**: Timestamps for reference tracking
```yaml
created: 2025-11-06
updated: 2025-11-06
```

**authors**: Attribution (use handles or names)
```yaml
authors: [chris, engineering-team]
```

### AI Assistant-Specific Sections

Add assistant-specific configuration as needed:

**Claude Code**:
```yaml
claude:
  loading_strategy: |
    Always load README.md for overview.
    Load references/patterns.md when need detailed pattern documentation.
    Load references/case_studies.md when investigating real-world examples.
    Assets are copy-paste ready, not loaded to context.
  allowed_tools: [Read, Write, Edit, Bash]
```

**GitHub Copilot**:
```yaml
copilot:
  file_patterns: ["**/*.py", "**/*.ts"]
  context_hints: ["langchain", "expert", "task", "tool"]
```

**Cursor**:
```yaml
cursor:
  rules: |
    When implementing LangChain experts, follow Expert-Task-Tool pattern.
    See assets/reference_implementation/core/ for abstractions.
```

**Windsurf** (or other assistants):
```yaml
windsurf:
  context: |
    Reference implementation available in assets/.
    Patterns documented in references/patterns.md.
```

## Reference Types and Patterns

Different reference types suit different extraction goals:

### Pattern Catalog

**Structure**:
- README.md: Overview + quick reference
- references/patterns.md: Comprehensive pattern documentation
- assets/examples/: Demonstrative code

**When to use**:
- Documenting multiple distinct patterns
- Patterns are independently useful
- Goal is comprehensive coverage

**Example**: `multi-expert-llm-patterns`

### Prescriptive Guide

**Structure**:
- README.md: Overview + step-by-step workflow
- references/: Detailed decisions and trade-offs
- assets/reference_implementation/: Copy-paste ready code

**When to use**:
- Goal is to enable implementation
- Clear workflow exists
- Reusable abstractions available

**Example**: `langchain-expert-builder`

### Framework Reference

**Structure**:
- README.md: Overview + getting started + API surface
- references/: Advanced patterns, migration guides
- assets/: Full framework code

**When to use**:
- Creating reusable framework/library
- Complex abstractions with many components
- Need comprehensive documentation

**Example**: `temporal-workflow-framework`

### Standards & Conventions

**Structure**:
- README.md: Overview + core principles + decision guidance
- references/: Detailed conventions, anti-patterns
- assets/templates/: Configuration templates

**When to use**:
- Team coding standards
- Style guides
- Configuration conventions

**Example**: `python-style-guide`

## Version Control and Collaboration

### Git Workflow

References should be version controlled:

```bash
git add .agents/references/new-reference/
git commit -m "Add new-reference: [Brief description]"
git push
```

**Commit message conventions**:
- Prefix with reference name: `langchain-expert-builder: [change]`
- Use conventional commit types: `feat:`, `fix:`, `docs:`
- Examples:
  - `langchain-expert-builder: feat: add multi-tool expert pattern`
  - `aws-client-factory: fix: correct S3 bucket creation example`
  - `multi-expert-patterns: docs: clarify validation pipeline section`

### Collaboration Patterns

**Single owner**: One person maintains reference, accepts contributions
**Team ownership**: Team collectively maintains, collaborative editing
**Fork and merge**: Fork for experimentation, merge back refined versions

### Change Review

When updating references:
1. Review impact on dependent code
2. Document changes in commit message or CHANGELOG
3. Consider backward compatibility

## Token Optimization Strategies

Since AI assistants have context limits, optimize references for token efficiency:

### 1. File References Over Inline Code

**Instead of**:
```markdown
Here's the Expert dataclass:

```python
@dataclass
class Expert:
    llm: Runnable
    system_prompt_factory: Callable
    tools: ToolBundle
```
```

**Use**:
```markdown
See `assets/reference_implementation/core/experts.py:28-32` for Expert dataclass.
```

**Savings**: ~15-20 lines per example

### 2. Progressive Disclosure

- Essential info in README.md (always loaded)
- Detailed patterns in references/ (loaded on demand)
- Code in assets/ (copied, not loaded)
- Purpose: token efficiency and context window protection by structuring information in layers to allow at-need retrieval

**Result**: Main document stays <700 lines

### 3. Self-Documenting Code

Make assets/ code self-teaching via docstrings:

```python
"""
PATTERN DEMONSTRATED: Factory pattern for expert creation

This module shows how to create expert factories that encapsulate:
- LLM client configuration
- Tool binding
- Prompt factory association

KEY CONCEPTS:
- Late binding: Factory creates expert on-demand
- Configuration encapsulation: LLM config internal to factory
- Testability: Can mock factory for testing

WHEN TO USE:
- Multiple expert types with different LLM configs
- Need runtime expert creation
- Want centralized expert configuration
"""
```

**Result**: Code teaches itself, README.md just points to it

### 4. Single Source of Truth

Avoid duplication:
- Pattern described once (in patterns.md)
- README.md references patterns.md
- Code demonstrates pattern (doesn't redocument)

**Result**: ~20-30% duplication elimination

## Format Compliance and Validation

References should comply with this format. AI assistants can validate compliance:

**Required elements**:
- [ ] README.md exists with YAML frontmatter
- [ ] Frontmatter contains: name, description
- [ ] Name in frontmatter matches directory name
- [ ] Description is 1-3 sentences with "when to use"

**Recommended elements**:
- [ ] Tags provided for discoverability
- [ ] README.md is 400-700 lines (not too short, not too long)
- [ ] Uses file references instead of inline code
- [ ] Includes trade-offs and "when NOT to use"

**Optional elements**:
- [ ] references/ directory for detailed docs
- [ ] assets/ directory for code/templates
- [ ] AI assistant-specific configuration

## Examples

### Minimal Reference

```
.agents/
└── references/
    └── simple-pattern/
        └── README.md
```

README.md:
```markdown
---
name: simple-pattern
description: >
  Simple pattern for [use case]. Use when [scenario].
---

# Simple Pattern

## Overview
[2-3 paragraphs]

## Core Concepts
[Key patterns and decisions]

## Usage
[How to apply]
```

### Comprehensive Reference

```
.agents/
└── references/
    └── complex-framework/
        ├── README.md
        ├── references/
        │   ├── patterns.md
        │   ├── decisions.md
        │   └── case_studies.md
        └── assets/
            ├── reference_implementation/
            │   ├── core/
            │   └── examples/
            └── templates/
```

README.md:
```markdown
---
name: complex-framework
description: >
  Comprehensive framework for [domain]. Use when building [type of system]
  that requires [specific capabilities]. Provides reusable abstractions
  and complete reference implementation.
tags: [framework, pattern, architecture]
languages: [python, typescript]
frameworks: [fastapi, react]
claude:
  loading_strategy: |
    Load references/patterns.md for detailed pattern documentation.
    Load references/decisions.md for architecture decision context.
    Assets are copy-paste ready code.
---

# Complex Framework

## Overview
[Comprehensive introduction]

## Quick Start
[Minimal path to success]

## Core Concepts
[Foundational knowledge]

## Step-by-Step Workflow
[Prescriptive guidance]

## Key Design Decisions
[Rationale and trade-offs]

## Advanced Patterns
[Beyond basics]

## Resources
[Pointers to references/ and assets/]
```

## Format Philosophy

This format embodies key principles:

**AI-First, Human-Friendly**: Optimized for AI consumption (structured, semantic, progressive disclosure) while remaining readable for humans.

**Progressive Disclosure**: Essential information in README.md, details in references/, code in assets/. Load only what's needed.

**Portable**: Core format works across AI assistants. Assistant-specific metadata is optional and isolated.

**Pragmatic**: Format should serve the content, not constrain it. Adapt sections as needed for reference type.

**Evolvable**: This format will evolve based on real usage. When changes are needed, document them at that time rather than speculatively planning migrations. Git provides full version history.

**Token-Conscious**: File references, minimal duplication, self-documenting code. Respect context limits.

**Discoverable**: Rich metadata, clear descriptions, consistent structure enable AI assistants to find and use references effectively.

---

**This is a living document**. As references are created and used, this format will evolve. Feedback and improvements welcome.
