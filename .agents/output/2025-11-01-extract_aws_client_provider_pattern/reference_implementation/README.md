# Reference Implementation - AWS Client Provider Pattern

Complete, working example demonstrating all **CRITICAL** patterns from the AWS SDK pattern guide.

---

## Structure

```
reference_implementation/
├── core/
│   ├── aws_client_provider.py    # Factory class (Pattern 1)
│   └── aws_environment.py         # Optional context dataclass
├── aws_interactions/
│   └── s3_interactions.py         # Service wrapper (Patterns 2-6)
└── tests/
    └── test_s3_interactions.py    # Test suite (Patterns 7-10)
```

---

## Pattern Mapping

### Implementation Patterns (core/ + aws_interactions/)

| Pattern | File | Lines | Description |
|---------|------|-------|-------------|
| **1. Factory Pattern** | `core/aws_client_provider.py` | 14-104 | AwsClientProvider class with getter methods |
| **2. Dependency Injection** | `aws_interactions/s3_interactions.py` | All functions | `aws_provider` parameter in all wrappers |
| **3. Service Wrapper Structure** | `aws_interactions/s3_interactions.py` | 51-80, 83-109, etc. | Module-level functions with consistent structure |
| **4. Error Handling** | `aws_interactions/s3_interactions.py` | 26-29, 74-79, 98-104 | Custom exceptions + ClientError mapping |
| **5. Data Transfer Objects** | `aws_interactions/s3_interactions.py` | 43-48 | S3Object dataclass |
| **6. Enum-Based Status** | `aws_interactions/s3_interactions.py` | 33-38 | BucketStatus enum |

### Testing Patterns (tests/)

| Pattern | File | Lines | Description |
|---------|------|-------|-------------|
| **7 (13). Mocking AwsClientProvider** | `test_s3_interactions.py` | 20-33, all tests | Mock provider returns mock clients |
| **8 (14). Mocking boto3 Clients** | `test_s3_interactions.py` | 37-57, 91-111 | Mock return_value and side_effect |
| **9 (17). Error Scenario Testing** | `test_s3_interactions.py` | 37-84, 117-139 | Test 403, 404, unexpected errors, domain exceptions |
| **10 (18). Pagination Testing** | `test_s3_interactions.py` | 143-185 | Test multi-page results accumulation |

---

## Key Examples

### Pattern 1: Factory Pattern

```python
# core/aws_client_provider.py:14-104
class AwsClientProvider:
    def __init__(self, aws_profile, aws_region, aws_compute, assume_role_arn):
        # Store configuration

    def _get_session(self) -> boto3.Session:
        # Create session with credentials/role assumption

    def get_s3(self):
        session = self._get_session()
        return session.client("s3")
```

**Demonstrates**:
- Getter methods for each AWS service
- Private `_get_session()` for credential logic
- Session created per-call (not cached)

---

### Pattern 2: Dependency Injection

```python
# aws_interactions/s3_interactions.py:51-80
def get_bucket_status(
    bucket_name: str,
    aws_provider: AwsClientProvider  # ← Injected parameter
) -> BucketStatus:
    s3_client = aws_provider.get_s3()  # ← Get client from provider
    # ...
```

**Demonstrates**:
- Provider accepted as parameter (not global)
- Provider parameter after domain parameters
- Request specific client via `get_*()` method

---

### Pattern 3: Service Wrapper Structure

```python
# aws_interactions/s3_interactions.py:83-109
def create_bucket(bucket_name: str, aws_provider: AwsClientProvider) -> None:
    """Business-focused docstring."""
    # 1. Get boto3 client from provider
    s3_client = aws_provider.get_s3()

    # 2. Make AWS SDK call(s)
    try:
        s3_client.create_bucket(Bucket=bucket_name)

    # 3. Handle errors & transform to domain concepts
    except ClientError as e:
        # Map to domain exception
```

**Demonstrates**:
- Module-level function (not class method)
- Stateless (no instance state)
- Get client → Call boto3 → Handle errors → Return domain object

---

### Pattern 4: Error Handling

```python
# aws_interactions/s3_interactions.py:51-80
def get_bucket_status(...):
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        return BucketStatus.EXISTS_HAVE_ACCESS

    except ClientError as e:
        error_code = e.response["Error"]["Code"]  # ← Inspect error code

        if error_code == "403":
            return BucketStatus.EXISTS_NO_ACCESS
        elif error_code == "404":
            return BucketStatus.DOES_NOT_EXIST
        else:
            raise  # ← Re-raise unexpected errors
```

