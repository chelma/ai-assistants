# AWS SDK Interaction Pattern Guide

**Pattern**: Factory-Provider-Wrapper Architecture for boto3
**Source**: aws-aio repository (production Arkime infrastructure management)
**Lines Analyzed**: 2,890 lines (1,203 implementation + 1,687 test code)

---

## Quick Start

**Goal**: Build testable, maintainable AWS integrations with centralized credential management.

**File structure to create**:
```
your_project/
├── aws_interactions/
│   ├── aws_client_provider.py    # Factory for boto3 clients
│   ├── aws_environment.py         # Account/region context dataclass
│   ├── ec2_interactions.py        # Service wrapper example
│   └── s3_interactions.py         # Service wrapper example
└── tests/
    ├── test_aws_client_provider.py
    ├── test_ec2_interactions.py
    └── test_s3_interactions.py
```

**Pattern in 3 steps**:
1. Create `AwsClientProvider` factory class with getter methods for each AWS service
2. Create service wrapper modules with functions that accept `AwsClientProvider` via dependency injection
3. Commands/entrypoints instantiate provider and pass it to service wrappers

See `reference_implementation/` for complete working code.

---

## Core Concepts

### AwsClientProvider (Factory Pattern)

**What**: Centralized factory class for creating boto3 clients.

**Why**: [TODO: WHY? - Why centralize client creation vs calling boto3.client() directly in each wrapper?]

**Implementation**: See `reference_implementation/core/aws_client_provider.py:14-137`

**Key responsibilities**:
- Manage AWS profiles, regions, and cross-account role assumption
- Provide getter methods: `get_ec2()`, `get_s3()`, `get_cloudwatch()`, etc.
- Create boto3 sessions on-demand (not cached)
- Support multiple credential modes: profile-based, EC2 instance role, assumed role

**Design choice**: [TODO: WHY? - Why create new session per getter call instead of caching sessions/clients?]

### Service Wrapper Modules (Dependency Injection)

**What**: Python modules (not classes) containing functions that wrap boto3 API calls.

**Why**: Separate AWS SDK interactions from business logic for testability and reusability.

**Implementation**: See `reference_implementation/example_service/s3_wrapper.py` for example

