# FetchAll + FetchOne Endpoint Patterns - Index

**Scope**: Patterns for creating read-only endpoints (FetchAll, FetchOne) in Scriptdash and Rails Engines
**Source**: PRs #48986 (Scriptdash), #535 (Actions Engine), Actions Engine codebase analysis
**Philosophy**: Prescriptive guidance based on current best practices
**Last Updated**: 2025-11-20

---

## Pattern Documents

This reference is split into focused documents for readability:

### 1. [Proto Patterns](proto_patterns.md) (~600 lines)
**Layer 1: Proto System**
- Proto-First Design
- Service V2.0 Annotation
- Type Definitions & Reuse
- Request/Response Naming
- Standard Response Structure
- FetchAll/FetchOne Request Patterns
- Package Naming
- Field Annotations

### 2. [Implementation Patterns](implementation_patterns.md) (~500 lines)
**Layer 3: Engine Endpoint Implementation**
- Endpoint Class Structure
- FetchAll Implementations (Simple, Adapter, Optional IDs)
- FetchOne Implementation
- Adapter Pattern
- Database Query Optimization
- Scopes and Ordering
- Post-Processing

### 3. [Scriptdash Patterns](scriptdash_patterns.md) (~530 lines)
**Layer 6-7: Core API Integration & Permissions**
- Core API Module Structure
- add_api Pattern
- Endpoint Configuration (Local vs RPC)
- Dotted Accessor Pattern
- Permissions (Ability Classes)
- Authorization Checks
- Delegation Pattern

### 4. [Controller & Routes Patterns](controller_routes_patterns.md) (~450 lines)
**Layer 4-5: HTTP Integration**
- Controller Structure
- Generated Controller Mixins
- Endpoint Accessor Pattern
- Routes Extension
- HTTP Verb Mapping
- URL Patterns

### 5. [Testing Patterns](testing_patterns.md) (~570 lines)
**Layer 8: Testing**
- Engine Request Specs (:rpc_client_requests)
- Scriptdash Controller Specs
- Mocking Patterns
- Factory Usage
- Permission Testing

### 6. [Troubleshooting Guide](troubleshooting.md) (~570 lines)
**Common Errors & Fixes**
- Proto generation issues
- Sorbet type errors
- RPC vs Local configuration
- N+1 query problems
- Permission errors
- Common gotchas
- Quick fix checklist

---

## Quick Start

**New to this codebase?** Start here:

1. Read Proto Patterns - Understand the foundation
2. Read Implementation Patterns - Learn how to write endpoints
3. Reference others as needed

**Creating a FetchAll endpoint?** Follow this order:

1. Proto Patterns → Define your .proto files
2. Implementation Patterns → Write your endpoint.rb
3. Controller & Routes → Wire up HTTP
4. Testing Patterns → Write specs
5. Scriptdash Patterns (if frontend-facing) → Add permissions & Core API

**Creating a FetchOne endpoint?** Same as above, but simpler.

---

## Pattern Priority Legend

- **[CRITICAL]** - Must follow. Core abstractions that define the architecture.
- **[PREFERRED]** - Strong recommendations. Best practices that improve quality.
- **[OBSERVED]** - Common conventions. Nice-to-have consistency.

---

## Iteration Progress

- ✅ Iteration 1: Proto Patterns (9 patterns)
- ✅ Iteration 2: Implementation Patterns (8 patterns)
- ✅ Iteration 3: Controller/Routes/Testing (13 patterns)
- ✅ Iteration 4: Scriptdash Patterns (7 patterns)
- ✅ Iteration 5: Validation (integrated with iterations 1-4)
- ✅ Iteration 6: Troubleshooting Guide (complete)

**Total**: 37 patterns across 6 comprehensive documents
**Ready for**: Human priority review → Claude Skill creation
