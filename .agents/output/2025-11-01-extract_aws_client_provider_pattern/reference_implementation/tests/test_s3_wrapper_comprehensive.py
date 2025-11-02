"""
Comprehensive testing examples demonstrating all 11 AWS SDK testing patterns.

PATTERNS DEMONSTRATED:
12. Test Naming Convention
13. Mocking AwsClientProvider
14. Mocking boto3 Clients
15. Test Structure (AAA Pattern)
16. Assertion Patterns
17. Error Scenario Testing
18. Pagination Testing
19. Multi-Scenario Testing
20. Side Effects for Sequential Calls
21. Patching Strategies
22. Testing Domain Objects (ABCs) - See test_cloudwatch_metrics.py for full example

This file serves as a reference for implementing tests in your own project.
Adjust import paths to match your project structure.
"""

import pytest
from unittest import mock
from botocore.exceptions import ClientError

# Adjust these imports to match your project structure
import sys
sys.path.insert(0, '..')
from example_service.s3_wrapper import (
    get_bucket_status,
    BucketStatus,
    create_bucket,
    list_objects,
    delete_object,
    BucketDoesntExist,
    BucketAccessDenied,
    BucketNameNotAvailable,
)


# =============================================================================
# PATTERN 12: Test Naming Convention
# =============================================================================
# Convention: test_WHEN_<action>_called_AND_<condition>_THEN_<expected_result>
#
# - WHEN_<action>_called: Function being tested
# - AND_<condition>: Test scenario/precondition (optional)
# - THEN_<expected_result>: Expected outcome
#
# Benefits:
# - Searchable (grep for "WHEN_get_bucket_status")
# - Self-documenting (test intent clear from name)
# - Consistent across test suite
# =============================================================================


def test_WHEN_get_bucket_status_called_THEN_as_expected():
    """
    PATTERN 19: Multi-Scenario Testing

    Single test with multiple TEST sections, each with ACT + ASSERT.
    Reduces boilerplate by sharing mock setup across related scenarios.
    """
    # =========================================================================
    # PATTERN 15: Test Structure (AAA Pattern)
    # =========================================================================
    # Organize tests into clear sections with comment markers:
    # - ARRANGE: Set up mocks and test data
    # - ACT: Execute function under test
    # - ASSERT: Verify behavior
    # =========================================================================

    # ARRANGE: Set up our mock (shared across all scenarios in this test)
    # =========================================================================
    # PATTERN 13: Mocking AwsClientProvider
    # =========================================================================
    # Create mock provider that returns mock boto3 client.
    # This enables dependency injection testing.
    # =========================================================================
    mock_s3_client = mock.Mock()

    mock_aws_provider = mock.Mock()
    mock_aws_provider.get_s3.return_value = mock_s3_client

    # =========================================================================
    # TEST: Bucket exists and we have access
    # =========================================================================
    # PATTERN 14: Mocking boto3 Clients (return_value)
    # =========================================================================
    # Configure mock to return specific boto3 response structure.
    # Match actual AWS API response format.
    # =========================================================================
    mock_s3_client.head_bucket.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}

    # ACT: Call function under test
    actual_value = get_bucket_status("test-bucket", mock_aws_provider)

    # ASSERT: Verify results
    # =========================================================================
    # PATTERN 16: Assertion Patterns
    # =========================================================================
    # Convention: expected == actual (expected on left)
    # Use specific enum values for type safety
    # =========================================================================
    assert BucketStatus.EXISTS_HAVE_ACCESS == actual_value

    # =========================================================================
    # TEST: Bucket exists but access denied
    # =========================================================================
    # PATTERN 17: Error Scenario Testing
    # =========================================================================
    # Configure mock to raise ClientError, verify wrapper handles it correctly.
    # =========================================================================
    # PATTERN 14: Mocking boto3 Clients (side_effect with exception)
    # =========================================================================
    mock_s3_client.head_bucket.side_effect = ClientError(
        error_response={"Error": {"Code": "403", "Message": "Forbidden"}},
        operation_name="HeadBucket"
    )

    # ACT
    actual_value = get_bucket_status("test-bucket", mock_aws_provider)

    # ASSERT: Verify error mapped to correct status
    assert BucketStatus.EXISTS_NO_ACCESS == actual_value

    # =========================================================================
    # TEST: Bucket does not exist
    # =========================================================================
    mock_s3_client.head_bucket.side_effect = ClientError(
        error_response={"Error": {"Code": "404", "Message": "Not Found"}},
        operation_name="HeadBucket"
    )

    # ACT
    actual_value = get_bucket_status("test-bucket", mock_aws_provider)

    # ASSERT
    assert BucketStatus.DOES_NOT_EXIST == actual_value

    # =========================================================================
    # TEST: Unexpected error (not mapped to status)
    # =========================================================================
    mock_s3_client.head_bucket.side_effect = ClientError(
        error_response={"Error": {"Code": "500", "Message": "Internal Error"}},
        operation_name="HeadBucket"
    )

    # ACT + ASSERT: Verify exception propagates
    with pytest.raises(ClientError):
        get_bucket_status("test-bucket", mock_aws_provider)


