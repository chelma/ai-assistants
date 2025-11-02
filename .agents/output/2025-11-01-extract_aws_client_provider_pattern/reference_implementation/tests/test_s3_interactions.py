"""
Tests for S3 interactions - Demonstrates all CRITICAL testing patterns.

Patterns demonstrated:
- Pattern 7 (13): Mocking AwsClientProvider
- Pattern 8 (14): Mocking boto3 Clients
- Pattern 9 (17): Error Scenario Testing
- Pattern 10 (18): Pagination Testing
"""
from unittest import mock

import pytest
from botocore.exceptions import ClientError

# Import code under test
from aws_interactions import s3_interactions


# Pattern 7 (13): Mocking AwsClientProvider
def test_get_bucket_status_when_exists_have_access():
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
    result = s3_interactions.get_bucket_status("test-bucket", mock_provider)

    # Assert: Verify boto3 call and result
    assert result == s3_interactions.BucketStatus.EXISTS_HAVE_ACCESS
    mock_s3_client.head_bucket.assert_called_once_with(Bucket="test-bucket")


# Pattern 8 (14): Mocking boto3 Clients - Exception side effects
def test_get_bucket_status_when_exists_no_access():
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
    result = s3_interactions.get_bucket_status("test-bucket", mock_provider)

    # Assert: 403 maps to EXISTS_NO_ACCESS
    assert result == s3_interactions.BucketStatus.EXISTS_NO_ACCESS


# Pattern 9 (17): Error Scenario Testing
def test_get_bucket_status_when_does_not_exist():
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
    result = s3_interactions.get_bucket_status("test-bucket", mock_provider)

    # Assert: 404 maps to DOES_NOT_EXIST
    assert result == s3_interactions.BucketStatus.DOES_NOT_EXIST


# Pattern 9 (17): Error Scenario Testing - Unexpected errors re-raised
def test_get_bucket_status_when_unexpected_error_then_raises():
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
def test_create_bucket_when_already_owned_by_you_then_succeeds():
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
def test_create_bucket_when_already_exists_then_raises_domain_exception():
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
def test_list_bucket_objects_with_pagination():
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
    result = s3_interactions.list_bucket_objects(
        "test-bucket", mock_provider, prefix="logs/"
    )

    # Assert: All pages accumulated
    assert len(result) == 3

    # Assert: Results are S3Object dataclasses (Pattern 5)
    assert isinstance(result[0], s3_interactions.S3Object)
    assert result[0].key == "file1.txt"
    assert result[0].size_bytes == 100

    assert result[1].key == "file2.txt"
    assert result[1].size_bytes == 200

    assert result[2].key == "file3.txt"
    assert result[2].size_bytes == 300

    # Assert: Paginator called with correct parameters
    mock_s3_client.get_paginator.assert_called_once_with("list_objects_v2")
    mock_paginator.paginate.assert_called_once_with(
        Bucket="test-bucket", Prefix="logs/"
    )


# Pattern 10 (18): Pagination Testing - Empty results
def test_list_bucket_objects_when_empty():
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
    result = s3_interactions.list_bucket_objects("empty-bucket", mock_provider)

    # Assert: Empty list returned
    assert result == []


# Pattern 8 (14): Mocking boto3 Clients - Return value mocking
def test_delete_bucket_success():
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
def test_delete_bucket_when_not_exists_then_raises():
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
