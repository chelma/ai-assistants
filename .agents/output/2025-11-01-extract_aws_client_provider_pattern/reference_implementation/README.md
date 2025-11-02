# Reference Implementation: AWS SDK Interaction Pattern

Domain-agnostic implementation of the Factory-Provider-Wrapper pattern for boto3.

## Structure

```
reference_implementation/
├── core/
│   ├── aws_client_provider.py    # Factory for boto3 clients (137 lines)
│   └── aws_environment.py         # Account/region context dataclass (19 lines)
└── example_service/
    └── s3_wrapper.py              # Example service wrapper demonstrating patterns
```

## Key Patterns Demonstrated

**Factory Pattern** (`core/aws_client_provider.py`)
- Centralized boto3 client creation
- Getter methods for each AWS service
- Cross-account role assumption support
- Multiple credential modes (profile, EC2 instance role, assumed role)

**Dependency Injection** (`example_service/s3_wrapper.py`)
- Service wrapper functions accept `AwsClientProvider` as parameter
- Enables testability through mocking
- Callers control credential context

**Error Handling** (`example_service/s3_wrapper.py`)
- Map boto3 `ClientError` to domain-specific exceptions
- Error code inspection for status classification
- String matching for complex error scenarios

**Pagination** (`example_service/s3_wrapper.py:list_objects()`)
- NextToken loop for AWS paginated responses
- Accumulate results across pages

**Status Classification** (`example_service/s3_wrapper.py`)
- Enum-based return values for fixed state sets
- Example: `BucketStatus.EXISTS_HAVE_ACCESS`

## Usage

See `../aws_sdk_pattern_guide.md` for step-by-step implementation guide.

## Customization Points

All files contain `# TODO` comments marking areas requiring customization:
- Service getter methods (add services your application uses)
- Exception types (define domain-specific exceptions)
- Logging configuration
- Session caching strategy
- Resource vs client interface decisions

## Source

Extracted from aws-aio production codebase (Arkime infrastructure management).
Patterns tested with 2,890 lines of production code + comprehensive test suite.
