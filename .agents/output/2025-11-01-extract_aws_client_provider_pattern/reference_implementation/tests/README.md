# Test Examples

Comprehensive testing patterns for AWS SDK wrapper functions.

## Files

**test_s3_wrapper_comprehensive.py** - Complete demonstration of all 11 testing patterns:
- Pattern 12: Test naming convention (`test_WHEN_action_AND_condition_THEN_result`)
- Pattern 13: Mocking AwsClientProvider
- Pattern 14: Mocking boto3 clients (return_value, side_effect)
- Pattern 15: AAA pattern with comment markers
- Pattern 16: Assertion patterns (call verification, return values, call counts)
- Pattern 17: Error scenario testing (ClientError → domain exceptions)
- Pattern 18: Pagination testing (NextToken loops)
- Pattern 19: Multi-scenario testing (multiple TEST sections)
- Pattern 20: Side effects for sequential calls
- Pattern 21: Patching strategies (@mock.patch decorator)
- Pattern 22: Testing ABCs (see references/patterns_testing.md for details)

## Key Testing Principles

**Test Naming**: `test_WHEN_<action>_called_AND_<condition>_THEN_<expected_result>`
- Searchable and self-documenting
- Consistent across entire test suite

**Test Structure**: AAA pattern with explicit comments
- `# ARRANGE`: Set up mocks
- `# ACT`: Call function under test
- `# ASSERT`: Verify behavior

**Mocking Pattern**: Provider → Client hierarchy
```python
mock_client = mock.Mock()
mock_provider = mock.Mock()
mock_provider.get_service.return_value = mock_client
```

**Assertion Convention**: `expected == actual` (expected on left)

**Pagination Testing**: Use `side_effect` with list of responses
```python
mock_client.list_items.side_effect = [
    {"Items": [...], "NextToken": "token-1"},  # First page
    {"Items": [...]}  # Final page, no NextToken
]
```

## Running Tests

```bash
# Install dependencies
pip install pytest botocore

# Run all tests
pytest tests/

# Run with verbose output
pytest -v tests/

# Run specific test
pytest tests/test_s3_wrapper_comprehensive.py::test_WHEN_get_bucket_status_called_THEN_as_expected
```

## Complete Pattern Documentation

See `../references/patterns_testing.md` for comprehensive documentation of all testing patterns with multiple examples from production code.
