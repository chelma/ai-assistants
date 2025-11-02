"""
AWS Client Provider - Factory for creating boto3 clients with centralized credential management.

CRITICAL PATTERN DEMONSTRATED:

Pattern 1: Factory Pattern
    - Centralized factory class for creating boto3 clients on-demand
    - Getter methods for each AWS service: get_s3(), get_ec2(), get_sts()
    - Private _get_session() method centralizes credential logic
    - Session created per-call (not cached) for simplicity
    - See: AwsClientProvider class lines 9-101

KEY DESIGN CHOICES:

1. Getter methods vs get_client(service_name)
    - Explicit methods (get_s3, get_ec2) are more obvious and easier to mock
    - Allows service-specific customization without conditional logic
    - Minimal maintenance burden (methods rarely change)

2. Session-per-call vs caching
    - Creating session each call is simpler than cache management
    - Supports different regions/credentials within same application lifecycle
    - Session overhead is negligible compared to cache complexity

3. _get_session() credential hierarchy
    - EC2 instance profile (aws_compute=True, no assume_role_arn)
    - Named profile (~/.aws/credentials)
    - Cross-account role assumption (STS AssumeRole)
    - See: lines 46-83

WHEN TO USE THIS PATTERN:
- Applications needing credentials for multiple environments (dev/staging/prod)
- Multi-account AWS access (role assumption)
- Both local development (named profiles) and cloud runtime (instance profiles)
- Projects requiring testable AWS integrations (mock the provider)
"""
from typing import Any

import boto3


class AwsClientProvider:
    """
    Factory for creating boto3 clients with centralized session and credential management.

    Supports:
    - Named AWS profiles (~/.aws/credentials)
    - Custom regions
    - EC2 instance profile credentials
    - Cross-account role assumption via STS

    Example:
        >>> provider = AwsClientProvider(aws_profile="prod", aws_region="us-east-1")
        >>> s3_client = provider.get_s3()
        >>> ec2_client = provider.get_ec2()
    """

    def __init__(
        self,
        aws_profile: str = "default",
        aws_region: str = None,
        aws_compute: bool = False,
        assume_role_arn: str = None,
    ):
        """
        Initialize AWS client provider with configuration.

        aws_profile: AWS profile name from ~/.aws/credentials (default: "default")
        aws_region: AWS region (default: None, uses profile default or us-east-1)
        aws_compute: If True, use EC2 instance profile credentials (default: False)
        assume_role_arn: Optional ARN of role to assume via STS (default: None)
        """
        self.aws_profile = aws_profile
        self.aws_region = aws_region
        self.aws_compute = aws_compute
        self.assume_role_arn = assume_role_arn

    def _get_session(self) -> boto3.Session:
        """
        Create boto3 session with appropriate credentials. Returns boto3.Session configured with
        credentials and region.

        Demonstrates Pattern 3 (Session & Credential Management):
        - EC2 instance profile credentials (aws_compute=True, no assume_role_arn)
        - Named profile credentials (aws_profile)
        - Cross-account role assumption (assume_role_arn)
        """
        # EC2 instance profile credentials (no assume role)
        if self.aws_compute and not self.assume_role_arn:
            return boto3.Session(region_name=self.aws_region)

        # Named profile from ~/.aws/credentials
        session = boto3.Session(
            profile_name=self.aws_profile, region_name=self.aws_region
        )

        # Cross-account role assumption via STS
        if self.assume_role_arn:
            sts_client = session.client("sts")
            assumed_role = sts_client.assume_role(
                RoleArn=self.assume_role_arn,
                RoleSessionName="aws-client-provider-session",
            )

            credentials = assumed_role["Credentials"]
            session = boto3.Session(
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"],
                region_name=self.aws_region,
            )

        return session

    def get_s3(self) -> Any:
        """Get boto3 S3 client."""
        session = self._get_session()
        return session.client("s3")

    def get_ec2(self) -> Any:
        """Get boto3 EC2 client."""
        session = self._get_session()
        return session.client("ec2")

    def get_sts(self) -> Any:
        """Get boto3 STS client."""
        session = self._get_session()
        return session.client("sts")

    # Add additional get_<service>() methods as needed for your project
