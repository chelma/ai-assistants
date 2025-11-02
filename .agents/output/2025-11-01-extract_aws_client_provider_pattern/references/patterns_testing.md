## Testing Patterns

**Source**: aws-aio test suite (10 test files, 1,687 lines)
**Coverage**: 1:1 test-to-implementation parity
**Last Updated**: 2025-11-01 (Iteration 2 - Testing Patterns)

This section documents testing patterns observed across the comprehensive test suite.

### Pattern Categories

12. [Test Naming Convention](#12-test-naming-convention)
13. [Mocking AwsClientProvider](#13-mocking-awsclientprovider)
14. [Mocking boto3 Clients](#14-mocking-boto3-clients)
15. [Test Structure (AAA Pattern)](#15-test-structure-aaa-pattern)
16. [Assertion Patterns](#16-assertion-patterns)
17. [Error Scenario Testing](#17-error-scenario-testing)
18. [Pagination Testing](#18-pagination-testing)
19. [Multi-Scenario Testing](#19-multi-scenario-testing)
20. [Side Effects for Sequential Calls](#20-side-effects-for-sequential-calls)
21. [Patching Strategies](#21-patching-strategies)
22. [Testing Domain Objects (ABCs)](#22-testing-domain-objects-abcs)

---

## 12. Test Naming Convention

**[PRIORITY: OBSERVED]** - Standard per the `python-style` guide Claude Skill, not core to testing architecture

### Purpose
Provide descriptive, searchable test names that clearly communicate test intent.

### Implementation

**Convention**: `test_WHEN_<action>_called_AND_<condition>_THEN_<expected_result>`

**Examples from test files**:
```python
# Simple case (test_s3_interactions.py:9)
def test_WHEN_get_bucket_status_called_THEN_as_expected():

# With condition (test_ec2_interactions.py:37)
def test_WHEN_get_subnets_of_vpc_called_AND_doesnt_exist_THEN_raises():

# Multiple conditions (test_aws_client_provider.py:12)
def test_WHEN_get_session_called_AND_aws_compute_not_assume_THEN_as_expected():

# Edge case (test_ec2_interactions.py:135)
def test_WHEN_get_enis_of_subnet_called_AND_no_enis_THEN_empty_list():
```

### Convention Breakdown

**`WHEN_<action>_called`**: Describes the function/operation being tested
- `get_bucket_status_called`
- `destroy_s3_bucket_called`
- `put_event_metrics_called`

**`AND_<condition>`** (optional): Specifies test scenario/precondition
- `AND_exists` (resource exists)
- `AND_doesnt_exist` (resource missing)
- `AND_aws_compute_not_assume` (configuration state)
- `AND_no_enis` (empty result case)
- `AND_happy_path` (success scenario)

**`THEN_<expected_result>`**: States expected outcome
- `THEN_as_expected` (normal success)
- `THEN_raises` (exception expected)
- `THEN_destroys_it` (action completed)
- `THEN_empty_list` (specific return value)
- `THEN_skips_destruction` (conditional behavior)

### When to Use
- **Use this convention** when: Writing tests for service wrapper functions
- **Use descriptive names** when: Test scenarios are complex or have preconditions
- **Use `as_expected`** when: Multiple assertions verify standard behavior
- **Use specific outcomes** when: Single clear expected result (e.g., `raises`, `empty_list`)

### When NOT to Use
- Very simple unit tests where function name is self-explanatory
- Tests following different project conventions

### Trade-offs
- ✅ **Searchability**: Easy to find tests for specific scenarios
- ✅ **Readability**: Test intent clear from name alone
- ✅ **Consistency**: Predictable naming across test suite
- ✅ **Documentation**: Test names document behavior
- ❌ **Verbosity**: Names can be very long
- ❌ **Rigidity**: Convention must be followed consistently to be useful

### Related Patterns
- [Multi-Scenario Testing](#19-multi-scenario-testing) - Multiple tests with varying `AND` conditions
- [Test Structure](#15-test-structure-aaa-pattern) - How test bodies are organized

---

## 13. Mocking AwsClientProvider

**[PRIORITY: CRITICAL]** - Core testing pattern enabling dependency injection testing strategy

### Purpose
Enable testing service wrapper functions by mocking the provider and controlling boto3 client behavior.

### Implementation

**Pattern**: Create mock provider that returns mock boto3 client.

**Example 1: Basic provider mock** (test_s3_interactions.py:10-14):
```python
# Set up our mock
mock_s3_client = mock.Mock()

mock_aws_provider = mock.Mock()
mock_aws_provider.get_s3.return_value = mock_s3_client

# Function under test calls aws_provider.get_s3()
actual_value = s3.get_bucket_status("bucket-name", mock_aws_provider)
```

**Example 2: Multiple getter methods** (test_events_interactions.py:8-12):
```python
mock_events_client = mock.Mock()

mock_aws_provider = mock.Mock()
mock_aws_provider.get_events.return_value = mock_events_client

events.put_events(test_events, "bus-1", mock_aws_provider)
```

**Example 3: Provider with get_aws_env** (test_s3_interactions.py:39-43):
```python
mock_s3_client = mock.Mock()
test_env = AwsEnvironment("XXXXXXXXXXX", "my-region-1", "profile")

mock_aws_provider = mock.Mock()
mock_aws_provider.get_s3.return_value = mock_s3_client
mock_aws_provider.get_aws_env.return_value = test_env
```

### Provider Getter Methods Mocked

**Most common**:
- `get_s3()` - S3 tests
- `get_ec2()` - EC2 tests
- `get_ssm()` - SSM tests
- `get_iam()` - IAM tests
- `get_ecs()` - ECS tests
- `get_acm()` - ACM tests
- `get_opensearch()` - OpenSearch tests
- `get_cloudwatch()` - CloudWatch tests
- `get_events()` - EventBridge tests

**Less common**:
- `get_aws_env()` - When function needs account/region context
- `get_sts()` - For provider's own tests

### When to Use
- **Use mock provider** when: Testing service wrapper functions
- **Mock getter method** when: Function calls specific AWS service
- **Mock get_aws_env()** when: Function uses account/region information

### When NOT to Use
- Testing AwsClientProvider itself (use boto3.Session mocking instead)
- Integration tests (use real provider with test AWS account)

### Trade-offs
- ✅ **Isolation**: No actual AWS calls
- ✅ **Speed**: Tests run instantly
- ✅ **Control**: Precise control over client behavior
- ✅ **Simplicity**: Standard mock.Mock() pattern
- ❌ **Not real**: Won't catch boto3 API changes
- ❌ **Mock drift**: Mocks may diverge from real boto3 behavior

### Related Patterns
- [Mocking boto3 Clients](#14-mocking-boto3-clients) - What provider returns
- [Patching Strategies](#21-patching-strategies) - Alternative to mocking provider

---

## 14. Mocking boto3 Clients

**[PRIORITY: CRITICAL]** - Core pattern for testing AWS SDK interactions without making real API calls

### Purpose
Control boto3 client behavior to test different AWS API responses and errors.

### Implementation

**Pattern 1: Return value mocking**:
```python
# Simple return value (test_ssm_operations.py:12-13)
mock_ssm_client = mock.Mock()
mock_ssm_client.get_parameter.return_value = {"Parameter": {"Value": "param"}}

# Nested response structure (test_ec2_interactions.py:56-75)
mock_ec2_client.describe_instances.return_value = {
    "Reservations": [{
        "Instances": [{
            "NetworkInterfaces": [
                {
                    "NetworkInterfaceId": "eni-1",
                    "SubnetId": "subnet-1",
                    "VpcId": "vpc-1",
                    "InterfaceType": "type-1"
                }
            ]
        }]
    }]
}
```

**Pattern 2: Side effects for multiple calls** (test_ec2_interactions.py:11-18):
```python
mock_ec2_client.describe_subnets.side_effect = [
    {
        "Subnets": [{"SubnetId": "subnet-1"}, {"SubnetId": "subnet-2"}],
        "NextToken": "next-1",  # First call returns NextToken
    },
    {
        "Subnets": [{"SubnetId": "subnet-3"}, {"SubnetId": "subnet-4"}],
        # Second call omits NextToken (pagination complete)
    }
]
```

**Pattern 3: Exception side effects** (test_s3_interactions.py:22-24):
```python
mock_s3_client.head_bucket.side_effect = ClientError(
    error_response={"Error": {"Code": "403", "Message": "Forbidden"}},
    operation_name=""
)
```

**Pattern 4: Mixed side effects** (test_iam_interactions.py:15-18):
```python
mock_iam_client.get_role.side_effect = [
    {"response": []},  # First call succeeds
    ClientError(...),  # Second call raises
    ExpectedException()  # Third call raises different exception
]
```

### boto3 Response Structures

Tests replicate actual boto3 response structures:

**Pagination responses**:
- Include `NextToken` key in first response(s)
- Omit `NextToken` in final response
- Maintain consistent structure across pages

**List/describe responses**:
- Top-level key matches operation (`"Subnets"`, `"Parameters"`, `"Vpcs"`)
- Empty lists for "not found" scenarios
- Nested structures match boto3 documentation

**Success responses**:
- Include all keys that implementation accesses
- Realistic values for IDs, ARNs, names

### When to Use
- **Use return_value** when: Single call or all calls return same response
- **Use side_effect list** when: Multiple calls with different responses (pagination, changing state)
- **Use side_effect exception** when: Testing error handling
- **Match boto3 structure** when: Implementation accesses nested response keys

### When NOT to Use
- Testing actual boto3 behavior (use integration tests)
- When response structure is so complex that mocking becomes fragile

### Trade-offs
- ✅ **Precise control**: Exact responses for each scenario
- ✅ **Error injection**: Easy to simulate AWS errors
- ✅ **Pagination simulation**: Test pagination logic without AWS calls
- ❌ **Maintenance**: Must update mocks when boto3 responses change
- ❌ **Verbosity**: Complex responses require many lines
- ❌ **Coupling**: Tests coupled to boto3 response structure

### Related Patterns
- [Side Effects for Sequential Calls](#20-side-effects-for-sequential-calls) - Detailed side_effect patterns
- [Pagination Testing](#18-pagination-testing) - Using side_effect for pagination
- [Error Scenario Testing](#17-error-scenario-testing) - Exception side effects

---

## 15. Test Structure (AAA Pattern)

**[PRIORITY: OBSERVED]** - Standard testing practice, not specific to AWS SDK testing architecture

### Purpose
Organize test code into clear sections: Arrange (setup), Act (execute), Assert (verify).

### Implementation

**Standard structure** observed across all tests:

```python
def test_WHEN_something_happens_THEN_expected_result():
    # Set up our mock (ARRANGE)
    mock_client = mock.Mock()
    mock_client.some_method.return_value = {"data": "value"}

    mock_provider = mock.Mock()
    mock_provider.get_service.return_value = mock_client

    # Run our test (ACT)
    result = function_under_test("arg", mock_provider)

    # Check our results (ASSERT)
    expected_calls = [
        mock.call(Param="arg")
    ]
    assert expected_calls == mock_client.some_method.call_args_list

    expected_result = "value"
    assert expected_result == result
```

### Section Markers

**Comment markers** explicitly label sections:
- `# Set up our mock` - Arrange section
- `# Run our test` - Act section
- `# Check our results` - Assert section

**Alternative markers**:
- `# TEST: <scenario description>` - For multi-scenario tests (test_s3_interactions.py:16-34)

### Arrange Section Patterns

**Mock creation order**:
1. Create deepest mocks first (boto3 clients)
2. Configure mock behavior (return_value, side_effect)
3. Create provider mock
4. Wire up provider getter methods
5. Create any test data (AwsEnvironment, domain objects, etc.)

**Example** (test_s3_interactions.py:38-43):
```python
# Set up our mock
mock_s3_client = mock.Mock()  # 1. boto3 client mock
test_env = AwsEnvironment("XXXXXXXXXXX", "my-region-1", "profile")  # 5. Test data

mock_aws_provider = mock.Mock()  # 3. Provider mock
mock_aws_provider.get_s3.return_value = mock_s3_client  # 4. Wire up
```

### Act Section Patterns

**Single line** execution:
```python
# Run our test
result = s3.get_bucket_status("bucket-name", mock_aws_provider)
```

**Multi-line** for complex setup:
```python
# Run our test
test_eni = ec2i.NetworkInterface("vpc-1", "subnet-1", "eni-1", "type-1")
result = ec2i.mirror_eni(test_eni, "target-1", "filter-1", "vpc-1", mock_aws_provider)
```

### Assert Section Patterns

**Call verification** (most common):
```python
# Check our results
expected_calls = [
    mock.call(Param1="value1", Param2="value2")
]
assert expected_calls == mock_client.method.call_args_list
```

**Return value verification**:
```python
expected_result = "expected-value"
assert expected_result == result
```

**Multiple assertions**:
```python
# Check our results
assert expected_calls == mock_client.method.call_args_list
assert expected_result == result
assert mock.call_count == 3
```

### When to Use
- **Use AAA pattern** when: Writing all tests (universal pattern)
- **Use comment markers** when: Test has clear sections
- **Arrange mocks bottom-up** when: Creating mock hierarchies
- **Single assert per concept** when: Verifying multiple aspects

### When NOT to Use
- Very simple tests where sections are obvious
- Parameterized tests with different structure

### Trade-offs
- ✅ **Readability**: Clear test structure
- ✅ **Consistency**: Predictable layout across tests
- ✅ **Maintainability**: Easy to modify specific sections
- ✅ **Documentation**: Comments explain intent
- ❌ **Verbosity**: Comments add lines
- ❌ **Rigidity**: Must follow structure even for simple tests

### Related Patterns
- [Assertion Patterns](#16-assertion-patterns) - Assert section details
- [Multi-Scenario Testing](#19-multi-scenario-testing) - Multiple ACT/ASSERT pairs in one test

---

## 16. Assertion Patterns

**[PRIORITY: PREFERRED]** - Important for verification strategy but standard pytest patterns

### Purpose
Verify function behavior comprehensively and clearly.

### Implementation

**Pattern 1: Call argument verification** (most common):

```python
# Check boto3 method was called with expected arguments
expected_calls = [
    mock.call(Bucket="bucket-name", Key="key-name")
]
assert expected_calls == mock_s3_client.put_object.call_args_list
```

**Pattern 2: Multiple calls verification** (test_ec2_interactions.py:28-32):
```python
expected_describe_calls = [
    mock.call(Filters=[{"Name": "vpc-id", "Values": ["my-vpc"]}]),
    mock.call(Filters=[{"Name": "vpc-id", "Values": ["my-vpc"]}], NextToken="next-1"),
]
assert expected_describe_calls == mock_ec2_client.describe_subnets.call_args_list
```

**Pattern 3: Return value equality**:
```python
expected_result = ["subnet-1", "subnet-2", "subnet-3", "subnet-4"]
assert expected_result == result
```

**Pattern 4: Dataclass equality** (test_ec2_interactions.py:89-92):
```python
expected_result = [
    ec2i.NetworkInterface("vpc-1", "subnet-1", "eni-1", "type-1"),
    ec2i.NetworkInterface("vpc-1", "subnet-1", "eni-2", "type-2"),
]
assert expected_result == result
```

**Pattern 5: Call count verification** (test_s3_interactions.py:110-111):
```python
assert 1 == mock_objects_all.delete.call_count
assert 1 == mock_bucket.delete.call_count
```

**Pattern 6: Boolean assertions** (test_iam_interactions.py:26, 30):
```python
assert True == actual_value  # Explicit True check
assert False == actual_value  # Explicit False check
```

**Pattern 7: Negation assertions** (test_s3_interactions.py:139-140):
```python
assert not mock_objects_all.delete.called
assert not mock_bucket.delete.called
```

**Pattern 8: Complex structure assertions** (test_cloudwatch_interactions.py:16-54):
```python
expected_metric_data = [
    {
        "MetricName": cwi.CreateEniMirrorEventOutcome.SUCCESS.value,
        "Value": 1,
        "Dimensions": [
            {"Name": "ClusterName", "Value": "cluster-1"},
            {"Name": "VpcId", "Value": "vpc-1"},
        ]
    },
    # ... more metric dictionaries ...
]
assert expected_metric_data == actual_value.metric_data
```

### Assertion Ordering

**Convention**: Expected value on left, actual on right
```python
assert expected_value == actual_value  # Consistent across all tests
```

### Call Argument List Patterns

**mock.call() usage**:
- Named arguments: `mock.call(Bucket="name", Key="key")`
- Positional arguments: `mock.call("arg1", "arg2")`
- Mix: `mock.call("positional", Keyword="value")`

**call_args_list**:
- Returns list of mock.call objects
- Empty list `[]` when not called
- Verify exact call sequence

### When to Use
- **Use call verification** when: Verifying boto3 API calls
- **Use return value assertions** when: Checking function output
- **Use call_count** when: Number of calls matters (idempotency, loops)
- **Use negation** when: Verifying method NOT called (early returns, conditional logic)
- **Use complex structures** when: Verifying dataclass properties or nested data

### When NOT to Use
- Asserting on mock internals not part of contract
- Multiple assertions that should be separate tests

### Trade-offs
- ✅ **Explicit**: Expected values clearly stated
- ✅ **Precise**: Exact argument matching
- ✅ **Comprehensive**: Can verify multiple aspects
- ✅ **Clear failures**: Assertion errors show expected vs actual
- ❌ **Brittle**: Argument order changes break tests
- ❌ **Verbose**: Large expected structures take many lines

### Related Patterns
- [Side Effects for Sequential Calls](#20-side-effects-for-sequential-calls) - Multiple call verification
- [Test Structure](#15-test-structure-aaa-pattern) - Where assertions appear

---

## 17. Error Scenario Testing

**[PRIORITY: CRITICAL]** - Essential pattern for testing error handling and custom exception mapping

### Purpose
Verify service wrappers properly handle AWS errors and raise domain-specific exceptions.

### Implementation

**Pattern 1: pytest.raises with custom exception** (test_ec2_interactions.py:50-51):
```python
with pytest.raises(ec2i.VpcDoesNotExist):
    result = ec2i.get_subnets_of_vpc("my-vpc", mock_aws_provider)
```

**Pattern 2: pytest.raises with boto3 ClientError** (test_s3_interactions.py:33-34):
```python
with pytest.raises(ClientError):
    actual_value = s3.get_bucket_status("bucket-name", mock_aws_provider)
```

**Pattern 3: Exception side_effect setup** (test_ssm_operations.py:33-35):
```python
mock_ssm_client.get_parameter.side_effect = [
    ClientError(error_response={"Error": {"Code": "ParameterNotFound"}}, operation_name="")
]

with pytest.raises(ssm.ParamDoesNotExist):
    ssm.get_ssm_param_value("my-param", mock_aws_provider)
```

**Pattern 4: Testing exception swallowing** (test_s3_interactions.py:70-72):
```python
mock_s3_client.create_bucket.side_effect = ClientError(
    error_response={"Error": {"Message": "BucketAlreadyOwnedByYou"}},
    operation_name=""
)
s3.create_bucket("bucket-name", mock_aws_provider)
assert True  # The ClientError was swallowed
```

### ClientError Construction

**Standard pattern**:
```python
ClientError(
    error_response={"Error": {"Code": "ErrorCode", "Message": "Description"}},
    operation_name=""
)
```

**Error codes tested**:
- **S3**: `"403"`, `"404"`, `"500"`, `"NoSuchBucket"`, `"BucketAlreadyExists"`, `"NoSuchKey"`
- **EC2**: `"InvalidTrafficMirrorSessionId.NotFound"`
- **SSM**: `"ParameterNotFound"`
- **IAM**: `"NoSuchEntity"`
- **OpenSearch**: `"ResourceNotFoundException"`

### Testing Error Mapping

Tests verify boto3 ClientError → domain exception mapping:

**Example** (test_ec2_interactions.py:228-240):
```python
# Setup: boto3 raises ClientError with specific code
mock_ec2_client.delete_traffic_mirror_session.side_effect = [
    ClientError(error_response={"Error": {"Code": "InvalidTrafficMirrorSessionId.NotFound"}},
                operation_name="")
]

# Assert: wrapper raises domain exception
with pytest.raises(ec2i.MirrorDoesntExist):
    ec2i.delete_eni_mirroring("session-1", mock_aws_provider)
```

### When to Use
- **Use pytest.raises** when: Function should raise exception
- **Use ClientError** when: Testing boto3 error handling
- **Test error codes** when: Implementation inspects error code
- **Test error swallowing** when: Implementation catches and handles errors gracefully

### When NOT to Use
- Testing exceptions unrelated to AWS errors
- When function shouldn't raise (test successful path instead)

### Trade-offs
- ✅ **Coverage**: Verifies error handling paths
- ✅ **Correctness**: Ensures domain exceptions raised
- ✅ **Realistic**: Uses actual boto3 exception types
- ✅ **Complete**: Tests both error detection and exception mapping
- ❌ **Maintenance**: Must update if boto3 error codes change
- ❌ **Complexity**: Requires understanding boto3 error structure

### Related Patterns
- [Side Effects for Sequential Calls](#20-side-effects-for-sequential-calls) - Exception in sequence
- [Multi-Scenario Testing](#19-multi-scenario-testing) - Error scenarios alongside success

---

## 18. Pagination Testing

**[PRIORITY: CRITICAL]** - Essential for verifying pagination implementation correctness

### Purpose
Verify service wrappers correctly handle AWS API pagination with NextToken.

### Implementation

**Pattern**: Use side_effect with list of responses, first response(s) include NextToken, final omits it.

**Example 1: EC2 subnet pagination** (test_ec2_interactions.py:11-35):
```python
mock_ec2_client.describe_subnets.side_effect = [
    {
        "Subnets": [{"SubnetId": "subnet-1"}, {"SubnetId": "subnet-2"}],
        "NextToken": "next-1",  # Indicates more pages
    },
    {
        "Subnets": [{"SubnetId": "subnet-3"}, {"SubnetId": "subnet-4"}],
        # No NextToken - pagination complete
    }
]

result = ec2i.get_subnets_of_vpc("my-vpc", mock_aws_provider)

# Verify both pages were requested
expected_describe_calls = [
    mock.call(Filters=[{"Name": "vpc-id", "Values": ["my-vpc"]}]),
    mock.call(Filters=[{"Name": "vpc-id", "Values": ["my-vpc"]}], NextToken="next-1"),
]
assert expected_describe_calls == mock_ec2_client.describe_subnets.call_args_list

# Verify results from both pages accumulated
expected_result = ["subnet-1", "subnet-2", "subnet-3", "subnet-4"]
assert expected_result == result
```

**Example 2: SSM parameter pagination** (test_ssm_operations.py:71-92):
```python
mock_ssm_client.get_parameters_by_path.side_effect = [
    {"Parameters": [{"k1": "v1"}, {"k2": "v2"}], "NextToken": "1234"},
    {"Parameters": [{"k3": "v3"}]},  # Final page, no NextToken
]

actual_value = ssm.get_ssm_params_by_path("/the/path", mock_aws_provider)

expected_get_calls = [
    mock.call(Path="/the/path", Recursive=False),
    mock.call(Path="/the/path", Recursive=False, NextToken="1234"),
]
assert expected_get_calls == mock_ssm_client.get_parameters_by_path.call_args_list

expected_value = [
    {"k1": "v1"}, {"k2": "v2"}, {"k3": "v3"}  # All pages combined
]
assert expected_value == actual_value
```

**Example 3: boto3 paginator testing** (test_s3_interactions.py:222-258):
```python
mock_paginator = mock.Mock()
mock_s3_client.get_paginator.return_value = mock_paginator

page_1 = {
    "Contents": [
        {"Key": "prefix/file1.txt", "LastModified": "2021-01-01T12:00:00"},
        {"Key": "prefix/file2.txt", "LastModified": "2021-01-02T12:00:00"}
    ]
}
page_2 = {
    "Contents": [
        {"Key": "prefix/file3.txt", "LastModified": "2021-01-03T12:00:00"}
    ]
}
mock_paginator.paginate.return_value = [page_1, page_2]

result = s3.list_bucket_objects("my-bucket", mock_aws_provider, prefix="prefix")

expected_result = [
    {"key": "prefix/file1.txt", "date_modified": "2021-01-01T12:00:00"},
    {"key": "prefix/file2.txt", "date_modified": "2021-01-02T12:00:00"},
    {"key": "prefix/file3.txt", "date_modified": "2021-01-03T12:00:00"},
]
assert expected_result == result
```

### Verification Strategy

**Verify call sequence**:
- First call has no NextToken parameter
- Subsequent calls include NextToken from previous response
- Exact number of calls matches number of side_effect responses

**Verify result accumulation**:
- Results from all pages combined
- Correct order maintained
- No duplicates

### When to Use
- **Use side_effect list** when: Testing manual NextToken pagination
- **Use paginator mock** when: Testing boto3 paginator usage
- **Test 2+ pages** when: Verifying pagination logic (not just first page)

### When NOT to Use
- Functions that don't paginate
- When single page is sufficient to test core logic

### Trade-offs
- ✅ **Realistic**: Simulates actual AWS pagination behavior
- ✅ **Complete**: Tests pagination loop logic
- ✅ **Correct**: Verifies NextToken passed correctly
- ❌ **Complexity**: Requires multiple mock responses
- ❌ **Fragile**: Breaks if pagination logic changes

### Related Patterns
- [Side Effects for Sequential Calls](#20-side-effects-for-sequential-calls) - Pagination uses this
- [Mocking boto3 Clients](#14-mocking-boto3-clients) - Response structure details

---

## 19. Multi-Scenario Testing

**[PRIORITY: OBSERVED]** - Test organization technique, not architecturally significant

### Purpose
Test multiple related scenarios in a single test function to reduce boilerplate.

### Implementation

**Pattern**: Single test function with multiple TEST sections, each with ACT + ASSERT.

**Example 1: S3 bucket status** (test_s3_interactions.py:9-34):
```python
def test_WHEN_get_bucket_status_called_THEN_as_expected():
    # Set up our mock (SHARED ARRANGE)
    mock_s3_client = mock.Mock()
    mock_aws_provider = mock.Mock()
    mock_aws_provider.get_s3.return_value = mock_s3_client

    # TEST: Bucket exists and we have access to it
    mock_s3_client.head_bucket.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
    actual_value = s3.get_bucket_status("bucket-name", mock_aws_provider)
    assert actual_value == s3.BucketStatus.EXISTS_HAVE_ACCESS

    # TEST: Bucket exists but we don't have access to it
    mock_s3_client.head_bucket.side_effect = ClientError(...)
    actual_value = s3.get_bucket_status("bucket-name", mock_aws_provider)
    assert actual_value == s3.BucketStatus.EXISTS_NO_ACCESS

    # TEST: Bucket does not exist
    mock_s3_client.head_bucket.side_effect = ClientError(...)
    actual_value = s3.get_bucket_status("bucket-name", mock_aws_provider)
    assert actual_value == s3.BucketStatus.DOES_NOT_EXIST

    # TEST: Unexpected error
    mock_s3_client.head_bucket.side_effect = ClientError(...)
    with pytest.raises(ClientError):
        actual_value = s3.get_bucket_status("bucket-name", mock_aws_provider)
```

**Example 2: ECS deployment status** (test_ecs_interactions.py:24-62):
```python
def test_WHEN_is_deployment_in_progress_called_THEN_as_expected():
    mock_ecs_client = mock.Mock()
    mock_aws_provider = mock.Mock()
    mock_aws_provider.get_ecs.return_value = mock_ecs_client

    # TEST: Deployment is in progress
    mock_ecs_client.describe_services.return_value = {
        "services": [{"deployments": [{"rolloutState": "IN_PROGRESS"}]}]
    }
    result = ecsi.is_deployment_in_progress("cluster", "service", mock_aws_provider)
    assert True == result

    # TEST: Deployment is not in progress
    mock_ecs_client.describe_services.return_value = {
        "services": [{"deployments": [{"rolloutState": "COMPLETED"}]}]
    }
    result = ecsi.is_deployment_in_progress("cluster", "service", mock_aws_provider)
    assert False == result
```

**Example 3: IAM role existence** (test_iam_interactions.py:24-34):
```python
# TEST: Role does exist
actual_value = iami.does_iam_role_exist("role", mock_provider)
assert True == actual_value

# TEST: Role does not exist
actual_value = iami.does_iam_role_exist("role", mock_provider)
assert False == actual_value

# TEST: Unexpected error
with pytest.raises(ExpectedException):
    iami.does_iam_role_exist("role", mock_provider)
```

### Multi-Scenario Structure

**Shared ARRANGE section** at top:
- Mock setup used by all scenarios
- Provider wiring

**Multiple TEST sections**:
- Comment: `# TEST: <scenario description>`
- Mock configuration for specific scenario
- Function call (ACT)
- Assertions (ASSERT)

### Scenario Variations

**Common patterns**:
- Success vs error cases
- Different error codes
- Empty vs populated results
- True vs False returns
- Different enum values
- Edge cases (boundary conditions)

### When to Use
- **Use multi-scenario** when: Testing related scenarios with same setup
- **Use multi-scenario** when: Enum-based returns or multiple success paths
- **Separate tests** when: Scenarios need different mock setup
- **Separate tests** when: Scenarios test different functions

### When NOT to Use
- Scenarios require complex different setups
- Unrelated scenarios (violates single responsibility)
- When test becomes too long/hard to follow

### Trade-offs
- ✅ **Reduced boilerplate**: Shared mock setup
- ✅ **Related scenarios grouped**: Easier to see all cases
- ✅ **Less duplication**: Mock configuration not repeated
- ❌ **Test independence**: Scenarios share state (mocks)
- ❌ **Failure clarity**: One scenario failure may affect others
- ❌ **Length**: Tests can become very long

### Related Patterns
- [Test Structure](#15-test-structure-aaa-pattern) - Modified AAA with multiple ACT/ASSERT
- [Side Effects for Sequential Calls](#20-side-effects-for-sequential-calls) - Enables multi-scenario

---

## 20. Side Effects for Sequential Calls

**[PRIORITY: PREFERRED]** - Important mocking technique that enables CRITICAL patterns (pagination, error testing)

### Purpose
Simulate different behaviors across multiple calls to the same mocked method.

### Implementation

**Pattern**: `side_effect` with list of return values or exceptions.

**Example 1: Sequential return values** (test_iam_interactions.py:15-18):
```python
mock_iam_client.get_role.side_effect = [
    {"response": []},  # First call returns successfully
    ClientError(...),  # Second call raises ClientError
    ExpectedException()  # Third call raises different exception
]

# First call succeeds
actual_value = iami.does_iam_role_exist("role", mock_provider)

# Second call raises ClientError
actual_value = iami.does_iam_role_exist("role", mock_provider)

# Third call raises ExpectedException
with pytest.raises(ExpectedException):
    iami.does_iam_role_exist("role", mock_provider)
```

**Example 2: Pagination with NextToken** (test_ec2_interactions.py:98-112):
```python
mock_ec2_client.describe_network_interfaces.side_effect = [
    {
        "NetworkInterfaces": [...],
        "NextToken": "next-1",  # First page
    },
    {
        "NetworkInterfaces": [...],  # Second page, no NextToken
    }
]
```

**Example 3: Exhaustion sentinel** (test_aws_client_provider.py:18):
```python
mock_session_cls.side_effect = [mock_session, FailedTest()]

# First call uses mock_session
test_client = aws_provider.get_acm()

# If called again, raises FailedTest (catches unexpected calls)
```

**Example 4: Polling loop** (test_destroy_os_domain.py:11-16):
```python
mock_os_client.describe_domain.side_effect = [
    {},  # Initial check: exists
    {},  # Wait once: still exists
    {},  # Wait twice: still exists
    ClientError(...)  # Finally destroyed (ResourceNotFoundException)
]
```

### Side Effect Types

**List of values**: Each call consumes next item in list
```python
side_effect = [response1, response2, response3]
```

**List with exceptions**: Mix return values and exceptions
```python
side_effect = [response, ClientError(...), response]
```

**Single exception**: Always raises
```python
side_effect = ClientError(...)
```

**Callable**: Dynamic behavior
```python
side_effect = lambda param: {"result": param}
```

### Exhaustion Pattern

**FailedTest sentinel** (test_aws_client_provider.py:7-9):
```python
class FailedTest(Exception):
    def __init__(self):
        super().__init__("This should not have been raised")
```

**Usage**: Place at end of side_effect list to catch unexpected extra calls
```python
side_effect = [expected_response, FailedTest()]
```

### When to Use
- **Use side_effect list** when: Testing pagination or state changes
- **Use exception in list** when: Testing error recovery
- **Use exhaustion sentinel** when: Verifying exact number of calls
- **Use callable** when: Response depends on call arguments

### When NOT to Use
- All calls return same value (use return_value instead)
- Complex stateful behavior (use custom mock class)

### Trade-offs
- ✅ **Sequential behavior**: Different responses per call
- ✅ **Stateful testing**: Simulate state changes
- ✅ **Pagination simulation**: Natural pagination testing
- ✅ **Call count verification**: List length enforces exact calls
- ❌ **Order dependency**: Must match exact call sequence
- ❌ **Fragility**: Extra/missing calls break test
- ❌ **Unclear**: Not obvious from code what each item represents

### Related Patterns
- [Pagination Testing](#18-pagination-testing) - Primary use case
- [Multi-Scenario Testing](#19-multi-scenario-testing) - Different side_effect per scenario
- [Error Scenario Testing](#17-error-scenario-testing) - Exception in side_effect list

---

## 21. Patching Strategies

**[PRIORITY: PREFERRED]** - Useful testing technique but alternative to dependency injection

### Purpose
Replace imports, module-level functions, or attributes during tests without modifying mocks directly.

### Implementation

**Pattern 1: Decorator patching - module functions** (test_s3_interactions.py:142-143):
```python
@mock.patch("aws_interactions.s3_interactions.create_bucket")
@mock.patch("aws_interactions.s3_interactions.get_bucket_status")
def test_WHEN_ensure_bucket_exists_called_THEN_as_expected(mock_get_status, mock_create_bucket):
    # Patches are passed as function arguments in reverse order
    mock_get_status.return_value = s3.BucketStatus.DOES_NOT_EXIST
    mock_create_bucket.side_effect = s3.BucketNameNotAvailable("bucket-name")
```

**Pattern 2: Decorator patching - built-in functions** (test_s3_interactions.py:178):
```python
@mock.patch("aws_interactions.s3_interactions.open")
def test_WHEN_put_file_to_bucket_called_THEN_as_expected(mock_open):
    mock_data = mock.Mock()
    mock_open.return_value.__enter__.return_value = mock_data
```

**Pattern 3: Decorator patching - os.path** (test_s3_interactions.py:306-307):
```python
@mock.patch("aws_interactions.s3_interactions.os.path.exists")
@mock.patch("aws_interactions.s3_interactions.AwsClientProvider")
def test_WHEN_get_object_called_AND_file_exists_THEN_raises(mock_aws_provider, mock_exists):
    mock_exists.side_effect = lambda path: True
```

**Pattern 4: Context manager patching** (test_destroy_os_domain.py:7):
```python
@mock.patch("aws_interactions.destroy_os_domain.time")
def test_WHEN_destroy_os_domain_and_wait_called_AND_exists_THEN_destroys_it(mock_time):
    # Patches time.sleep to avoid actual waiting
    assert 3 == mock_time.sleep.call_count
```

**Pattern 5: Patching boto3.Session** (test_aws_client_provider.py:11):
```python
@mock.patch("aws_interactions.aws_client_provider.boto3.Session")
def test_WHEN_get_session_called_AND_aws_compute_not_assume_THEN_as_expected(mock_session_cls):
    mock_session = mock.Mock()
    mock_session_cls.side_effect = [mock_session, FailedTest()]
```

**Pattern 6: Patching class constructors** (test_acm_interactions.py:32):
```python
@mock.patch("aws_interactions.acm_interactions.SelfSignedCert")
def test_WHEN_upload_default_elb_cert_called_THEN_as_expected(mock_cert_cls):
    mock_cert = mock.Mock()
    mock_cert_cls.return_value = mock_cert
```

### Patch Target Patterns

**Full module path**: `"module.submodule.function"`
- Patch where function is used, not where it's defined
- Example: `"aws_interactions.s3_interactions.open"` (not `"builtins.open"`)

**Reverse parameter order**: Decorators applied bottom-up, parameters top-down
```python
@mock.patch("module.function1")  # Third parameter
@mock.patch("module.function2")  # Second parameter
@mock.patch("module.function3")  # First parameter
def test_name(param3, param2, param1):
    pass
```

### Common Patch Targets

**Built-ins**:
- `open` - File operations
- `os.path.exists` - File existence checks
- `os.path.dirname` - Path manipulation

**Module functions** (to isolate units):
- Other functions in same module
- Dependency functions

**Time/sleep**:
- `time.sleep` - Avoid actual delays
- `time.time` - Control timestamps

**Class constructors**:
- External classes (e.g., `SelfSignedCert`)
- boto3.Session

### When to Use
- **Patch module functions** when: Testing function that calls other module functions
- **Patch built-ins** when: Testing file I/O or system calls
- **Patch time.sleep** when: Testing polling loops
- **Patch class constructors** when: Testing code that instantiates external classes

### When NOT to Use
- Patching too many things (test becomes unclear)
- Patching code under test (defeats purpose)
- When dependency injection can be used instead

### Trade-offs
- ✅ **Isolation**: Test one function without running dependencies
- ✅ **Speed**: Avoid slow operations (file I/O, sleep)
- ✅ **Control**: Precise control over dependency behavior
- ❌ **Coupling**: Tests coupled to implementation details
- ❌ **Fragility**: Refactoring breaks tests
- ❌ **Complexity**: Many patches make tests hard to understand

### Related Patterns
- [Mocking AwsClientProvider](#13-mocking-awsclientprovider) - Alternative to patching
- [Test Structure](#15-test-structure-aaa-pattern) - Where patches are configured

---

## 22. Testing Domain Objects (ABCs)

**[PRIORITY: PREFERRED]** - Important for testing ABC implementations, but depends on CRITICAL pattern #11

### Purpose
Verify domain objects (events, metrics) correctly implement ABC contracts and produce expected data structures.

### Implementation

**Pattern 1: Testing concrete ABC implementations** (test_cloudwatch_interactions.py:8-54):
```python
def test_WHEN_CreateEniMirrorEventMetrics_created_AND_success_THEN_correct_metrics():
    # Run our test (create domain object)
    actual_value = cwi.CreateEniMirrorEventMetrics(
        "cluster-1", "vpc-1", cwi.CreateEniMirrorEventOutcome.SUCCESS
    )

    # Check our results
    expected_namespace = cwi.CW_ARKIME_EVENT_NAMESPACE
    assert expected_namespace == actual_value.namespace

    expected_metric_data = [
        {
            "MetricName": cwi.CreateEniMirrorEventOutcome.SUCCESS.value,
            "Value": 1,  # Only SUCCESS is 1
            "Dimensions": [...]
        },
        {
            "MetricName": cwi.CreateEniMirrorEventOutcome.ABORTED_EXISTS.value,
            "Value": 0,  # All others are 0
            "Dimensions": [...]
        },
        # ... more outcomes with Value: 0
    ]
    assert expected_metric_data == actual_value.metric_data
```

**Pattern 2: Testing each enum outcome** (test_cloudwatch_interactions.py:8-198):
- Separate test for each `CreateEniMirrorEventOutcome` enum value
- Verify only the matching outcome has `Value: 1`, others have `Value: 0`
- Verify all outcomes produce correct `Dimensions`

**Pattern 3: Testing polymorphic functions** (test_cloudwatch_interactions.py:261-281):
```python
def test_WHEN_put_event_metrics_called_THEN_metrics_are_put():
    # Set up our mock
    mock_metrics = mock.Mock()  # Could be any ArkimeEventMetric subclass
    mock_metrics.namespace = "name-1"
    mock_metrics.metric_data = [{"blah": "blah"}]

    # Run our test
    cwi.put_event_metrics(mock_metrics, mock_aws_provider)

    # Check our results (function uses ABC properties)
    expected_put_calls = [
        mock.call(
            Namespace=mock_metrics.namespace,  # ABC property
            MetricData=mock_metrics.metric_data  # ABC property
        )
    ]
    assert expected_put_calls == mock_cw_client.put_metric_data.call_args_list
```

**Pattern 4: Testing event construction** (test_events_interactions.py:15-22):
```python
create_eni_event = events.CreateEniMirrorEvent(
    "cluster-1", "vpc-1", "subnet-1", "eni-1", "eni-type-1", "filter-1", 42
)
destroy_eni_event = events.DestroyEniMirrorEvent(
    "cluster-1", "vpc-1", "subnet-1", "eni-2"
)

test_events = [create_eni_event, destroy_eni_event]  # List of ABC instances
events.put_events(test_events, "bus-1", mock_aws_provider)
```

### Testing Strategy for ABCs

**Concrete implementation tests**:
- One test per enum outcome (for metric classes)
- Verify namespace property (shared behavior)
- Verify metric_data property (subclass-specific behavior)
- Verify exact structure of output data

**Polymorphic function tests**:
- Mock ABC instance (don't use concrete subclass)
- Verify function uses ABC properties correctly
- Don't test concrete implementations (that's in other tests)

### When to Use
- **Test each enum value** when: Multi-outcome pattern with enum-based initialization
- **Test exact data structure** when: Output is consumed by AWS APIs (must match boto3 format)
- **Mock ABC** when: Testing polymorphic functions accepting any subclass

### When NOT to Use
- Testing ABC base class itself (test concrete implementations instead)
- When simpler dataclasses would suffice

### Trade-offs
- ✅ **Contract verification**: Ensures ABC contract implemented
- ✅ **Polymorphism tested**: Verifies functions work with any subclass
- ✅ **Exhaustive enum coverage**: All outcomes tested
- ❌ **Repetitive**: Similar tests for each enum value
- ❌ **Verbose**: Large expected data structures

### Related Patterns
- [Abstract Base Classes for Domain Objects](#11-abstract-base-classes-for-domain-objects) - What's being tested
- [Enum-Based Status Classification](#8-enum-based-status-classification) - Enums used with ABCs

---

## Summary of Testing Patterns

**Test Organization**:
- **Naming**: `test_WHEN_action_called_AND_condition_THEN_result` convention
- **Structure**: AAA pattern with comment markers
- **Multi-scenario**: Multiple TEST sections in one function

**Mocking**:
- **Provider**: Mock AwsClientProvider with getter methods
- **Clients**: Mock boto3 clients with return_value and side_effect
- **Patching**: Decorator patching for module functions, built-ins, time

**Assertions**:
- **Call verification**: `call_args_list` with expected `mock.call()` list
- **Return values**: Expected == actual pattern
- **Call counts**: Verify number of calls, or that method NOT called

**Advanced Patterns**:
- **Pagination**: side_effect list with NextToken in early responses
- **Error scenarios**: ClientError side_effect → pytest.raises domain exception
- **Sequential calls**: side_effect list for different responses per call
- **Domain objects**: Test ABC implementations exhaustively per enum value

**Key Principles**:
- 1:1 test-to-implementation file parity
- Comprehensive error scenario coverage
- Pagination testing with multiple pages
- Explicit expected values before assertions
- Comments marking test sections and scenarios
