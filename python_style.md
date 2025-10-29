# Chris's Python Coding Style Guide

**Last Updated**: 2025-10-29
**Status**: Phase 2 Complete (All 9 iterations complete)
**Coverage**: 152 files analyzed (~24,500 lines from both ocsf-playground and aws-aio)

This document captures Chris's personal Python coding style and engineering philosophy based on analysis of two production repositories: `ocsf-playground` and `aws-aio`.

---

## 1. Code Organization & Architecture

### Module Organization
- **Confidence**: High
- **Pattern**: Domain-driven directory structure with clear separation of concerns
- **Examples**:
  - `ocsf-playground`: `backend/{expert_name}_expert/` structure for each AI expert system
  - `aws-aio`: `{function}_interactions/` for external system boundaries (aws, cdk, opensearch)

**Observation**: Each major domain gets its own package with explicit boundaries:
```
backend/
├── categorization_expert/    # Self-contained expert
├── entities_expert/           # Self-contained expert
├── regex_expert/              # Self-contained expert
└── core/                      # Shared utilities
```

### Separation of Concerns
- **Confidence**: High
- **Pattern**: Dedicated modules for specific responsibilities
- **Examples**:
  - `expert_def.py` - Expert initialization and invocation
  - `task_def.py` - Task data structures
  - `tool_def.py` - LangChain tool definitions
  - `validators.py` - Validation logic
  - File: `ocsf-playground/backend/core/experts.py:1`

### Package Naming
- **Confidence**: High
- **Pattern**: `snake_case` for packages/modules, descriptive and specific
- **Examples**: `aws_interactions`, `entities_expert`, `capacity_planning`, `config_wrangling`

---

## 2. Type System & Annotations

### Type Hints Usage
- **Confidence**: High
- **Pattern**: Comprehensive type hints on function signatures, including return types
- **Examples**:
  ```python
  def get_capture_node_capacity_plan(expected_traffic: float, azs: List[str]) -> CaptureNodesPlan:
  ```
  File: `aws-aio/manage_arkime/core/capacity_planning.py:100`

  ```python
  def invoke_expert(expert: Expert, task: PlaygroundTask) -> PlaygroundTask:
  ```
  File: `ocsf-playground/playground/backend/core/experts.py:37`

### Custom Types & Type Aliases
- **Confidence**: High
- **Pattern**: Extensive use of TypeVar for generic type bounds on dataclasses
- **Examples**:
  ```python
  T_ClusterPlan = TypeVar('T_ClusterPlan', bound='ClusterPlan')

  @classmethod
  def from_dict(cls: Type[T_ClusterPlan], input: Dict[str, any]) -> T_ClusterPlan:
  ```
  File: `aws-aio/manage_arkime/core/capacity_planning.py:478-507`

### Typing Module Constructs
- **Confidence**: High
- **Pattern**: Uses `Dict`, `List`, `Type`, `TypeVar`, `Callable`, `Any` from typing
- **Observation**: Prefers explicit imports from typing module rather than PEP 585 built-in generics
- **Examples**: `from typing import Dict, Any, Callable, Type`

### Runtime Type Checking
- **Confidence**: Medium
- **Pattern**: Manual type validation in critical paths (serializers, task setters)
- **Examples**:
  ```python
  def set_work_item(self, new_work_item: Any):
      if not isinstance(new_work_item, EntityReport):
          raise TypeError("new_work_item must be of type EntityReport")
  ```
  File: `ocsf-playground/playground/backend/entities_expert/task_def.py:19-22`

  ```python
  # Type validation in transformers
  if isinstance(extract_output, list):
      report.append_entry(f"The extract output matches the expected type: 'list'", logger.info)
  else:
      report.append_entry(f"The extract output does NOT match the expected type: 'list'", logger.warning)
      raise ValueError(f"The extract output does NOT match the expected type: 'list'")
  ```
  File: `ocsf-playground/playground/backend/entities_expert/validators.py:50-54`

### Pydantic for Schema Validation
- **Confidence**: High
- **Pattern**: Uses Pydantic BaseModel for LangChain tool schemas and structured inputs
- **Examples**:
  ```python
  class EntityInput(BaseModel):
      """A single entity extracted from the data entry"""
      value: str = Field(description="The raw value extracted from the input data...")
      description: str = Field(description="A precise explanation of what the value represents...")
  ```
  File: `ocsf-playground/playground/backend/entities_expert/tool_def.py:22-25`

---

## 3. Documentation Philosophy

### Docstring Style
- **Confidence**: Low-Medium
- **Pattern**: Minimal docstrings; some functions have triple-quoted explanatory comments
- **Examples**:
  ```python
  def get_ecs_sys_resource_plan(instance_type: str) -> EcsSysResourcePlan:
      """
      Creates a capacity plan for the indicated instance type.
      instance_type: The instance type to plan for
      """
  ```
  File: `aws-aio/manage_arkime/core/capacity_planning.py:177-181`

- **Custom serializer field to validate entity data with the structure:**
  ```python
  class EntityField(serializers.Field):
      """
      Custom serializer field to validate entity data with the structure:
      {"value": <string>, "description": <dict>}
      """
  ```
  File: `ocsf-playground/playground/playground_api/serializers.py:65-69`

### Comment Style
- **Confidence**: High
- **Pattern**: Inline comments explain "why" not "what", often for complex business logic
- **Examples**:
  ```python
  # Inference APIs can be throttled pretty aggressively.  Performing them as a batch operation can help with increasing
  # throughput. Ideally, we'd be using Bedrock's batch inference API, but Bedrock's approach to that is an asynchronous
  # process that writes the results to S3 and returns a URL to the results.  This is not implemented by default in the
  # ChatBedrockConverse class, so we'll skip true batch processing for now.  Instead, we'll just perform the inferences in
  # parallel with aggressive retry logic.
  ```
  File: `ocsf-playground/playground/backend/core/inference.py:38-42`

### Hardcoded Values Documentation
- **Confidence**: High
- **Pattern**: Inline comments explain magic numbers and why values are chosen
- **Examples**:
  ```python
  MINIMUM_TRAFFIC = 0.01 # Gbps; arbitrarily chosen, but will yield a minimal cluster
  CAPACITY_BUFFER_FACTOR = 1.25 # Arbitrarily chosen
  MASTER_NODE_COUNT = 3 # Recommended number in docs
  ```
  File: `aws-aio/manage_arkime/core/capacity_planning.py:12-14`

### Prompt Engineering for LLMs
- **Confidence**: High
- **Pattern**: Multi-paragraph prompt templates with XML-tagged sections for structured guidance
- **Examples**:
  ```python
  analyze_prompt_template = """
  You are an AI assistant whose goal is to assist users in transforming their log and data entries...

  While working towards your goal, you will ALWAYS follow the below general guidelines:
  <guidelines>
  - Do not attempt to be friendly in your responses.  Be as direct and succinct as possible.
  - Think through the problem carefully.
  </guidelines>

  <output_guidelines>
  - When selecting entities, your goal is to fill out the OCSF schema as completely as possible.
  </output_guidelines>

  <ocsf_version>{ocsf_version}</ocsf_version>
  <input_entry>{input_entry}</input_entry>
  """
  ```
  File: `ocsf-playground/playground/backend/entities_expert/prompting/templates.py:1-67`

**Observation**: Templates use XML tags for structured sections, Python format strings for parameterization, and explicit behavioral constraints

### String Templates with .format()
- **Confidence**: High
- **Pattern**: Multi-line string constants with `.format()` for parameterization, used for prompt/knowledge embedding
- **Examples**:
  ```python
  OCSF_KNOWLEDGE = """
  <ocsf_event_classes>
  {ocsf_event_classes}
  </ocsf_event_classes>
  """.format(ocsf_event_classes=json.dumps(OCSF_EVENT_CLASSES, indent=4))
  ```
  File: `ocsf-playground/playground/backend/categorization_expert/prompting/knowledge/ocsf_v1_1_0.py:9-13`

**Observation**: For static templates with dynamic content insertion, use triple-quoted strings with `.format()` called immediately at module level. This pre-renders the template once at import time.

### Inline Comments for Provenance
- **Confidence**: High
- **Pattern**: Include comments with links to ChatGPT conversations, documentation, and explanations of data origin
- **Examples**:
  ```python
  # This JSON blob was created with some prompt engineering and manually pasting portions of the OCSF
  # documentation into a GenAI prompt.
  #
  # See: https://schema.ocsf.io/1.1.0/
  # See: https://chatgpt.com/share/67ed81bd-4c64-8001-8824-6084c99a76fe
  OCSF_EVENT_CLASSES = [
      # ... data
  ]
  ```
  File: `ocsf-playground/playground/backend/core/ocsf/ocsf_schema_v1_1_0.py:3-8`

**Observation**: When data is generated or derived from external sources (AI, documentation, conversations), include inline comments documenting the source and method. This aids future maintenance and verification.

---

## 4. Error Handling & Robustness

### Custom Exception Hierarchy
- **Confidence**: High
- **Pattern**: Custom exceptions inherit from base Exception with descriptive names
- **Examples**:
  ```python
  class TooMuchTraffic(Exception):
      def __init__(self, expected_traffic: int):
          super().__init__(f"User's expected traffic ({expected_traffic} Gbps) exceeds the limit of a single cluster ({MAX_TRAFFIC})")
  ```
  File: `aws-aio/manage_arkime/core/capacity_planning.py:73-75`

  ```python
  class ExpertInvocationError(Exception):
      pass
  ```
  File: `ocsf-playground/playground/backend/core/experts.py:34-35`

### Exception Naming
- **Confidence**: High
- **Pattern**: Descriptive, specific exception names that indicate the problem
- **Examples**: `TooMuchTraffic`, `NotEnoughStorage`, `InvalidCidr`, `FileNotGenerated`, `AssumeRoleNotSupported`, `RESTOperationFailedException`

### Logging Approach
- **Confidence**: High
- **Pattern**: Module-level logger instances; consistent use throughout
- **Examples**:
  ```python
  logger = logging.getLogger(__name__)
  ```
  File: `aws-aio/manage_arkime.py:25`

  ```python
  logger = logging.getLogger("backend")
  ```
  File: `ocsf-playground/playground/backend/core/experts.py:17`

### Django Multi-Handler Logging Configuration
- **Confidence**: High
- **Pattern**: Comprehensive logging setup with module-specific file handlers, separate debug/info levels
- **Examples**:
  ```python
  LOGGING = {
      'version': 1,
      'disable_existing_loggers': False,
      'formatters': {
          'verbose': {'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'},
      },
      'handlers': {
          'playground_api_debug_file': {
              'level': 'DEBUG',
              'class': 'logging.FileHandler',
              'filename': 'logs/playground_api.debug.log',
              'formatter': 'verbose',
          },
          'playground_api_info_file': {
              'level': 'INFO',
              'class': 'logging.FileHandler',
              'filename': 'logs/playground_api.info.log',
              'formatter': 'verbose',
          },
      },
      'loggers': {
          'playground_api': {
              'handlers': ['playground_api_debug_file', 'playground_api_info_file'],
              'level': 'DEBUG',
              'propagate': False,
          },
      },
  }
  ```
  File: `ocsf-playground/playground/playground/settings.py:151-211`

### Custom Logging Formatter with UTC Timestamps
- **Confidence**: High
- **Pattern**: Custom formatter for UTC timestamps and invisible Unicode line separators
- **Examples**:
  ```python
  class LoggingFormatter(logging.Formatter):
      def formatTime(self, record, datefmt=None):
          return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')

  # Invisible Unicode character for log entry boundaries
  LINE_SEP = '\u2063'

  file_formatter = LoggingFormatter(f"%(asctime)s - %(name)s - %(message)s{LINE_SEP}")
  ```
  File: `aws-aio/manage_arkime/core/logging_wrangler.py:8-49`

### Context Manager for Log Level Control
- **Confidence**: High
- **Pattern**: Temporarily change boto log levels, restore after with statement
- **Examples**:
  ```python
  @contextmanager
  def set_boto_log_level(log_level = 'INFO'):
      boto_log_level = logging.getLogger('boto').level
      botocore_log_level = logging.getLogger('botocore').level

      logging.getLogger('boto').setLevel(log_level)
      logging.getLogger('boto3').setLevel(log_level)
      logging.getLogger('botocore').setLevel(log_level)

      yield

      logging.getLogger('boto').setLevel(boto_log_level)
      logging.getLogger('boto3').setLevel(boto_log_level)
      logging.getLogger('botocore').setLevel(botocore_log_level)
  ```
  File: `aws-aio/manage_arkime/core/logging_wrangler.py:60-74`