**Demonstrates**:
- Inspect `error_code` from ClientError response
- Map expected errors to domain enum values
- Re-raise unexpected errors (don't swallow)

---

### Pattern 5: Data Transfer Objects

```python
# aws_interactions/s3_interactions.py:43-48
@dataclass
class S3Object:
    """Domain representation (not raw boto3 dict)."""
    key: str
    size_bytes: int
    last_modified: str

# aws_interactions/s3_interactions.py:151-158
for obj in page.get("Contents", []):
    objects.append(S3Object(  # ← Transform to dataclass
        key=obj["Key"],
        size_bytes=obj["Size"],
        last_modified=str(obj["LastModified"])
    ))
```

**Demonstrates**:
- `@dataclass` decorator for structure
- Domain-focused field names (differ from boto3 keys)
- Transform boto3 dict to typed object

---

### Pattern 6: Enum-Based Status

```python
# aws_interactions/s3_interactions.py:33-38
class BucketStatus(Enum):
    """Domain status (not strings or booleans)."""
    EXISTS_HAVE_ACCESS = "exists_have_access"
    EXISTS_NO_ACCESS = "exists_no_access"
    DOES_NOT_EXIST = "does_not_exist"

# aws_interactions/s3_interactions.py:70-78
if error_code == "403":
    return BucketStatus.EXISTS_NO_ACCESS  # ← Return enum member
```

**Demonstrates**:
- Enum for multi-value status (>2 states)
- Snake_case string values
- Type-safe returns (enables IDE autocomplete)

---

### Pattern 7 (13): Mocking AwsClientProvider

```python
# tests/test_s3_interactions.py:20-33
def test_get_bucket_status_when_exists_have_access():
    # Create mock boto3 client
    mock_s3_client = mock.Mock()
    mock_s3_client.head_bucket.return_value = {"ResponseMetadata": {...}}

    # Create mock provider that returns mock client
    mock_provider = mock.Mock()
    mock_provider.get_s3.return_value = mock_s3_client  # ← Wire up

    # Call wrapper with mock provider
    result = s3_interactions.get_bucket_status("test-bucket", mock_provider)

    # Verify
    assert result == s3_interactions.BucketStatus.EXISTS_HAVE_ACCESS
```

**Demonstrates**:
- Mock provider, not boto3 directly
- Mock provider's `get_*()` method returns mock client
- No @mock.patch needed

---

### Pattern 8 (14): Mocking boto3 Clients

```python
# tests/test_s3_interactions.py:37-48
# Exception side effect
mock_s3_client.head_bucket.side_effect = ClientError(
    error_response={"Error": {"Code": "403"}},
    operation_name="HeadBucket"
)

# tests/test_s3_interactions.py:143-167
# Multiple pages via paginator
mock_paginator.paginate.return_value = [page_1, page_2]
```

**Demonstrates**:
- `return_value` for success cases
- `side_effect` exception for errors
- `side_effect` list for multiple calls (pagination)

---

### Pattern 9 (17): Error Scenario Testing

```python
# tests/test_s3_interactions.py:60-73
def test_get_bucket_status_when_unexpected_error_then_raises():
    # Mock unexpected error code
    mock_s3_client.head_bucket.side_effect = ClientError(
        error_response={"Error": {"Code": "InternalError"}},
        operation_name="HeadBucket"
    )

    # Verify unexpected error is re-raised
    with pytest.raises(ClientError):
        s3_interactions.get_bucket_status("test-bucket", mock_provider)
```

**Demonstrates**:
- Test expected errors (403, 404)
- Test unexpected errors are re-raised
- Test idempotent errors (BucketAlreadyOwnedByYou)
- Test domain exception mapping

---

### Pattern 10 (18): Pagination Testing

```python
# tests/test_s3_interactions.py:143-185
def test_list_bucket_objects_with_pagination():
    # Mock multiple pages
    page_1 = {"Contents": [{"Key": "file1.txt", ...}, {"Key": "file2.txt", ...}]}
    page_2 = {"Contents": [{"Key": "file3.txt", ...}]}
    mock_paginator.paginate.return_value = [page_1, page_2]

    # Act
    result = s3_interactions.list_bucket_objects("test-bucket", mock_provider)

    # Assert: All pages accumulated
    assert len(result) == 3
```

**Demonstrates**:
- Test multiple pages (not just one)
- Verify results accumulated correctly
- Verify paginator called with correct parameters

---

## Usage

### Run Tests

```bash
# From reference_implementation/ directory
pytest tests/ -v
```

### Use as Template

1. **Copy core/** to your project
   - Modify `get_*()` methods in `AwsClientProvider` for services you need

2. **Copy structure** from `aws_interactions/s3_interactions.py`
   - Create one `<service>_interactions.py` per AWS service
   - Define custom exceptions, enums, dataclasses at top
   - Write wrapper functions following Pattern 3 structure

3. **Copy test patterns** from `tests/test_s3_interactions.py`
   - Create 1:1 test file for each wrapper module
   - Mock provider + client (Pattern 7, 8)
   - Test error scenarios (Pattern 9)
   - Test pagination (Pattern 10)

---

## What's NOT Included

This reference implementation focuses on **CRITICAL** patterns only. For additional patterns, see:

- **Session caching** (Pattern 3 - PREFERRED): See `references/patterns_implementation.md`
- **Manual pagination loops** (Pattern 6 - PREFERRED): See `references/patterns_implementation.md`
- **Abstract Base Classes** (Pattern 11 - PREFERRED): See `references/patterns_implementation.md`
- **Test naming conventions** (Pattern 12 - OBSERVED): See `references/patterns_testing.md`
- **AAA test structure** (Pattern 15 - OBSERVED): See `references/patterns_testing.md`
- **Patching strategies** (Pattern 21 - PREFERRED): See `references/patterns_testing.md`

---

## Integration with Guide

- **Quick Start**: See `aws_sdk_pattern_guide.md` Quick Start section for step-by-step setup
- **Core Patterns**: See guide sections for detailed explanations of each pattern
- **Full Details**: See `references/patterns_*.md` for comprehensive pattern catalog

---

## File Sizes

- `core/aws_client_provider.py`: ~104 lines
- `aws_interactions/s3_interactions.py`: ~180 lines
- `tests/test_s3_interactions.py`: ~225 lines
- Total: ~509 lines demonstrating all 10 CRITICAL patterns
