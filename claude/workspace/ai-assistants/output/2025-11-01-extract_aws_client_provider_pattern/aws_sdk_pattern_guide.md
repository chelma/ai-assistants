# AWS Client Provider Pattern Guide

**Pattern**: Factory + Dependency Injection for AWS SDK (boto3) interactions
**Source**: Extracted from [aws-aio](https://github.com/arkime/aws-aio) repository
**Use Case**: Python applications requiring structured, testable AWS SDK interactions across multiple services

---

## Overview

The AWS Client Provider pattern centralizes boto3 client creation through a **factory class** (`AwsClientProvider`) that manages credentials, sessions, regions, and cross-account role assumption. Service-specific logic lives in **wrapper functions** that accept the provider via **dependency injection**, enabling clean separation of concerns and comprehensive testability.

### Core Architecture

```
┌─────────────────────────┐
│   AwsClientProvider     │  Factory for boto3 clients
│   (Factory)             │  - Credential management
└───────────┬─────────────┘  - Session management
            │                - Cross-account support
            │ injected into
            ▼
┌─────────────────────────┐
│  Service Wrappers       │  Business logic + boto3 calls
│  (s3_interactions.py)   │  - Accept provider parameter
│  (ec2_interactions.py)  │  - Get specific boto3 client
└─────────────────────────┘  - Return domain objects
```

**Key Benefits**:
- ✅ Single point of credential/session configuration
- ✅ Testable without real AWS calls (mock the provider)
- ✅ Business logic separated from AWS SDK details
- ✅ Type-safe domain objects instead of raw boto3 responses

**Why use a factory pattern?** The factory pattern centralizes the moderately complex behavior of setting up credentials for each use-case: local development (named profiles), EC2/Lambda/Fargate (instance profile credentials), cross-account access (role assumption), and different regions. Without centralization, this credential logic would be duplicated across every service wrapper, making it brittle and hard to maintain as authentication requirements evolve.

---

## Quick Start

### 1. Create the Factory

**See:** `reference_implementation/core/aws_client_provider.py` for complete implementation

**Key structure:**
- `__init__`: Store configuration (profile, region, compute mode, role ARN)
- `_get_session()`: Create boto3 session with credential logic (lines 46-83)
- `get_<service>()`: Getter methods for each AWS service (lines 85-100)

**Pattern:**
```python
class AwsClientProvider:
    def _get_session(self) -> boto3.Session:
        # Handle EC2 instance profile OR named profile OR role assumption

    def get_s3(self):
        return self._get_session().client("s3")
```

**Why create a new session per call?** Session overhead is light, and applications often need to create clients targeting different regions and credential sets within the same lifecycle. Creating a fresh session each time is simpler than implementing caching logic to handle multiple region/credential combinations. The slight performance cost is negligible compared to the complexity of managing a session cache.

### 2. Create Service Wrappers

**See:** `reference_implementation/aws_interactions/s3_interactions.py` for complete S3 wrapper implementation

**File structure:**
1. **Import dependencies** (lines 1-17)
2. **Define domain exceptions** (lines 20-30): `BucketDoesNotExist`, `BucketNameNotAvailable`
3. **Define domain enums** (lines 33-39): `BucketStatus` with three states
4. **Define domain DTOs** (lines 42-49): `S3Object` dataclass
5. **Write wrapper functions** (lines 52+): Accept `aws_provider`, return domain objects

**Pattern:**
```python
def wrapper_function(domain_param: str, aws_provider: AwsClientProvider) -> DomainType:
    """Business-focused docstring."""
    # 1. Get boto3 client from provider
    client = aws_provider.get_s3()

    # 2. Call AWS SDK
    try:
        response = client.some_operation(Param=domain_param)
        return DomainEnum.SUCCESS

    # 3. Handle errors & map to domain exceptions
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            raise DomainException("Not found") from e
        else:
            raise  # Re-raise unexpected errors
```

**Why wrap boto3 ClientError in domain exceptions?** Using very specific custom exceptions makes error handling clearer in catch blocks and produces more obvious stack traces. When calling code catches `BucketDoesNotExist`, it's immediately clear what went wrong and what business condition occurred, whereas catching generic `ClientError` and inspecting error codes scatters AWS-specific logic throughout the codebase. This approach aligns with the python-style guide's preference for explicit, domain-focused error handling.

**Why return enums instead of raw boto3 dictionaries?** Wrapping states from external libraries in enums we control reframes them in our application's context, ensuring the interface solves the problems our code has rather than the problems the library authors envisioned. Enums provide type safety, IDE autocomplete, and make invalid states unrepresentable. This insulates calling code from boto3 response structure changes.

### 3. Use in Application Code

```python
# app.py or command handler
from core.aws_client_provider import AwsClientProvider
from aws_interactions import s3_interactions

def main():
    # Create provider once, inject everywhere
    aws_provider = AwsClientProvider(
        aws_profile="prod",
        aws_region="us-east-1"
    )

    # Call service wrappers with provider
    status = s3_interactions.get_bucket_status("my-bucket", aws_provider)

    if status == s3_interactions.BucketStatus.DOES_NOT_EXIST:
        s3_interactions.create_bucket("my-bucket", aws_provider)
```

### 4. Test Without AWS

**See:** `reference_implementation/tests/test_s3_interactions.py` for complete test suite demonstrating all testing patterns

**Pattern:**
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

**Why mock the provider instead of patching boto3?** This is a style preference that makes tests more obvious and understandable. Creating a mock object and passing it into methods under test is more explicit than patching underlying libraries with decorators. You can see exactly what behavior is being controlled without having to trace through patch decorators and understand import-time vs runtime behavior.

---

## Core Patterns (CRITICAL)

These 10 patterns form the architectural foundation. Understanding these is essential for adopting this pattern effectively.

### Pattern 1: Factory Pattern (AwsClientProvider)

**What**: Centralized factory class that creates boto3 clients on-demand.

**See**: `reference_implementation/core/aws_client_provider.py:9-101` for complete implementation

**Key Design Decisions**:
- Getter methods (`get_s3()`, `get_ec2()`, etc.) create clients on-demand (lines 85-100)
- Private `_get_session()` method centralizes session/credential logic (lines 46-83)
- Session creation happens per-call (not cached)

**Why use getter methods instead of `get_client(service_name: str)`?** Having separate methods (`get_s3()`, `get_ec2()`, etc.) is more explicit and makes mocking easier in tests. The lightweight nature of these methods (they'll practically never change) means there's minimal maintenance burden, and the explicit approach allows customizing setup for services requiring oddball configurations without complicating a generic method with conditional logic.

**Reference**: See `references/patterns_implementation.md` Pattern 1 for full details.

---

### Pattern 2: Dependency Injection

**What**: Service wrapper functions accept `AwsClientProvider` as a parameter.

**See**: `reference_implementation/aws_interactions/s3_interactions.py` - all functions demonstrate this pattern

**Key Design Decisions**:
- Provider is **always** a function parameter (never global, never imported module-level)
- Provider parameter typically last in signature (after domain parameters)
- Functions request specific client via `aws_provider.get_<service>()`

**Example**: See `s3_interactions.py:53-54` (function signature), line 74 (getting client)

**Why pass provider as parameter instead of using a global?** Passing the provider as a parameter makes mocking trivial during unit tests - you just create a mock provider and pass it in. This avoids the complexity of patching module-level globals and makes test setup explicit. It also provides flexibility to use different providers for different contexts (different AWS accounts, regions, or credential sets) without global state management.

**Reference**: See `references/patterns_implementation.md` Pattern 2 for full details.

---

### Pattern 3: Service Wrapper Structure

**What**: Consistent structure for functions that wrap boto3 calls.

**See**: `reference_implementation/aws_interactions/s3_interactions.py:53-96` (get_bucket_status), lines 99-120 (create_bucket), lines 140-173 (list_bucket_objects)

**Three-step pattern**:
1. Get boto3 client from provider
2. Make AWS SDK call(s)
3. Transform response to domain object (or handle errors)

**Key Design Decisions**:
- Functions are **module-level** (not class methods)
- Functions are **stateless** (no instance state)
- Returns are **domain objects** (DTOs, enums), not raw boto3 dicts

**Why use module-level functions instead of classes?** This is a style preference rooted in the python-style guide's philosophy: avoid classes unless you specifically need to organize both inter-related state and behavior into a type. Service wrappers are stateless - they don't maintain instance state between calls. Module-level functions communicate this statelessness clearly and avoid the ceremony of class definitions when they add no value. For state management, use dataclasses; for behavior, use functions.

**Reference**: See `references/patterns_implementation.md` Pattern 4 for full details.

---

### Pattern 4: Error Handling & Custom Exceptions

**What**: Map boto3 `ClientError` to domain-specific exceptions.

**See**:
- Exception definitions: `reference_implementation/aws_interactions/s3_interactions.py:20-30`
- Error handling examples: Lines 82-95 (get_bucket_status), lines 112-119 (create_bucket)

**Key Design Decisions**:
- Inspect `error_code` from `e.response["Error"]["Code"]` (line 84)
- Raise **domain exceptions** for expected AWS errors (lines 115-119)
- **Re-raise ClientError** for unexpected errors (line 95) - don't swallow
- Use `raise ... from e` to preserve stack trace (line 119)

**Why wrap in custom exceptions instead of propagating ClientError?** This goes back to the general philosophy of exception handling explained in the python-style guide: very specific custom exceptions make error handling clearer in catch blocks and produce more obvious stack traces. When production code catches `BucketDoesNotExist`, developers immediately understand what business condition occurred without having to inspect AWS error codes. This approach centralizes AWS-specific error handling logic in wrappers rather than scattering it across calling code.

**Reference**: See `references/patterns_implementation.md` Pattern 5 for full details.

---

### Pattern 5: Data Transfer Objects (Dataclasses)

**What**: Use Python `@dataclass` for structured return values instead of raw boto3 dicts.

**See**:
- DTO definition: `reference_implementation/aws_interactions/s3_interactions.py:42-49` (S3Object)
- Usage: Lines 151-159 (transforming boto3 response to dataclass)

**Key Design Decisions**:
- Use `@dataclass` decorator (not plain classes or TypedDict)
- Field names are **domain-focused** (may differ from boto3 response keys)
- Include only fields needed by calling code (not entire boto3 response)

**Example transformation** (lines 151-159): `boto3 dict → S3Object(key=..., size_bytes=..., last_modified=...)`

**Why convert to dataclasses instead of returning raw dictionaries?** Converting boto3 responses to dataclasses provides type safety, enables customization, and creates an insulating layer between your codebase and third-party library changes. This is the usual reason you create an intermediate layer: boto3 response structures serve AWS's needs, while dataclasses serve your application's needs. The type hints enable IDE autocomplete and catch errors at development time rather than runtime. It also documents exactly which fields your code actually uses rather than exposing the entire boto3 response surface area.

**Reference**: See `references/patterns_implementation.md` Pattern 7 for full details.

---

### Pattern 6: Enum-Based Status Classification

**What**: Use Python `Enum` for status/outcome classification instead of strings or booleans.

**See**:
- Enum definition: `reference_implementation/aws_interactions/s3_interactions.py:33-39` (BucketStatus)
- Usage: Lines 80, 87, 89 (returning enum values based on AWS error codes)

**Key Design Decisions**:
- Enum values are **lowercase with underscores** (snake_case strings)
- Enum names describe **domain states**, not AWS API terminology
- Return enum, not boolean or string (enables >2 states)

**Why use enums instead of booleans or string constants?** Enums are very flexible and obvious. Their values can be compound types, and their names can be type-checked against a known list. Unlike booleans which force binary thinking, enums naturally accommodate complex state spaces (e.g., "exists with access" vs "exists without access" vs "doesn't exist"). Unlike string constants, enums provide IDE autocomplete and catch typos at development time. The python-style guide emphasizes explicit, type-safe interfaces, and enums deliver both.

**Reference**: See `references/patterns_implementation.md` Pattern 8 for full details.

---

## Testing Patterns (CRITICAL)

These 4 testing patterns enable comprehensive test coverage without making real AWS API calls.

### Pattern 7: Mocking AwsClientProvider

**What**: Create mock provider that returns mock boto3 clients.

**See**: `reference_implementation/tests/test_s3_interactions.py` - all tests demonstrate this pattern

**Examples**:
- Lines 20-33: Basic provider mocking (test_get_bucket_status_when_exists_have_access)
- Lines 37-48: Provider mocking with ClientError side effect
- Lines 91-100: Provider mocking for delete operation

**Key Design Decisions**:
- Mock the **provider**, not boto3 directly
- Mock client behavior with `return_value` or `side_effect`
- Verify boto3 calls using `assert_called_*` or `call_args_list`

**Why is mocking the provider easier than patching boto3?** As mentioned earlier, this is a personal style preference for writing more obvious and understandable tests. Creating mock objects and passing them explicitly into methods under test is clearer than using patch decorators. You avoid having to understand the subtleties of where and when to patch (import-time vs runtime behavior), and test setup is more explicit - you can see exactly what's being mocked and what behavior is controlled without tracing through decorator chains.

**Reference**: See `references/patterns_testing.md` Pattern 13 for full details.

---

### Pattern 8: Mocking boto3 Clients

**What**: Control boto3 client behavior to simulate different AWS responses.

**See**: `reference_implementation/tests/test_s3_interactions.py` for examples

**Techniques**:

**1. Simple return value** (lines 22-23, 93-94):
```python
mock_s3_client.head_bucket.return_value = {"ResponseMetadata": {...}}
```

**2. Exception side effects** (lines 39-42, 74-77): Mock ClientError with specific error codes

**3. Paginator mocking** (lines 146-150): Mock paginator for multi-page results

**Key Design Decisions**:
- Replicate boto3 response structure (match keys, nesting)
- Use `side_effect` for exceptions or sequential calls
- Use `ClientError` with realistic error codes

**What's the benefit of replicating exact boto3 response structures?** Replicating exact boto3 response structures exercises the behavior of the code under test with higher fidelity. If your wrapper code navigates nested response dictionaries (`response["Contents"][0]["Key"]`), the mock needs to match that structure or the test won't catch bugs. High-fidelity mocks also serve as documentation of what boto3 actually returns, making tests more valuable for understanding the integration. However, this comes with a maintenance trade-off - mocks must be updated if boto3 responses change.

**Reference**: See `references/patterns_testing.md` Pattern 14 for full details.

---

### Pattern 9: Error Scenario Testing

**What**: Verify service wrappers handle AWS errors correctly and raise domain exceptions.

**See**: `reference_implementation/tests/test_s3_interactions.py` for examples

**Examples**:
- Lines 37-48: Test 403 error returns correct enum value
- Lines 51-58: Test 404 error returns correct enum value
- Lines 60-73: Test unexpected error re-raises ClientError
- Lines 117-139: Test domain exception mapping (BucketDoesNotExist)

**Test Coverage Requirements**:
- Test **each error code** wrapper handles (404, 403, etc.)
- Test **unexpected errors** are re-raised (not swallowed)
- Test **idempotent errors** that should be swallowed (lines 76-87)

**Why test error scenarios separately instead of only testing happy path?** Error handling is first-class behavior in production applications, not an edge case. These tests verify that custom exception mapping works correctly (boto3 `ClientError` → domain exceptions), ensuring errors surface clearly with good stack traces when problems occur. This code is used in customer-facing applications where these specific errors were encountered in production and had to be debugged. Testing error scenarios thoroughly prevents regressions and documents how the system behaves under failure conditions, which is critical for maintainability.

**Reference**: See `references/patterns_testing.md` Pattern 17 for full details.

---

### Pattern 10: Pagination Testing

**What**: Verify wrappers correctly handle AWS pagination (boto3 paginators or manual NextToken loops).

**See**: `reference_implementation/tests/test_s3_interactions.py:143-185` (test_list_bucket_objects_with_pagination)

**Test demonstrates**:
- Mock paginator with multiple pages (lines 146-150)
- Verify results from all pages accumulated (line 183)
- Verify paginator called with correct parameters (lines 177-182)

**Key Verification Points**:
- Results from all pages are **accumulated** (line 183: `assert len(objects) == 3`)
- Paginator configured correctly (lines 177-182: verify `paginate()` call)
- Each page's objects transformed to dataclasses (lines 183-185)

**What are the benefits of testing with 2+ pages?** Testing with multiple pages validates that the pagination logic actually works (proper accumulation of results across pages, correct stopping condition). A single-page test only verifies the first call succeeds but doesn't exercise pagination at all. That said, this isn't always critical - single-page tests may be sufficient for simpler wrappers where pagination logic is straightforward or when the wrapper uses boto3's built-in paginator rather than manual NextToken loops.

**Reference**: See `references/patterns_testing.md` Pattern 18 for full details.

---

## Supporting Patterns (PREFERRED)

These patterns enhance the core architecture but aren't strictly required. Include them when they solve specific problems in your project.

### Session & Credential Management

**What**: Pattern for managing boto3 sessions with profile/region/role assumption support.

**When to Use**:
- Multi-account access (role assumption)
- Multiple AWS profiles (dev, staging, prod)
- EC2 instance profile credentials vs local credentials

**Key Snippet**:
```python
def _get_session(self):
    if self.aws_compute and not self.assume_role_arn:
        return boto3.Session(region_name=self.aws_region)

    session = boto3.Session(profile_name=self.aws_profile, region_name=self.aws_region)

    if self.assume_role_arn:
        # Use STS to assume role, create new session with temp credentials
        ...

    return session
```

**Reference**: See `references/patterns_implementation.md` Pattern 3 for full details.

---

### Pagination Patterns (Implementation)

**What**: Handle AWS API pagination with NextToken loops.

**Manual Pagination Pattern**:
```python
subnets = []
next_token = None

while True:
    if next_token:
        response = client.describe_subnets(Filters=[...], NextToken=next_token)
    else:
        response = client.describe_subnets(Filters=[...])

    subnets.extend(response["Subnets"])

    next_token = response.get("NextToken")
    if not next_token:
        break

return subnets
```

**boto3 Paginator Pattern** (preferred when available):
```python
paginator = client.get_paginator("list_objects_v2")
pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

objects = []
for page in pages:
    objects.extend(page.get("Contents", []))

return objects
```

**Reference**: See `references/patterns_implementation.md` Pattern 6 for full details.

---

## Project Structure

```
your_project/
├── core/
│   ├── aws_client_provider.py    # Factory class
│   └── aws_environment.py         # Optional: Account/region context dataclass
├── aws_interactions/
│   ├── s3_interactions.py         # S3 wrappers
│   ├── ec2_interactions.py        # EC2 wrappers
│   └── ...                        # One file per AWS service
└── tests/
    ├── test_aws_client_provider.py
    ├── test_s3_interactions.py
    └── ...                        # 1:1 mapping to implementation files
```

**Organization Principles**:
- `core/`: Factory and shared infrastructure
- `aws_interactions/`: One module per AWS service (not per business domain)
- `tests/`: 1:1 test file for each implementation file
- No inter-service dependencies (EC2 wrapper doesn't import S3 wrapper)

---

## Adoption Workflow

### Step 1: Create Core Factory

1. Create `core/aws_client_provider.py` with `AwsClientProvider` class
2. Implement `__init__` with parameters: `aws_profile`, `aws_region`, `aws_compute`, `assume_role_arn`
3. Implement `_get_session()` method with session/credential logic
4. Add `get_<service>()` methods for each AWS service you'll use

### Step 2: Create Service Wrappers

For each AWS service:

1. Create `aws_interactions/<service>_interactions.py`
2. Define domain exceptions (extend `Exception`)
3. Define domain DTOs (use `@dataclass`)
4. Define domain enums (extend `Enum`)
5. Write wrapper functions:
   - Accept domain parameters + `aws_provider: AwsClientProvider`
   - Get client: `client = aws_provider.get_<service>()`
   - Call boto3: `response = client.operation(...)`
   - Handle errors: Try/except `ClientError`, map to domain exceptions
   - Transform response: Convert to dataclass/enum
   - Return domain object

### Step 3: Write Tests

For each wrapper function:

1. Create test in `tests/test_<service>_interactions.py`
2. Mock the provider and boto3 client
3. Test happy path (success case)
4. Test error scenarios (each error code handled)
5. Test pagination (if applicable)
6. Verify boto3 calls with `assert_called_*` or `call_args_list`

### Step 4: Update Application Code

1. Create provider instance once: `provider = AwsClientProvider(...)`
2. Pass provider to wrapper functions: `result = wrapper_func(domain_arg, provider)`
3. Handle domain exceptions in calling code (not ClientError)

---

## Design Principles

### Principle 1: Separation of Concerns

**Why separate AWS SDK calls from business logic?** Separating these concerns makes each layer easier to understand, test, and modify independently. The factory centralizes complex credential logic (which can differ between local dev, EC2, Lambda, and cross-account scenarios). Wrappers isolate AWS-specific details, making it trivial to swap implementations (e.g., using LocalStack for local testing) or upgrade boto3 versions without touching business logic. Application code works with domain concepts, not AWS API quirks, keeping business rules readable and maintainable. This separation also enables different team members to work on different layers without conflicts.

**Pattern Example**:
- **Factory** (AwsClientProvider): Credential/session management
- **Wrappers**: AWS SDK calls + response transformation
- **Application**: Business logic using domain objects

### Principle 2: Dependency Injection for Testability

**How does dependency injection make testing easier?** Dependency injection makes testing dramatically simpler because you can pass in mock objects without any import patching or global state management. Tests become explicit about what's being controlled: you create a mock provider, configure its behavior, pass it into the function under test, and verify the results. This is more obvious than decorator-based patching where you have to understand import-time vs runtime behavior. It also provides flexibility - the same production code works with different providers (test account, prod account, different regions) just by changing what you inject.

**Pattern Example**:
- Provider passed as parameter (not global)
- Tests mock provider, control boto3 behavior
- No @mock.patch needed

### Principle 3: Domain-Focused Interfaces

**What are the benefits of domain objects over raw boto3 dictionaries?** Domain objects (DTOs, enums, custom exceptions) create an insulating layer that serves your application's needs rather than AWS's API design. This provides type safety (IDE autocomplete, compile-time error checking), customization (field names that make sense in your domain), and resilience to boto3 changes (response structure changes don't ripple through your codebase). It also makes your application code more readable - seeing `BucketStatus.EXISTS_NO_ACCESS` is immediately clear, while parsing `{"ResponseMetadata": {"HTTPStatusCode": 403}}` requires AWS knowledge. This aligns with the python-style guide's emphasis on explicit, type-safe interfaces.

**Pattern Example**:
- Return `BucketStatus` enum, not `{"Status": "exists"}`
- Return `NetworkInterface` dataclass, not `{"NetworkInterfaceId": ...}`
- Raise `BucketDoesNotExist`, not `ClientError`

---

## Reference Implementation

See `reference_implementation/` directory for working example:
- `core/aws_client_provider.py` - Complete factory implementation
- `aws_interactions/s3_interactions.py` - Full S3 wrapper with all CRITICAL patterns
- `tests/test_s3_interactions.py` - Comprehensive test suite

---

## Further Reading

- **Full Pattern Catalog**: See `references/patterns_implementation.md` (11 patterns) and `references/patterns_testing.md` (11 patterns) for comprehensive details on all patterns including PREFERRED and OBSERVED patterns
- **Original Source**: [aws-aio repository](https://github.com/arkime/aws-aio) - Production implementation of this pattern