### Log Levels
- **Confidence**: High
- **Pattern**: Strategic use of info, debug, warning, error levels
- **Examples**:
  ```python
  logger.info(f"Received heuristic creation request: {request.data}")
  logger.debug(f"Regex value:\n{result.regex.value}")
  logger.error(f"Regex creation failed: {str(e)}")
  logger.exception(e)  # Includes traceback
  ```
  File: `ocsf-playground/playground/playground_api/views.py:52-69`

### Input Validation
- **Confidence**: High
- **Pattern**: Early validation with clear error messages
- **Examples**:
  ```python
  def _validate_cidr(self, cidr_str: str ):
      overall_form = re.compile("^[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}/[0-9]{1,2}$")
      if not overall_form.match(cidr_str):
          raise InvalidCidr(cidr_str)
  ```
  File: `aws-aio/manage_arkime/core/capacity_planning.py:372-375`

### CLI Mutually Exclusive Flag Validation
- **Confidence**: High
- **Pattern**: Validate mutually exclusive CLI flags with clear error messages and sys.exit(1)
- **Examples**:
  ```python
  def cmd_config_pull(profile: str, region: str, cluster_name: str, capture: bool, viewer: bool, previous: bool,
                      config_version: int):
      try:
          if not (capture or viewer):
              logger.error("You must indicate whether to operate on the Capture or Viewer config; see --help.")
              sys.exit(1)
          elif capture and viewer:
              logger.error("You must indicate either to operate on the Capture or Viewer config, not both; see --help.")
              sys.exit(1)
          elif 1 < sum([1 for param in [config_version, previous] if param]):
              logger.error("You can only select one filter from the set: --config-version, --previous.")
              sys.exit(1)
          elif previous:
              # ... handle previous flag
          elif config_version:
              # ... handle config_version flag
          else:
              # ... default behavior
      except (s3.CantWriteFileAlreadyExists, s3.S3ObjectDoesntExist) as ex:
          logger.error(str(ex))
          sys.exit(1)
  ```
  File: `aws-aio/manage_arkime/commands/config_pull.py:13-51`

**Observation**: Uses sum() with generator expression to count how many flags are set, clear error messages point to --help

### Validation Report Pattern
- **Confidence**: High
- **Pattern**: Accumulate validation steps in a report object rather than failing fast
- **Examples**:
  ```python
  def validate(self) -> ValidationReport:
      report = ValidationReport(
          input=self.input_entry,
          output={"transformer_output": None},
          report_entries=[],
          passed=False
      )
      try:
          transformer_logic = self._try_load_transformer_logic(report, self.transformer)
          transformer_output = self._try_invoke_transformer_logic(transformer_logic, report)
          self._try_validate_transformer_output(self.input_entry, self.transformer, transformer_output, report)
          report.passed = True
      except Exception as e:
          report.passed = False
          report.append_entry(f"Error: {str(e)}", logger.error)
      return report
  ```
  File: `ocsf-playground/playground/backend/transformers/validators.py:67-86`

### Try-Wrapper Methods
- **Confidence**: High
- **Pattern**: Methods prefixed with `_try_*` wrap operations in try-catch and append to ValidationReport
- **Examples**: `_try_load_transformer_logic()`, `_try_invoke_transformer_logic()`, `_try_validate_transformer_output()`
- **Purpose**: Consistent error handling and reporting for validation pipelines
- File: `ocsf-playground/playground/backend/transformers/validators.py:29-65`

---

## 5. Testing Approach

### Test Framework Preferences
- **Confidence**: High
- **Pattern**: Dual framework approach - pytest for aws-aio, Django TestCase for ocsf-playground
- **Examples**:
  ```python
  # pytest style (aws-aio)
  import pytest
  import unittest.mock as mock

  def test_WHEN_action_called_AND_condition_THEN_result():
      # Test implementation
      pass
  ```
  File: `aws-aio/test_manage_arkime/core/test_capacity_planning.py:11`

  ```python
  # Django TestCase style (ocsf-playground)
  from django.test import TestCase

  class RESTClientTestCase(TestCase):
      def setUp(self):
          # Setup code
          pass

      def test_get_happy_path(self):
          # Test implementation
          pass
  ```
  File: `ocsf-playground/playground/backend/core/tests/test_rest_client.py:9-15`

### Test Naming Convention
- **Confidence**: High
- **Pattern**: `test_WHEN_<action>_<conditions>_THEN_<expected_result>` for comprehensive context
- **Examples**:
  - `test_WHEN_cmd_cluster_create_called_THEN_cdk_command_correct`
  - `test_WHEN_deploy_called_AND_not_bootstrapped_THEN_executes_command`
  - `test_WHEN_should_proceed_with_operation_AND_abort_usage_THEN_as_expected`
  File: `aws-aio/test_manage_arkime/commands/test_cluster_create.py:40, 102, 440`

**Observation**: The naming convention makes test purpose immediately clear and provides complete context without needing to read the test body.

### Mocking Strategy
- **Confidence**: High
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
  File: `aws-aio/test_manage_arkime/commands/test_cluster_create.py:27-85`

  ```python
  # Using side_effect for sequences
  mock_call_shell.side_effect = [
      (1, [exceptions.NOT_BOOTSTRAPPED_1]),
      (0, ["bootstrap success"]),
      (0, ["deploy success"])
  ]
  ```
  File: `aws-aio/test_manage_arkime/cdk_interactions/test_cdk_client.py:105-109`

**Observation**: Mock at the module level to control dependencies, use `side_effect` for sequential returns or exceptions, and verify behavior with `call_args_list`.

### Test Organization
- **Confidence**: High
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
  File: `ocsf-playground/playground/backend/core/tests/test_rest_client.py:9-40`

### Assertion Style
- **Confidence**: High
- **Pattern**: Direct equality assertions with `assert expected == actual` order
- **Examples**:
  ```python
  expected_value = UserConfig(0.1, 30, 120, 1, 30)
  assert expected_value == actual_value

  expected_calls = [mock.call(constants.get_cluster_ssm_param_name("cluster-name"), "userConfig", mock_provider)]
  assert expected_calls == mock_ssm_ops.get_ssm_param_json_value.call_args_list
  ```
  File: `aws-aio/test_manage_arkime/commands/test_cluster_create.py:514-520`

**Observation**: Always put expected value first, actual value second. Use named variables for complex expectations to improve readability.

### Test Data Organization
- **Confidence**: High
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
  File: `aws-aio/test_manage_arkime/lambda_aws_event_listener/test_aws_event_listener_handler.py:868-900`

  ```python
  # Method-level for simple data
  def test_WHEN_get_next_user_config_called_AND_partial_update_THEN_as_expected(mock_ssm_ops):
      mock_ssm_ops.get_ssm_param_json_value.return_value = {
          "expectedTraffic": 1.2,
          "spiDays": 40,
          # ...
      }
  ```
  File: `aws-aio/test_manage_arkime/commands/test_cluster_create.py:570-588`

### Comprehensive Test Coverage
- **Confidence**: High
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
  File: `aws-aio/test_manage_arkime/core/test_ssm_vni_provider.py:10-68`

### Test Scenario Organization
- **Confidence**: High
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
  File: `aws-aio/test_manage_arkime/commands/test_cluster_create.py:403-437`

**Observation**: When testing multiple related scenarios, group them in a single test function with clear `# TEST:` comments rather than creating many tiny test functions.

### Mock Verification Patterns
- **Confidence**: High
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
  File: `aws-aio/test_manage_arkime/commands/test_cluster_create.py:79-85, 865-868`

### Exception Testing
- **Confidence**: High
- **Pattern**: Use `pytest.raises` context manager for exception verification
- **Examples**:
  ```python
  with pytest.raises(cap.TooMuchTraffic):
      cap.get_capture_node_capacity_plan(cap.MAX_TRAFFIC + 10, azs)

  with pytest.raises(exceptions.CdkDeployFailedUnknown):
      client.deploy(["MyStack"])
  ```
  File: `aws-aio/test_manage_arkime/core/test_capacity_planning.py:44-45`
  File: `aws-aio/test_manage_arkime/cdk_interactions/test_cdk_client.py:169-170`

### Mock Side Effects for AWS SDK Error Responses
- **Confidence**: High
- **Pattern**: Use `side_effect` with `ClientError` to test AWS SDK error handling
- **Examples**:
  ```python
  from botocore.exceptions import ClientError

  # TEST: Bucket exists but we don't have access to it
  mock_s3_client.head_bucket.side_effect = ClientError(
      error_response={"Error": {"Code": "403", "Message": "Forbidden"}},
      operation_name=""
  )
  actual_value = s3.get_bucket_status("bucket-name", mock_aws_provider)
  assert actual_value == s3.BucketStatus.EXISTS_NO_ACCESS

  # TEST: Bucket does not exist
  mock_s3_client.head_bucket.side_effect = ClientError(
      error_response={"Error": {"Code": "404", "Message": "Not found"}},
      operation_name=""
  )
  actual_value = s3.get_bucket_status("bucket-name", mock_aws_provider)
  assert actual_value == s3.BucketStatus.DOES_NOT_EXIST
  ```
  File: `aws-aio/test_manage_arkime/aws_interactions/test_s3_interactions.py:21-28`

**Observation**: Simulate AWS SDK errors by constructing ClientError with error_response dict containing Error/Code/Message fields

### Testing AWS SDK Pagination
- **Confidence**: High
- **Pattern**: Use `side_effect` with list of responses to test pagination logic
- **Examples**:
  ```python
  mock_ec2_client.describe_subnets.side_effect = [
      {
          "Subnets": [{"SubnetId": "subnet-1"}, {"SubnetId": "subnet-2"}],
          "NextToken": "next-1",
      },
      {
          "Subnets": [{"SubnetId": "subnet-3"}, {"SubnetId": "subnet-4"}],
      }
  ]

  result = ec2i.get_subnets_of_vpc("my-vpc", mock_aws_provider)

  expected_describe_calls = [
      mock.call(Filters=[{"Name": "vpc-id", "Values": ["my-vpc"]}]),
      mock.call(Filters=[{"Name": "vpc-id", "Values": ["my-vpc"]}], NextToken="next-1"),
  ]
  assert expected_describe_calls == mock_ec2_client.describe_subnets.call_args_list
  ```
  File: `aws-aio/test_manage_arkime/aws_interactions/test_ec2_interactions.py:10-31`

**Observation**: First response includes NextToken, second response omits it to signal end of pagination

### Testing CloudWatch Metrics Structure
- **Confidence**: High
- **Pattern**: Test metric dataclasses by verifying complete metric_data structure with all outcomes
- **Examples**:
  ```python
  def test_WHEN_CreateEniMirrorEventMetrics_created_AND_success_THEN_correct_metrics():
      # Run our test
      actual_value = cwi.CreateEniMirrorEventMetrics(
          "cluster-1", "vpc-1", cwi.CreateEniMirrorEventOutcome.SUCCESS
      )

      # Check our results
      expected_metric_data = [
          {
              "MetricName": cwi.CreateEniMirrorEventOutcome.SUCCESS.value,
              "Value": 1,
              "Dimensions": [
                  {"Name": "ClusterName", "Value": "cluster-1"},
                  {"Name": "VpcId", "Value": "vpc-1"},
                  {"Name": "EventType", "Value": constants.EVENT_DETAIL_TYPE_CREATE_ENI_MIRROR},
              ]
          },
          {
              "MetricName": cwi.CreateEniMirrorEventOutcome.ABORTED_EXISTS.value,
              "Value": 0,
              "Dimensions": [ ... ]
          },
          # ... all other outcomes with Value: 0
      ]
      assert expected_metric_data == actual_value.metric_data
  ```
  File: `aws-aio/test_manage_arkime/aws_interactions/test_cloudwatch_interactions.py:7-53`

