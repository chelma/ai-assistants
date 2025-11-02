"""
AwsEnvironment - Dataclass encapsulating AWS account/region context.

PATTERN DEMONSTRATED: Context dataclass for AWS environment information
- Lightweight encapsulation of account/region/profile
- Provides context without coupling to boto3 session objects

KEY CONCEPTS:
- AWS Environment = Account + Region + Profile
- Uniqueness: Same account+region can have different resources per profile
- Availability zones differ per account (e.g., us-east-1a maps to different physical DC)

WHEN TO USE:
- Service wrappers need account/region info for operations (e.g., S3 CreateBucket requires region)
- Logging/debugging context (which account/region/profile is being used)
- Building resource identifiers that include account info

DESIGN CHOICE: Why dataclass vs dict?
# TODO: What's the advantage of this structured approach?

See: https://docs.aws.amazon.com/cdk/v2/guide/environments.html
SOURCE: Extracted from aws-aio production codebase
"""

from dataclasses import dataclass


@dataclass
class AwsEnvironment:
    """
    AWS environment context (account + region + profile).

    Attributes:
        aws_account: AWS account ID (12-digit string)
        aws_region: AWS region code (e.g., "us-east-1", "eu-west-2")
        aws_profile: AWS CLI profile name used for credentials

    Example usage:
        env = aws_provider.get_aws_env()
        print(f"Operating in: {env}")  # "aws://123456789012/us-west-2"

        # Access individual fields
        if env.aws_region == "us-east-1":
            # Special handling for us-east-1
            pass
    """

    aws_account: str
    aws_region: str
    aws_profile: str

    def __str__(self) -> str:
        """String representation in AWS URI format."""
        return f"aws://{self.aws_account}/{self.aws_region}"
