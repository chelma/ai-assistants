"""
Tests for S3 interactions - Demonstrates all CRITICAL testing patterns.

CRITICAL TESTING PATTERNS DEMONSTRATED:

Pattern 7 (13): Mocking AwsClientProvider
    - Create mock provider, wire to return mock boto3 client
    - Pass mock provider to wrapper functions (no @mock.patch needed)
    - See: All test functions lines 20-225

Pattern 8 (14): Mocking boto3 Clients
    - Simple return values: lines 22-23 (return success response)
    - Exception side effects: lines 39-42 (mock ClientError with error code)
    - Paginator mocking: lines 146-150 (mock multi-page results)

Pattern 9 (17): Error Scenario Testing
    - Test expected error codes: lines 37-48 (403), lines 51-58 (404)
    - Test unexpected errors re-raised: lines 60-73 (InternalError)
    - Test domain exception mapping: lines 117-139 (BucketDoesNotExist)
    - Test idempotent errors: lines 76-87 (BucketAlreadyOwnedByYou)

Pattern 10 (18): Pagination Testing
    - Mock paginator with multiple pages: lines 146-150
    - Verify all pages accumulated: line 183 (assert len == 3)
    - Verify paginator called correctly: lines 177-182

KEY TEST ORGANIZATION:
    - One test file per implementation module (1:1 mapping)
    - Test function names: test_WHEN_<action>_AND_<condition>_THEN_<expected>
    - AAA structure: Arrange (mock setup), Act (call function), Assert (verify results)
    - Comprehensive error coverage: happy path + expected errors + unexpected errors
"""
from unittest import mock

import pytest
from botocore.exceptions import ClientError

# Import code under test
from aws_interactions import s3_interactions


# Pattern 7 (13): Mocking AwsClientProvider
def test_WHEN_get_bucket_status_called_AND_exists_have_access_THEN_returns_enum():
    """
    Demonstrates Pattern 7: Mock provider returns mock S3 client.
    """
    # Arrange: Create mock S3 client
    mock_s3_client = mock.Mock()
    mock_s3_client.head_bucket.return_value = {
        "ResponseMetadata": {"HTTPStatusCode": 200}
    }

    # Arrange: Create mock provider that returns mock S3 client
    mock_provider = mock.Mock()
    mock_provider.get_s3.return_value = mock_s3_client

    # Act: Call wrapper with mock provider
    actual_result = s3_interactions.get_bucket_status("test-bucket", mock_provider)

    # Assert: Verify boto3 call and result
    expected_result = s3_interactions.BucketStatus.EXISTS_HAVE_ACCESS
    assert expected_result == actual_result
    mock_s3_client.head_bucket.assert_called_once_with(Bucket="test-bucket")


# Pattern 8 (14): Mocking boto3 Clients - Exception side effects
def test_WHEN_get_bucket_status_called_AND_exists_no_access_THEN_returns_enum():
    """
    Demonstrates Pattern 8: Mock client raises ClientError with specific error code.
    Demonstrates Pattern 9: Test error scenario (403 handling).
    """
    # Arrange: Mock ClientError with 403 error code
    mock_s3_client = mock.Mock()
    mock_s3_client.head_bucket.side_effect = ClientError(
        error_response={"Error": {"Code": "403", "Message": "Forbidden"}},
        operation_name="HeadBucket",
    )

    mock_provider = mock.Mock()
    mock_provider.get_s3.return_value = mock_s3_client

    # Act
    actual_result = s3_interactions.get_bucket_status("test-bucket", mock_provider)

    # Assert: 403 maps to EXISTS_NO_ACCESS
    expected_result = s3_interactions.BucketStatus.EXISTS_NO_ACCESS
    assert expected_result == actual_result


