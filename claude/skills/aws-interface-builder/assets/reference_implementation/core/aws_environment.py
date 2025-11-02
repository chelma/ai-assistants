"""
AWS Environment context - Lightweight dataclass for account/region information.

Optional utility for functions that need account context.
"""
from dataclasses import dataclass


@dataclass
class AwsEnvironment:
    """
    AWS account and region context.

    Example:
        >>> env = AwsEnvironment("123456789012", "us-east-1", "prod")
        >>> print(f"Deploying to {env.aws_region} in account {env.aws_account_id}")
    """

    aws_account_id: str
    aws_region: str
    aws_profile: str
