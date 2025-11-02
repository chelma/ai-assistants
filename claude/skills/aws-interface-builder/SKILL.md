---
name: aws-interface-builder
description: Build production-ready Python interfaces for AWS SDK (boto3) using the Factory + Dependency Injection pattern. This skill should be used when implementing testable AWS integrations, creating service wrappers for boto3 clients, or structuring Python applications that need multi-account AWS access. Provides reference implementation demonstrating 10 CRITICAL patterns for implementation and testing, with complete S3 wrapper examples.
---

# AWS Interface Builder

## Overview

Build structured, testable Python interfaces to AWS services using the **Factory + Dependency Injection** pattern. This skill provides a complete architectural pattern extracted from production code that:

- **Centralizes credential management**: Single factory class handles profiles, regions, instance credentials, and cross-account role assumption
- **Enables comprehensive testing**: Mock the provider instead of patching boto3, making tests explicit and understandable
- **Provides domain-focused interfaces**: Service wrappers return dataclasses and enums, not raw boto3 dictionaries
- **Handles errors cleanly**: Maps boto3 ClientError to domain exceptions with clear semantics

**Core Architecture:**
```
AwsClientProvider (Factory)
    ├─> Manages: credentials, sessions, regions, role assumption
    └─> Injected into: Service wrapper functions
            └─> Return: Domain objects (dataclasses, enums, exceptions)
```

**Key Benefits:**
- Single point of credential configuration
- Testable without real AWS calls
- Business logic separated from AWS SDK details
- Type-safe domain objects instead of raw responses

**When to use this skill:**
- Implementing AWS SDK interactions in Python applications
- Creating multi-service AWS integrations with centralized credential management
- Building testable interfaces to S3, EC2, Lambda, or other AWS services
- Migrating from scattered boto3 calls to structured service wrappers

## Quick Start Workflow

### Step 1: Copy the Foundation

Copy `assets/reference_implementation/core/` to the target project. These files provide the factory pattern foundation:

```
your_project/
└── core/
    ├── aws_client_provider.py    # Factory class for boto3 clients
    └── aws_environment.py         # Optional: Account/region context dataclass
```

**Key structure in aws_client_provider.py:**
- `__init__`: Store configuration (profile, region, compute mode, role ARN)
- `_get_session()`: Create boto3 session with credential hierarchy
- `get_<service>()`: Getter methods for each AWS service (get_s3, get_ec2, etc.)

### Step 2: Study the Reference Implementation

Review `assets/reference_implementation/aws_interactions/s3_interactions.py` and `tests/test_s3_interactions.py` to understand the complete pattern.

**What the reference implementation demonstrates:**
- **Pattern 1**: Factory class (AwsClientProvider) with getter methods
- **Pattern 2**: Dependency injection (provider parameter in all wrappers)
- **Pattern 3**: Service wrapper structure (3-step flow: get client → call AWS → transform response)
- **Pattern 4**: Error handling (map ClientError to domain exceptions)
- **Pattern 5**: Data transfer objects (S3Object dataclass)
- **Pattern 6**: Enum-based status (BucketStatus with 3 states)
- **Pattern 7-10**: Complete test suite with mocking, error scenarios, pagination

### Step 3: Build Service Wrappers

Follow the seven-step wrapper creation process (see "Building Your First Wrapper" section below). Use `s3_interactions.py` as a template: copy the structure, replace S3-specific logic with your target service.

## Building Your First Wrapper

### Step 1: Create Service Module

Create `aws_interactions/<service>_interactions.py` for each AWS service.

**File organization principle**: One module per AWS service (not per business domain). For example:
- `s3_interactions.py` - All S3 operations
- `ec2_interactions.py` - All EC2 operations
- `lambda_interactions.py` - All Lambda operations

### Step 2: Define Domain Exceptions

Create custom exceptions that represent business errors, not AWS errors.