# Pattern 9 (17): Error Scenario Testing
def test_WHEN_get_bucket_status_called_AND_does_not_exist_THEN_returns_enum():
    """
    Demonstrates Pattern 9: Test error code mapping (404 → DOES_NOT_EXIST).
    """
    # Arrange: Mock ClientError with 404 error code
    mock_s3_client = mock.Mock()
    mock_s3_client.head_bucket.side_effect = ClientError(
        error_response={"Error": {"Code": "404", "Message": "Not Found"}},
        operation_name="HeadBucket",
    )

    mock_provider = mock.Mock()
    mock_provider.get_s3.return_value = mock_s3_client

    # Act
    actual_result = s3_interactions.get_bucket_status("test-bucket", mock_provider)

    # Assert: 404 maps to DOES_NOT_EXIST
    expected_result = s3_interactions.BucketStatus.DOES_NOT_EXIST
    assert expected_result == actual_result


# Pattern 9 (17): Error Scenario Testing - Unexpected errors re-raised
def test_WHEN_get_bucket_status_called_AND_unexpected_error_THEN_raises():
    """
    Demonstrates Pattern 9: Unexpected errors are re-raised (not swallowed).
    """
    # Arrange: Mock unexpected error code
    mock_s3_client = mock.Mock()
    mock_s3_client.head_bucket.side_effect = ClientError(
        error_response={"Error": {"Code": "InternalError", "Message": "Server error"}},
        operation_name="HeadBucket",
    )

    mock_provider = mock.Mock()
    mock_provider.get_s3.return_value = mock_s3_client

    # Act & Assert: Unexpected error is re-raised
    with pytest.raises(ClientError):
        s3_interactions.get_bucket_status("test-bucket", mock_provider)


# Pattern 9 (17): Error Scenario Testing - Idempotent error handling
def test_WHEN_create_bucket_called_AND_already_owned_by_you_THEN_succeeds():
    """
    Demonstrates Pattern 9: Test idempotent error handling (BucketAlreadyOwnedByYou is success).
    """
    # Arrange: Mock BucketAlreadyOwnedByYou error (idempotent case)
    mock_s3_client = mock.Mock()
    mock_s3_client.create_bucket.side_effect = ClientError(
        error_response={
            "Error": {"Code": "BucketAlreadyOwnedByYou", "Message": "You already own this bucket"}
        },
        operation_name="CreateBucket",
    )

    mock_provider = mock.Mock()
    mock_provider.get_s3.return_value = mock_s3_client

    # Act: Should not raise (idempotent success)
    s3_interactions.create_bucket("test-bucket", mock_provider)

    # Assert: No exception raised (implicit success)


# Pattern 9 (17): Error Scenario Testing - Domain exception mapping
def test_WHEN_create_bucket_called_AND_already_exists_THEN_raises_domain_exception():
    """
    Demonstrates Pattern 9: ClientError mapped to domain exception.
    """
    # Arrange: Mock BucketAlreadyExists error
    mock_s3_client = mock.Mock()
    mock_s3_client.create_bucket.side_effect = ClientError(
        error_response={
            "Error": {"Code": "BucketAlreadyExists", "Message": "Bucket already exists"}
        },
        operation_name="CreateBucket",
    )

    mock_provider = mock.Mock()
    mock_provider.get_s3.return_value = mock_s3_client

    # Act & Assert: Domain exception raised
    with pytest.raises(s3_interactions.BucketNameNotAvailable):
        s3_interactions.create_bucket("test-bucket", mock_provider)


# Pattern 10 (18): Pagination Testing
def test_WHEN_list_bucket_objects_called_AND_multiple_pages_THEN_accumulates_all():
    """
    Demonstrates Pattern 10: Test pagination with multiple pages via boto3 paginator.

    Verifies:
    - Results from all pages are accumulated
    - Paginator is used correctly
    - boto3 response transformed to dataclass objects
    """
    # Arrange: Mock paginator with multiple pages
    mock_paginator = mock.Mock()
    page_1 = {
        "Contents": [
            {"Key": "file1.txt", "Size": 100, "LastModified": "2021-01-01T12:00:00"},
            {"Key": "file2.txt", "Size": 200, "LastModified": "2021-01-02T12:00:00"},
        ]
    }
    page_2 = {
        "Contents": [
            {"Key": "file3.txt", "Size": 300, "LastModified": "2021-01-03T12:00:00"}
        ]
    }
    mock_paginator.paginate.return_value = [page_1, page_2]

    mock_s3_client = mock.Mock()
    mock_s3_client.get_paginator.return_value = mock_paginator

    mock_provider = mock.Mock()
    mock_provider.get_s3.return_value = mock_s3_client

    # Act
    actual_result = s3_interactions.list_bucket_objects(
        "test-bucket", mock_provider, prefix="logs/"
    )

    # Assert: All pages accumulated
    expected_count = 3
    assert expected_count == len(actual_result)

    # Assert: Results are S3Object dataclasses (Pattern 5)
    assert isinstance(actual_result[0], s3_interactions.S3Object)
    assert "file1.txt" == actual_result[0].key
    assert 100 == actual_result[0].size_bytes

    assert "file2.txt" == actual_result[1].key
    assert 200 == actual_result[1].size_bytes

    assert "file3.txt" == actual_result[2].key
    assert 300 == actual_result[2].size_bytes

    # Assert: Paginator called with correct parameters
    mock_s3_client.get_paginator.assert_called_once_with("list_objects_v2")
    mock_paginator.paginate.assert_called_once_with(
        Bucket="test-bucket", Prefix="logs/"
    )