**Observation**: Verify that metric classes emit all possible outcomes (one=1, rest=0) for CloudWatch metric math

### Mock.assert_not_called() Pattern
- **Confidence**: High
- **Pattern**: Use `assert_not_called()` to verify functions weren't called in conditional branches
- **Examples**:
  ```python
  def test_WHEN_cmd_cluster_destroy_called_AND_dont_destroy_everything_THEN_expected_cmds(...):
      # ... setup ...
      cmd_cluster_destroy("profile", "region", TEST_CLUSTER, False, True)

      # Check our results
      mock_destroy_bucket.assert_not_called()
      mock_destroy_domain.assert_not_called()
  ```
  File: `aws-aio/test_manage_arkime/commands/test_cluster_destroy.py:62-63`

**Observation**: Clearer than `assert [] == mock.call_args_list` for verifying no-op behavior

### Module-Level Test Constants
- **Confidence**: High
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
  File: `aws-aio/test_manage_arkime/commands/test_cluster_destroy.py:16`

**Observation**: Reduces duplication and ensures consistent test data across related tests

### Complex JSON Context Validation
- **Confidence**: High
- **Pattern**: Validate complex nested JSON structures passed to CDK with shlex.quote()
- **Examples**:
  ```python
  expected_cdk_calls = [
      mock.call(
          ["stack-name"],
          context={
              constants.CDK_CONTEXT_CMD_VAR: constants.CMD_vpc_add,
              constants.CDK_CONTEXT_PARAMS_VAR: shlex.quote(json.dumps({
                  "nameCluster": "cluster-1",
                  "nameVpcMirrorStack": constants.get_vpc_mirror_setup_stack_name("cluster-1", "vpc-1"),
                  "idVni": str(42),
                  "idVpc": "vpc-1",
                  "listSubnetIds": subnet_ids,
                  "vpcCidrs": ["192.168.0.0/24", "192.168.128.0/24"]
              }))
          }
      )
  ]
  assert expected_cdk_calls == mock_cdk.deploy.call_args_list
  ```
  File: `aws-aio/test_manage_arkime/commands/test_vpc_add.py:76-97`

**Observation**: Test verifies exact structure of context passed to CDK subprocess, including shell-quoted JSON

### Testing Exception Swallowing
- **Confidence**: Medium
- **Pattern**: Use `assert True # Comment` to document when an exception should be caught and suppressed
- **Examples**:
  ```python
  # TEST: Bucket exists and we own it
  mock_s3_client.create_bucket.side_effect = ClientError(
      error_response={"Error": {"Message": "BucketAlreadyOwnedByYou"}},
      operation_name=""
  )
  s3.create_bucket("bucket-name", mock_aws_provider)
  assert True # The ClientError was swallowed
  ```
  File: `aws-aio/test_manage_arkime/aws_interactions/test_s3_interactions.py:69-71`

**Observation**: Explicit `assert True` with comment clarifies that the test passing without exception is the expected behavior

### Custom Mock Classes for Complex Test Scenarios
- **Confidence**: High
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
  File: `aws-aio/test_manage_arkime/core/test_shell_interactions.py:15-30`

**Observation**: Custom mock classes encapsulate complex mock behavior (like sequence tracking) rather than using nested side_effect lambdas

### Test Exception Classes for Flow Control
- **Confidence**: High
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
  File: `aws-aio/test_manage_arkime/core/test_shell_interactions.py:7-12, 34-40`

**Observation**: Allows early termination of test execution when verifying just the initial setup phase

### pytest Fixtures for Test Data
- **Confidence**: High
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

  @pytest.fixture
  def failure_response():
      response = mock.Mock()
      response.json.side_effect = json.JSONDecodeError("", "", 1)
      response.status_code = 404
      response.reason = "fate"
      response.text = "Not Found"
      response.url = str(REST_PATH)
      return response

  def test_WHEN_perform_get_AND_success_THEN_as_expected(mock_requests, success_response):
      mock_requests.get.return_value = success_response
      actual_value = ops.perform_get(rest_path=REST_PATH)
      # ...
  ```
  File: `aws-aio/test_manage_arkime/opensearch_interactions/test_rest_ops.py:10-29`

**Observation**: Fixtures eliminate duplication when multiple tests need similar mock objects

### pytest tmpdir Fixture for Filesystem Testing
- **Confidence**: High
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
  File: `aws-aio/test_manage_arkime/core/test_versioning.py:8-24`

**Observation**: Fixtures can wrap tmpdir to create custom test files with specific content

### Testing Filesystem Operations
- **Confidence**: High
- **Pattern**: Mock filesystem modules (`os`, `shutil`, `tarfile`) to test file operations without I/O
- **Examples**:
  ```python
  @mock.patch("cdk_interactions.cfn_wrangling.shutil.copyfile")
  @mock.patch("cdk_interactions.cfn_wrangling.os.path.isfile")
  @mock.patch("cdk_interactions.cfn_wrangling.os.listdir")
  def test_WHEN_copy_templates_to_cfn_dir_called_THEN_as_expected(
      mock_listdir, mock_isfile, mock_copyfile
  ):
      mock_listdir.return_value = [
          "MyCluster-CaptureBucket.template.json",
          "MyCluster3-CaptureBucket.template.json",
          "MyCluster3-CaptureNodes.template.json",
      ]
      mock_isfile.return_value = True

      actual_value = cfn._copy_templates_to_cfn_dir("MyCluster3", "/path/cfn", "path/cdk.out")

      expected_copy_calls = [
          mock.call("path/cdk.out/MyCluster3-CaptureBucket.template.json",
                    "/path/cfn/MyCluster3-CaptureBucket.template.json"),
          mock.call("path/cdk.out/MyCluster3-CaptureNodes.template.json",
                    "/path/cfn/MyCluster3-CaptureNodes.template.json")
      ]
      assert expected_copy_calls == mock_copyfile.call_args_list
  ```
  File: `aws-aio/test_manage_arkime/cdk_interactions/test_cfn_wrangling.py:45-71`

**Observation**: Multiple filesystem mocks in decorator stack, verified with call_args_list

### Testing State-Guarding with Custom Exceptions
- **Confidence**: High
- **Pattern**: Test that operations raise custom exceptions when required state hasn't been set up
- **Examples**:
  ```python
  def test_WHEN_TarGzDirectory_THEN_lifecycle_as_expected(mock_tarfile):
      source = "/my/source/dir"
      tarball = "/test/file.tgz"
      tgz_dir = lf.TarGzDirectory(source, tarball)

      # TEST: Raises when you try to get the path before generating
      with pytest.raises(lf.FileNotGenerated):
          tgz_dir.local_path

      # TEST: When generate called, then file is created
      tar_obj = mock.MagicMock()
      mock_tarfile.open.return_value.__enter__.return_value = tar_obj
      tgz_dir.generate()

      # TEST: After generate is called, you can get the path
      actual_value = tgz_dir.local_path
      assert tarball == actual_value
  ```
  File: `aws-aio/test_manage_arkime/core/test_local_file.py:8-30`

**Observation**: Test lifecycle progression: pre-state (raises) → setup → post-state (works)

### REST API Response Mocking
- **Confidence**: High
- **Pattern**: Mock HTTP responses with structured attributes (`status_code`, `reason`, `text`, `json()`)
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

  @mock.patch("opensearch_interactions.rest_ops.requests")
  def test_WHEN_perform_get_AND_success_THEN_as_expected(mock_requests, success_response):
      mock_requests.get.return_value = success_response
      actual_value = ops.perform_get(rest_path=REST_PATH)

      expected_value = {
          "response_json": success_response.json(),
          "response_text": success_response.text,
          "status_code": success_response.status_code,
          "status_reason": success_response.reason,
          "succeeded": True,
          "url": str(REST_PATH)
      }
      assert expected_value == actual_value.to_dict()
  ```
  File: `aws-aio/test_manage_arkime/opensearch_interactions/test_rest_ops.py:10-49`

**Observation**: Mock responses match requests library interface; test both success and failure paths

---

## 6. Code Style & Idioms

### Naming Conventions

#### Variables & Functions
- **Confidence**: High
- **Pattern**: `snake_case` for variables and functions
- **Examples**: `expected_traffic`, `cluster_name`, `get_capture_node_capacity_plan`

#### Classes
- **Confidence**: High
- **Pattern**: `PascalCase` for classes
- **Examples**: `Expert`, `CaptureNodesPlan`, `AwsClientProvider`, `RESTPath`

#### Constants
- **Confidence**: High
- **Pattern**: `SCREAMING_SNAKE_CASE` for module-level constants
- **Examples**: `MAX_TRAFFIC`, `MINIMUM_TRAFFIC`, `DEFAULT_SPI_DAYS`, `DEFULT_BOTO_CONFIG` [sic]

#### Private/Internal
- **Confidence**: High
- **Pattern**: Leading underscore for internal methods and variables
- **Examples**: `_aws_profile`, `_get_session()`, `_create_regex()`, `_validate()`

### Line Length
- **Confidence**: Medium
- **Pattern**: Generally stays under 120 characters; breaks long strings and method chains
- **Examples**:
  ```python
  command_prefix = get_command_prefix(
      aws_profile=self._aws_env.aws_profile,
      aws_region=self._aws_env.aws_region,
      context=context
  )
  ```
  File: `aws-aio/manage_arkime/cdk_interactions/cdk_client.py:36`

### Import Organization
- **Confidence**: High
- **Pattern**: Imports grouped by: stdlib → third-party → local (with blank lines between)
- **Examples**:
  ```python
  import json
  import logging
  from typing import List
  import uuid

  from django.views.decorators.csrf import csrf_exempt
  from drf_spectacular.utils import extend_schema
  from langchain_core.messages import HumanMessage
  from rest_framework.views import APIView
  from rest_framework.response import Response
  from rest_framework import status

  from backend.categorization_expert.expert_def import get_categorization_expert
  from backend.core.ocsf.ocsf_versions import OcsfVersion
  ```
  File: `ocsf-playground/playground/playground_api/views.py:1-16`

### Comprehensions vs Loops
- **Confidence**: Medium
- **Pattern**: Prefers list comprehensions for simple transformations
- **Examples**:
  ```python
  [pattern.to_json() for pattern in result.patterns]
  ```
  File: `ocsf-playground/playground/playground_api/views.py:350`

### F-Strings
- **Confidence**: High
- **Pattern**: Consistent use of f-strings for string formatting
- **Examples**:
  ```python
  logger.info(f"Received heuristic creation request: {request.data}")
  logger.error(f"Invalid heuristic creation request: {request.errors}")
  ```
  File: `ocsf-playground/playground/playground_api/views.py:52-57`

### String Manipulation for Code Generation
- **Confidence**: High
- **Pattern**: Uses string methods to manage indentation when generating code
- **Examples**:
  ```python
  def _get_pattern_function_code(pattern: ExtractionPattern) -> str:
      # Ensure proper indentation by adding 4 spaces to each line
      indented_extract_logic = "\n    ".join(pattern.extract_logic.splitlines())
      indented_transform_logic = "\n    ".join(pattern.transform_logic.splitlines())
      return f"""
  def {_get_pattern_function_name(pattern)}(input_data: str) -> str:
      {indented_extract_logic}

      {indented_transform_logic}
  """
  ```
  File: `ocsf-playground/playground/backend/transformers/transformers.py:31-46`

### Boolean Expressions for Control Flow
- **Confidence**: High
- **Pattern**: Clear boolean variable names and XOR logic
- **Examples**:
  ```python
  one_component_specified = (capture or viewer) and not (capture and viewer)  # XOR
  no_component_specified = not (capture or viewer)
  if config_version and (not one_component_specified):
      logger.error("If you specify a specific config version...")
  ```
  File: `aws-aio/manage_arkime/commands/config_update.py:23-29`

### Conditional Assignment Patterns
- **Confidence**: High
- **Pattern**: Use ternary expressions for conditional assignments
- **Examples**:
  ```python
  next_config_version = (
      str(switch_to_version)
      if switch_to_version
      else str(int(cloud_config_details.version.config_version) + 1)
  )
  ```
  File: `aws-aio/manage_arkime/commands/config_update.py:144-148`