**Pattern** (see `s3_interactions.py:20-30`):
```python
class BucketDoesNotExist(Exception):
    """Raised when S3 bucket does not exist."""
    pass

class BucketNameNotAvailable(Exception):
    """Raised when bucket name is already taken by another account."""
    pass
```

**Why custom exceptions?** Using specific exceptions makes error handling clearer in catch blocks and produces obvious stack traces. When code catches `BucketDoesNotExist`, it's immediately clear what business condition occurred, whereas catching generic `ClientError` scatters AWS-specific logic throughout the codebase.

### Step 3: Define Domain Enums

Use Python `Enum` for status/outcome classification instead of strings or booleans.

**Pattern** (see `s3_interactions.py:33-39`):
```python
from enum import Enum

class BucketStatus(Enum):
    """S3 bucket existence and access status."""
    EXISTS_HAVE_ACCESS = "exists_have_access"
    EXISTS_NO_ACCESS = "exists_no_access"
    DOES_NOT_EXIST = "does_not_exist"
```

**Why enums over booleans?** Enums naturally accommodate complex state spaces (more than 2 states), provide IDE autocomplete, and catch typos at development time. Unlike string constants, enums are type-safe.

### Step 4: Define Data Transfer Objects

Use Python `@dataclass` for structured return values instead of raw boto3 dicts.

**Pattern** (see `s3_interactions.py:42-49`):
```python
from dataclasses import dataclass

@dataclass
class S3Object:
    """Represents an object in S3."""
    key: str
    size_bytes: int
    last_modified: str
```

**Why convert to dataclasses?** Provides type safety, enables customization, and creates an insulating layer between your codebase and boto3 response structure changes. Field names are domain-focused (may differ from boto3 keys).

### Step 5: Write Wrapper Functions

Create module-level functions (not class methods) that follow the 3-step pattern.

**Three-step wrapper pattern** (see `s3_interactions.py:53-96`):
```python
def wrapper_function(domain_param: str, aws_provider: AwsClientProvider) -> DomainType:
    """Business-focused docstring."""

    # Step 1: Get boto3 client from provider
    client = aws_provider.get_s3()

    # Step 2: Call AWS SDK
    try:
        response = client.some_operation(Param=domain_param)
        return DomainEnum.SUCCESS

    # Step 3: Handle errors & map to domain exceptions
    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        if error_code == "404":
            raise DomainException("Not found") from e
        else:
            raise  # Re-raise unexpected errors
```

**Key design decisions:**
- Functions are **stateless** (no instance state needed)
- Provider is **always a parameter** (never global or module-level)
- Returns are **domain objects** (DTOs, enums, exceptions)
- Unexpected errors are **re-raised** (not swallowed)

**Why module-level functions instead of classes?** Avoids ceremony when there's no state to manage. Service wrappers don't maintain instance state between calls, so functions communicate this statelessness clearly.

### Step 6: Handle Pagination

Use boto3 paginators when available, or implement manual NextToken loops.

**boto3 paginator pattern** (see `s3_interactions.py:202-243`):
```python
def list_bucket_objects(
    bucket_name: str, aws_provider: AwsClientProvider, prefix: str = ""
) -> list[S3Object]:
    """List all objects in S3 bucket with optional prefix."""
    s3_client = aws_provider.get_s3()

    try:
        # Use boto3 paginator
        paginator = s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

        objects = []
        for page in pages:
            for obj in page.get("Contents", []):
                # Transform boto3 dict to dataclass
                objects.append(
                    S3Object(
                        key=obj["Key"],
                        size_bytes=obj["Size"],
                        last_modified=str(obj["LastModified"]),
                    )
                )

        return objects
    except ClientError as e:
        # Handle errors...
```

**For services without paginators**, see `references/patterns_implementation.md` Pattern 6 for manual NextToken loop pattern.

### Step 7: Write Tests

Create `tests/test_<service>_interactions.py` with 1:1 mapping to implementation file.

**Test structure** (see `tests/test_s3_interactions.py`):

