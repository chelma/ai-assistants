---
name: tech-writing
description: This skill should be used when writing technical documentation including README files, GitHub issues, pull requests, and technical proposals/RFCs. Apply this skill to ensure consistent writing style (third-person objective, no marketing language), structure (context before instructions), code formatting (complete examples, no shell prompts), and visual creation strategy (generate draft Mermaid/PlantUML diagrams for review). Emphasizes pragmatic completeness - include what's needed to understand and use effectively, no more and no less.
---

# Technical Writing

## Overview

This skill encapsulates preferences and patterns for technical writing across various contexts. Apply these guidelines to produce documentation that is clear, concise, and follows established conventions for structure and style.

## Supported Document Types

This skill provides specialized guidance for the following document types. Each has detailed preferences stored in the `references/` directory that will be loaded when working on that specific type:

### README Files

When creating or updating README files, consult `references/readme-guide.md` for detailed preferences on:

**Core Principles:**
- Context before instructions (what/why before how)
- Third-person objective tone, no marketing language
- Pragmatic completeness (include what's needed, omit the rest)

**Writing Standards:**
- Section naming conventions (descriptive nouns, gerunds for actions)
- Code formatting (no shell prompts, complete copy-pastable examples, language tags)
- Inline code usage (commands, paths, service names, technical identifiers)

**Visual Elements:**
- Architecture diagrams: Generate draft Mermaid/PlantUML with detailed specification for human review
- Screenshots: Provide placeholder specifications for human to capture
- Never include: badges, emoji, decorative images, annotated screenshots

**Project-Specific Guidance:**
- Infrastructure/CLI tools (emphasize architecture, constraints, troubleshooting)
- Web applications (workflow focus, screenshots of key stages)
- Developer tools/libraries (API examples, multiple input/output samples)

To apply README preferences, read the guide and follow the line-item preferences defined there.

### GitHub Issues

When creating or updating GitHub issues, tickets, or similar tracking items, consult `references/issue-guide.md` for detailed preferences on:

**Title Conventions:**
- Title tags for categorization: `[TASK]`, `[BUG]`
- Concise descriptions (under 80 characters total)
- Use backticks for technical terms

**Standard Issue Structure:**
- **Situation:** Context explaining current state and why work is needed
- **Request:** Clear statement of what should be accomplished
- **Acceptance Criteria:** Specific, testable conditions for completion


**Writing Standards:**
- Third-person objective tone, imperative for requests
- Substantial context enabling action without synchronous communication
- Specific, independently verifiable acceptance criteria
- Include code references, error logs, and technical details

**Working with Templates:**
- Apply these preferences within any repository-specific template constraints

To apply issue writing preferences, read the guide and follow the patterns defined there. The guide documents evolution from 2023-2025, with recent patterns weighted more heavily.

### Pull Requests (Coming Soon)

Guidance for writing comprehensive PR descriptions that facilitate effective code review.

### Technical Proposals/RFCs (Coming Soon)

Guidance for structuring technical proposals and architectural decision documents.

## Usage Pattern

When working on any supported document type:

1. Identify the document type being created or edited
2. Read the corresponding guide from `references/`
3. Apply the specific preferences and patterns defined in that guide
4. Maintain consistency with examples and templates when provided

## Resources

### references/

This skill uses the `references/` directory to store detailed writing guides for each document type. These files are loaded into context when working on specific document types to inform writing decisions.

Current references:
- `readme-guide.md` - Line-item preferences for README file creation
- `issue-guide.md` - Line-item preferences for GitHub issue/ticket creation

Future references will include guides for pull requests and technical proposals.

### assets/

The `assets/` directory can be used to store document templates, example files, or other resources that should be used in the output Claude produces. This directory is currently empty but available for future use.