# Pattern 10 (18): Pagination Testing - Empty results
def test_WHEN_list_bucket_objects_called_AND_empty_THEN_returns_empty_list():
    """
    Demonstrates Pattern 10: Test pagination edge case (empty bucket).
    """
    # Arrange: Mock empty page
    mock_paginator = mock.Mock()
    mock_paginator.paginate.return_value = [{}]  # No Contents key

    mock_s3_client = mock.Mock()
    mock_s3_client.get_paginator.return_value = mock_paginator

    mock_provider = mock.Mock()
    mock_provider.get_s3.return_value = mock_s3_client

    # Act
    actual_result = s3_interactions.list_bucket_objects("empty-bucket", mock_provider)

    # Assert: Empty list returned
    expected_result = []
    assert expected_result == actual_result


# Pattern 8 (14): Mocking boto3 Clients - Return value mocking
def test_WHEN_delete_bucket_called_THEN_deletes_objects_and_bucket():
    """
    Demonstrates Pattern 8: Mock client return values for success case.
    """
    # Arrange: Mock boto3 resource and bucket
    mock_bucket = mock.Mock()
    mock_objects_all = mock.Mock()
    mock_bucket.objects.all.return_value = mock_objects_all

    with mock.patch("boto3.resource") as mock_resource:
        mock_resource.return_value.Bucket.return_value = mock_bucket

        mock_s3_client = mock.Mock()
        mock_provider = mock.Mock()
        mock_provider.get_s3.return_value = mock_s3_client

        # Act
        s3_interactions.delete_bucket("test-bucket", mock_provider)

        # Assert: Objects deleted and bucket deleted
        mock_objects_all.delete.assert_called_once()
        mock_bucket.delete.assert_called_once()


# Pattern 9 (17): Error Scenario Testing - Domain exception for missing resource
def test_WHEN_delete_bucket_called_AND_not_exists_THEN_raises_domain_exception():
    """
    Demonstrates Pattern 9: NoSuchBucket maps to domain exception.
    """
    # Arrange: Mock NoSuchBucket error
    with mock.patch("boto3.resource") as mock_resource:
        mock_bucket = mock_resource.return_value.Bucket.return_value
        mock_bucket.objects.all.return_value.delete.side_effect = ClientError(
            error_response={"Error": {"Code": "NoSuchBucket"}},
            operation_name="DeleteObjects",
        )

        mock_s3_client = mock.Mock()
        mock_provider = mock.Mock()
        mock_provider.get_s3.return_value = mock_s3_client

        # Act & Assert: Domain exception raised
        with pytest.raises(s3_interactions.BucketDoesNotExist):
            s3_interactions.delete_bucket("missing-bucket", mock_provider)


# Summary of patterns demonstrated:
# ✅ Pattern 7 (13): Mocking AwsClientProvider - All tests
# ✅ Pattern 8 (14): Mocking boto3 Clients - return_value, side_effect
# ✅ Pattern 9 (17): Error Scenario Testing - 403, 404, unexpected errors, domain exceptions
# ✅ Pattern 10 (18): Pagination Testing - Multiple pages, empty results