def test_WHEN_create_bucket_called_AND_doesnt_exist_THEN_creates_it():
    """
    Demonstrates call argument verification and AwsEnvironment mocking.
    """
    # Set up our mock
    mock_s3_client = mock.Mock()

    # =========================================================================
    # PATTERN 13: Mocking AwsClientProvider with get_aws_env()
    # =========================================================================
    # Some wrappers need account/region context via get_aws_env().
    # Mock this method to return test AwsEnvironment.
    # =========================================================================
    from core.aws_environment import AwsEnvironment
    test_env = AwsEnvironment("123456789012", "us-west-2", "test-profile")

    mock_aws_provider = mock.Mock()
    mock_aws_provider.get_s3.return_value = mock_s3_client
    mock_aws_provider.get_aws_env.return_value = test_env

    # Run our test
    create_bucket("my-test-bucket", mock_aws_provider)

    # Check our results
    # =========================================================================
    # PATTERN 16: Assertion Patterns (call verification)
    # =========================================================================
    # Use call_args_list to verify exact boto3 calls.
    # Build expected_calls list with mock.call() for each expected call.
    # =========================================================================
    expected_calls = [
        mock.call(
            ACL="private",
            Bucket="my-test-bucket",
            ObjectOwnership="BucketOwnerPreferred",
            CreateBucketConfiguration={"LocationConstraint": "us-west-2"}
        )
    ]
    assert expected_calls == mock_s3_client.create_bucket.call_args_list


def test_WHEN_create_bucket_called_AND_already_exists_THEN_swallows_error():
    """
    Demonstrates testing exception swallowing (early return on expected error).
    """
    # Set up our mock
    mock_s3_client = mock.Mock()

    from core.aws_environment import AwsEnvironment
    test_env = AwsEnvironment("123456789012", "us-east-1", "test-profile")  # Note: us-east-1 special case

    mock_aws_provider = mock.Mock()
    mock_aws_provider.get_s3.return_value = mock_s3_client
    mock_aws_provider.get_aws_env.return_value = test_env

    # =========================================================================
    # PATTERN 17: Error Scenario Testing (exception swallowing)
    # =========================================================================
    # Some functions catch errors and treat them as normal conditions.
    # Verify error is swallowed correctly.
    # =========================================================================
    mock_s3_client.create_bucket.side_effect = ClientError(
        error_response={"Error": {"Message": "BucketAlreadyOwnedByYou"}},
        operation_name="CreateBucket"
    )

    # Run our test (should NOT raise)
    create_bucket("my-test-bucket", mock_aws_provider)

    # Check our results
    # =========================================================================
    # PATTERN 16: Assertion Patterns (call count)
    # =========================================================================
    # Verify method was called expected number of times.
    # =========================================================================
    assert 1 == mock_s3_client.create_bucket.call_count


