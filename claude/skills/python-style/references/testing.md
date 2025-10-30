## Testing Approach

### Test Framework Preferences
- **Priority**: PREFERRED
- **Pattern**: Preference for Pytest
- **Examples**:
  ```python
  # pytest style (aws-aio)
  import pytest
  import unittest.mock as mock

  def test_WHEN_action_called_AND_condition_THEN_result():
      # Test implementation
      pass
  ```

### Test Naming Convention
- **Priority**: CRITICAL
- **Pattern**: `test_WHEN_<action>_<conditions>_THEN_<expected_result>` for comprehensive context
- **Examples**:
  - `test_WHEN_cmd_cluster_create_called_THEN_cdk_command_correct`
  - `test_WHEN_deploy_called_AND_not_bootstrapped_THEN_executes_command`
  - `test_WHEN_should_proceed_with_operation_AND_abort_usage_THEN_as_expected`
**Observation**: The naming convention makes test purpose immediately clear and provides complete context without needing to read the test body.

### Mocking Strategy
- **Priority**: CRITICAL
- **Pattern**: Use `unittest.mock` with `@mock.patch` decorator and `side_effect` for complex scenarios
- **Examples**:
  ```python
  @mock.patch("commands.cluster_create.AwsClientProvider")
  @mock.patch("commands.cluster_create.CdkClient")
  def test_WHEN_cmd_cluster_create_called_THEN_cdk_command_correct(
      mock_cdk_client_cls, mock_aws_provider_cls):
      # Set up our mock
      mock_client = mock.Mock()
      mock_cdk_client_cls.return_value = mock_client

      # Run our test
      cmd_cluster_create("profile", "region", "my-cluster", ...)

      # Check our results
      expected_calls = [mock.call(["stack1", "stack2"], context={"key": "value"})]
      assert expected_calls == mock_client.deploy.call_args_list
  ```

  ```python
  # Using side_effect for sequences
  mock_call_shell.side_effect = [
      (1, [exceptions.NOT_BOOTSTRAPPED_1]),
      (0, ["bootstrap success"]),
      (0, ["deploy success"])
  ]
  ```
**Observation**: Mock at the module level to control dependencies, use `side_effect` for sequential returns or exceptions, and verify behavior with `call_args_list`.

### Test Organization
- **Priority**: PREFERRED
- **Pattern**: One test class per production class, with `setUp()` for common initialization
- **Examples**:
  ```python
  class RESTClientTestCase(TestCase):
      def setUp(self):
          self.connection_details = ConnectionDetails(base_url="http://api.example.com")
          self.client = RESTClient(connection_details=self.connection_details)

      @patch("requests.get")
      def test_get_happy_path(self, mock_get):
          # Test using self.client
          pass

      @patch("requests.get")
      def test_get_error_path(self, mock_get):
          # Test using self.client
          pass
  ```

### Assertion Style
- **Priority**: CRITICAL
- **Pattern**: Direct equality assertions with `assert expected == actual` order
- **Examples**:
  ```python
  expected_value = UserConfig(0.1, 30, 120, 1, 30)
  assert expected_value == actual_value

  expected_calls = [mock.call(constants.get_cluster_ssm_param_name("cluster-name"), "userConfig", mock_provider)]
  assert expected_calls == mock_ssm_ops.get_ssm_param_json_value.call_args_list
  ```
**Observation**: Always put expected value first, actual value second. Use named variables for complex expectations to improve readability.

### Test Data Organization
- **Priority**: PREFERRED
- **Pattern**: Module-level constants for large test data (events, fixtures), method-level for simple test data
- **Examples**:
  ```python
  # Module-level test events (at end of file)
  TEST_EVENT_EC2_RUNNING = {
      "version": "0",
      "id": "59444e21-1551-617e-42f7-4ada553d3463",
      "detail-type": "EC2 Instance State-change Notification",
      # ... 900 lines of test event data
  }
  ```

  ```python
  # Method-level for simple data
  def test_WHEN_get_next_user_config_called_AND_partial_update_THEN_as_expected(mock_ssm_ops):
      mock_ssm_ops.get_ssm_param_json_value.return_value = {
          "expectedTraffic": 1.2,
          "spiDays": 40,
          # ...
      }
  ```

### Comprehensive Test Coverage
- **Priority**: CRITICAL
- **Pattern**: Test happy path, error conditions, edge cases, and boundary conditions
- **Examples**:
  ```python
  # Happy path
  def test_WHEN_get_next_vni_called_AND_next_available_THEN_returns_it():
      pass

  # Error condition
  def test_WHEN_get_next_vni_called_AND_pool_exhausted_THEN_raises():
      with pytest.raises(vni.VniPoolExhausted):
          provider.get_next_vni()

  # Edge case
  def test_WHEN_get_next_vni_called_AND_next_not_available_THEN_handles_gracefully():
      pass
  ```

### Test Scenario Organization
- **Priority**: PREFERRED
- **Pattern**: Multiple scenarios within single test function using inline comments `# TEST:` to separate
- **Examples**:
  ```python
  def test_WHEN_should_proceed_with_operation_AND_check_overlapping_cidrs_THEN_as_expected(mock_confirm):
      # TEST: Both specified, and don't overlap
      cluster_plan = ClusterPlan(...)
      actual_value = _should_proceed_with_operation(...)
      assert True == actual_value

      # TEST: Both specified, and do overlap
      cluster_plan = ClusterPlan(...)
      actual_value = _should_proceed_with_operation(...)
      assert False == actual_value
  ```
