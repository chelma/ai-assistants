"""
S3 interactions - Service wrapper functions for S3 operations.

Demonstrates all CRITICAL implementation patterns:
- Pattern 2: Dependency Injection (aws_provider parameter)
- Pattern 3: Service Wrapper Structure (module-level functions)
- Pattern 4: Error Handling & Custom Exceptions (ClientError → domain exceptions)
- Pattern 5: Data Transfer Objects (dataclasses for structured returns)
- Pattern 6: Enum-Based Status Classification (BucketStatus enum)
"""
from dataclasses import dataclass
from enum import Enum

from botocore.exceptions import ClientError

# Pattern 2: Type hint for dependency injection
from core.aws_client_provider import AwsClientProvider


# Pattern 4: Custom domain exceptions
class BucketDoesNotExist(Exception):
    """Raised when S3 bucket does not exist."""

    pass


class BucketNameNotAvailable(Exception):
    """Raised when bucket name is already taken by another account."""

    pass


# Pattern 6: Enum for status classification
class BucketStatus(Enum):
    """S3 bucket existence and access status."""

    EXISTS_HAVE_ACCESS = "exists_have_access"
    EXISTS_NO_ACCESS = "exists_no_access"
    DOES_NOT_EXIST = "does_not_exist"


# Pattern 5: Dataclass for structured return
@dataclass
class S3Object:
    """Represents an object in S3."""

    key: str
    size_bytes: int
    last_modified: str


# Pattern 3: Module-level wrapper functions with consistent structure
def get_bucket_status(
    bucket_name: str, aws_provider: AwsClientProvider
) -> BucketStatus:
    """
    Check if S3 bucket exists and is accessible.

    Pattern 2: Accepts aws_provider via dependency injection
    Pattern 4: Maps ClientError to domain enum values
    Pattern 6: Returns enum instead of boolean or string

    Args:
        bucket_name: Name of the S3 bucket to check
        aws_provider: Factory for creating boto3 clients

    Returns:
        BucketStatus enum indicating existence and access

    Raises:
        ClientError: For unexpected AWS errors (not 403/404/500)
    """
    # Pattern 2: Get boto3 client from provider
    s3_client = aws_provider.get_s3()

    try:
        # Call AWS SDK
        s3_client.head_bucket(Bucket=bucket_name)
        # Pattern 6: Return domain enum
        return BucketStatus.EXISTS_HAVE_ACCESS

    except ClientError as e:
        # Pattern 4: Inspect error code and map to domain status
        error_code = e.response["Error"]["Code"]

        if error_code == "403":
            return BucketStatus.EXISTS_NO_ACCESS
        elif error_code == "404":
            return BucketStatus.DOES_NOT_EXIST
        elif error_code == "500":
            # For demonstration: handle server errors
            raise
        else:
            # Re-raise unexpected errors (don't swallow)
            raise


def create_bucket(bucket_name: str, aws_provider: AwsClientProvider) -> None:
    """
    Create S3 bucket (idempotent if bucket already owned by you).

    Pattern 4: Handles BucketAlreadyOwnedByYou as success (idempotent)
    Pattern 4: Raises domain exception for BucketAlreadyExists (owned by another account)

    Args:
        bucket_name: Name of the S3 bucket to create
        aws_provider: Factory for creating boto3 clients

    Returns:
        None

    Raises:
        BucketNameNotAvailable: If bucket name is taken by another account
        ClientError: For unexpected AWS errors
    """
    s3_client = aws_provider.get_s3()

    try:
        s3_client.create_bucket(Bucket=bucket_name)
    except ClientError as e:
        error_message = str(e)

        # Pattern 4: Idempotent success case
        if "BucketAlreadyOwnedByYou" in error_message:
            # Already exists and we own it - success
            return

        # Pattern 4: Domain exception for business error
        if "BucketAlreadyExists" in error_message:
            raise BucketNameNotAvailable(
                f"Bucket name '{bucket_name}' is already taken"
            ) from e

        # Re-raise unexpected errors
        raise


def delete_bucket(bucket_name: str, aws_provider: AwsClientProvider) -> None:
    """
    Delete S3 bucket and all objects in it.

    Pattern 4: Maps NoSuchBucket to domain exception

    Args:
        bucket_name: Name of the S3 bucket to delete
        aws_provider: Factory for creating boto3 clients

    Returns:
        None

    Raises:
        BucketDoesNotExist: If bucket doesn't exist
        ClientError: For unexpected AWS errors
    """
    s3_client = aws_provider.get_s3()

    try:
        # Delete all objects first
        bucket = boto3.resource("s3").Bucket(bucket_name)
        bucket.objects.all().delete()

        # Delete the bucket
        bucket.delete()

    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        # Pattern 4: Map to domain exception
        if error_code == "NoSuchBucket":
            raise BucketDoesNotExist(f"Bucket '{bucket_name}' does not exist") from e

        # Re-raise unexpected errors
        raise


def list_bucket_objects(
    bucket_name: str, aws_provider: AwsClientProvider, prefix: str = ""
) -> list[S3Object]:
    """
    List all objects in S3 bucket with optional prefix (with pagination).

    Pattern 5: Returns list of dataclass objects, not raw boto3 dicts
    Pattern 6 (Pagination): Uses boto3 paginator to handle multiple pages

    Args:
        bucket_name: Name of the S3 bucket
        aws_provider: Factory for creating boto3 clients
        prefix: Optional prefix to filter objects

    Returns:
        List of S3Object dataclasses

    Raises:
        BucketDoesNotExist: If bucket doesn't exist
        ClientError: For unexpected AWS errors
    """
    s3_client = aws_provider.get_s3()

    try:
        # Pattern 6 (Pagination - PREFERRED): Use boto3 paginator
        paginator = s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

        objects = []
        for page in pages:
            for obj in page.get("Contents", []):
                # Pattern 5: Transform boto3 dict to dataclass
                objects.append(
                    S3Object(
                        key=obj["Key"],
                        size_bytes=obj["Size"],
                        last_modified=str(obj["LastModified"]),
                    )
                )

        return objects

    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        # Pattern 4: Map to domain exception
        if error_code == "NoSuchBucket":
            raise BucketDoesNotExist(f"Bucket '{bucket_name}' does not exist") from e

        # Re-raise unexpected errors
        raise


# Note: In real implementation, import boto3 at module level
# Omitted here to avoid confusion with aws_provider pattern
import boto3