def test_WHEN_create_bucket_called_AND_name_taken_THEN_raises():
    """
    Demonstrates testing domain exception mapping from boto3 ClientError.
    """
    # Set up our mock
    mock_s3_client = mock.Mock()

    from core.aws_environment import AwsEnvironment
    test_env = AwsEnvironment("123456789012", "us-west-2", "test-profile")

    mock_aws_provider = mock.Mock()
    mock_aws_provider.get_s3.return_value = mock_s3_client
    mock_aws_provider.get_aws_env.return_value = test_env

    # =========================================================================
    # PATTERN 17: Error Scenario Testing (exception mapping)
    # =========================================================================
    # Configure mock to raise ClientError.
    # Verify wrapper maps it to domain exception.
    # =========================================================================
    mock_s3_client.create_bucket.side_effect = ClientError(
        error_response={"Error": {"Message": "BucketAlreadyExists"}},
        operation_name="CreateBucket"
    )

    # Run our test + assert exception raised
    with pytest.raises(BucketNameNotAvailable):
        create_bucket("my-test-bucket", mock_aws_provider)


def test_WHEN_list_objects_called_AND_multiple_pages_THEN_returns_all():
    """
    PATTERN 18: Pagination Testing

    Demonstrates testing pagination logic with NextToken loops.
    Use side_effect with list of responses to simulate multiple pages.
    """
    # Set up our mock
    mock_s3_client = mock.Mock()

    mock_aws_provider = mock.Mock()
    mock_aws_provider.get_s3.return_value = mock_s3_client

    # =========================================================================
    # PATTERN 20: Side Effects for Sequential Calls
    # =========================================================================
    # Use side_effect with list to return different responses per call.
    # Essential for testing pagination, state changes, retry logic.
    # =========================================================================
    # PATTERN 18: Pagination Testing (NextToken pattern)
    # =========================================================================
    # First response includes NextContinuationToken (more pages exist).
    # Final response omits token (pagination complete).
    # =========================================================================
    mock_s3_client.list_objects_v2.side_effect = [
        {
            "Contents": [
                {"Key": "prefix/file1.txt"},
                {"Key": "prefix/file2.txt"}
            ],
            "NextContinuationToken": "token-1"  # Indicates more pages
        },
        {
            "Contents": [
                {"Key": "prefix/file3.txt"}
            ]
            # No NextContinuationToken - pagination complete
        }
    ]

    # Run our test
    result = list_objects("my-bucket", "prefix/", mock_aws_provider)

    # Check our results
    # =========================================================================
    # PATTERN 16: Assertion Patterns (verifying pagination calls)
    # =========================================================================
    # First call has no ContinuationToken.
    # Second call includes token from first response.
    # =========================================================================
    expected_calls = [
        mock.call(Bucket="my-bucket", Prefix="prefix/"),
        mock.call(Bucket="my-bucket", Prefix="prefix/", ContinuationToken="token-1")
    ]
    assert expected_calls == mock_s3_client.list_objects_v2.call_args_list

    # =========================================================================
    # PATTERN 16: Assertion Patterns (return value verification)
    # =========================================================================
    # Verify all pages accumulated correctly.
    # =========================================================================
    expected_result = ["prefix/file1.txt", "prefix/file2.txt", "prefix/file3.txt"]
    assert expected_result == result


def test_WHEN_list_objects_called_AND_empty_THEN_returns_empty_list():
    """
    Edge case: Empty result set.
    """
    # Set up our mock
    mock_s3_client = mock.Mock()

    mock_aws_provider = mock.Mock()
    mock_aws_provider.get_s3.return_value = mock_s3_client

    # =========================================================================
    # PATTERN 14: Mocking boto3 Clients (empty response)
    # =========================================================================
    # Test edge cases: empty results, missing keys, None values.
    # =========================================================================
    mock_s3_client.list_objects_v2.return_value = {}  # No "Contents" key

    # Run our test
    result = list_objects("my-bucket", "prefix/", mock_aws_provider)

    # Check our results
    expected_result = []
    assert expected_result == result


