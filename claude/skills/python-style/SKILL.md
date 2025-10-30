---
name: python-style
description: Comprehensive Python coding style guidelines for Chris's projects. This skill should be used when writing, reviewing, refactoring, or discussing Python code. Includes patterns for code organization, type system, documentation, error handling, testing, code style, design patterns, data handling, async patterns, and API design. Trigger when working with Python files (.py), discussing Python architecture, or implementing Python features.
---

# Python Style Guide

## Overview

This skill provides comprehensive Python coding style guidelines extracted from Chris's production codebases. The patterns represent preferences and observed practices from real-world projects, emphasizing engineering judgment over rigid rules.

**Core philosophy:** Favor readability, type safety, explicit behavior, and comprehensive testing.

## Loading Strategy

### Always Load

Read `references/core.md` for all Python work. This contains:
- Code Organization & Architecture
- Type System & Annotations
- Documentation Philosophy
- Error Handling & Robustness
- Code Style & Idioms
- Dependencies & Tooling
- Design Patterns & Principles
- Data Handling
- API Design
- Meta Patterns
- Guidance on when to deviate from these patterns

### Conditional Loading

Load additional references based on task context:

**When writing, reviewing, or discussing tests:**
- Read `references/testing.md`
- Covers test framework preferences, naming conventions, mocking strategies, assertion style, test organization, and pytest patterns

**When writing, reviewing, or discussing async/await code:**
- Read `references/async.md`
- Covers async/await usage patterns, async wrapper patterns, and concurrency approaches

## Priority Level System

All patterns are marked with priority indicators:

- **CRITICAL** - Core principles to always follow (e.g., test naming conventions, type hints on public APIs, assertion style)
- **PREFERRED** - Default choices unless project context suggests otherwise (e.g., dataclasses over dicts, pytest over unittest, f-strings)
- **OBSERVED** - Context-dependent patterns from analyzed code; apply when relevant (e.g., domain-specific module naming like `{function}_interactions/`)

### Applying Priority Levels

- **CRITICAL**: Always follow these patterns
- **PREFERRED**: Follow unless existing project conventions conflict; when conflicts detected, ask user for guidance
- **OBSERVED**: Apply when contextually appropriate and doesn't conflict with existing project style

## Handling Project Conflicts

When working in a codebase with established patterns that differ from this guide:

1. **Check priority level** of the conflicting pattern
2. **CRITICAL patterns** - Always apply, but can suggest improvements with clear rationale if project conventions are problematic
3. **PREFERRED patterns** - Ask user whether to follow project conventions or apply the style guide pattern
4. **OBSERVED patterns** - Defer to project conventions

## Philosophy and Context

These patterns emerged from production code solving real problems in domains including:
- LLM/AI agent systems (LangChain, prompt engineering)
- AWS infrastructure automation (boto3, CDK)
- Django web applications
- CLI tools (Click)

Apply patterns when relevant, but don't force-fit them into unrelated contexts. When strong engineering reasons exist to deviate (performance, security, maintainability, new language features), propose alternatives with clear rationale.

See the "When to Deviate From This Guide" section in `references/core.md` for detailed guidance on valid deviations.
