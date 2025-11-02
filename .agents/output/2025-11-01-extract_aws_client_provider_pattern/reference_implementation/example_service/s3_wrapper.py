"""
S3 service wrapper - Example demonstrating AWS SDK interaction patterns.

PATTERN DEMONSTRATED: Service wrapper with dependency injection
- Module-level functions (not class-based)
- Functions accept AwsClientProvider via dependency injection
- Map boto3 ClientError to domain-specific exceptions
- Return dataclasses/enums instead of raw boto3 response dicts

KEY CONCEPTS:
- Separation of concerns: AWS SDK calls isolated from business logic
- Testability: AwsClientProvider can be mocked in tests
- Type safety: Explicit return types (BucketStatus, not dict)
- Error mapping: Domain exceptions (BucketAccessDenied) vs boto3 ClientError

WHEN TO USE THIS PATTERN:
- Building reusable AWS service operations
- Need testability and mocking capability
- Want type-safe, self-documenting APIs
- Supporting multiple callers with different credential contexts

DESIGN CHOICES:
- Why module-level functions vs class-based wrapper?
  # TODO: What are the trade-offs?
- Why custom exceptions vs letting ClientError propagate?
  # TODO: What's the principle here?
- Why return enums vs raising exceptions for "not found" scenarios?
  # TODO: When should you use enum vs exception?

SOURCE: Extracted from aws-aio production codebase (s3_interactions.py)
"""

import logging
from enum import Enum
from typing import List

from botocore.exceptions import ClientError

# In real implementation, adjust import to match your project structure:
# from aws_interactions.aws_client_provider import AwsClientProvider
# For reference implementation, using relative import:
from ..core.aws_client_provider import AwsClientProvider

logger = logging.getLogger(__name__)


# =============================================================================
# Domain-Specific Exceptions
# =============================================================================
# PATTERN: Map boto3 ClientError to domain-specific exceptions
# - Provides type-safe error handling for callers
# - Hides boto3 implementation details
# - Enables clear, domain-oriented error messages
# =============================================================================


class BucketAccessDenied(Exception):
    """Raised when S3 bucket exists but caller lacks access permissions."""

    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        super().__init__(f"You do not have access to S3 bucket {bucket_name}")


class BucketDoesntExist(Exception):
    """Raised when S3 bucket does not exist."""

    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        super().__init__(f"The S3 bucket {bucket_name} does not exist")


class BucketNameNotAvailable(Exception):
    """Raised when S3 bucket name is already owned by another AWS account."""

    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        super().__init__(
            f"The S3 bucket name {bucket_name} is already owned by another account"
        )


class S3ObjectDoesntExist(Exception):
    """Raised when S3 object (file) does not exist."""

    def __init__(self, bucket: str, key: str):
        self.bucket = bucket
        self.key = key
        super().__init__(
            f"The S3 object requested does not appear to exist: "
            f"Bucket '{bucket}', Key '{key}'"
        )


# =============================================================================
# Enums for Status Classification
# =============================================================================
# PATTERN: Use enums when return value represents fixed set of states
# - Type-safe vs string constants
# - IDE autocomplete and validation
# - Clear documentation of possible values
#
# DESIGN CHOICE: When to use enum vs exception?
# # TODO: What's the decision rule? Enum for "expected outcomes", exception for errors?
# =============================================================================


class BucketStatus(Enum):
    """Status of S3 bucket from caller's perspective."""

    DOES_NOT_EXIST = "does not exist"
    EXISTS_HAVE_ACCESS = "exists have access"
    EXISTS_NO_ACCESS = "exists no access"


# =============================================================================
# Service Wrapper Functions
# =============================================================================
# PATTERN: Dependency injection via aws_provider parameter
# - All functions accept AwsClientProvider as parameter
# - Enables mocking in tests
# - Callers control which credentials/profile to use
#
# NAMING CONVENTION: Either aws_provider or aws_client_provider (both used)
# # TODO: Should we standardize on one naming convention?
# =============================================================================


def get_bucket_status(bucket_name: str, aws_provider: AwsClientProvider) -> BucketStatus:
    """
    Check if S3 bucket exists and whether caller has access.

    PATTERN: Error code inspection for status classification
    - Use HeadBucket API (doesn't retrieve bucket contents)
    - Map error codes to status enum values
    - Return enum instead of raising exception (status check, not operation)

    Args:
        bucket_name: S3 bucket name
        aws_provider: Factory for creating boto3 clients

    Returns:
        BucketStatus enum indicating existence and access

    Example:
        status = get_bucket_status("my-bucket", aws_provider)
        if status == BucketStatus.EXISTS_HAVE_ACCESS:
            print("Can use this bucket")
        elif status == BucketStatus.EXISTS_NO_ACCESS:
            print("Bucket exists but access denied")
        else:
            print("Bucket doesn't exist")
    """
    s3_client = aws_provider.get_s3()

    try:
        # HeadBucket API call - returns metadata or error
        s3_client.head_bucket(Bucket=bucket_name)
        return BucketStatus.EXISTS_HAVE_ACCESS

    except ClientError as ex:
        # PATTERN: Inspect error code to determine specific error condition
        # Access error response dict: ex.response["Error"]["Code"]
        error_code = ex.response["Error"]["Code"]

        if error_code == "403":
            # Forbidden - bucket exists but no access
            return BucketStatus.EXISTS_NO_ACCESS
        elif error_code == "404":
            # Not found - bucket doesn't exist
            return BucketStatus.DOES_NOT_EXIST
        else:
            # Unexpected error - re-raise
            raise ex