### List Comprehensions for Data Extraction
- **Confidence**: High
- **Pattern**: Use list comprehensions with accessor methods for extracting data from AWS SDK responses
- **Examples**:
  ```python
  deployment_statuses = [dep["rolloutState"] for dep in describe_response["services"][0]["deployments"]]
  failed_task_counts = [dep["failedTasks"] for dep in describe_response["services"][0]["deployments"]]
  return sum(failed_task_counts)
  ```
  File: `aws-aio/manage_arkime/aws_interactions/ecs_interactions.py:23-33`

  ```python
  return [param["Name"].split("/")[-1] for param in raw_params]
  ```
  File: `aws-aio/manage_arkime/aws_interactions/ssm_operations.py:54`

### ANSI Escape Codes for Terminal Formatting
- **Confidence**: High
- **Pattern**: Use ANSI escape codes for highlighting changes in terminal output
- **Examples**:
  ```python
  def _line(self, name: str, oldVal: UserVal, newVal: UserVal) -> str:
      if oldVal is None or oldVal == newVal:
          return f"    {name}: {newVal}\n"
      else:
          return f"    {name}: \033[1m{oldVal} -> {newVal}\033[0m\n"  # Bold text for changes
  ```
  File: `aws-aio/manage_arkime/core/usage_report.py:17-21`

**Observation**: `\033[1m` for bold, `\033[0m` to reset formatting

---

## 7. Dependencies & Tooling

### Dependency Management
- **Confidence**: High
- **Pattern**: Uses setuptools with setup.py for package distribution
- **Examples**:
  ```python
  setuptools.setup(
      name="manage_arkime",
      version="1.0.0",
      description=("Tooling and configuration to install/manage Arkime Clusters in an AWS account"),
      author="Chris Helma",
      package_dir={"": "."},
      packages=setuptools.find_packages(where="."),
      install_requires=[
          "boto3",
          "click",
          "coloredlogs",
          "cryptography",
          "pexpect",
          "pytest",
          "pytest-cov",
          "ruff",
          "requests",
      ],
      python_requires=">=3.9",
  )
  ```
  File: `aws-aio/manage_arkime/setup.py:1-22`

**Observation**: Package dependencies listed alphabetically in install_requires, python_requires specifies minimum version

### Standard Library vs Third-Party
- **Confidence**: High
- **Pattern**: Leverages stdlib heavily (logging, abc, dataclasses, typing), brings in third-party for specific needs
- **Third-party observed**: Django, DRF, Click, boto3, LangChain, requests

### AWS SDK (boto3) Usage
- **Confidence**: High
- **Pattern**: Encapsulate AWS API calls in dedicated interaction modules with error handling
- **Examples**:
  ```python
  def get_bucket_status(bucket_name: str, aws_provider: AwsClientProvider) -> BucketStatus:
      s3_client = aws_provider.get_s3()
      try:
          s3_client.head_bucket(Bucket=bucket_name)
          return BucketStatus.EXISTS_HAVE_ACCESS
      except ClientError as ex:
          if ex.response["Error"]["Code"] == "403":
              return BucketStatus.EXISTS_NO_ACCESS
          elif ex.response["Error"]["Code"] == "404":
              return BucketStatus.DOES_NOT_EXIST
  ```
  File: `aws-aio/manage_arkime/aws_interactions/s3_interactions.py:59-72`

**Observation**: Pattern includes custom exception classes for domain errors, ClientError parsing, pagination handling, and regional API nuances (e.g., us-east-1 special case)

### AWS SDK Pagination Pattern
- **Confidence**: High
- **Pattern**: Manual pagination handling with NextToken, extending results list
- **Examples**:
  ```python
  response: Dict = ssm_client.get_parameters_by_path(Path=param_path, Recursive=recursive)

  return_params = []
  return_params.extend(response["Parameters"])
  next_token = response.get("NextToken")

  while next_token:
      next_response: Dict = ssm_client.get_parameters_by_path(Path=param_path, Recursive=recursive, NextToken=next_token)
      return_params.extend(next_response["Parameters"])
      next_token = next_response.get("NextToken")

  return return_params
  ```
  File: `aws-aio/manage_arkime/aws_interactions/ssm_operations.py:32-50`

**Observation**: Pattern uses `extend()` to accumulate results across pages, checks for NextToken presence with `.get()`

### CLI Framework
- **Confidence**: High
- **Pattern**: Uses Click for command-line interfaces
- **Examples**: Extensive use of `@click.command()`, `@click.option()`, `@click.group()`
- File: `aws-aio/manage_arkime.py:27-367`

### Django Framework Patterns
- **Confidence**: High
- **Pattern**: Standard Django project structure with WSGI/ASGI entry points using os.environ.setdefault
- **Examples**:
  ```python
  # WSGI Entry Point
  import os
  from django.core.wsgi import get_wsgi_application

  os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playground.settings')
  application = get_wsgi_application()
  ```
  File: `ocsf-playground/playground/playground/wsgi.py:1-16`

  ```python
  # ASGI Entry Point
  import os
  from django.core.asgi import get_asgi_application

  os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playground.settings')
  application = get_asgi_application()
  ```
  File: `ocsf-playground/playground/playground/asgi.py:1-16`

  ```python
  # Django App Configuration
  from django.apps import AppConfig

  class ApiConfig(AppConfig):
      default_auto_field = 'django.db.models.BigAutoField'
      name = 'playground_api'
  ```
  File: `ocsf-playground/playground/playground_api/apps.py:1-8`

**Observation**: Django boilerplate follows framework conventions exactly. Empty models.py and admin.py files exist as placeholders even when unused, maintaining standard Django app structure.

---

## 8. Design Patterns & Principles

### Dataclass Usage
- **Confidence**: High
- **Pattern**: Heavy use of `@dataclass` for data structures; prefers dataclasses over plain classes or dicts
- **Examples**:
  ```python
  @dataclass
  class Expert:
      llm: Runnable[LanguageModelInput, BaseMessage]
      system_prompt_factory: Callable[[Dict[str, Any]], SystemMessage]
      tools: ToolBundle
  ```
  File: `ocsf-playground/playground/backend/core/experts.py:28-32`

  ```python
  @dataclass
  class CaptureNodesPlan:
      instanceType: str
      desiredCount: int
      maxCount: int
      minCount: int
  ```
  File: `aws-aio/manage_arkime/core/capacity_planning.py:82-86`

### Serialization Patterns
- **Confidence**: High
- **Pattern**: Dataclasses have `to_dict()` / `to_json()` instance methods and `from_dict()` / `from_json()` class methods
- **Examples**:
  ```python
  def to_dict(self) -> Dict[str, any]:
      return {
          "count": self.count,
          "instanceType": self.instanceType,
          "volumeSize": self.volumeSize
      }

  @classmethod
  def from_dict(cls: Type[T_ClusterPlan], input: Dict[str, any]) -> T_ClusterPlan:
      capture_nodes = CaptureNodesPlan(**input["captureNodes"])
      # ...
  ```
  File: `aws-aio/manage_arkime/core/capacity_planning.py:212-217, 506-524`

### Ternary Expression for Optional Field Serialization
- **Confidence**: High
- **Pattern**: Use ternary expressions to conditionally serialize optional fields to None
- **Examples**:
  ```python
  def to_json(self) -> dict:
      return {
          "id": self.id,
          "mapping": self.mapping.to_json() if self.mapping else None,
          "dependency_setup": self.dependency_setup,
          "extract_logic": self.extract_logic,
          "transform_logic": self.transform_logic,
          "validation_report": self.validation_report.to_json() if self.validation_report else None
      }
  ```
  File: `ocsf-playground/playground/backend/entities_expert/extraction_pattern.py:16-24`

### Selective Dataclass Deserialization with fields()
- **Confidence**: High
- **Pattern**: Use `fields()` to filter valid keys from dict, allows ignoring config no longer used
- **Examples**:
  ```python
  @dataclass
  class UserConfig:
      expectedTraffic: float
      spiDays: int
      # ...

      """ Only process fields we still need, this allows us to ignore config no longer used """
      @classmethod
      def from_dict(cls, d):
          valid_keys = {f.name for f in fields(cls)}
          valid_kwargs = {key: value for key, value in d.items() if key in valid_keys}
          return cls(**valid_kwargs)
  ```
  File: `aws-aio/manage_arkime/core/user_config.py:43-48`

### Dataclass Configuration with Explicit __init__ and Defaults
- **Confidence**: High
- **Pattern**: Override `__init__` to handle None values and apply default constants
- **Examples**:
  ```python
  @dataclass
  class UserConfig:
      expectedTraffic: float
      spiDays: int
      historyDays: int
      replicas: int
      pcapDays: int
      viewerPrefixList: str = None
      extraTags: List[Dict[str, str]] = None

      def __init__(self, expectedTraffic: float, spiDays: int, historyDays: int, replicas: int, pcapDays: int,
                   viewerPrefixList: str = None, extraTags: List[Dict[str, str]] = []):
          self.expectedTraffic = expectedTraffic
          # ...

          if (expectedTraffic is None):
              self.expectedTraffic = MINIMUM_TRAFFIC
          if (spiDays is None):
              self.spiDays = DEFAULT_SPI_DAYS
          # ...
  ```
  File: `aws-aio/manage_arkime/core/user_config.py:9-42`

### Abstract Base Classes
- **Confidence**: High
- **Pattern**: Uses ABC for defining interfaces/contracts
- **Examples**:
  ```python
  class PlaygroundTask(ABC):
      @abstractmethod
      def get_work_item(self) -> Any:
          pass

      @abstractmethod
      def set_work_item(self, new_work_item: Any):
          pass
  ```
  File: `ocsf-playground/playground/backend/core/tasks.py:13-23`

  ```python
  class LocalFile(ABC):
      @property
      @abstractmethod
      def local_path(self) -> str:
          pass
  ```
  File: `aws-aio/manage_arkime/core/local_file.py:13-20`

### Large Static Data Structures as Module-Level Constants
- **Confidence**: High
- **Pattern**: Define large schema/configuration data as module-level lists of dicts with ALL_CAPS names
- **Examples**:
  ```python
  OCSF_EVENT_CLASSES = [
      {
          "event_name": "File System Activity",
          "event_id": "1001",
          "event_details": "The File System Activity category covers file system events..."
      },
      {
          "event_name": "Kernel Extension Activity",
          "event_id": "1002",
          "event_details": "The Kernel Extension Activity category covers kernel-level events..."
      },
      # ... 60+ more entries
  ]

  OCSF_EVENT_SCHEMAS = [
      {
          "name": "Authentication",
          "fields": [
              {
                  "name": "auth_protocol_id",
                  "data_type": "Integer",
                  "description": "The normalized identifier...",
                  "enum_values": {
                      "0": "Unknown",
                      "1": "NTLM",
                      # ...
                  },
                  "requirement": "Recommended"
              },
              # ... more fields
          ]
      },
      # ... more schemas
  ]
  ```
  File: `ocsf-playground/playground/backend/core/ocsf/ocsf_schema_v1_1_0.py:8-219, 235-535`

**Observation**: For large static configuration data (hundreds of lines), prefer simple Python data structures over JSON files. Includes inline comments documenting provenance (ChatGPT links, documentation URLs).

### Dataclass with Helper Methods (to_list)
- **Confidence**: Medium
- **Pattern**: Dataclasses with convenience methods to convert to other formats
- **Examples**:
  ```python
  @dataclass
  class ToolBundle:
      task_tool: StructuredTool

      def to_list(self) -> List[StructuredTool]:
          return [self.task_tool]
  ```
  File: `ocsf-playground/playground/backend/core/tools.py:11-16`

**Observation**: When a dataclass is primarily used as a bundle/wrapper, provide conversion methods to unwrap the contents.

### Client/Provider Pattern
- **Confidence**: High
- **Pattern**: Provider classes encapsulate client initialization and credential management
- **Examples**:
  ```python
  class AwsClientProvider:
      def __init__(self, aws_profile: str = "default", aws_region: str = None,
                   aws_compute=False, assume_role_arn: str=None):
          self._aws_profile = aws_profile
          # ...

      def get_ec2(self):
          session = self._get_session()
          client = session.client("ec2")
          return client
  ```
  File: `aws-aio/manage_arkime/aws_interactions/aws_client_provider.py:14-92`