**Key characteristics**:
- Functions accept `AwsClientProvider` as parameter
- No inter-service dependencies (wrappers don't call other wrappers)
- Return dataclasses or enums (not raw boto3 response dicts)
- Map boto3 `ClientError` to domain-specific exceptions
- Include module-level logger

**Design choice**: [TODO: WHY? - Why module-level functions instead of service wrapper classes?]

### AwsEnvironment (Context Dataclass)

**What**: Lightweight dataclass encapsulating AWS account + region + profile.

**Why**: Provide account/region context without coupling to boto3 session objects.

**Implementation**: See `reference_implementation/core/aws_environment.py:14-20`

**Usage**: Call `aws_provider.get_aws_env()` when wrappers need account/region info (e.g., S3 bucket creation requires region).

---

## Building Your First AWS Integration

### Step 1: Create AwsClientProvider

Copy `reference_implementation/core/aws_client_provider.py` to your project.

**Customize for your AWS services**:
- Add getter methods for services you'll use
- Follow pattern: `def get_<service>()` returns `session.client("<service>")`
- Example: To add DynamoDB support:

```python
def get_dynamodb(self):
    session = self._get_session()
    client = session.client("dynamodb")
    return client
```

**Constructor parameters**:
- `aws_profile`: Which AWS CLI profile to use (default: "default")
- `aws_region`: Override region (default: use profile's configured region)
- `aws_compute`: Set True when running on EC2 (uses instance role instead of profile)
- `assume_role_arn`: ARN of IAM role to assume for cross-account access

**[TODO: PRINCIPLE? - What's the guiding principle for deciding which parameters AwsClientProvider should expose?]**

### Step 2: Create AwsEnvironment Dataclass

Copy `reference_implementation/core/aws_environment.py` to your project.

**Customization**: Typically used as-is. Add fields if you need additional context (e.g., VPC ID, environment name).

### Step 3: Define Domain-Specific Exceptions

For each service wrapper, create exceptions that map boto3 errors to domain concepts.

**Example** (S3):
```python
# s3_interactions.py

class BucketAccessDenied(Exception):
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        super().__init__(f"You do not have access to S3 bucket {bucket_name}")

class BucketDoesntExist(Exception):
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        super().__init__(f"The S3 bucket {bucket_name} does not exist")
```

**Why domain exceptions**: [TODO: WHY? - Why create custom exceptions instead of letting boto3 ClientError propagate?]

See `references/patterns.md` section "5. Error Handling & Custom Exceptions" for complete pattern details.

### Step 4: Create Service Wrapper Module

Create one module per AWS service (e.g., `ec2_interactions.py`, `s3_interactions.py`).

**Module structure**:
```python
import logging
from botocore.exceptions import ClientError
from aws_interactions.aws_client_provider import AwsClientProvider

logger = logging.getLogger(__name__)

# 1. Define custom exceptions (Step 3)

# 2. Define dataclasses for structured returns (Step 5)

# 3. Define wrapper functions (this step)
def get_bucket_status(bucket_name: str, aws_provider: AwsClientProvider) -> BucketStatus:
    s3_client = aws_provider.get_s3()  # Get boto3 client via dependency injection

    try:
        s3_client.head_bucket(Bucket=bucket_name)
        return BucketStatus.EXISTS_HAVE_ACCESS
    except ClientError as ex:
        # Map boto3 errors to domain exceptions or enum values
        if ex.response["Error"]["Code"] == "403":
            return BucketStatus.EXISTS_NO_ACCESS
        elif ex.response["Error"]["Code"] == "404":
            return BucketStatus.DOES_NOT_EXIST
        else:
            raise ex
```

**Key pattern**: Function signature is `def operation_name(business_params, aws_provider: AwsClientProvider) -> ReturnType`

See `reference_implementation/example_service/s3_wrapper.py` for complete example.

### Step 5: Define Dataclasses for Structured Returns

Return dataclasses instead of raw boto3 response dictionaries.

**Example** (EC2):
```python
from dataclasses import dataclass

@dataclass
class NetworkInterface:
    eni_id: str
    subnet_id: str
    vpc_id: str
    private_ip: str
```

**Why dataclasses**: [TODO: WHY? - What's the benefit of dataclasses vs returning boto3 response dicts directly?]

See `references/patterns.md` section "7. Data Transfer Objects (Dataclasses)" for complete pattern.

### Step 6: Define Enums for Status Classification

Use enums when return value represents a fixed set of states.

**Example** (S3):
```python
from enum import Enum

class BucketStatus(Enum):
    DOES_NOT_EXIST = "does not exist"
    EXISTS_HAVE_ACCESS = "exists have access"
    EXISTS_NO_ACCESS = "exists no access"
```

**When to use enums vs exceptions**: [TODO: PRINCIPLE? - What's the decision rule for when to return enum vs raise exception?]

See `references/patterns.md` section "8. Enum-Based Status Classification" for complete pattern.

### Step 7: Implement Pagination

For AWS APIs that return paginated results, use NextToken loops.

**Pattern**:
```python
def list_all_items(aws_provider: AwsClientProvider) -> List[Item]:
    client = aws_provider.get_service()
    items = []
    next_token = None

    while True:
        kwargs = {}
        if next_token:
            kwargs["NextToken"] = next_token

        response = client.list_items(**kwargs)
        items.extend(response["Items"])

        next_token = response.get("NextToken")
        if not next_token:
            break

    return items
```

**Alternative**: For S3, use boto3 paginators when available.

See `references/patterns.md` section "6. Pagination Patterns" for examples.

### Step 8: Write Tests

For each service wrapper function, create a test that mocks `AwsClientProvider`.

**Basic test pattern**:
```python
from unittest import mock
from aws_interactions.s3_interactions import get_bucket_status, BucketStatus

def test_WHEN_get_bucket_status_called_AND_exists_THEN_as_expected():
    # ARRANGE: Set up mocks
    mock_s3_client = mock.Mock()
    mock_s3_client.head_bucket.return_value = {}  # Success case

    mock_aws_provider = mock.Mock()
    mock_aws_provider.get_s3.return_value = mock_s3_client

    # ACT: Call function under test
    result = get_bucket_status("test-bucket", mock_aws_provider)

    # ASSERT: Verify behavior
    assert result == BucketStatus.EXISTS_HAVE_ACCESS
    mock_s3_client.head_bucket.assert_called_once_with(Bucket="test-bucket")
```

**Test naming convention**: `test_WHEN_<action>_called_AND_<condition>_THEN_<expected_result>`

See `references/patterns.md` sections 12-22 for comprehensive testing patterns.

### Step 9: Integrate in Commands/Entrypoints

In your CLI commands or application entrypoints, instantiate `AwsClientProvider` and pass it to wrappers.

**Example** (Click CLI):
```python
import click
from aws_interactions.aws_client_provider import AwsClientProvider
from aws_interactions import s3_interactions

@click.command()
@click.option("--profile", default="default", help="AWS profile to use")
@click.option("--region", help="AWS region")
@click.argument("bucket_name")
def check_bucket(profile: str, region: str, bucket_name: str):
    """Check if S3 bucket exists and is accessible."""
    aws_provider = AwsClientProvider(aws_profile=profile, aws_region=region)

    status = s3_interactions.get_bucket_status(bucket_name, aws_provider)

    if status == s3_interactions.BucketStatus.EXISTS_HAVE_ACCESS:
        click.echo(f"Bucket {bucket_name} exists and is accessible")
    elif status == s3_interactions.BucketStatus.EXISTS_NO_ACCESS:
        click.echo(f"Bucket {bucket_name} exists but you don't have access")
    else:
        click.echo(f"Bucket {bucket_name} does not exist")
```

**[TODO: WHY? - Is there a principle for where to instantiate AwsClientProvider (command level vs shared instance)?]**

### Step 10: Handle Cross-Account Access (Optional)

If your application needs to access resources in a different AWS account, use role assumption.

**Setup**:
1. Create IAM role in target account with trust relationship to source account
2. Instantiate provider with `assume_role_arn`:

```python
aws_provider = AwsClientProvider(
    aws_profile="source-account-profile",
    assume_role_arn="arn:aws:iam::123456789012:role/CrossAccountRole"
)
```

**How it works**: Provider calls `sts.assume_role()` to get temporary credentials, then creates session with those credentials.

**Limitation**: Role assumption not supported when `aws_compute=True` (running on EC2 instance).

See `reference_implementation/core/aws_client_provider.py:45-77` for implementation details.

---

## Key Design Decisions

### Decision 1: Factory Pattern for Client Creation

**What**: AwsClientProvider acts as factory with getter methods vs passing boto3 clients directly.

**Trade-offs**:
- ✅ Single point of configuration (profile/region/role)
- ✅ Testability (mock entire provider in tests)
- ✅ Cross-account support built-in
- ✅ Lazy initialization (clients created on-demand)
- ❌ Additional indirection layer
- ❌ New session per getter call (not cached)

**When to use this pattern**: [TODO: PRINCIPLE? - Under what circumstances should you NOT use this pattern?]

### Decision 2: Dependency Injection for Service Wrappers

**What**: Functions accept `AwsClientProvider` parameter vs instantiating provider internally.

**Trade-offs**:
- ✅ Testability (easy to mock provider)
- ✅ Flexibility (callers control which provider/credentials)
- ✅ Explicit dependencies (clear from function signature)
- ❌ Boilerplate (every function takes provider parameter)

**Alternative approaches**: [TODO: WHY? - What are the alternatives and why was dependency injection chosen?]

### Decision 3: Module-Level Functions vs Service Classes

**What**: Service wrappers are modules with functions, not classes with methods.

**Trade-offs**:
- ✅ Simplicity (no class boilerplate)
- ✅ Functional style (no state management needed)
- ✅ Easy composition (import and call functions)
- ❌ Can't use class features (inheritance, instance state)

**When to use classes instead**: [TODO: PRINCIPLE? - When would a service wrapper class be more appropriate?]

### Decision 4: Custom Exceptions vs boto3 ClientError

**What**: Map boto3 `ClientError` to domain-specific exceptions.

**Trade-offs**:
- ✅ Domain-oriented error handling (callers don't need boto3 knowledge)
- ✅ Type safety (specific exception types vs generic ClientError)
- ✅ Cleaner error messages for end users
- ❌ Additional exception classes to maintain
- ❌ Loss of original boto3 context if not preserved

**Pattern**: Inspect `ex.response["Error"]["Code"]` to determine specific error, then raise domain exception.

### Decision 5: Dataclasses for Returns vs Raw Dicts

**What**: Return dataclasses instead of boto3 response dictionaries.

**Trade-offs**:
- ✅ Type safety and IDE autocomplete
- ✅ Self-documenting (clear structure in code)
- ✅ Validation at construction time
- ❌ Additional boilerplate (dataclass definitions)
- ❌ Transformation overhead (dict → dataclass)

**When to return raw dicts**: [TODO: PRINCIPLE? - Are there cases where raw boto3 responses are preferable?]

### Decision 6: No Inter-Service Dependencies

**What**: Service wrapper modules don't import or call other service wrappers.

**Why**: [TODO: WHY? - What's the architectural benefit of keeping wrappers isolated?]

**Implication**: If an operation needs multiple services (e.g., EC2 + IAM), implement it in the command layer or create a higher-level orchestration module.

---

## Advanced Patterns

### Pagination with NextToken

**Problem**: AWS APIs limit response size and require multiple calls to fetch all results.

**Solution**: Loop with NextToken until no more pages.

See complete examples in `references/patterns.md` section "6. Pagination Patterns".

### Error Handling Strategies

**Pattern 1: Map ClientError to Domain Exception**

See `reference_implementation/example_service/s3_wrapper.py:59-72` for example.

**Pattern 2: Early Return for Expected "Errors"**

Some error codes represent expected conditions, not exceptions. Return enum values instead.

**Pattern 3: String Matching for Complex Errors**

When error code isn't sufficient, match error message strings (e.g., "BucketAlreadyOwnedByYou").

See `references/patterns.md` section "5. Error Handling & Custom Exceptions" for details.

### Resource vs Client Interfaces

**Default**: Use boto3 `client` interface for all operations.

**Exception**: Use boto3 `resource` interface when it provides significant convenience (e.g., S3 bucket deletion with objects).

**Trade-off**: [TODO: WHY? - Why prefer client over resource by default?]

See `references/patterns.md` section "9. Resource vs Client Interfaces" for details.

### Logging Best Practices

**Pattern**: Module-level logger with debug/info/error levels.

```python
import logging
logger = logging.getLogger(__name__)

def wrapper_function():
    logger.debug(f"Starting operation with params: {params}")
    # ... operation ...
    logger.info(f"Operation completed successfully")
```

**When to log**: Debug for detailed traces, info for key milestones, error for exceptions.

See `references/patterns.md` section "10. Logging Patterns" for examples.

### Abstract Base Classes for Domain Objects

**Use case**: When multiple types of objects share common interface but different implementations.

**Example**: CloudWatch metrics with shared properties (account, region) but type-specific properties.

See `references/patterns.md` section "11. Abstract Base Classes for Domain Objects" for complete pattern.

---

## Testing Guide

### Mocking AwsClientProvider

**Pattern**: Create mock provider that returns mock boto3 client.

```python
from unittest import mock

# Create mock boto3 client
mock_s3_client = mock.Mock()
mock_s3_client.head_bucket.return_value = {}

# Create mock provider that returns mock client
mock_aws_provider = mock.Mock()
mock_aws_provider.get_s3.return_value = mock_s3_client

# Call function under test
result = get_bucket_status("bucket", mock_aws_provider)
```

See `references/patterns.md` section "13. Mocking AwsClientProvider" for details.

### Testing Error Scenarios

**Pattern**: Configure mock to raise `ClientError`, verify wrapper maps to domain exception.

```python
from botocore.exceptions import ClientError

mock_s3_client.head_bucket.side_effect = ClientError(
    {"Error": {"Code": "404", "Message": "Not Found"}},
    "HeadBucket"
)

result = get_bucket_status("bucket", mock_aws_provider)
assert result == BucketStatus.DOES_NOT_EXIST
```

See `references/patterns.md` section "17. Error Scenario Testing" for details.

### Testing Pagination

**Pattern**: Use `side_effect` to return sequence of responses with/without NextToken.

See `references/patterns.md` section "18. Pagination Testing" for complete examples.

### Test Structure (AAA Pattern)

Organize tests with clear ARRANGE → ACT → ASSERT sections:

```python
def test_WHEN_operation_called_THEN_as_expected():
    # ARRANGE: Set up mocks, test data
    mock_client = mock.Mock()
    # ... mock setup ...

    # ACT: Call function under test
    result = wrapper_function(params, mock_aws_provider)

    # ASSERT: Verify results and call expectations
    assert result == expected_value
    mock_client.method.assert_called_once_with(expected_args)
```

See `references/patterns.md` section "15. Test Structure (AAA Pattern)" for details.

---

## Common Pitfalls

### Pitfall 1: Forgetting to Call get_X() on Provider

**Wrong**:
```python
def wrapper(aws_provider: AwsClientProvider):
    aws_provider.list_buckets()  # AwsClientProvider doesn't have this method!
```

**Right**:
```python
def wrapper(aws_provider: AwsClientProvider):
    s3_client = aws_provider.get_s3()  # Get the boto3 client first
    s3_client.list_buckets()
```

### Pitfall 2: Inter-Service Dependencies in Wrappers

**Wrong**:
```python
# In ec2_interactions.py
from aws_interactions import iam_interactions  # Don't import other wrappers!

def create_instance_with_role(aws_provider):
    role = iam_interactions.create_role(...)  # Don't call other wrappers!
```

**Right**: Implement cross-service operations at command/orchestration layer, not in wrappers.

### Pitfall 3: Returning Raw boto3 Response Dicts

**Less Preferred**:
```python
def get_vpc_details(vpc_id, aws_provider):
    ec2_client = aws_provider.get_ec2()
    return ec2_client.describe_vpcs(VpcIds=[vpc_id])  # Raw boto3 response
```

**Preferred**:
```python
@dataclass
class VpcDetails:
    vpc_id: str
    cidr_block: str

def get_vpc_details(vpc_id, aws_provider) -> VpcDetails:
    ec2_client = aws_provider.get_ec2()
    response = ec2_client.describe_vpcs(VpcIds=[vpc_id])
    vpc = response["Vpcs"][0]
    return VpcDetails(vpc_id=vpc["VpcId"], cidr_block=vpc["CidrBlock"])
```

### Pitfall 4: Not Handling Pagination

**Wrong**:
```python
def list_items(aws_provider):
    client = aws_provider.get_service()
    response = client.list_items()
    return response["Items"]  # Only returns first page!
```

**Right**: Implement NextToken loop (see Step 7 above).

### Pitfall 5: Catching ClientError Without Inspection

**Wrong**:
```python
try:
    s3_client.head_bucket(Bucket=name)
except ClientError:
    raise BucketDoesntExist(name)  # Might actually be 403 Forbidden, not 404!
```

**Right**: Inspect error code before mapping to exception (see Step 3 above).

---

## Resources

- **Reference Implementation**: `reference_implementation/` - Domain-agnostic AwsClientProvider + example S3 wrapper
- **Pattern Catalog**: `references/patterns.md` - Comprehensive documentation of all 22 patterns (production + testing)
- **Source Repository**: aws-aio (internal - not publicly available)

---

## Summary

This pattern provides a **production-tested** architecture for building AWS integrations with:
- ✅ Centralized credential management
- ✅ Cross-account support
- ✅ High testability through dependency injection
- ✅ Clear separation of concerns
- ✅ Type-safe, self-documenting code

**Start with**: AwsClientProvider factory + one simple service wrapper + tests
**Expand to**: Multiple services as needed, following consistent patterns
**Key principle**: [TODO: PRINCIPLE? - What's the overarching architectural philosophy that ties these patterns together?]
