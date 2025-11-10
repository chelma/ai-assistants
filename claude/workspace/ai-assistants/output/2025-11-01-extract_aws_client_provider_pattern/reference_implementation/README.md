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

## Pattern Examples

Each file's module-level docstring contains detailed pattern demonstrations with line references:

**Implementation Patterns:**
- **Pattern 1**: See `core/aws_client_provider.py` module docstring - Factory pattern with KEY DESIGN CHOICES explained
- **Patterns 2-6**: See `aws_interactions/s3_interactions.py` module docstring - All CRITICAL implementation patterns with line references

**Testing Patterns:**
- **Patterns 7-10**: See `tests/test_s3_interactions.py` module docstring - All CRITICAL testing patterns with line references and test organization guidance

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