### Composition Over Inheritance
- **Confidence**: Medium-High
- **Pattern**: Dataclasses composed of other dataclasses rather than deep inheritance
- **Examples**:
  ```python
  @dataclass
  class ClusterPlan:
      captureNodes: CaptureNodesPlan
      captureVpc: VpcPlan
      ecsResources: EcsSysResourcePlan
      osDomain: OSDomainPlan
      s3: S3Plan
      viewerNodes: ViewerNodesPlan
      viewerVpc: VpcPlan
  ```
  File: `aws-aio/manage_arkime/core/capacity_planning.py:481-488`

### Template Method Pattern
- **Confidence**: High
- **Pattern**: ABC base classes define validation flow, subclasses implement specific steps
- **Examples**:
  ```python
  class TransformerValidatorBase(ABC):
      def validate(self) -> ValidationReport:
          # Template method defines the flow
          transformer_logic = self._try_load_transformer_logic(report, self.transformer)
          transformer_output = self._try_invoke_transformer_logic(transformer_logic, report)
          self._try_validate_transformer_output(self.input_entry, self.transformer, transformer_output, report)

      @abstractmethod
      def _load_transformer_logic(self, transformer: Transformer) -> Callable[[str], str]:
          pass  # Subclass implements
  ```
  File: `ocsf-playground/playground/backend/transformers/validators.py:19-54`

### Dynamic Code Generation
- **Confidence**: High
- **Pattern**: Programmatically generate Python code as strings, then exec() into modules
- **Examples**:
  ```python
  def create_transformer_python(transformer_id: str, patterns: List[ExtractionPattern]) -> Transformer:
      transformer_logic = ""
      for pattern in patterns:
          function_code = _get_pattern_function_code(pattern)
          transformer_logic += function_code
      transformer_logic += _get_helper_code()
      transformer_logic += _get_transformer_wrapper_code(patterns)
      return Transformer(id=transformer_id, dependency_setup=..., transformer_logic=transformer_logic)
  ```
  File: `ocsf-playground/playground/backend/transformers/transformers.py:85-104`

### Code Loading with exec()
- **Confidence**: High
- **Pattern**: Use `ModuleType` and `exec()` to load dynamically generated Python code
- **Examples**:
  ```python
  transformer_module = ModuleType("transformer")
  exec(f"{transformer.dependency_setup}\n\n{transformer.transformer_logic}", transformer_module.__dict__)
  if not hasattr(transformer_module, "transformer"):
      raise PythonLogicNotInModuleError("...")
  return transformer_module.transformer
  ```
  File: `ocsf-playground/playground/backend/transformers/validators.py:186-197`

### Command Pattern for CLI
- **Confidence**: High
- **Pattern**: Each CLI command is a self-contained function with explicit parameters
- **Examples**:
  ```python
  def cmd_cluster_create(profile: str, region: str, name: str, expected_traffic: float, ...):
      # Self-contained command logic with helper functions
  ```
  File: `aws-aio/manage_arkime/commands/cluster_create.py:33-88`

### State Provider Pattern
- **Confidence**: High
- **Pattern**: ABC defines interface for state management, concrete implementations use different backends
- **Examples**:
  ```python
  class VniProvider(ABC):
      @abstractmethod
      def get_next_vni(self) -> int:
          pass

  class SsmVniProvider(VniProvider):
      # Implementation using AWS SSM Parameter Store as backend
  ```
  File: `aws-aio/manage_arkime/core/vni_provider.py:30-206`

### Dynamically Created Enums
- **Confidence**: High
- **Pattern**: Create Enum classes at runtime from data structures using dict comprehensions and `Enum()` constructor
- **Examples**:
  ```python
  # Create a custom Enum class with additional methods
  class OcsfEventClassEnum(Enum):
      def get_event_name(self):
          """Extract the event name from the value"""
          match = re.match(r"(.+) \(\d+\)", self.value)
          return match.group(1) if match else ""

      def get_event_id(self):
          """Extract the event ID from the value"""
          match = re.search(r"\((\d+)\)", self.value)
          return match.group(1) if match else ""

  # Dynamically create the enum members from a data structure
  members = {
      f"{event_class["event_name"]} {event_class["event_id"]}".upper().replace(" ", "_").replace("-", "_"):
      f"{event_class["event_name"]} ({event_class["event_id"]})"
      for event_class in ocsf_events_V1_1_0
  }

  # Create the enum class with all members at once
  OcsfEventClassesV1_1_0 = OcsfEventClassEnum(
      "OcsfEventClassesV1_1_0",
      members,
      module=__name__,  # Important to make the enum picklable
  )
  ```
  File: `ocsf-playground/playground/backend/core/ocsf/ocsf_event_classes.py:8-34`

**Observation**: When enum values need to be generated from data rather than hard-coded, use the `Enum()` functional API with dict comprehensions. Custom Enum base classes can add domain-specific methods (regex parsing in this case).

### Strategy Pattern with Version Selection
- **Confidence**: High
- **Pattern**: Functions dispatch to different implementations based on version/flavor enum
- **Examples**:
  ```python
  def get_ocsf_event_class_knowledge(ocsf_version: OcsfVersion, ocsf_event_name: str) -> str:
      if ocsf_version == OcsfVersion.V1_1_0:
          event_details = next(
              event for event in ocsf_events_V1_1_0 if event["event_name"] == ocsf_event_name
          )
          return json.dumps(event_details, indent=4)

      return ""

  def get_ocsf_event_schema(ocsf_version: OcsfVersion, event_name: str, paths: List[str]) -> PrintableOcsfEvent:
      if ocsf_version == OcsfVersion.V1_1_0:
          return make_get_ocsf_event_schema(v1_1_0_schema)(event_name, paths)

      return None
  ```
  File: `ocsf-playground/playground/backend/entities_expert/prompting/knowledge/__init__.py:10-29`

  ```python
  def get_regex_guidance(regex_flavor: RegexFlavor) -> str:
      if regex_flavor == RegexFlavor.JAVASCRIPT:
          return javascript_guidance

      return ""

  def get_regex_knowledge(regex_flavor: RegexFlavor) -> str:
      if regex_flavor == RegexFlavor.JAVASCRIPT:
          return javascript_knowledge

      return ""
  ```
  File: `ocsf-playground/playground/backend/regex_expert/prompting/knowledge/__init__.py:6-16`

**Observation**: For version-specific or flavor-specific logic, use if-elif chains returning implementation-specific code. Return empty/None for unsupported versions. This pattern allows adding new versions without modifying calling code.

### Retry and Rollback Logic
- **Confidence**: High
- **Pattern**: Monitor deployment progress, automatically rollback on failure
- **Examples**:
  ```python
  while ecs.is_deployment_in_progress(ecs_cluster, ecs_service, aws_provider):
      failed_task_count = ecs.get_failed_task_count(ecs_cluster, ecs_service, aws_provider)
      if failed_task_count >= failed_task_limit and not reverted:
          logger.warning(f"Failed task limit exceeded; rolling back to previous config")
          _revert_arkime_config(ssm_param, aws_provider)
          reverted = True
  ```
  File: `aws-aio/manage_arkime/commands/config_update.py:235-242`

### Lambda Event Handler Pattern
- **Confidence**: High
- **Pattern**: Class-based Lambda handler with routing logic and structured error handling
- **Examples**:
  ```python
  class AwsEventListenerHandler:
      def __init__(self):
          self.logger = logging.getLogger()
          self.logger.handlers = []  # Start with clean slate
          self.logger.setLevel(logging.INFO)

      def handler(self, event: Dict[str, any], context):
          self.logger.info("Event:")
          self.logger.info(json.dumps(event))

          try:
              event_type = self._get_event_type(event)
              if event_type == AwsEventType.EC2_RUNNING:
                  return self._handle_ec2_running(event, ...)
              elif event_type == AwsEventType.FARGATE_RUNNING:
                  return self._handle_fargate_running(event, ...)
              # ... other event types
          except Exception as ex:
              self.logger.error(ex, exc_info=True)
              return {"statusCode": 500}
  ```
  File: `aws-aio/manage_arkime/lambda_aws_event_listener/aws_event_listener_handler.py:18-73`

**Observation**: Pattern includes router logic based on event type enums, separate handler methods for each event type, and always returns status code

### Lambda Handler Consistency Pattern
- **Confidence**: High
- **Pattern**: All Lambda handlers follow identical structure: `__init__` with logger cleanup, `handler` with event logging first, try-except with 200/500 returns, metrics on all code paths
- **Examples**:
  ```python
  class CreateEniMirrorHandler:
      def __init__(self):
          self.logger = logging.getLogger()
          self.logger.handlers = []  # Clean slate
          self.logger.setLevel(logging.INFO)
          console_handler = logging.StreamHandler()
          self.logger.addHandler(console_handler)

      def handler(self, event: Dict[str, any], context):
          # Log the triggering event; first thing every Lambda should do
          self.logger.info("Event:")
          self.logger.info(json.dumps(event))

          # Ensure our Lambda will always return a status code
          try:
              create_event = events.CreateEniMirrorEvent.from_event_dict(event)
              # ... business logic ...
              cwi.put_event_metrics(cwi.CreateEniMirrorEventMetrics(..., SUCCESS), aws_provider)
              return {"statusCode": 200}
          except Exception as ex:
              self.logger.error(ex, exc_info=True)
              cwi.put_event_metrics(cwi.CreateEniMirrorEventMetrics(..., FAILURE), aws_provider)
              return {"statusCode": 500}
  ```
  File: `aws-aio/manage_arkime/lambda_create_eni_mirror/create_eni_mirror_handler.py:12-117`

**Observation**: Comments explicitly state "first thing every Lambda should do" and "ensure our Lambda will always return a status code", showing intentional consistency across all handlers

### Event-Driven Architecture with EventBridge
- **Confidence**: High
- **Pattern**: Custom event classes inherit from ABC base, define structure for publishing to EventBridge
- **Examples**:
  ```python
  class ArkimeEvent(ABC):
      @classmethod
      def from_event_dict(cls, raw_event: Dict[str, any]):
          detail_dict = raw_event["detail"]
          return cls(**detail_dict)

      @property
      @abstractmethod
      def detail_type(self) -> str:
          pass

      @property
      @abstractmethod
      def details(self) -> Dict[str, any]:
          pass

  class CreateEniMirrorEvent(ArkimeEvent):
      def __init__(self, cluster_name: str, vpc_id: str, subnet_id: str, eni_id: str, ...):
          # ...

      @property
      def details(self) -> Dict[str, any]:
          return {"cluster_name": self.cluster_name, "vpc_id": self.vpc_id, ...}
  ```
  File: `aws-aio/manage_arkime/aws_interactions/events_interactions.py:12-115`

### Enum-Based Metrics Pattern
- **Confidence**: High
- **Pattern**: Use Enums for metric outcomes, emit separate metric values for each outcome (0 or 1)
- **Examples**:
  ```python
  class CreateEniMirrorEventOutcome(Enum):
      SUCCESS="Success"
      ABORTED_EXISTS="AbortedExists"
      ABORTED_ENI_TYPE="AbortedEniType"
      FAILURE="Failure"

  class CreateEniMirrorEventMetrics(ArkimeEventMetric):
      def __init__(self, cluster_name: str, vpc_id: str, outcome: CreateEniMirrorEventOutcome):
          # Set one value to 1, rest to 0 based on outcome
          self.value_success = 1 if outcome == CreateEniMirrorEventOutcome.SUCCESS else 0
          self.value_abort_exists = 1 if outcome == CreateEniMirrorEventOutcome.ABORTED_EXISTS else 0
          # ...
  ```
  File: `aws-aio/manage_arkime/aws_interactions/cloudwatch_interactions.py:89-116`

**Observation**: Makes CloudWatch metric math and alarming easier by emitting all possible outcomes

