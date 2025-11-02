"""
AwsClientProvider - Factory for creating boto3 AWS clients.

PATTERN DEMONSTRATED: Factory Pattern + Dependency Injection
- Centralizes boto3 client creation for testability and credential management
- Provides getter methods for each AWS service
- Supports multiple credential modes: profile-based, EC2 instance role, assumed role

KEY CONCEPTS:
- Single point of configuration for AWS profile, region, and role assumption
- Lazy client initialization (created on-demand via getter methods)
- Session created per getter call (not cached) # TODO: Why not cache sessions?
- Dependency injection pattern: service wrappers accept provider as parameter

WHEN TO USE THIS PATTERN:
- Applications interacting with multiple AWS services
- Need centralized credential/session management
- Supporting cross-account access or multiple AWS profiles
- Want testability through dependency injection

DESIGN CHOICES:
- Getter methods (get_s3, get_ec2, etc.) vs direct client dictionary access
  # TODO: What's the trade-off here?
- Module-level functions in service wrappers vs class-based wrappers
  # TODO: Why this architectural choice?

SOURCE: Extracted from aws-aio production codebase
"""

import logging
from typing import Dict

import boto3

from .aws_environment import AwsEnvironment

logger = logging.getLogger(__name__)


class AssumeRoleNotSupported(Exception):
    """Raised when attempting role assumption on AWS compute platform (not currently supported)."""

    def __init__(self):
        super().__init__("We don't currently support role assumption on AWS Compute platforms")