**Observation**: When testing multiple related scenarios, group them in a single test function with clear `# TEST:` comments rather than creating many tiny test functions.

### Mock Verification Patterns
- **Priority**: CRITICAL
- **Pattern**: Verify mock behavior with `call_args_list`, use `mock.ANY` for unimportant parameters
- **Examples**:
  ```python
  expected_calls = [
      mock.call(
          ["stack1", "stack2"],
          context={"key": "value"}
      )
  ]
  assert expected_calls == mock_client.deploy.call_args_list

  # Using mock.ANY for unimportant params
  expected_upload_calls = [mock.call(mock.ANY)]
  assert expected_upload_calls == mock_upload.call_args_list
  ```

### Exception Testing
- **Priority**: CRITICAL
- **Pattern**: Use `pytest.raises` context manager for exception verification
- **Examples**:
  ```python
  with pytest.raises(cap.TooMuchTraffic):
      cap.get_capture_node_capacity_plan(cap.MAX_TRAFFIC + 10, azs)

  with pytest.raises(exceptions.CdkDeployFailedUnknown):
      client.deploy(["MyStack"])
  ```

### Module-Level Test Constants
- **Priority**: PREFERRED
- **Pattern**: Define test constants at module level for reuse across multiple test functions
- **Examples**:
  ```python
  TEST_CLUSTER = "my-cluster"

  def test_WHEN_cmd_cluster_destroy_called_AND_dont_destroy_everything_THEN_expected_cmds(...):
      cmd_cluster_destroy("profile", "region", TEST_CLUSTER, False, True)
      # ...

  def test_WHEN_cmd_cluster_destroy_called_AND_destroy_everything_THEN_expected_cmds(...):
      cmd_cluster_destroy("profile", "region", TEST_CLUSTER, True, False)
      # ...
  ```
**Observation**: Reduces duplication and ensures consistent test data across related tests

### Custom Mock Classes for Complex Test Scenarios
- **Priority**: PREFERRED
- **Pattern**: Extend `unittest.mock.Mock` to create custom mock classes with stateful behavior
- **Examples**:
  ```python
  class MockPexpectProcess(mock.Mock):
      def __init__(self, *args, before_values=[], exit_status=0, expect_values=[], **kwargs):
          super().__init__()
          self._expect_calls = 0
          self._before_values = before_values
          self.exitstatus = exit_status
          self._expect_values = expect_values

      def expect(self, *arg, **kwargs):
          if self._expect_calls >= len(self._expect_values):
              raise EndTestUnxpectedException()

          self.before = self._before_values[self._expect_calls]
          return_value = self._expect_values[self._expect_calls]
          self._expect_calls += 1
          return return_value
  ```
**Observation**: Custom mock classes encapsulate complex mock behavior (like sequence tracking) rather than using nested side_effect lambdas

### Test Exception Classes for Flow Control
- **Priority**: PREFERRED
- **Pattern**: Define custom exceptions at module level to control test execution flow
- **Examples**:
  ```python
  class EndTestExpectedException(Exception):
      pass

  class EndTestUnxpectedException(Exception):
      pass

  @mock.patch('core.shell_interactions.pexpect')
  def test_WHEN_call_shell_command_called_THEN_process_spawned_as_expected(mock_pexpect):
      mock_pexpect.spawn.side_effect = EndTestExpectedException()
      with pytest.raises(EndTestExpectedException):
          shell.call_shell_command('test command')
  ```
**Observation**: Allows early termination of test execution when verifying specific branches or sections of code

### pytest Fixtures for Test Data
- **Priority**: PREFERRED
- **Pattern**: Use `@pytest.fixture` to define reusable test data and mock objects
- **Examples**:
  ```python
  @pytest.fixture
  def success_response():
      response = mock.Mock()
      response.json.return_value = {"key": "value"}
      response.status_code = 200
      response.reason = "fate"
      response.text = str(response.json())
      response.url = str(REST_PATH)
      return response

  def test_WHEN_perform_get_AND_success_THEN_as_expected(mock_requests, success_response):
      mock_requests.get.return_value = success_response
      actual_value = ops.perform_get(rest_path=REST_PATH)
      # ...
  ```
**Observation**: Fixtures eliminate duplication when multiple tests need similar mock objects

### pytest tmpdir Fixture for Filesystem Testing
- **Priority**: PREFERRED
- **Pattern**: Use pytest's built-in `tmpdir` fixture for temporary file/directory testing
- **Examples**:
  ```python
  @pytest.fixture
  def local_test_file_path(tmpdir):
      temp_file_path = tmpdir.join("test.txt")
      with open(temp_file_path, "w") as file_handle:
          file_handle.write("Aure entuluva!" * 1000)  # larger than 4096 bytes
      return str(temp_file_path)

  def test_WHEN_get_md5_of_file_called_THEN_as_expected(local_test_file_path):
      mock_file = mock.Mock()
      mock_file.local_path = local_test_file_path
      actual_md5 = ver.get_md5_of_file(mock_file)
      assert "ffc2c982c7363a318de4b18ee1357402" == actual_md5
  ```
**Observation**: Fixtures can wrap tmpdir to create custom test files with specific content

---