def test_WHEN_delete_object_called_THEN_deletes_and_logs():
    """
    Simple test demonstrating basic mocking and call verification.
    """
    # Set up our mock
    mock_s3_client = mock.Mock()

    mock_aws_provider = mock.Mock()
    mock_aws_provider.get_s3.return_value = mock_s3_client

    # Run our test
    delete_object("my-bucket", "file.txt", mock_aws_provider)

    # Check our results
    expected_calls = [
        mock.call(Bucket="my-bucket", Key="file.txt")
    ]
    assert expected_calls == mock_s3_client.delete_object.call_args_list


# =============================================================================
# PATTERN 21: Patching Strategies
# =============================================================================
# Use @mock.patch decorator to replace imports, module functions, or built-ins.
#
# Key concepts:
# - Patch where function is USED, not where it's DEFINED
# - Decorators applied bottom-up, parameters passed top-down (reverse order)
# - Common targets: built-ins (open), time.sleep, module functions
#
# Example: @mock.patch("module.submodule.function")
# =============================================================================


@mock.patch("example_service.s3_wrapper.create_bucket")
@mock.patch("example_service.s3_wrapper.get_bucket_status")
def test_WHEN_hypothetical_ensure_bucket_exists_called_THEN_creates_if_missing(
    mock_get_status,  # ← Second decorator (reversed)
    mock_create_bucket  # ← First decorator (reversed)
):
    """
    Demonstrates decorator patching of module functions.

    NOTE: This tests a hypothetical ensure_bucket_exists() function.
    Demonstrates how to patch other functions in same module.

    PATTERN 21: Patching Strategies (decorator patching)
    - Decorators applied bottom-up
    - Parameters passed top-down (REVERSED)
    - Use to isolate function under test from dependencies
    """
    # Set up our mocks
    mock_get_status.return_value = BucketStatus.DOES_NOT_EXIST
    mock_create_bucket.return_value = None

    mock_aws_provider = mock.Mock()

    # If this function existed, we'd test it:
    # ensure_bucket_exists("my-bucket", mock_aws_provider)

    # Would verify both functions called:
    # mock_get_status.assert_called_once_with("my-bucket", mock_aws_provider)
    # mock_create_bucket.assert_called_once_with("my-bucket", mock_aws_provider)


# =============================================================================
# ADDITIONAL TESTING PATTERNS NOT SHOWN HERE
# =============================================================================
#
# PATTERN 22: Testing Domain Objects (ABCs)
# - Test each enum outcome produces correct metric values
# - Test polymorphic functions accept any ABC subclass
# - Verify exact structure of output data
# - See test_cloudwatch_metrics.py for complete example
#
# For comprehensive examples of all patterns, see:
# - references/patterns_testing.md (detailed pattern documentation)
# - Original aws-aio test suite (production test patterns)
# =============================================================================


# =============================================================================
# TESTING BEST PRACTICES SUMMARY
# =============================================================================
#
# 1. NAMING: Use WHEN_action_AND_condition_THEN_result convention
# 2. STRUCTURE: AAA pattern with comment markers
# 3. MOCKING: Mock AwsClientProvider → returns mock boto3 client
# 4. SIDE_EFFECT: Use lists for pagination, sequential calls, error scenarios
# 5. ASSERTIONS: expected == actual, verify call_args_list
# 6. MULTI-SCENARIO: Group related scenarios in one test function
# 7. PATCHING: Use @mock.patch for module functions, built-ins, time.sleep
# 8. ERROR TESTING: ClientError side_effect → pytest.raises domain exception
# 9. PAGINATION: side_effect list with NextToken in early responses
# 10. CALL VERIFICATION: Build expected_calls list with mock.call()
# 11. EDGE CASES: Test empty results, None values, missing keys
#
# =============================================================================