### Module-Level Lambda Handler Export
- **Confidence**: High
- **Pattern**: Export instantiated handler methods at module level for AWS Lambda entry points
- **Examples**:
  ```python
  # lambda_handlers.py
  from lambda_aws_event_listener.aws_event_listener_handler import AwsEventListenerHandler
  from lambda_configure_ism.configure_ism_handler import ConfigureIsmHandler
  from lambda_create_eni_mirror.create_eni_mirror_handler import CreateEniMirrorHandler
  from lambda_destroy_eni_mirror.destroy_eni_mirror_handler import DestroyEniMirrorHandler

  aws_event_listener_handler = AwsEventListenerHandler().handler
  configure_ism_handler = ConfigureIsmHandler().handler
  create_eni_mirror_handler = CreateEniMirrorHandler().handler
  destroy_eni_mirror_handler = DestroyEniMirrorHandler().handler
  ```
  File: `aws-aio/manage_arkime/lambda_handlers.py:1-9`

**Observation**: Pattern provides single module with all Lambda entry points, instantiates handler classes and exposes their handler methods

### Dictionary-Based Policy Generation
- **Confidence**: High
- **Pattern**: Functions return complex nested dictionaries representing policies/configurations
- **Examples**:
  ```python
  def get_sessions_ism_policy(hot_days: int, warm_days: int, replicas: int, merge_segments: int) -> Dict[str, any]:
      """
      hot_days: Number of days for the sessions data to stay in the "hot" state
      warm_days: Number of additional days for the sessions data to stay in a "warm" state after it has left the "hot" state
      replicas: Number of replicas of the sessions data to keep
      merge_segments: The maximum number of Lucene segments to allow after a merge occurs
      """
      return {
          "policy": {
              "description": "Arkime sessions3 Policy",
              "default_state": "hot",
              "states": [
                  {
                      "name": "hot",
                      "transitions": [
                          {
                              "state_name": "warm",
                              "conditions": {
                                  "min_index_age": f"{hot_days}d"
                              }
                          }
                      ]
                  },
                  # ... more states
              ],
              "ism_template": [
                  {
                      "index_patterns": [INDEX_PATTERN_SESSIONS],
                      "priority": 95
                  }
              ]
          }
      }
  ```
  File: `aws-aio/manage_arkime/opensearch_interactions/ism_policies.py:47-135`

**Observation**: Parameterized functions generate policy dicts with f-strings for dynamic values, comprehensive docstrings explain each parameter

### Polling with Sleep Pattern
- **Confidence**: High
- **Pattern**: Use `time.sleep()` in while loops to poll for async operation completion
- **Examples**:
  ```python
  def destroy_os_domain_and_wait(domain_name: str, aws_client_provider: AwsClientProvider):
      # ... initiate deletion ...
      logger.info(f"Destruction in progress.  Beginning wait; this could be a while (15-20 min)...")

      # Keep periodically checking the status of the domain until the check throws a ResourceNotFound
      while True:
          time.sleep(10)

          try:
              describe_response = os_client.describe_domain(DomainName=domain_name)
              logger.debug(describe_response)
          except ClientError as exc:
              if exc.response['Error']['Code'] == 'ResourceNotFoundException':
                  break
              raise

          logger.info("Waiting a bit more...")

      logger.info(f"OS Domain {domain_name} has been destroyed")
  ```
  File: `aws-aio/manage_arkime/aws_interactions/destroy_os_domain.py:10-43`

**Observation**: Pattern includes informative logging about expected wait time, periodic status updates, exception-based exit condition

---

## 9. Data Handling

### Data Structure Choices
- **Confidence**: High
- **Pattern**: Prefers dataclasses for structured data, dicts for JSON interop
- **Examples**: All data models are dataclasses (Entity, EntityMapping, CaptureNodesPlan, etc.)

### Serialization
- **Confidence**: High
- **Pattern**: `to_dict()` / `to_json()` methods for serialization, `from_dict()` / `from_json()` class methods for deserialization
- **Examples**: See Design Patterns section

### Dataclasses vs NamedTuples vs Pydantic
- **Confidence**: High
- **Pattern**: Uses `@dataclass` from stdlib for data models; Pydantic BaseModel for LangChain tool schemas only
- **Observation**: Django REST Framework used for REST API validation, Pydantic for LangChain structured outputs

### Nested Dataclass Deserialization
- **Confidence**: High
- **Pattern**: `from_dict()` class methods handle nested dataclass instantiation with **kwargs unpacking
- **Examples**:
  ```python
  @classmethod
  def from_dict(cls, input: Dict[str, any]) -> 'ConfigDetails':
      previous_config = ConfigDetails.from_dict(input['previous']) if input.get('previous') else None
      return cls(
          s3=S3Details(**input['s3']),
          version=VersionInfo(**input['version']),
          previous=previous_config
      )
  ```
  File: `aws-aio/manage_arkime/arkime_interactions/config_wrangling.py` (pattern inferred from similar structures)

### Printable Wrappers with Attribute Filtering
- **Confidence**: High
- **Pattern**: Extend external dataclasses with printable versions that add `to_dict()` and attribute filtering
- **Examples**:
  ```python
  @dataclass
  class PrintableOcsfObject(OcsfObject):
      include_all_attrs: bool = False
      attrs_to_include: Optional[List[str]] = None

      def __init__(self, *args, **kwargs):
          self.include_all_attrs = kwargs.pop("include_all_attrs", False)
          self.attrs_to_include = kwargs.pop("attrs_to_include", None)
          super().__init__(*args, **kwargs)

          if self.include_all_attrs and self.attrs_to_include:
              raise ValueError("Cannot specify to include all attributes and a specific list...")

      def to_dict(self, filter_attributes: bool = False) -> Dict[str, Any]:
          if self.include_all_attrs:
              filtered_attributes = self.attributes
          elif filter_attributes and self.attrs_to_include:
              filtered_attributes = {attr_name: attr for attr_name, attr in self.attributes.items()
                                     if attr_name in self.attrs_to_include}
          else:
              filtered_attributes = self.attributes
          return {
              "caption": self.caption,
              "attributes": {attr_name: PrintableOcsfAttr(**attr.__dict__).to_dict()
                             for attr_name, attr in filtered_attributes.items()}
          }
  ```
  File: `ocsf-playground/playground/backend/core/ocsf/ocsf_schemas.py:60-95`

**Observation**: Pattern adds serialization capabilities to third-party dataclasses without modifying the original library

### Price Calculation Helper with Dict-Based Pricing
- **Confidence**: High
- **Pattern**: Module-level dict with prices, calculation class generates formatted report
- **Examples**:
  ```python
  AWS_HOURS_PER_MONTH=730
  US_EAST_1_PRICES: Dict[str, float] = {
      "t3.small.search": 0.0360 * AWS_HOURS_PER_MONTH,
      "m5.large.search": 0.1420 * AWS_HOURS_PER_MONTH,
      "ebs-GB": 0.10,
      "gwlb-GB": 0.004,
  }

  class PriceReport:
      def __init__(self, plan: ClusterPlan, config: UserConfig, prices: Dict[str, float] = None):
          self._prices = prices if prices else US_EAST_1_PRICES.copy()
          self._total = 0

      def _line(self, name: str, key: str, num: float) -> str:
          if num <= 0:
              return ""
          cost: float = self._prices[key]
          self._total += cost * num
          if key.endswith("-GB"):
              return f"   {name:23} {num:9,} * ${cost:9.4f}/GB = ${cost * num:10.2f}/mo\n"
          else:
              return f"   {name:23} {num:9,} * ${cost:9.4f}/mo = ${cost * num:10.2f}/mo\n"
  ```
  File: `aws-aio/manage_arkime/core/price_report.py:6-62`

**Observation**: Uses formatted strings with alignment for columnar output, accumulates total as side effect

### Recursive Data Structures
- **Confidence**: High
- **Pattern**: Dataclasses reference themselves for linked structures (with None termination)
- **Examples**:
  ```python
  @dataclass
  class ConfigDetails:
      s3: S3Details
      version: VersionInfo
      previous: ConfigDetails = None  # Recursive reference
  ```
  File: `aws-aio/manage_arkime/commands/config_update.py:150-151`

### Immutability
- **Confidence**: Low
- **Pattern**: Dataclasses are mutable by default; no frozen=True observed
- **Note**: May change in later iterations

---

## 10. Async & Concurrency

### Async/Await Usage
- **Confidence**: High
- **Pattern**: Uses async/await for I/O-bound operations (LLM API calls)
- **Examples**:
  ```python
  async def _perform_async_inference(llm: Runnable[LanguageModelInput, BaseMessage],
                                      batched_tasks: List[InferenceRequest]) -> List[InferenceResult]:
      async_responses = [llm.ainvoke(task.context) for task in batched_tasks]
      responses = await asyncio.gather(*async_responses)
      return [InferenceResult(task_id=task.task_id, response=response)
              for task, response in zip(batched_tasks, responses)]
  ```
  File: `ocsf-playground/playground/backend/core/inference.py:43-47`

### Async Wrapper Pattern
- **Confidence**: High
- **Pattern**: Sync wrapper function calls `asyncio.run()` for async implementation
- **Examples**:
  ```python
  def perform_inference(llm: Runnable[LanguageModelInput, BaseMessage],
                        batched_tasks: List[InferenceRequest]) -> List[InferenceResult]:
      return asyncio.run(_perform_async_inference(llm, batched_tasks))
  ```
  File: `ocsf-playground/playground/backend/core/inference.py:35-36`

---

### Sequential Resource Cleanup Pattern
- **Confidence**: High
- **Pattern**: Follow AWS best practices for resource deletion in proper sequence
- **Examples**:
  ```python
  def delete_iam_role(role_name: str, aws_provider: AwsClientProvider):
      """
      One does not simply delete an IAM role; you have to follow the right steps.
      https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_manage_delete.html#roles-managingrole-deleting-cli
      """

      if not does_iam_role_exist(role_name, aws_provider):
          logger.debug(f"Role {role_name} does not exist; skipping deletion steps")
          return

      # Remove any attached instance profiles
      list_profiles_response = iam_client.list_instance_profiles_for_role(RoleName=role_name)
      for profile in list_profiles_response["InstanceProfiles"]:
          iam_client.remove_role_from_instance_profile(...)

      # Remove any inline policies
      list_inline_policies_response = iam_client.list_role_policies(RoleName=role_name)
      for inline_policy_name in list_inline_policies_response["PolicyNames"]:
          iam_client.delete_role_policy(...)

      # Detach any managed policies
      list_managed_policies_response = iam_client.list_attached_role_policies(RoleName=role_name)
      for managed_policy in list_managed_policies_response["AttachedPolicies"]:
          iam_client.detach_role_policy(...)

      # Now we can delete the IAM role
      iam_client.delete_role(RoleName=role_name)
  ```
  File: `aws-aio/manage_arkime/aws_interactions/iam_interactions.py:20-58`

**Observation**: Docstring includes AWS documentation link explaining why sequence matters, early return if resource doesn't exist

### AWS Account Validation Pattern
- **Confidence**: High
- **Pattern**: Validate AWS account credentials match expected account before destructive operations
- **Examples**:
  ```python
  aws_env = aws_provider.get_aws_env()
  if aws_env.aws_account != association.clusterAccount:
      logger.error("This command must be called with AWS Credential associated with the same AWS Account as the Cluster"
                   + f" {cluster_name}.  Expected Account: {association.clusterAccount}, Actual Account: {aws_env.aws_account}."
                   + " Aborting...")
      return
  ```
  File: `aws-aio/manage_arkime/commands/cluster_deregister_vpc.py:39-44`

**Observation**: Pattern includes descriptive error message explaining which account was expected vs actual, explicit "Aborting..." message

### If-Else Policy Update Pattern
- **Confidence**: High
- **Pattern**: Check if resource exists, update if present, create if absent
- **Examples**:
  ```python
  def setup_user_history_ism(history_days: int, client: OpenSearchClient):
      # Create the new policy template
      policy = policies.get_user_history_ism_policy(history_days)

      # Get the existing policy, if it exists
      get_policy_raw = client.get_ism_policy(policies.ISM_ID_HISTORY)

      # If it exists
      if get_policy_raw.succeeded:
          # Update the existing policy
          sequence_number = get_policy_raw.response_json["_seq_no"]
          primary_term = get_policy_raw.response_json["_primary_term"]
          client.update_ism_policy(policies.ISM_ID_HISTORY, policy, sequence_number, primary_term)

          # Ensure existing indices with that policy use the updated version
          client.set_ism_policy_of_index(policies.ISM_ID_HISTORY, policies.INDEX_PATTERN_HISTORY)

          # Add the policy to any new indices
          client.add_ism_policy_to_index(policies.ISM_ID_HISTORY, policies.INDEX_PATTERN_HISTORY)
      else:
          # Create the policy
          client.create_ism_policy(policies.ISM_ID_HISTORY, policy)

          # Add the policy to the indices
          client.add_ism_policy_to_index(policies.ISM_ID_HISTORY, policies.INDEX_PATTERN_HISTORY)
  ```
  File: `aws-aio/manage_arkime/opensearch_interactions/ism_interactions.py:6-30`