**1. Mock the provider** (Pattern 7):
```python
def test_wrapper_function():
    # Arrange: Create mock boto3 client
    mock_s3_client = mock.Mock()
    mock_s3_client.some_operation.return_value = {"Result": "data"}

    # Arrange: Create mock provider
    mock_provider = mock.Mock()
    mock_provider.get_s3.return_value = mock_s3_client

    # Act: Call wrapper with mock provider
    result = wrapper_function("param", mock_provider)

    # Assert: Verify calls and result
    mock_s3_client.some_operation.assert_called_once_with(Expected="args")
    assert result == expected_value
```

**2. Test error scenarios** (Pattern 9 - see `test_s3_interactions.py:37-73`):
- Test each error code wrapper handles (404, 403, etc.)
- Test unexpected errors are re-raised (not swallowed)
- Test domain exception mapping (ClientError → custom exceptions)

**3. Test pagination** (Pattern 10 - see `test_s3_interactions.py:143-185`):
- Mock paginator with multiple pages
- Verify results from all pages accumulated
- Verify paginator called with correct parameters

**Why mock provider instead of patching boto3?** Makes tests more obvious and understandable. Creating mock objects and passing them explicitly is clearer than using patch decorators where you have to understand import-time vs runtime behavior.

## Key Design Decisions

### Factory Pattern for Client Creation

**Decision**: Use `AwsClientProvider` factory class with explicit getter methods (`get_s3()`, `get_ec2()`) instead of generic `get_client(service_name: str)`.

**Rationale**: Explicit methods are more obvious, easier to mock in tests, and allow service-specific customization without conditional logic. The lightweight nature of these methods (rarely change) means minimal maintenance burden.

**See**: `assets/reference_implementation/core/aws_client_provider.py` for complete implementation

### Session-Per-Call vs Caching

**Decision**: Create new boto3 session on each `get_<service>()` call instead of caching sessions.

**Rationale**: Applications often need clients targeting different regions and credential sets within the same lifecycle. Creating fresh sessions is simpler than implementing cache logic to handle multiple region/credential combinations. Session overhead is negligible compared to cache complexity.

### Dependency Injection for Testability

**Decision**: Pass provider as parameter to all wrapper functions (never global, never module-level).

**Rationale**: Makes mocking trivial during tests - just create mock provider and pass it in. Avoids complexity of patching module-level globals. Provides flexibility to use different providers for different contexts (different AWS accounts, regions) without global state management.

### Domain Objects Over Raw Responses

**Decision**: Return dataclasses, enums, and custom exceptions instead of boto3 dictionaries and ClientError.

**Rationale**: Creates insulating layer serving application needs rather than AWS API design. Provides type safety (IDE autocomplete, compile-time checking), customization (field names that make sense in your domain), and resilience to boto3 changes. Makes calling code more readable.

## Core Patterns Overview

This pattern consists of **10 CRITICAL patterns**:

**Implementation Patterns (1-6):**
1. **Factory Pattern** - AwsClientProvider centralizes client creation
2. **Dependency Injection** - Provider passed as parameter
3. **Service Wrapper Structure** - 3-step flow (get client → call AWS → transform)
4. **Error Handling** - Map ClientError to domain exceptions
5. **Data Transfer Objects** - Use dataclasses for responses
6. **Enum-Based Status** - Use Enum for multi-state outcomes

**Testing Patterns (7-10):**
7. **Mocking AwsClientProvider** - Mock provider returns mock clients
8. **Mocking boto3 Clients** - Control client behavior with return_value/side_effect
9. **Error Scenario Testing** - Test error codes, unexpected errors, domain exceptions
10. **Pagination Testing** - Test multi-page accumulation

**For detailed explanations of each pattern**, see:
- `references/patterns_implementation.md` - 11 implementation patterns with code examples
- `references/patterns_testing.md` - 11 testing patterns with test examples

## Adoption Workflow

### Phase 1: Setup Factory

1. Copy `assets/reference_implementation/core/` to project
2. Review `aws_client_provider.py` credential hierarchy (instance profile → named profile → role assumption)
3. Add `get_<service>()` methods for each AWS service needed