def create_bucket(bucket_name: str, aws_provider: AwsClientProvider) -> None:
    """
    Create S3 bucket with private ACL in provider's configured region.

    PATTERN: Use AwsEnvironment for region-aware operations
    - S3 CreateBucket API requires explicit region (except us-east-1)
    - Call aws_provider.get_aws_env() to get current region
    - Handle special case: us-east-1 doesn't need LocationConstraint

    PATTERN: String matching for complex error scenarios
    - Some errors need message inspection, not just error code
    - Example: "BucketAlreadyOwnedByYou" vs "BucketAlreadyExists"

    Args:
        bucket_name: S3 bucket name (must be globally unique)
        aws_provider: Factory for creating boto3 clients

    Raises:
        BucketNameNotAvailable: Bucket name already owned by another account

    Example:
        try:
            create_bucket("my-app-data-bucket", aws_provider)
        except BucketNameNotAvailable:
            print("Choose a different bucket name")
    """
    s3_client = aws_provider.get_s3()

    # Get AWS environment context for region information
    aws_env = aws_provider.get_aws_env()

    try:
        # Build CreateBucket arguments
        create_args = {
            "ACL": "private",
            "Bucket": bucket_name,
            "ObjectOwnership": "BucketOwnerPreferred",
        }

        # SPECIAL CASE: us-east-1 is the default region
        # Don't specify LocationConstraint for us-east-1, will cause API error
        if aws_env.aws_region != "us-east-1":
            create_args["CreateBucketConfiguration"] = {
                "LocationConstraint": aws_env.aws_region
            }

        s3_client.create_bucket(**create_args)

    except ClientError as ex:
        # PATTERN: String matching for error message inspection
        # Some errors require examining message text, not just error code
        error_message = str(ex)

        if "BucketAlreadyOwnedByYou" in error_message:
            # Not actually an error - bucket exists and we own it
            logger.debug(f"Bucket {bucket_name} already exists and is owned by this account")
            return  # Early return for "expected error" condition

        elif "BucketAlreadyExists" in error_message:
            # Bucket name taken by another account - raise domain exception
            raise BucketNameNotAvailable(bucket_name)

        else:
            # Unexpected error - re-raise
            raise ex


def list_objects(
    bucket_name: str, prefix: str, aws_provider: AwsClientProvider
) -> List[str]:
    """
    List all object keys in S3 bucket with given prefix.

    PATTERN: Pagination with NextToken loop
    - S3 ListObjectsV2 returns max 1000 objects per call
    - Use ContinuationToken to retrieve subsequent pages
    - Accumulate results across pages before returning

    DESIGN CHOICE: Manual pagination vs boto3 paginator
    # TODO: When to use manual NextToken loop vs boto3 get_paginator()?
    # This example shows manual approach for explicitness

    Args:
        bucket_name: S3 bucket name
        prefix: Object key prefix (e.g., "logs/2024/")
        aws_provider: Factory for creating boto3 clients

    Returns:
        List of object keys matching prefix

    Example:
        keys = list_objects("my-bucket", "logs/", aws_provider)
        for key in keys:
            print(f"Found object: {key}")
    """
    s3_client = aws_provider.get_s3()
    object_keys = []
    continuation_token = None

    # PATTERN: NextToken pagination loop
    # - Continue until no ContinuationToken in response
    # - Build kwargs dynamically (only include token if present)
    while True:
        # Build request kwargs
        kwargs = {"Bucket": bucket_name, "Prefix": prefix}

        # Include continuation token for subsequent pages
        if continuation_token:
            kwargs["ContinuationToken"] = continuation_token

        # Make API call
        response = s3_client.list_objects_v2(**kwargs)

        # Extract object keys from this page
        if "Contents" in response:
            for obj in response["Contents"]:
                object_keys.append(obj["Key"])

        # Check if more pages exist
        continuation_token = response.get("NextContinuationToken")
        if not continuation_token:
            # No more pages - exit loop
            break

    return object_keys


def delete_object(bucket_name: str, object_key: str, aws_provider: AwsClientProvider) -> None:
    """
    Delete object from S3 bucket.

    PATTERN: Simple wrapper with minimal error handling
    - Some operations are thin wrappers around boto3 calls
    - Still use dependency injection for consistency and testability
    - Let boto3 ClientError propagate for unexpected errors

    # TODO: Should this map ClientError to domain exception?
    # Current design lets boto3 errors bubble up for simplicity

    Args:
        bucket_name: S3 bucket name
        object_key: Object key to delete
        aws_provider: Factory for creating boto3 clients

    Example:
        delete_object("my-bucket", "logs/old-file.txt", aws_provider)
    """
    s3_client = aws_provider.get_s3()
    s3_client.delete_object(Bucket=bucket_name, Key=object_key)
    logger.info(f"Deleted object {object_key} from bucket {bucket_name}")


# =============================================================================
# ADDITIONAL PATTERNS TO EXPLORE
# =============================================================================
# The source codebase demonstrates additional patterns:
#
# 1. Dataclass returns for structured data
#    - See patterns.md section "7. Data Transfer Objects (Dataclasses)"
#    - Example: Return VpcDetails dataclass instead of raw EC2 response
#
# 2. Resource interface usage
#    - See patterns.md section "9. Resource vs Client Interfaces"
#    - Example: S3 bucket deletion with objects using resource interface
#
# 3. Advanced error handling
#    - See patterns.md section "5. Error Handling & Custom Exceptions"
#    - Example: Multiple exception types for different error scenarios
#
# 4. Pagination with boto3 paginators
#    - See patterns.md section "6. Pagination Patterns"
#    - Example: Using get_paginator() for S3 operations
#
# This example demonstrates core patterns. Consult patterns.md for complete coverage.
# =============================================================================