**Observation**: Pattern comments clarify each step, duplicates some operations (add_ism_policy_to_index) in both branches for completeness

### Type Alias for Union Types
- **Confidence**: High
- **Pattern**: Create descriptive type aliases for complex union types
- **Examples**:
  ```python
  from typing import Union
  UserVal = Union[int, str, float]

  def _line(self, name: str, oldVal: UserVal, newVal: UserVal) -> str:
      # ...
  ```
  File: `aws-aio/manage_arkime/core/usage_report.py:7-17`

**Observation**: Type alias makes function signatures more readable and self-documenting

## 11. API Design

### Public vs Private Boundaries
- **Confidence**: High
- **Pattern**: Leading underscore (`_`) for private/internal methods
- **Examples**: `_create_regex()`, `_validate()`, `_get_session()`, `_perform_async_inference()`

### Parameter Patterns
- **Confidence**: High
- **Pattern**: Explicit parameters preferred; defaults for optional params; kwargs for flexible APIs
- **Examples**:
  ```python
  def __init__(self, aws_profile: str = "default", aws_region: str = None,
               aws_compute=False, assume_role_arn: str=None):
  ```
  File: `aws-aio/manage_arkime/aws_interactions/aws_client_provider.py:15`

### Return Value Conventions
- **Confidence**: High
- **Pattern**: Returns typed objects (dataclasses); uses None for optional returns
- **Examples**: All functions have explicit return types in signatures

### Explicit Over Implicit
- **Confidence**: High
- **Pattern**: Explicit parameter passing, explicit imports (no `import *`)
- **Examples**: All imports are explicit; functions take explicit parameters

### Callback/Provider Function Parameters
- **Confidence**: High
- **Pattern**: Pass provider functions as parameters for flexibility and testability
- **Examples**:
  ```python
  def _upload_arkime_config_if_necessary(cluster_name: str, bucket_name: str, s3_key: str,
                                         ssm_param: str, archive_provider: Callable[[str], LocalFile],
                                         aws_provider: AwsClientProvider):
      # archive_provider is a function that creates the archive when called
      archive = archive_provider(cluster_name, aws_provider.get_aws_env())
  ```
  File: `aws-aio/manage_arkime/commands/cluster_create.py:243-260`

### Factory Functions that Return Functions
- **Confidence**: High
- **Pattern**: Factory functions return parameterized closures for creating prompts/messages
- **Examples**:
  ```python
  def get_analyze_system_prompt_factory(ocsf_version: OcsfVersion, ocsf_event_name: str) -> Callable[[Dict[str, Any]], SystemMessage]:
      def factory(input_entry: str) -> SystemMessage:
          event_schema = get_ocsf_event_schema(ocsf_version, ocsf_event_name, [])
          return SystemMessage(content=analyze_prompt_template.format(...))
      return factory
  ```
  File: `ocsf-playground/playground/backend/entities_expert/prompting/generation.py:15-33`

  **Observation**: This pattern encapsulates configuration (ocsf_version, event_name) in outer function and allows parameterization (input_entry) in returned closure

### Helper Functions with Underscores
- **Confidence**: High
- **Pattern**: Private helper functions prefixed with `_`, often defined at module level
- **Examples**: `_get_pattern_function_name()`, `_get_helper_code()`, `_get_transformer_wrapper_code()`, `_should_proceed_with_operation()`
- **Purpose**: Break down complex command functions into smaller, testable units

---

## 12. Meta Patterns

### Module-Level Constants
- **Confidence**: High
- **Pattern**: Constants defined at module top, right after imports
- **Examples**:
  ```python
  MAX_TRAFFIC = 100 # Gbps, scaling limit of a single User Subnet VPC Endpoint
  MINIMUM_TRAFFIC = 0.01 # Gbps; arbitrarily chosen
  CAPACITY_BUFFER_FACTOR = 1.25 # Arbitrarily chosen
  ```
  File: `aws-aio/manage_arkime/core/capacity_planning.py:11-13`

### Cross-Boundary Constants Module
- **Confidence**: High
- **Pattern**: Dedicated constants.py module for values shared across Python/CDK boundary
- **Examples**:
  ```python
  # constants.py
  CDK_CONTEXT_CMD_VAR: str = "ARKIME_CMD"
  CDK_CONTEXT_PARAMS_VAR: str = "ARKIME_PARAMS"

  EVENT_SOURCE = "arkime"
  EVENT_DETAIL_TYPE_CONFIGURE_ISM = "ConfigureIsm"
  EVENT_DETAIL_TYPE_CREATE_ENI_MIRROR = "CreateEniMirror"

  SSM_CLUSTERS_PREFIX = "/arkime/clusters"

  def get_capture_bucket_ssm_param_name(cluster_name: str) -> str:
      return f"{SSM_CLUSTERS_PREFIX}/{cluster_name}/capture-bucket-name"

  def get_vpc_mirror_setup_stack_name(cluster_name: str, vpc_id: str) -> str:
      return f"{cluster_name}-{vpc_id}-Mirror"
  ```
  File: `aws-aio/manage_arkime/core/constants.py:1-166`

**Observation**: Pattern groups constants by purpose with comments explaining cross-boundary coordination, includes helper functions for generating consistent resource names

### CDK Context Generation
- **Confidence**: High
- **Pattern**: Use `shlex.quote()` to safely pass JSON context to CDK subprocess
- **Examples**:
  ```python
  def generate_cluster_create_context(name: str, viewer_cert_arn: str, ...) -> Dict[str, str]:
      cmd_params = {
          "nameCluster": name,
          "nameCaptureBucketSsmParam": constants.get_capture_bucket_ssm_param_name(name),
          "planCluster": json.dumps(cluster_plan.to_dict()),
          "stackNames": json.dumps(stack_names.to_dict()),
      }
      return {
          constants.CDK_CONTEXT_PARAMS_VAR: shlex.quote(json.dumps(cmd_params))
      }
  ```
  File: `aws-aio/manage_arkime/cdk_interactions/cdk_context.py:39-94`

### Factory Functions
- **Confidence**: High
- **Pattern**: `get_*` prefix for factory/provider functions
- **Examples**: `get_regex_expert()`, `get_categorization_expert()`, `get_capture_node_capacity_plan()`, `get_ecs_sys_resource_plan()`

### Context Management
- **Confidence**: Medium
- **Pattern**: Uses context managers (with statements) appropriately
- **Examples**:
  ```python
  with tarfile.open(self._tarball_path, "w:gz") as tar:
      tar.add(self._source_dir_path, arcname=os.path.basename(self._source_dir_path))
  ```
  File: `aws-aio/manage_arkime/core/local_file.py:42-43`

### Equality Methods
- **Confidence**: High
- **Pattern**: Custom `__eq__` methods on dataclasses for semantic equality
- **Examples**:
  ```python
  def __eq__(self, other) -> bool:
      return (self.instanceType == other.instanceType and self.desiredCount == other.desiredCount
              and self.maxCount == other.maxCount and self.minCount == other.minCount)
  ```
  File: `aws-aio/manage_arkime/core/capacity_planning.py:88-90`

### Interactive Shell Automation with pexpect
- **Confidence**: High
- **Pattern**: Use pexpect for automating interactive commands with request/response pairs
- **Examples**:
  ```python
  def call_shell_command(command: str, cwd: str = None, env: Dict[str, str] = None,
                         request_response_pairs: List[Tuple[str, str]] = [], suppress_stdout: bool = False,
                         output_logger: Callable = None):
      """
      Execute a command in a child shell process.
      The user can optionally supply a list of request/response pairs to handle command invocations that expect
      a user response. For example:
          call_shell_command('my_shell_command', request_response_pairs=[('Do you really want to?', 'yes')])
      """
      process_handle = pexpect.spawn(command, cwd=cwd, env=env, timeout=None)

      while True:
          default_expectation = [os.linesep, pexpect.EOF]
          expectations = [pair[0] for pair in request_response_pairs]
          expectations.extend(default_expectation)

          responses = [pair[1] for pair in request_response_pairs]
          match_number = process_handle.expect(expectations)

          if match_number < len(responses):
              process_handle.sendline(responses[match_number])

          if match_number == len(expectations) - 1:  # EOF
              break
  ```
  File: `aws-aio/manage_arkime/core/shell_interactions.py:11-54`

### Cryptography Pattern with State Guarding
- **Confidence**: High
- **Pattern**: Self-signed cert generation with state checking and domain-specific exceptions
- **Examples**:
  ```python
  class CertNotYetGenerated(Exception):
      def __init__(self):
          super().__init__("The certificate for this object has not yet been generated")

  class SelfSignedCert:
      def __init__(self, issuer_cn: str, subject_cn: str, sans: List[str], validity_duration: datetime.timedelta, key_size: int = 2048):
          self._private_key = None
          self._certificate = None

      def generate(self):
          if self._private_key or self._certificate:
              logger.warning("Certificate already generated for this instance; aborting")
              return

          self._private_key = rsa.generate_private_key(public_exponent=RSA_PUBLIC_EXPONENT, key_size=self._key_size)
          # ... cert generation logic ...
          self._certificate = cert_builder.sign(self._private_key, hashes.SHA256())

      def get_cert_bytes(self) -> bytes:
          if not self._certificate:
              raise CertNotYetGenerated()
          return self._certificate.public_bytes(serialization.Encoding.PEM)
  ```
  File: `aws-aio/manage_arkime/core/certificate_generation.py:14-100`

**Observation**: Pattern uses module-level constants (RSA_PUBLIC_EXPONENT), guards against duplicate generation, and raises specific exceptions for invalid state

### Versioning with Git + MD5
- **Confidence**: High
- **Pattern**: Combine `git describe --tags` with MD5 file hashing for comprehensive version tracking
- **Examples**:
  ```python
  def get_md5_of_file(file: LocalFile) -> str:
      hash_md5 = hashlib.md5()
      with open(file.local_path, "rb") as f:
          for chunk in iter(lambda: f.read(4096), b""):
              hash_md5.update(chunk)
      return hash_md5.hexdigest()

  def get_source_version() -> str:
      exit_code, stdout = call_shell_command("git describe --tags")
      if exit_code != 0:
          raise CouldntReadSourceVersion()
      return stdout[0]

  @dataclass
  class VersionInfo:
      aws_aio_version: str    # Manual version number
      config_version: str
      md5_version: str         # MD5 hash of config file
      source_version: str      # Git tag
      time_utc: str
  ```
  File: `aws-aio/manage_arkime/core/versioning.py:15-79`

### Simple REST Client Wrapper
- **Confidence**: High
- **Pattern**: Thin wrapper around requests library with consistent logging and error handling
- **Examples**:
  ```python
  @dataclass
  class ConnectionDetails:
      base_url: str

  class RESTClient():
      def __init__(self, connection_details: ConnectionDetails) -> None:
          self.base_url = connection_details.base_url.rstrip('/')

      def get(self, endpoint: str) -> Dict[str, Any]:
          url = f"{self.base_url}/{endpoint}"
          logger.debug(f"GET request to URL: {url}")
          response = requests.get(url)
          response.raise_for_status()
          logger.debug(f"GET response: {response.status_code} {response.text}")
          return response.json()

      def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
          url = f"{self.base_url}/{endpoint}"
          logger.debug(f"POST request to URL: {url} with data: {data}")
          response = requests.post(url, json=data)
          response.raise_for_status()
          return response.json()
  ```
  File: `ocsf-playground/playground/backend/core/rest_client.py:8-47`

**Observation**: Pattern includes base_url normalization with rstrip('/'), logging before/after each call, and raise_for_status() for error handling