### Phase 2: Create First Wrapper

1. Choose one AWS service to start with (e.g., S3, EC2, Lambda)
2. Create `aws_interactions/<service>_interactions.py`
3. Follow Steps 2-6 from "Building Your First Wrapper" section
4. Use `assets/reference_implementation/aws_interactions/s3_interactions.py` as template

### Phase 3: Write Tests

1. Create `tests/test_<service>_interactions.py`
2. Follow Step 7 from "Building Your First Wrapper" section
3. Use `assets/reference_implementation/tests/test_s3_interactions.py` as template
4. Test happy path, error scenarios, and pagination (if applicable)

### Phase 4: Integrate into Application

1. Create provider instance once: `provider = AwsClientProvider(aws_profile="prod", aws_region="us-east-1")`
2. Pass provider to wrapper functions: `result = wrapper_func(domain_arg, provider)`
3. Handle domain exceptions in calling code (not ClientError)

### Phase 5: Expand to Other Services

Repeat Phases 2-4 for each additional AWS service needed.

## Design Principles

### Separation of Concerns

**Factory layer** (AwsClientProvider): Credential/session management

**Wrapper layer**: AWS SDK calls + response transformation

**Application layer**: Business logic using domain objects

**Why separate?** Makes each layer easier to understand, test, and modify independently. Enables swapping implementations (LocalStack for testing) or upgrading boto3 without touching business logic.

### Domain-Focused Interfaces

Return domain objects that serve application needs, not AWS API design.

**Benefits:**
- Type safety (IDE autocomplete, compile-time checking)
- Customization (field names that make sense in your domain)
- Resilience to boto3 changes (response structures don't ripple through codebase)
- Readability (`BucketStatus.EXISTS_NO_ACCESS` vs parsing `{"ResponseMetadata": {"HTTPStatusCode": 403}}`)

### Explicit Over Implicit

Use explicit patterns that are obvious to understand:
- Getter methods (`get_s3()`) over generic method with string parameter
- Module-level functions over classes without state
- Mock objects passed as parameters over decorator-based patching
- Custom exceptions over inspecting error codes in catch blocks

## Resources

### references/patterns_implementation.md

Comprehensive catalog of **11 implementation patterns** extracted from production code:

**CRITICAL patterns (1-6)**: Architectural foundation - factory, dependency injection, wrapper structure, error handling, DTOs, enums

**PREFERRED patterns (7-9)**: Session management, dataclass patterns, pagination

**OBSERVED patterns (10-11)**: Abstract base classes, file organization

Load this when need detailed understanding of specific patterns or want to see original source examples.

### references/patterns_testing.md

Comprehensive catalog of **11 testing patterns** for AWS service wrappers:

**CRITICAL patterns (13-14, 17-18)**: Mocking provider, mocking clients, error scenarios, pagination

**PREFERRED patterns (19-21)**: Patching strategies, boto3 resource testing

**OBSERVED patterns (12, 15-16)**: Test naming, AAA structure, success path testing

Load this when writing tests or need guidance on specific testing scenarios.

### assets/reference_implementation/

Complete, copy-paste ready Python implementation demonstrating all 10 CRITICAL patterns:

**core/** - Factory pattern foundation (copy to every project):
- `aws_client_provider.py` - Factory class with credential hierarchy, getter methods
- `aws_environment.py` - Optional context dataclass for account/region

**aws_interactions/** - Complete S3 wrapper demonstrating Patterns 2-6:
- `s3_interactions.py` - Domain exceptions, enums, DTOs, wrapper functions with error handling and pagination

**tests/** - Complete test suite demonstrating Patterns 7-10:
- `test_s3_interactions.py` - Provider mocking, client mocking, error scenario tests, pagination tests

**README.md** - Pattern mapping showing which lines demonstrate which patterns

Use the reference implementation as a starting template: copy the structure, replace S3-specific logic with your target AWS service.
