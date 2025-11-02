# AWS SDK Interaction Patterns

**Source**: aws-aio repository (AwsClientProvider + 9 AWS service wrappers)
**Lines Analyzed**: 1,203 lines (implementation code)
**Last Updated**: 2025-11-01 (Iteration 1 - Production Patterns)

---

## Pattern Categories

1. [Factory Pattern](#1-factory-pattern)
2. [Dependency Injection](#2-dependency-injection)
3. [Session & Credential Management](#3-session--credential-management)
4. [Service Wrapper Structure](#4-service-wrapper-structure)
5. [Error Handling & Custom Exceptions](#5-error-handling--custom-exceptions)
6. [Pagination Patterns](#6-pagination-patterns)
7. [Data Transfer Objects (Dataclasses)](#7-data-transfer-objects-dataclasses)
8. [Enum-Based Status Classification](#8-enum-based-status-classification)
9. [Resource vs Client Interfaces](#9-resource-vs-client-interfaces)
10. [Logging Patterns](#10-logging-patterns)
11. [Abstract Base Classes for Domain Objects](#11-abstract-base-classes-for-domain-objects)

---

## 1. Factory Pattern

**[PRIORITY: CRITICAL]** - Core architectural decision defining the entire pattern

### Purpose
Centralize boto3 client creation to manage credentials, sessions, regions, and cross-account role assumption in one place.

### Implementation

**AwsClientProvider** (`aws_client_provider.py:14-137`) acts as a factory with:
- Private session management method `_get_session()` (`:56-77`)
- Public getter methods for each AWS service (`:79-137`)

```python
# Constructor stores configuration
def __init__(self, aws_profile: str = "default", aws_region: str = None,
             aws_compute=False, assume_role_arn: str=None)

# Getter methods follow consistent pattern
def get_ec2(self):
    session = self._get_session()
    client = session.client("ec2")
    return client
```

### When to Use
- **Use when**: Building applications that interact with multiple AWS services
- **Use when**: Need centralized credential/session management
- **Use when**: Supporting cross-account access or multiple AWS profiles
- **Use when**: Want testability through dependency injection

### When NOT to Use
- Simple scripts using only one AWS service with default credentials
- AWS Lambda functions using execution role credentials exclusively
- Applications already using a different AWS SDK abstraction layer

### Trade-offs
- ✅ **Single point of configuration**: All AWS interactions use same credentials/region/profile
- ✅ **Testability**: Easy to mock entire provider in tests
- ✅ **Cross-account support**: Built-in role assumption handling
- ✅ **Lazy initialization**: Clients created on-demand, not upfront
- ❌ **Additional indirection**: Extra layer vs calling boto3 directly
- ❌ **Session per client**: Creates new session for each getter call (not cached)

### Related Patterns
- [Dependency Injection](#2-dependency-injection) - How service wrappers consume the factory
- [Session & Credential Management](#3-session--credential-management) - Internal session handling

---

## 2. Dependency Injection

**[PRIORITY: CRITICAL]** - Core architectural decision enabling testability and modularity

### Purpose
Service wrapper functions accept `AwsClientProvider` as parameter, enabling testability and separating AWS SDK calls from business logic.

### Implementation

**All service wrapper functions** follow this signature pattern:

```python
# EC2 example (ec2_interactions.py:167-185)
def get_vpc_details(vpc_id: str, aws_provider: AwsClientProvider) -> VpcDetails:
    ec2_client = aws_provider.get_ec2()
    # ... use client ...

# S3 example (s3_interactions.py:59-72)
def get_bucket_status(bucket_name: str, aws_provider: AwsClientProvider) -> BucketStatus:
    s3_client = aws_provider.get_s3()
    # ... use client ...

# CloudWatch example (cloudwatch_interactions.py:208-215)
def put_event_metrics(metrics: ArkimeEventMetric, aws_client_provider: AwsClientProvider):
    cw_client = aws_client_provider.get_cloudwatch()
    # ... use client ...
```

### Pattern Details
- **Parameter naming**: Either `aws_provider` or `aws_client_provider` (both used consistently)
- **Parameter position**: Typically last parameter in function signature
- **Client retrieval**: First line of function calls appropriate getter method
- **Type hints**: `AwsClientProvider` type hint on parameter

### When to Use
- **Use when**: Building reusable AWS service wrapper functions
- **Use when**: Need testability (mock provider instead of mocking boto3 clients directly)
- **Use when**: Functions are called from multiple places with different AWS contexts

### When NOT to Use
- One-off scripts where testability isn't important
- Functions that need to work with multiple AWS accounts simultaneously (pass multiple providers or use different pattern)
- Very simple functions where passing provider adds more complexity than value

### Trade-offs
- ✅ **Testability**: Mock provider once, all boto3 clients mocked
- ✅ **Flexibility**: Caller controls AWS context (profile, region, role)
- ✅ **Explicit dependencies**: Clear what AWS services function uses
- ✅ **Reusability**: Same function works across different AWS contexts
- ❌ **Verbosity**: Every function needs provider parameter
- ❌ **Caller burden**: Caller must manage provider lifecycle

### Related Patterns
- [Factory Pattern](#1-factory-pattern) - What's being injected
- [Service Wrapper Structure](#4-service-wrapper-structure) - How wrappers use injected provider

---

## 3. Session & Credential Management

**[PRIORITY: PREFERRED]** - Important implementation detail, but specific modes depend on deployment context

### Purpose
Handle AWS credential sourcing, region selection, and cross-account role assumption in a unified way.

### Implementation

**Private `_get_session()` method** (`aws_client_provider.py:56-77`) implements credential resolution logic:

```python
def _get_session(self) -> boto3.Session:
    # Mode 1: AWS Compute (EC2/Lambda with instance/execution role)
    if self._aws_compute:
        current_account_session = boto3.Session()
    # Mode 2: Named profile with optional region
    else:
        current_account_session = boto3.Session(
            profile_name=self._aws_profile,
            region_name=self._aws_region
        )

    # Cross-account role assumption (profile mode only)
    if self._assume_role_arn and not self._aws_compute:
        creds = self._get_assumed_credentials(current_account_session)
        session_to_use = boto3.Session(
            aws_access_key_id=creds["AccessKeyId"],
            aws_secret_access_key=creds["SecretAccessKey"],
            aws_session_token=creds["SessionToken"],
            region_name=self._aws_region
        )
    elif self._assume_role_arn and self._aws_compute:
        # Combination not supported
        raise AssumeRoleNotSupported()
    else:
        session_to_use = current_account_session

    return session_to_use
```

**Role assumption helper** (`aws_client_provider.py:45-54`):
```python
def _get_assumed_credentials(self, current_session: boto3.Session) -> Dict[str, str]:
    sts_client = current_session.client("sts")
    assumed_role_object = sts_client.assume_role(
        RoleArn=self._assume_role_arn,
        RoleSessionName="ArkimeAwsAioCLI"  # [TODO: PRINCIPLE?] Why hardcoded session name?
    )
    return assumed_role_object["Credentials"]
```

**Environment context retrieval** (`aws_client_provider.py:26-43`):
```python
def get_aws_env(self) -> AwsEnvironment:
    sts_client = self.get_sts()

    # Region: explicit > inferred from client metadata
    env_region = self._aws_region if self._aws_region else sts_client.meta.region_name

    # Account: call STS GetCallerIdentity
    env_account = sts_client.get_caller_identity()["Account"]

    return AwsEnvironment(env_account, env_region, self._aws_profile)
```

### Credential Resolution Modes

**Mode 1: AWS Compute** (`aws_compute=True`)
- Uses instance/execution role credentials
- No profile specified
- Region from instance metadata or explicit parameter
- Role assumption NOT supported (raises `AssumeRoleNotSupported`)

**Mode 2: Named Profile** (`aws_compute=False`, default)
- Uses `~/.aws/credentials` profile
- Defaults to "default" profile
- Region from explicit parameter or profile's default region
- Supports cross-account role assumption

**Mode 3: Named Profile + Role Assumption** (`aws_compute=False`, `assume_role_arn` provided)
- Creates initial session from profile
- Calls STS AssumeRole to get temporary credentials
- Creates new session with temporary credentials
- All subsequent clients use assumed role credentials

### When to Use
- **Use Mode 1** when: Running on EC2/Lambda with instance/execution roles
- **Use Mode 2** when: Local development or multi-profile CLI tools
- **Use Mode 3** when: Cross-account access needed (e.g., central account → workload accounts)

### When NOT to Use
- Applications requiring frequent role switching (session created per client getter call, not cached)
- Applications needing fine-grained credential expiry handling
- Multi-threaded applications (boto3 sessions aren't thread-safe without additional handling)

### Trade-offs
- ✅ **Flexibility**: Supports EC2 roles, named profiles, cross-account access
- ✅ **Explicit region handling**: Falls back to metadata when not specified
- ✅ **Environment introspection**: `get_aws_env()` provides account/region context
- ❌ **No session caching**: New session created for each client getter call
- ❌ **Limited role assumption**: Only from profile mode, not compute mode
- ❌ **Hardcoded session name**: AssumeRole session name not configurable

### Related Patterns
- [Factory Pattern](#1-factory-pattern) - Public interface consuming these sessions
- [Custom Exceptions](#5-error-handling--custom-exceptions) - `AssumeRoleNotSupported` exception

---

## 4. Service Wrapper Structure

**[PRIORITY: CRITICAL]** - Core architectural decision on how service wrappers are organized

### Purpose
Provide consistent, predictable structure across all AWS service wrapper modules.

### Implementation

**Module-level patterns** (observed across all 9 service wrappers):

1. **Imports at top**:
```python
import logging
from typing import Dict, List  # Type hints
from botocore.exceptions import ClientError  # Error handling

from aws_interactions.aws_client_provider import AwsClientProvider
# Domain-specific imports (dataclasses, constants, etc.)
```

2. **Logger initialization**:
```python
logger = logging.getLogger(__name__)
```

3. **Custom exceptions** (domain-specific):
```python
class BucketDoesntExist(Exception):
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        super().__init__(f"The S3 bucket {bucket_name} does not exist")
```

4. **Dataclass DTOs** (optional, for complex return types):
```python
@dataclass
class VpcDetails:
    vpc_id: str
    owner_id: str
    cidr_blocks: List[str]
    tenancy: str
```

5. **Service wrapper functions**:
```python
def operation_name(resource_id: str, aws_provider: AwsClientProvider) -> ReturnType:
    service_client = aws_provider.get_service()
    # ... boto3 calls ...
    # ... error handling ...
    # ... pagination if needed ...
    return result
```

### Consistency Patterns Across Wrappers

**EC2 Interactions** (`ec2_interactions.py`):
- Dataclasses: `NetworkInterface`, `VpcDetails`
- Exceptions: `VpcDoesNotExist`, `NonMirrorableEniType`, `MirrorDoesntExist`
- Functions: 7 functions covering VPC/ENI/traffic mirroring operations

**S3 Interactions** (`s3_interactions.py`):
- Enum: `BucketStatus` for tri-state bucket existence
- Exceptions: 8 custom exceptions for specific failure modes
- Functions: 9 functions covering bucket/object lifecycle
- Mix of client and resource interfaces

**CloudWatch Interactions** (`cloudwatch_interactions.py`):
- ABC: `ArkimeEventMetric` base class for metrics
- Enums: 3 outcome enums (`ConfigureIsmEventOutcome`, etc.)
- Classes: 3 metric classes extending ABC
- Function: 1 function `put_event_metrics()` accepting ABC

**EventBridge Interactions** (`events_interactions.py`):
- ABC: `ArkimeEvent` base class for events
- Classes: 3 event classes extending ABC
- Function: 1 function `put_events()` accepting list of ABC instances

**SSM Operations** (`ssm_operations.py`):
- Exception: `ParamDoesNotExist`
- Functions: 6 functions covering Parameter Store operations
- Pagination: `get_ssm_params_by_path()` uses NextToken loop

**IAM Interactions** (`iam_interactions.py`):
- Functions: 2 functions (`does_iam_role_exist`, `delete_iam_role`)
- No dataclasses (simple boolean/void returns)
- `delete_iam_role()` handles multi-step cleanup process

**ACM Interactions** (`acm_interactions.py`):
- Functions: 3 functions covering certificate import/generation/deletion
- Uses domain object `SelfSignedCert` from separate module
- Constant: `DEFAULT_ELB_DOMAIN`

**OpenSearch Domain** (`destroy_os_domain.py`):
- Function: 1 function `destroy_os_domain_and_wait()` with polling loop
- Polling pattern: `time.sleep(10)` loop checking domain status

**ECS Interactions** (`ecs_interactions.py`):
- Functions: 3 functions covering deployment operations
- Simple functions returning primitives or status checks

### Structural Decisions

**No inter-service dependencies**: Service wrappers don't import each other; each is standalone.

**Functions, not classes**: Service wrappers are module-level functions, not class methods (except ABC-based domain objects like `ArkimeEvent`, `ArkimeEventMetric`).

**Type hints throughout**: All function signatures use type hints for parameters and return values.

**Logging before AWS calls**: Debug/info messages logged before making AWS API calls.

### When to Use
- **Use function-based wrappers** when: Operations are independent and don't share state
- **Use dataclass returns** when: Returning multiple related values from boto3 response
- **Use enum-based status** when: boto3 responses have multiple states to classify
- **Use ABC-based classes** when: Multiple domain objects share structure and need polymorphism

### When NOT to Use
- Class-based wrappers if operations share significant state or configuration
- Flat dictionaries for return values if type safety and IDE autocomplete are important
- String-based status if you want type-checked exhaustive matching

### Trade-offs
- ✅ **Consistency**: Predictable structure across all service wrappers
- ✅ **Independence**: No coupling between service wrappers
- ✅ **Type safety**: Full type hints enable static analysis
- ✅ **Readability**: Clear separation of concerns (one module per service)
- ❌ **No state sharing**: Functions can't easily share cached data or configuration
- ❌ **No wrapper composition**: Can't easily combine operations from multiple services

### Related Patterns
- [Dependency Injection](#2-dependency-injection) - How functions accept provider
- [Data Transfer Objects](#7-data-transfer-objects-dataclasses) - Return type patterns
- [Custom Exceptions](#5-error-handling--custom-exceptions) - Error handling patterns

---

## 5. Error Handling & Custom Exceptions

**[PRIORITY: CRITICAL]** - Core pattern for handling AWS SDK errors in domain-friendly way.  Also - included in the `python-style` guide skill.

### Purpose
Map boto3 `ClientError` exceptions to domain-specific exceptions with meaningful context.

### Implementation

**Pattern**: Try-except blocks catch `ClientError`, inspect error code, raise custom exception.

**Example 1: S3 NoSuchBucket** (`s3_interactions.py:134-140`):
```python
try:
    s3_client.put_object(...)
except ClientError as ex:
    if "NoSuchBucket" in str(ex):
        raise BucketDoesntExist(bucket_name)
    elif "AccessDenied" in str(ex):
        raise BucketAccessDenied(bucket_name)
    else:
        raise ex  # Re-raise if unhandled
```

**Example 2: SSM ParameterNotFound** (`ssm_operations.py:24-30`):
```python
try:
    return ssm_client.get_parameter(Name=param_name)["Parameter"]
except ClientError as exc:
    if exc.response['Error']['Code'] == 'ParameterNotFound':
        raise ParamDoesNotExist(param_name=param_name)
    raise  # Re-raise if unhandled
```

**Example 3: EC2 Traffic Mirror Session Not Found** (`ec2_interactions.py:142-150`):
```python
try:
    ec2_client.delete_traffic_mirror_session(TrafficMirrorSessionId=traffic_session)
except ClientError as exc:
    if exc.response["Error"]["Code"] == "InvalidTrafficMirrorSessionId.NotFound":
        raise MirrorDoesntExist(traffic_session)
    else:
        raise
```

**Example 4: OpenSearch ResourceNotFoundException** (`destroy_os_domain.py:14-21`):
```python
try:
    describe_response = os_client.describe_domain(DomainName=domain_name)
except ClientError as exc:
    if exc.response['Error']['Code'] == 'ResourceNotFoundException':
        logger.info(f"OS Domain {domain_name} does not exist; no need to delete")
        return
    raise
```

### Custom Exception Patterns

**Standard exception structure**:
```python
class ResourceDoesntExist(Exception):
    def __init__(self, resource_id: str):
        self.resource_id = resource_id  # Store context as attribute
        super().__init__(f"Descriptive message: {resource_id}")
```

**Exceptions across modules**:
- **EC2**: `VpcDoesNotExist`, `NonMirrorableEniType`, `MirrorDoesntExist`
- **S3**: 8 exceptions (bucket access/existence/creation, file write failures, object existence)
- **SSM**: `ParamDoesNotExist`
- **AwsClientProvider**: `AssumeRoleNotSupported`

### Error Code Inspection Methods

**Method 1: String matching** (`"NoSuchBucket" in str(ex)`):
- Used in `s3_interactions.py` for S3 errors
- Matches error codes/messages in string representation

**Method 2: Response dictionary** (`exc.response['Error']['Code'] == 'ParameterNotFound'`):
- Used in `ssm_operations.py`, `ec2_interactions.py`, `destroy_os_domain.py`
- Inspects boto3's structured error response
- More reliable than string matching

**Method 3: HTTP status code** (`ex.response["Error"]["Code"] == "403"`):
- Used in `s3_interactions.py:67-70` for bucket access checks
- Checks HTTP status codes for access determination

### Unconditional Returns on Expected "Errors"

Some functions treat certain boto3 errors as expected conditions and return early:

**OpenSearch domain doesn't exist** (`destroy_os_domain.py:18-20`):
```python
except ClientError as exc:
    if exc.response['Error']['Code'] == 'ResourceNotFoundException':
        logger.info(f"OS Domain {domain_name} does not exist; no need to delete")
        return  # Normal completion, not an error
    raise
```

**IAM role doesn't exist** (`iam_interactions.py:16-18`):
```python
except ClientError as ex:
    if ex.response['Error']['Code'] == 'NoSuchEntity':
        return False  # Expected condition
    raise ex
```

### When to Use
- **Use custom exceptions** when: Callers need to handle specific AWS errors differently
- **Use early returns** when: boto3 "error" is actually an expected, valid state
- **Use string matching** when: Error codes aren't easily accessible in response structure
- **Use response dictionary** when: Error codes are in `exc.response['Error']['Code']`

### When NOT to Use
- Generic exception handling if all AWS errors should be treated the same
- Custom exceptions for every possible boto3 error (only wrap errors callers care about)
- String matching if response dictionary is available (less reliable)

### Trade-offs
- ✅ **Domain-specific context**: Exceptions carry relevant IDs/names
- ✅ **Caller clarity**: Clear what error occurred without inspecting boto3 internals
- ✅ **Selective handling**: Callers can catch specific errors
- ✅ **Expected vs exceptional**: Early returns distinguish valid states from errors
- ❌ **Maintenance burden**: Must update wrappers when boto3 error codes change
- ❌ **String matching fragility**: String-based checks can break with boto3 message changes

### Related Patterns
- [Service Wrapper Structure](#4-service-wrapper-structure) - Where exceptions are defined
- [Logging Patterns](#10-logging-patterns) - Logging before raising exceptions

---

## 6. Pagination Patterns

**[PRIORITY: PREFERRED]** - Common pattern, but specific implementation depends on AWS service pagination style

### Purpose
Handle AWS API pagination to retrieve complete result sets exceeding single-response limits.

### Implementation

**Pattern 1: Manual NextToken Loop** (most common):

```python
# Example from ec2_interactions.py:27-35
subnet_ids = [subnet["SubnetId"] for subnet in subnets_response["Subnets"]]

next_token = subnets_response.get("NextToken")
while next_token:
    subnets_response = ec2_client.describe_subnets(
        Filters=[{"Name": "vpc-id", "Values": [vpc_id]}],
        NextToken=next_token
    )
    next_subnets = [subnet["SubnetId"] for subnet in subnets_response["Subnets"]]
    subnet_ids.extend(next_subnets)
    next_token = subnets_response.get("NextToken")
```

**Pattern 2: boto3 Paginator** (used for S3):

```python
# Example from s3_interactions.py:172-189
paginator = s3_client.get_paginator('list_objects_v2')

page_iterator = (
    paginator.paginate(Bucket=bucket_name, Prefix=prefix)
    if prefix
    else paginator.paginate(Bucket=bucket_name)
)

for page in page_iterator:
    contents = page.get('Contents', [])
    for obj in contents:
        all_objects.append({
            "key": obj["Key"],
            "date_modified": obj["LastModified"],
        })
```

### Pagination Examples Across Services

**EC2 - describe_subnets** (`ec2_interactions.py:16-37`):
- Manual NextToken loop
- Initial call gets first page
- While loop fetches subsequent pages
- Results accumulated in list via `extend()`

**EC2 - describe_network_interfaces** (`ec2_interactions.py:69-94`):
- Manual NextToken loop
- Pattern identical to describe_subnets
- Builds `NetworkInterface` dataclasses during iteration

**SSM - get_parameters_by_path** (`ssm_operations.py:32-50`):
- Manual NextToken loop
- Handles recursive path traversal
- Uses `return_params.extend()` to accumulate results

**S3 - list_objects_v2** (`s3_interactions.py:166-190`):
- boto3 paginator (not manual loop)
- Conditional prefix parameter
- Extracts key + last modified date from each object

### Implementation Details

**NextToken retrieval**: `next_token = response.get("NextToken")` (returns `None` if absent)

**Loop termination**: `while next_token:` (loop ends when `NextToken` absent)

**Result accumulation**:
- List comprehension for initial page
- `extend()` to append subsequent pages
- Avoids nested loops creating sub-lists

**boto3 Paginator benefits**:
- Handles NextToken automatically
- Pythonic iteration over pages
- Used for `list_objects_v2` (S3's primary list operation)

### When to Use
- **Use manual NextToken** when: boto3 doesn't provide paginator for the operation
- **Use boto3 paginator** when: Available for the operation (check boto3 docs)
- **Use pagination** when: Result sets can exceed single-response limits (common for list/describe operations)

### When NOT to Use
- Operations guaranteed to return small result sets (e.g., describe single resource by ID)
- Operations that don't support pagination (e.g., put/delete operations)

### Trade-offs
- ✅ **Completeness**: Retrieve all results, not just first page
- ✅ **Correctness**: Avoid missing resources due to truncation
- ✅ **boto3 paginator**: Less boilerplate, handles token automatically
- ❌ **Complexity**: More code than single-call approach
- ❌ **Memory**: Accumulates all results in memory (not streaming)
- ❌ **Latency**: Multiple API calls increase total operation time

### Related Patterns
- [Service Wrapper Structure](#4-service-wrapper-structure) - Where pagination is implemented
- [Data Transfer Objects](#7-data-transfer-objects-dataclasses) - Building DTOs during pagination

---

## 7. Data Transfer Objects (Dataclasses)

**[PRIORITY: PREFERRED]** - Improves type safety and API clarity, but not architecturally essential.  Also - included in the `python-style` guide skill.

### Purpose
Return structured, typed data from service wrappers instead of raw boto3 response dictionaries.

### Implementation

**Pattern**: Use `@dataclass` decorator to define simple data containers.

**Example 1: NetworkInterface** (`ec2_interactions.py:39-52`):
```python
@dataclass
class NetworkInterface:
    vpc_id: str
    subnet_id: str
    eni_id: str
    eni_type: str

    def to_dict(self):
        return {
            'vpc_id': self.vpc_id,
            'subnet_id': self.subnet_id,
            'eni_id': self.eni_id,
            'eni_type': self.eni_type,
        }
```

**Example 2: VpcDetails** (`ec2_interactions.py:152-165`):
```python
@dataclass
class VpcDetails:
    vpc_id: str
    owner_id: str
    cidr_blocks: List[str]
    tenancy: str

    def to_dict(self) -> Dict[str, any]:
        return {
            'vpc_id': self.vpc_id,
            'owner_id': self.owner_id,
            'cidr_blocks': self.cidr_blocks,
            'tenancy': self.tenancy,
        }
```

**Example 3: AwsEnvironment** (`aws_environment.py:14-20`):
```python
@dataclass
class AwsEnvironment:
    aws_account: str
    aws_region: str
    aws_profile: str

    def __str__(self) -> str:
        return f"aws://{self.aws_account}/{self.aws_region}"
```

### Usage Patterns

**Construction from boto3 response** (`ec2_interactions.py:63-65`):
```python
for eni in instance_details.get("NetworkInterfaces", []):
    network_interfaces.append(
        NetworkInterface(eni["VpcId"], eni["SubnetId"], eni["NetworkInterfaceId"], eni["InterfaceType"])
    )
```

**Construction with transformation** (`ec2_interactions.py:177-185`):
```python
vpc_details = describe_vpc_response["Vpcs"][0]
cidr_blocks = [item["CidrBlock"] for item in vpc_details["CidrBlockAssociationSet"]
               if item["CidrBlockState"]["State"] in ["associating", "associated"]]

return VpcDetails(
    vpc_id=vpc_details["VpcId"],
    owner_id=vpc_details["OwnerId"],
    cidr_blocks=cidr_blocks,
    tenancy=vpc_details["InstanceTenancy"]
)
```

### Dataclass Features Used

**Type hints**: All fields have type annotations (`str`, `List[str]`, etc.)

**Optional `to_dict()` method**: Enables serialization back to dictionary (not automatic)

**Optional `__str__()` method**: Custom string representation (e.g., AwsEnvironment's `aws://account/region` format)

**Positional construction**: Dataclasses used with positional arguments, not keyword arguments

**No default values**: All observed dataclasses require all fields at construction time

### When to Use
- **Use dataclasses** when: Returning multiple related values from boto3 response
- **Use dataclasses** when: Type safety and IDE autocomplete are important
- **Use dataclasses** when: Callers should access fields by attribute, not dictionary key
- **Add `to_dict()`** when: Need to serialize back to dictionary (e.g., for JSON responses, database storage)
- **Add `__str__()`** when: Need human-readable representation for logging or display

### When NOT to Use
- Returning single values (use primitive types directly)
- Returning boto3 response dictionaries unchanged (no transformation needed)
- Complex domain objects with behavior (use regular classes with methods)
- Nested hierarchies (dataclasses get verbose; consider TypedDict or regular classes)

### Trade-offs
- ✅ **Type safety**: Static analysis can catch field access errors
- ✅ **IDE support**: Autocomplete for field names
- ✅ **Documentation**: Field types are self-documenting
- ✅ **Immutability option**: Can make frozen with `@dataclass(frozen=True)`
- ❌ **Boilerplate**: Must define dataclass for each return type
- ❌ **Maintenance**: Changes to boto3 response structure require dataclass updates
- ❌ **No automatic serialization**: Must implement `to_dict()` manually if needed

### Related Patterns
- [Service Wrapper Structure](#4-service-wrapper-structure) - Where dataclasses are defined
- [Pagination Patterns](#6-pagination-patterns) - Building dataclasses during paginated iteration

---

## 8. Enum-Based Status Classification

**[PRIORITY: CRITICAL]** - Provides type safety and self-documenting code.

### Purpose
Classify AWS resource states or operation outcomes into typed, exhaustive categories.

### Implementation

**Pattern**: Use `Enum` class with string values for status classification.

**Example 1: BucketStatus** (`s3_interactions.py:13-16`):
```python
class BucketStatus(Enum):
    DOES_NOT_EXIST="does not exist"
    EXISTS_HAVE_ACCESS="exists have access"
    EXISTS_NO_ACCESS="exists no access"
```

Usage:
```python
def get_bucket_status(bucket_name: str, aws_provider: AwsClientProvider) -> BucketStatus:
    s3_client = aws_provider.get_s3()
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        return BucketStatus.EXISTS_HAVE_ACCESS
    except ClientError as ex:
        if ex.response["Error"]["Code"] == "403":
            return BucketStatus.EXISTS_NO_ACCESS
        elif ex.response["Error"]["Code"] == "404":
            return BucketStatus.DOES_NOT_EXIST
        else:
            raise ex
```

**Example 2: CloudWatch Event Outcomes** (`cloudwatch_interactions.py:42-44, 89-93, 158-160`):
```python
class ConfigureIsmEventOutcome(Enum):
    SUCCESS="Success"
    FAILURE="Failure"

class CreateEniMirrorEventOutcome(Enum):
    SUCCESS="Success"
    ABORTED_EXISTS="AbortedExists"
    ABORTED_ENI_TYPE="AbortedEniType"
    FAILURE="Failure"

class DestroyEniMirrorEventOutcome(Enum):
    SUCCESS="Success"
    FAILURE="Failure"
```

Usage in metric classes (`cloudwatch_interactions.py:95-116`):
```python
class CreateEniMirrorEventMetrics(ArkimeEventMetric):
    def __init__(self, cluster_name: str, vpc_id: str, outcome: CreateEniMirrorEventOutcome):
        # ... initialization ...

        if outcome == CreateEniMirrorEventOutcome.SUCCESS:
            self.value_success = 1
        elif outcome == CreateEniMirrorEventOutcome.ABORTED_EXISTS:
            self.value_abort_exists = 1
        elif outcome == CreateEniMirrorEventOutcome.ABORTED_ENI_TYPE:
            self.value_abort_eni_type = 1
        elif outcome == CreateEniMirrorEventOutcome.FAILURE:
            self.value_failure = 1
```

### Design Decisions

**String values**: Enum values are human-readable strings (e.g., `"Success"`, `"does not exist"`)

**PascalCase for outcomes**: CloudWatch outcomes use PascalCase (e.g., `"AbortedExists"`)

**Lowercase with spaces for status**: BucketStatus uses lowercase with spaces (e.g., `"does not exist"`)

**Exhaustive matching**: if/elif chains exhaustively check all enum values

**Type hints**: Function signatures use enum as return type or parameter type

### Multi-Outcome Metric Pattern

CloudWatch metrics use enum outcomes to create multiple metric values, only one non-zero:

```python
# All outcomes initialized to 0
self.value_success = 0
self.value_abort_exists = 0
self.value_abort_eni_type = 0
self.value_failure = 0

# Only the matching outcome is set to 1
if outcome == CreateEniMirrorEventOutcome.SUCCESS:
    self.value_success = 1
# ... elif for other outcomes ...
```

This enables CloudWatch metric math and alarming on specific outcomes.

### When to Use
- **Use enums** when: Resource/operation has fixed set of mutually exclusive states
- **Use enums** when: Want type-checked exhaustive matching in callers
- **Use enums** when: State values should be treated as opaque (not compared as strings)
- **Use multi-outcome pattern** when: Emitting metrics for different operation results

### When NOT to Use
- Boolean states (use `bool` instead)
- Open-ended sets of values (use strings)
- States that are better represented as exceptions (e.g., errors)

### Trade-offs
- ✅ **Type safety**: IDEs and type checkers catch invalid states
- ✅ **Exhaustiveness**: Can detect missing enum cases with tools like mypy
- ✅ **Discoverability**: IDE autocomplete shows all possible values
- ✅ **Refactoring**: Renaming enum value updates all usages
- ❌ **Verbosity**: More code than plain strings
- ❌ **Import burden**: Callers must import enum class
- ❌ **String conversion**: Must use `.value` to get string representation

### Related Patterns
- [Service Wrapper Structure](#4-service-wrapper-structure) - Where enums are defined
- [Abstract Base Classes](#11-abstract-base-classes-for-domain-objects) - Enums used with ABC-based metrics

---

## 9. Resource vs Client Interfaces

**[PRIORITY: OBSERVED]** - Implementation detail; most wrappers use client interface exclusively

### Purpose
Choose between boto3 client (low-level API) and resource (high-level, object-oriented API) interfaces based on operation needs.

### Implementation

**Default: Client Interface** - Used in 99% of operations across all service wrappers.

**Exception: S3 Resource Interface** (`s3_interactions.py:102-118`):
```python
def destroy_bucket(bucket_name: str, aws_provider: AwsClientProvider):
    s3_resource = aws_provider.get_s3_resource()  # Resource, not client
    bucket = s3_resource.Bucket(bucket_name)

    # Resource provides Pythonic interface
    if not bucket.creation_date:  # Attribute access
        logger.info(f"S3 Bucket {bucket_name} does not exist")
        return

    # Resource provides higher-level operations
    bucket.objects.all().delete()  # Delete all objects in bucket
    bucket.delete()  # Delete bucket itself
```

**Resource getter in AwsClientProvider** (`aws_client_provider.py:119-122`):
```python
def get_s3_resource(self):
    boto3.setup_default_session(profile_name=self._aws_profile)
    resource = boto3.resource("s3", region_name=self._aws_region)
    return resource
```

### Client vs Resource Decision Matrix

**Use Client when**:
- Fine-grained control over API parameters
- Operation not available in resource interface
- Consistency with other service wrappers (most use client)
- Error handling requires inspecting `ClientError` response

**Use Resource when**:
- Object-oriented access is clearer (e.g., `bucket.objects.all()`)
- Bulk operations on collections (e.g., delete all objects in bucket)
- Pythonic attribute access instead of dictionary keys

### Resource Limitations Observed

**Only S3 has resource interface**: AwsClientProvider only provides `get_s3_resource()`; no other services have resource getters.

**Different session handling**: `get_s3_resource()` uses `boto3.setup_default_session()` + `boto3.resource()` instead of session-based approach used by client getters.

**[TODO: WHY?]** Why does `get_s3_resource()` use `setup_default_session()` instead of the session-based pattern used by client getters? Does this affect role assumption or multi-threading?

### When to Use
- **Use client** when: Default choice for new operations
- **Use client** when: Need consistency across service wrappers
- **Use resource** when: boto3 resource interface significantly simplifies code
- **Use resource** when: Working with collections (e.g., all objects in bucket)

### When NOT to Use
- Resource interface when client interface is needed for specific API parameter
- Resource interface when service doesn't support it (most AWS services)
- Client interface when resource interface makes code dramatically simpler

### Trade-offs
- ✅ **Client: Consistency**: All service wrappers use same pattern
- ✅ **Client: Completeness**: Access to all API parameters
- ✅ **Resource: Simplicity**: Higher-level abstractions (e.g., `bucket.objects.all().delete()`)
- ✅ **Resource: Pythonic**: Attribute access instead of dictionary keys
- ❌ **Client: Verbosity**: More code for common operations
- ❌ **Resource: Coverage**: Not available for all services/operations
- ❌ **Resource: Inconsistency**: Different session handling vs client interface

### Related Patterns
- [Factory Pattern](#1-factory-pattern) - Provides both client and resource getters
- [Service Wrapper Structure](#4-service-wrapper-structure) - Where interface choice is made

---

## 10. Logging Patterns

**[PRIORITY: OBSERVED]** - Standard practice, not specific to this architecture

### Purpose
Provide visibility into AWS operations for debugging and operational monitoring.

### Implementation

**Module-level logger initialization** (all service wrappers):
```python
import logging
logger = logging.getLogger(__name__)
```

**Log before AWS operations**:
```python
# Debug level for detailed operations (ssm_operations.py:25)
logger.debug(f"Pulling SSM Parameter {param_name}...")
ssm_client.get_parameter(Name=param_name)

# Info level for significant operations (s3_interactions.py:106)
logger.info(f"Ensuring S3 Bucket {bucket_name} currently exists...")

# Info level for progress updates (destroy_os_domain.py:24-27)
logger.info(f"Destroying OS Domain {domain_name}...")
delete_response = os_client.delete_domain(DomainName=domain_name)
logger.info(f"Destruction in progress.  Beginning wait; this could be a while (15-20 min)...")
```

**Log after AWS operations**:
```python
# Success confirmations (acm_interactions.py:22)
logger.debug("Self-signed certificate successfully imported")

# Completion notifications (destroy_os_domain.py:43)
logger.info(f"OS Domain {domain_name} has been destroyed")
```

**Log conditional outcomes**:
```python
# Early returns (destroy_os_domain.py:19)
logger.info(f"OS Domain {domain_name} does not exist; no need to delete")
return

# Already-exists scenarios (s3_interactions.py:96)
logger.debug(f"Bucket {bucket_name} already exists and is owned by this account")
```

**Log errors before raising**:
```python
# Error scenarios (s3_interactions.py:151-153)
logger.error(f"We ran into an unexpected situation with creating the S3 bucket {bucket_name};"
            + " its ownership status changed unexpectedly. Please try re-running...")
raise CouldntEnsureBucketExists(bucket_name)
```

**Log long-running operations**:
```python
# Polling loops (destroy_os_domain.py:41)
while True:
    time.sleep(10)
    # ... check domain status ...
    logger.info("Waiting a bit more...")
```

### Log Level Guidelines

**Debug**:
- Individual AWS API calls
- Parameter values
- Raw responses (`logger.debug(describe_response)`)
- Granular operation details

**Info**:
- Significant operation start/completion
- Resource existence checks
- Progress updates for long-running operations
- Expected early returns (e.g., resource doesn't exist, nothing to do)

**Error**:
- Unexpected situations before raising exceptions
- Actionable error messages with remediation guidance

### Message Formatting Patterns

**F-strings**: All logging uses f-strings for interpolation

**Resource identification**: Include resource name/ID in message (e.g., `f"S3 Bucket {bucket_name}"`)

**Action clarity**: Use active voice ("Pulling...", "Destroying...", "Deleting...")

**Context for errors**: Explain what happened and what to try (`:151-153` in s3_interactions.py)

### When to Use
- **Use debug** when: Logging granular details useful during troubleshooting
- **Use info** when: Logging significant milestones or state changes
- **Use error** when: Logging actionable errors before raising exceptions
- **Log before operations** when: Operation might fail or take time
- **Log after operations** when: Confirming successful completion

### When NOT to Use
- Excessive debug logging in hot loops (performance impact)
- Logging sensitive data (credentials, PII)
- Error-level logging for expected conditions (use info with early return)

### Trade-offs
- ✅ **Observability**: Clear visibility into operation flow
- ✅ **Debugging**: Detailed context when operations fail
- ✅ **Operational insights**: Progress updates for long-running operations
- ✅ **Consistency**: Predictable logging patterns across wrappers
- ❌ **Performance**: Logging has runtime cost (especially string formatting)
- ❌ **Noise**: Too much debug logging makes important messages hard to find
- ❌ **Maintenance**: Must update log messages when operations change

### Related Patterns
- [Service Wrapper Structure](#4-service-wrapper-structure) - Where loggers are initialized
- [Error Handling](#5-error-handling--custom-exceptions) - Error logging before raising exceptions

---

## 11. Abstract Base Classes for Domain Objects

**[PRIORITY: OBSERVED]** - Domain-specific pattern for events/metrics, not essential to AWS SDK interaction architecture

### Purpose
Define contracts for polymorphic domain objects (events, metrics) with shared structure but varying implementations.

### Implementation

**Pattern**: Use `ABC` with `@abstractmethod` to define required properties.

**Example 1: ArkimeEvent Base Class** (`events_interactions.py:12-44`):
```python
from abc import ABC, abstractmethod

class ArkimeEvent(ABC):
    @classmethod
    def from_event_dict(cls, raw_event: Dict[str, any]):
        detail_dict = raw_event["detail"]
        return cls(**detail_dict)

    @property
    def source(self) -> str:
        return constants.EVENT_SOURCE  # Shared implementation

    @property
    @abstractmethod
    def detail_type(self) -> str:
        pass  # Subclasses must implement

    @property
    @abstractmethod
    def details(self) -> Dict[str, any]:
        pass  # Subclasses must implement

    def __str__(self) -> str:
        event = {"source": self.source, "detail_type": self.detail_type, "details": self.details}
        return json.dumps(event)  # Shared implementation

    def __eq__(self, other: object) -> bool:
        return self.source == other.source and self.detail_type == other.detail_type and self.details == other.details
```

**Concrete Subclass** (`events_interactions.py:46-64`):
```python
class ConfigureIsmEvent(ArkimeEvent):
    def __init__(self, history_days: int, spi_days: int, replicas: int):
        super().__init__()
        self.history_days = history_days
        self.spi_days = spi_days
        self.replicas = replicas

    @property
    def details(self) -> Dict[str, any]:
        return {
            "history_days": self.history_days,
            "spi_days": self.spi_days,
            "replicas": self.replicas,
        }

    @property
    def detail_type(self) -> str:
        return constants.EVENT_DETAIL_TYPE_CONFIGURE_ISM
```

**Example 2: ArkimeEventMetric Base Class** (`cloudwatch_interactions.py:15-40`):
```python
class ArkimeEventMetric(ABC):
    @property
    def namespace(self) -> str:
        return CW_ARKIME_EVENT_NAMESPACE  # Shared implementation

    @property
    def unit(self) -> str:
        return "None"  # Shared implementation

    @property
    @abstractmethod
    def metric_data(self) -> List[Dict[str, any]]:
        pass  # Subclasses must implement

    def __str__(self) -> str:
        metric = {"namespace": self.namespace, "metric_data": self.metric_data}
        return json.dumps(metric)  # Shared implementation

    def __eq__(self, other: object) -> bool:
        return self.namespace == other.namespace and self.metric_data == other.metric_data
```

**Concrete Subclass** (`cloudwatch_interactions.py:46-87`):
```python
class ConfigureIsmEventMetrics(ArkimeEventMetric):
    def __init__(self, cluster_name: str, outcome: ConfigureIsmEventOutcome):
        super().__init__()
        self.cluster_name = cluster_name
        # ... set outcome values based on enum ...

    @property
    def metric_data(self) -> List[Dict[str, any]]:
        # Builds list of metric dictionaries with dimensions
        shared_dimensions = {
            "Dimensions": [
                {"Name": "ClusterName", "Value": self.cluster_name},
                {"Name": "EventType", "Value": self.event_type},
            ]
        }
        # ... create metrics for each outcome ...
        return [metric_success, metric_abort_failure]
```

### ABC Usage Patterns

**Abstract properties**: Use `@property` + `@abstractmethod` for required data

**Shared implementations**: Common logic in base class (e.g., `__str__()`, `__eq__()`)

**Polymorphic functions**: Functions accept base class, work with any subclass:
```python
def put_events(events: List[ArkimeEvent], event_bus_arn: str, aws_client_provider: AwsClientProvider):
    # Works with ConfigureIsmEvent, CreateEniMirrorEvent, DestroyEniMirrorEvent, etc.
    event_entries = [
        {
            'Source': event.source,  # Uses abstract property
            'DetailType': event.detail_type,  # Uses abstract property
            'Detail': json.dumps(event.details),  # Uses abstract property
        }
        for event in events
    ]
```

**Class method factories**: `from_event_dict()` enables construction from dictionaries

### When to Use
- **Use ABC** when: Multiple domain objects share structure but differ in details
- **Use ABC** when: Functions should accept any subclass polymorphically
- **Use ABC** when: Shared behavior (e.g., serialization) should be implemented once
- **Use `@abstractmethod`** when: Subclass must implement method/property

### When NOT to Use
- Simple data containers (use dataclasses instead)
- No polymorphism needed (subclasses used independently)
- Shared structure is minimal (not worth ABC complexity)

### Trade-offs
- ✅ **Polymorphism**: Functions work with any subclass
- ✅ **Code reuse**: Shared logic in base class
- ✅ **Contracts**: Subclasses must implement abstract members
- ✅ **Type safety**: Type hints use base class for polymorphic parameters
- ❌ **Complexity**: More abstract than dataclasses or plain classes
- ❌ **Learning curve**: Requires understanding ABC, properties, inheritance
- ❌ **Boilerplate**: Each subclass repeats property implementations

### Related Patterns
- [Enum-Based Status](#8-enum-based-status-classification) - Enums used with ABC metrics
- [Service Wrapper Structure](#4-service-wrapper-structure) - Where ABCs are defined

---

## Summary of Key Implementation Patterns

**Factory & Dependency Injection**:
- AwsClientProvider centralizes boto3 client creation
- Service wrappers accept provider via dependency injection
- Supports cross-account role assumption and multiple credential modes

**Error Handling**:
- Map boto3 ClientError to domain-specific exceptions
- Inspect error codes via response dictionary or string matching
- Use early returns for expected "error" conditions

**Data Structures**:
- Dataclasses for structured return values
- Enums for fixed state classifications
- ABCs for polymorphic domain objects

**Pagination & Boto3**:
- Manual NextToken loops for most operations
- boto3 paginators where available (S3)
- Client interface by default, resource for specific use cases (S3 bucket deletion)

**Code Organization**:
- Module-level functions (not classes) for service wrappers
- No inter-service dependencies
- Full type hints throughout
- Module-level logger for each wrapper

---