### String Representations
- **Confidence**: Medium-High
- **Pattern**: Custom `__str__` methods for human-readable output
- **Examples**:
  ```python
  def __str__(self):
      return json.dumps(self.to_dict())
  ```
  File: `aws-aio/manage_arkime/opensearch_interactions/rest_ops.py:58-59`

---

## Files Analyzed

### Iteration 1 (15 files, ~3,100 lines)

**ocsf-playground (8 files, ~1,500 lines)**
- `playground_api/views.py` (515 lines)
- `playground_api/serializers.py` (517 lines)
- `backend/core/experts.py` (74 lines)
- `backend/core/inference.py` (47 lines)
- `backend/entities_expert/entities.py` (58 lines)
- `backend/entities_expert/task_def.py` (56 lines)
- `backend/entities_expert/expert_def.py` (87 lines)
- `backend/core/tasks.py` (36 lines)

**aws-aio (7 files, ~1,600 lines)**
- `manage_arkime.py` (376 lines)
- `core/capacity_planning.py` (536 lines)
- `aws_interactions/aws_client_provider.py` (137 lines)
- `opensearch_interactions/rest_ops.py` (115 lines)
- `cdk_interactions/cdk_client.py` (136 lines)
- `core/local_file.py` (120 lines)
- `arkime_interactions/config_wrangling.py` (248 lines)

### Iteration 2 (12 files, ~2,900 lines)

**ocsf-playground (6 files, ~666 lines)**
- `backend/transformers/validators.py` (197 lines)
- `backend/entities_expert/validators.py` (160 lines)
- `backend/transformers/transformers.py` (104 lines)
- `backend/entities_expert/tool_def.py` (104 lines)
- `backend/regex_expert/expert_def.py` (51 lines)
- `backend/categorization_expert/expert_def.py` (50 lines)

**aws-aio (6 files, ~2,234 lines)**
- `commands/cluster_create.py` (401 lines)
- `commands/config_update.py` (260 lines)
- `commands/cluster_destroy.py` (147 lines)
- `commands/vpc_add.py` (151 lines)
- `core/cross_account_wrangling.py` (214 lines)
- `core/vni_provider.py` (205 lines)

### Iteration 3 (14 files, ~2,700 lines)

**ocsf-playground (7 files, ~558 lines)**
- `backend/entities_expert/prompting/templates.py` (172 lines)
- `backend/entities_expert/prompting/generation.py` (64 lines)
- `backend/regex_expert/prompting/templates.py` (49 lines)
- `backend/categorization_expert/prompting/templates.py` (49 lines)
- `backend/regex_expert/tool_def.py` (39 lines)
- `backend/categorization_expert/tool_def.py` (36 lines)
- `backend/regex_expert/prompting/generation.py` (30 lines)

**aws-aio (7 files, ~2,142 lines)**
- `manage_arkime/aws_interactions/s3_interactions.py` (238 lines)
- `manage_arkime/lambda_aws_event_listener/aws_event_listener_handler.py` (230 lines)
- `manage_arkime/aws_interactions/cloudwatch_interactions.py` (215 lines)
- `manage_arkime/aws_interactions/ec2_interactions.py` (193 lines)
- `manage_arkime/core/constants.py` (165 lines)
- `manage_arkime/aws_interactions/events_interactions.py` (135 lines)
- `manage_arkime/cdk_interactions/cdk_context.py` (128 lines)

### Iteration 4 (20 files, ~2,200 lines)

**ocsf-playground (10 files, ~645 lines)**
- `playground/playground/settings.py` (211 lines)
- `playground/backend/core/ocsf/ocsf_schemas.py` (176 lines)
- `playground/backend/core/rest_client.py` (47 lines)
- `playground/backend/regex_expert/task_def.py` (42 lines)
- `playground/backend/categorization_expert/task_def.py` (42 lines)
- `playground/backend/entities_expert/extraction_pattern.py` (36 lines)
- `playground/backend/core/validation_report.py` (29 lines)
- `playground/backend/categorization_expert/prompting/generation.py` (27 lines)
- `playground/manage.py` (22 lines)
- `playground/playground/urls.py` (18 lines)

**aws-aio (10 files, ~1,555 lines)**
- `manage_arkime/commands/config_pull.py` (133 lines)
- `manage_arkime/lambda_create_eni_mirror/create_eni_mirror_handler.py` (117 lines)
- `manage_arkime/core/certificate_generation.py` (99 lines)
- `manage_arkime/core/price_report.py` (90 lines)
- `manage_arkime/core/shell_interactions.py` (89 lines)
- `manage_arkime/core/versioning.py` (78 lines)
- `manage_arkime/core/user_config.py` (77 lines)
- `manage_arkime/core/logging_wrangler.py` (73 lines)
- `manage_arkime/lambda_destroy_eni_mirror/destroy_eni_mirror_handler.py` (72 lines)
- `manage_arkime/lambda_configure_ism/configure_ism_handler.py` (71 lines)

### Iteration 5 (24 files, ~2,700 lines)

**aws-aio (24 files, ~2,700 lines)**
- `commands/config_list.py` (78 lines)
- `commands/clusters_list.py` (78 lines)
- `commands/cluster_deregister_vpc.py` (66 lines)
- `commands/cluster_register_vpc.py` (57 lines)
- `commands/vpc_deregister_cluster.py` (50 lines)
- `commands/get_login_details.py` (50 lines)
- `commands/vpc_register_cluster.py` (40 lines)
- `commands/demo_traffic_destroy.py` (18 lines)
- `commands/demo_traffic_deploy.py` (18 lines)
- `opensearch_interactions/ism_policies.py` (134 lines)
- `opensearch_interactions/opensearch_client.py` (68 lines)
- `opensearch_interactions/ism_interactions.py` (55 lines)
- `cdk_interactions/cdk_exceptions.py` (96 lines)
- `cdk_interactions/cfn_wrangling.py` (61 lines)
- `aws_interactions/ssm_operations.py` (81 lines)
- `aws_interactions/iam_interactions.py` (57 lines)
- `aws_interactions/acm_interactions.py` (54 lines)
- `aws_interactions/destroy_os_domain.py` (42 lines)
- `aws_interactions/ecs_interactions.py` (32 lines)
- `aws_interactions/aws_environment.py` (19 lines)
- `core/compatibility.py` (59 lines)
- `core/usage_report.py` (55 lines)
- `setup.py` (22 lines)
- `lambda_handlers.py` (8 lines)

### Iteration 6 (17 files, ~1,000 lines)

**ocsf-playground (17 files, ~1,000 lines)**
- `backend/core/ocsf/ocsf_schema_v1_1_0.py` (775 lines)
- `backend/core/ocsf/ocsf_event_classes.py` (34 lines)
- `backend/entities_expert/prompting/knowledge/__init__.py` (29 lines)
- `backend/core/tools.py` (17 lines)
- `playground/wsgi.py` (16 lines)
- `playground/asgi.py` (16 lines)
- `backend/regex_expert/prompting/knowledge/__init__.py` (16 lines)
- `backend/categorization_expert/prompting/knowledge/__init__.py` (16 lines)
- `backend/regex_expert/parameters.py` (13 lines)
- `backend/categorization_expert/prompting/knowledge/ocsf_v1_1_0.py` (13 lines)
- `playground_api/apps.py` (9 lines)
- `backend/core/validators.py` (9 lines)
- `backend/regex_expert/prompting/knowledge/javascript.py` (8 lines)
- `playground_api/models.py` (6 lines)
- `backend/core/ocsf/ocsf_versions.py` (6 lines)
- `backend/transformers/parameters.py` (5 lines)
- `playground_api/admin.py` (4 lines)

### Iteration 7 (9 files, ~3,900 lines)

**ocsf-playground (3 files, ~520 lines)**
- `playground_api/tests/test_views.py` (334 lines)
- `playground_api/tests/test_serializers.py` (193 lines)
- `backend/core/tests/test_rest_client.py` (129 lines)

**aws-aio (6 files, ~3,380 lines)**
- `test_manage_arkime/commands/test_cluster_create.py` (1,244 lines)
- `test_manage_arkime/lambda_aws_event_listener/test_aws_event_listener_handler.py` (900 lines)
- `test_manage_arkime/core/test_ssm_vni_provider.py` (494 lines)
- `test_manage_arkime/core/test_cross_account_wrangling.py` (348 lines)
- `test_manage_arkime/cdk_interactions/test_cdk_client.py` (355 lines)
- `test_manage_arkime/core/test_capacity_planning.py` (306 lines)

### Iteration 8 (14 files, ~3,500 lines)

**aws-aio (14 files, ~3,500 lines)**
- `test_manage_arkime/commands/test_config_update.py` (716 lines)
- `test_manage_arkime/commands/test_vpc_add.py` (616 lines)
- `test_manage_arkime/commands/test_cluster_destroy.py` (522 lines)
- `test_manage_arkime/aws_interactions/test_s3_interactions.py` (380 lines)
- `test_manage_arkime/aws_interactions/test_ec2_interactions.py` (323 lines)
- `test_manage_arkime/commands/test_vpc_remove.py` (285 lines)
- `test_manage_arkime/aws_interactions/test_cloudwatch_interactions.py` (281 lines)
- `test_manage_arkime/lambda_create_eni_mirror/test_create_eni_mirror_handler.py` (252 lines)
- `test_manage_arkime/commands/test_config_pull.py` (228 lines)
- `test_manage_arkime/arkime_interactions/test_config_wrangling.py` (199 lines)
- `test_manage_arkime/commands/test_config_list.py` (184 lines)
- `test_manage_arkime/cdk_interactions/test_cdk_exceptions.py` (181 lines)
- `test_manage_arkime/aws_interactions/test_ssm_operations.py` (173 lines)
- `test_manage_arkime/lambda_destroy_eni_mirror/test_destroy_eni_mirror_handler.py` (170 lines)

### Iteration 9 (27 files, ~2,400 lines)

**aws-aio (27 files, ~2,400 lines)**
- `test_manage_arkime/core/test_shell_interactions.py` (160 lines)
- `test_manage_arkime/aws_interactions/test_aws_client_provider.py` (151 lines)
- `test_manage_arkime/commands/test_cluster_deregister_vpc.py` (147 lines)
- `test_manage_arkime/opensearch_interactions/test_ism_interactions.py` (183 lines)
- `test_manage_arkime/opensearch_interactions/test_opensearch_client.py` (131 lines)
- `test_manage_arkime/lambda_configure_ism/test_configure_ism_handler.py` (130 lines)
- `test_manage_arkime/commands/test_cluster_register_vpc.py` (130 lines)
- `test_manage_arkime/core/test_usage_report.py` (127 lines)
- `test_manage_arkime/core/test_certificate_generation.py` (123 lines)
- `test_manage_arkime/commands/test_clusters_list.py` (121 lines)
- `test_manage_arkime/aws_interactions/test_iam_interactions.py` (113 lines)
- `test_manage_arkime/opensearch_interactions/test_rest_ops.py` (108 lines)
- `test_manage_arkime/cdk_interactions/test_cfn_wrangling.py` (108 lines)
- `test_manage_arkime/commands/test_vpc_deregister_cluster.py` (103 lines)
- `test_manage_arkime/aws_interactions/test_ecs_interactions.py` (100 lines)
- `test_manage_arkime/aws_interactions/test_acm_interactions.py` (79 lines)
- `test_manage_arkime/core/test_versioning.py` (74 lines)
- `test_manage_arkime/core/test_local_file.py` (72 lines)
- `test_manage_arkime/commands/test_get_login_details.py` (60 lines)
- `test_manage_arkime/commands/test_vpc_register_cluster.py` (61 lines)
- `test_manage_arkime/core/test_price_report.py` (55 lines)
- `test_manage_arkime/core/test_compatibility.py` (54 lines)
- `test_manage_arkime/aws_interactions/test_destroy_os_domain.py` (46 lines)
- `test_manage_arkime/aws_interactions/test_events_interactions.py` (41 lines)
- `test_manage_arkime/commands/test_demo_traffic_destroy.py` (33 lines)
- `test_manage_arkime/commands/test_demo_traffic_deploy.py` (33 lines)
- `test_manage_arkime/core/test_constants.py` (22 lines)

---

**Phase 2 Complete**: All 174 Python files (22,124 lines) have been analyzed across 9 iterations. The style guide is now ready for Phase 3 (Human-Led Refinement).