class AwsClientProvider:
    """
    Factory for creating boto3 AWS clients with centralized credential management.

    Supports multiple credential modes:
    - AWS CLI profile (default)
    - EC2 instance role (when aws_compute=True)
    - Cross-account role assumption (when assume_role_arn provided)

    Example usage:
        # Basic usage with default profile
        provider = AwsClientProvider()
        s3_client = provider.get_s3()

        # With specific profile and region
        provider = AwsClientProvider(aws_profile="prod", aws_region="us-west-2")

        # Cross-account access
        provider = AwsClientProvider(
            aws_profile="source-account",
            assume_role_arn="arn:aws:iam::123456789012:role/CrossAccountRole"
        )

        # On EC2 instance (uses instance role)
        provider = AwsClientProvider(aws_compute=True, aws_region="us-east-1")
    """

    def __init__(
        self,
        aws_profile: str = "default",
        aws_region: str = None,
        aws_compute: bool = False,
        assume_role_arn: str = None,
    ):
        """
        Initialize AWS client provider.

        Args:
            aws_profile: AWS CLI profile name (default: "default")
            aws_region: AWS region (default: use profile's configured region)
            aws_compute: Whether running on AWS compute (EC2, Lambda, etc.)
                        If True, uses instance/execution role instead of profile
            assume_role_arn: ARN of IAM role to assume for cross-account access
                            Only supported when aws_compute=False
        """
        self._aws_profile = aws_profile
        self._aws_region = aws_region
        self._aws_compute = aws_compute
        self._assume_role_arn = assume_role_arn

    def get_aws_env(self) -> AwsEnvironment:
        """
        Get AWS account/region context for the configured credentials.

        Returns:
            AwsEnvironment dataclass with account, region, and profile information

        Example:
            env = provider.get_aws_env()
            print(f"Operating in account {env.aws_account}, region {env.aws_region}")
        """
        logger.debug(
            f"Getting AWS Environment for profile '{self._aws_profile}' "
            f"and region '{self._aws_region}'"
        )

        sts_client = self.get_sts()

        # Determine region: use specified region, otherwise pull from boto3 client's metadata
        env_region = self._aws_region if self._aws_region else sts_client.meta.region_name

        # Get AWS account ID via STS GetCallerIdentity
        env_account = sts_client.get_caller_identity()["Account"]

        return AwsEnvironment(env_account, env_region, self._aws_profile)

    def _get_assumed_credentials(self, current_session: boto3.Session) -> Dict[str, str]:
        """
        Assume IAM role and return temporary credentials.

        Args:
            current_session: boto3 session for source account

        Returns:
            Dict with AccessKeyId, SecretAccessKey, SessionToken

        PATTERN: Cross-account access via STS AssumeRole
        """
        sts_client = current_session.client("sts")

        # Assume the role in the target account
        assumed_role_object = sts_client.assume_role(
            RoleArn=self._assume_role_arn,
            RoleSessionName="AwsClientProviderSession"  # TODO: Make session name configurable?
        )

        return assumed_role_object["Credentials"]

    def _get_session(self) -> boto3.Session:
        """
        Create boto3 session based on credential configuration.

        Returns:
            boto3.Session configured with appropriate credentials

        DESIGN CHOICE: Creates new session on each call vs caching
        # TODO: Why create new session per call instead of caching?
        # Possible reasons: avoid stale credentials, thread safety, simplicity?

        PATTERN: Session creation with credential mode selection
        - aws_compute=True: Use ambient EC2/Lambda credentials
        - assume_role_arn provided: Assume role for cross-account access
        - Otherwise: Use AWS CLI profile credentials
        """
        if self._aws_compute:
            # Use ambient credentials (EC2 instance role, Lambda execution role, etc.)
            current_account_session = boto3.Session()
        else:
            # Use AWS CLI profile credentials
            current_account_session = boto3.Session(
                profile_name=self._aws_profile, region_name=self._aws_region
            )

        if self._assume_role_arn and not self._aws_compute:
            # Cross-account access via role assumption
            creds = self._get_assumed_credentials(current_account_session)
            session_to_use = boto3.Session(
                aws_access_key_id=creds["AccessKeyId"],
                aws_secret_access_key=creds["SecretAccessKey"],
                aws_session_token=creds["SessionToken"],
                region_name=self._aws_region,
            )
        elif self._assume_role_arn and self._aws_compute:
            # Role assumption from compute platform not supported
            # TODO: Why this limitation? Technical complexity or security concern?
            raise AssumeRoleNotSupported()
        else:
            session_to_use = current_account_session

        return session_to_use

    # =============================================================================
    # Service Getter Methods
    # =============================================================================
    # PATTERN: Each AWS service gets a dedicated getter method
    # - Consistent naming: get_<service_name>()
    # - Each returns boto3 client via _get_session()
    # - Add new services by copying this pattern
    #
    # CUSTOMIZATION: Add/remove getter methods based on services your application uses
    # =============================================================================

    def get_acm(self):
        """Get AWS Certificate Manager (ACM) client."""
        session = self._get_session()
        client = session.client("acm")
        return client

    def get_cloudwatch(self):
        """Get CloudWatch client for metrics and alarms."""
        session = self._get_session()
        client = session.client("cloudwatch")
        return client

    def get_ec2(self):
        """Get EC2 client for compute, VPC, and networking operations."""
        session = self._get_session()
        client = session.client("ec2")
        return client

    def get_ecs(self):
        """Get ECS client for container orchestration."""
        session = self._get_session()
        client = session.client("ecs")
        return client

    def get_events(self):
        """Get EventBridge (Events) client for event routing."""
        session = self._get_session()
        client = session.client("events")
        return client

    def get_iam(self):
        """Get IAM client for identity and access management."""
        session = self._get_session()
        client = session.client("iam")
        return client

    def get_opensearch(self):
        """Get OpenSearch client for search and analytics."""
        session = self._get_session()
        client = session.client("opensearch")
        return client

    def get_s3(self):
        """Get S3 client for object storage operations."""
        session = self._get_session()
        client = session.client("s3")
        return client

    def get_s3_resource(self):
        """
        Get S3 resource interface (higher-level than client).

        DESIGN CHOICE: Resource vs Client interface
        - Default to client interface for most operations
        - Use resource when it provides significant convenience
        - Example: S3 resource makes bucket deletion with objects easier

        # TODO: Why this implementation uses global default session?
        # Inconsistent with other getters that use _get_session()
        """
        boto3.setup_default_session(profile_name=self._aws_profile)
        resource = boto3.resource("s3", region_name=self._aws_region)
        return resource

    def get_secretsmanager(self):
        """Get Secrets Manager client for secret storage."""
        session = self._get_session()
        client = session.client("secretsmanager")
        return client

    def get_ssm(self):
        """Get Systems Manager (SSM) client for parameter store and operations."""
        session = self._get_session()
        client = session.client("ssm")
        return client

    def get_sts(self):
        """Get STS client for security token operations and identity info."""
        session = self._get_session()
        client = session.client("sts")
        return client

    # TODO: Add additional service getters as needed for your application
    # Example for DynamoDB:
    #
    # def get_dynamodb(self):
    #     """Get DynamoDB client for NoSQL database operations."""
    #     session = self._get_session()
    #     client = session.client("dynamodb")
    #     return client
