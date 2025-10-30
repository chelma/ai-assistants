# Chris's Python Coding Style Guide

This document captures Chris's personal Python coding style and engineering philosophy based primarily on analysis of two production repositories GitHub repos: `github.com/chelma/ocsf-playground` and `github.com/arkime/aws-aio`.

---

## 1. Code Organization & Architecture

### Module Organization
- **Pattern**: Domain-driven directory structure with clear separation of concerns
- **Examples**:
  - `backend/{expert_name}_expert/` structure for each AI expert system
  - `{function}_interactions/` for external system boundaries (aws, cdk, opensearch)

**Observation**: Each major domain gets its own package with explicit boundaries:
```
backend/
├── categorization_expert/    # Self-contained expert
├── entities_expert/           # Self-contained expert
├── regex_expert/              # Self-contained expert
└── core/                      # Shared utilities
```

### Separation of Concerns
- **Pattern**: Dedicated modules for specific responsibilities
- **Examples**:
  - `expert_def.py` - Expert initialization and invocation
  - `task_def.py` - Task data structures
  - `tool_def.py` - LangChain tool definitions
  - `validators.py` - Validation logic

### Package Naming
- **Pattern**: `snake_case` for packages/modules, descriptive and specific
- **Examples**: `aws_interactions`, `entities_expert`, `capacity_planning`, `config_wrangling`

---

## 2. Type System & Annotations

### Type Hints Usage
- **Pattern**: Comprehensive type hints on function signatures, including return types
- **Examples**:
  ```python
  def get_capture_node_capacity_plan(expected_traffic: float, azs: List[str]) -> CaptureNodesPlan:
  ```

### Custom Types & Type Aliases
- **Pattern**: Extensive use of TypeVar for generic type bounds on dataclasses
- **Examples**:
  ```python
  T_ClusterPlan = TypeVar('T_ClusterPlan', bound='ClusterPlan')

  @classmethod
  def from_dict(cls: Type[T_ClusterPlan], input: Dict[str, any]) -> T_ClusterPlan:
  ```

### Typing Module Constructs
- **Pattern**: Uses `Dict`, `List`, `Type`, `TypeVar`, `Callable`, `Any` from typing
- **Observation**: Prefers explicit imports from typing module rather than PEP 585 built-in generics
- **Examples**: `from typing import Dict, Any, Callable, Type`

### Runtime Type Checking
- **Pattern**: Manual type validation only in critical paths where there is real risk
- **Examples**:
  ```python
  def set_work_item(self, new_work_item: Any):
      if not isinstance(new_work_item, EntityReport):
          raise TypeError("new_work_item must be of type EntityReport")
  ```

### Pydantic for Schema Validation
- **Pattern**: Uses Pydantic BaseModel for LangChain tool schemas and structured inputs
- **Examples**:
  ```python
  class EntityInput(BaseModel):
      """A single entity extracted from the data entry"""
      value: str = Field(description="The raw value extracted from the input data...")
      description: str = Field(description="A precise explanation of what the value represents...")
  ```

---

## 3. Documentation Philosophy

### Docstring Style
- **Pattern**: Minimal docstrings; the most important and complex functions have triple-quoted explanatory comments
- **Examples**:
  ```python
  def get_ecs_sys_resource_plan(instance_type: str) -> EcsSysResourcePlan:
      """
      Creates a capacity plan for the indicated instance type.
      instance_type: The instance type to plan for
      """
  ```

### Comment Style
- **Pattern**: Inline comments explain "why" not "what", to document unintuitive or complex business logic
- **Examples**:
  ```python
  # Inference APIs can be throttled pretty aggressively.  Performing them as a batch operation can help with increasing
  # throughput. Ideally, we'd be using Bedrock's batch inference API, but Bedrock's approach to that is an asynchronous
  # process that writes the results to S3 and returns a URL to the results.  This is not implemented by default in the
  # ChatBedrockConverse class, so we'll skip true batch processing for now.  Instead, we'll just perform the inferences in
  # parallel with aggressive retry logic.
  ```

### Hardcoded Values Documentation
- **Pattern**: Inline comments explain magic numbers and why values are chosen
- **Examples**:
  ```python
  MINIMUM_TRAFFIC = 0.01 # Gbps; arbitrarily chosen, but will yield a minimal cluster
  CAPACITY_BUFFER_FACTOR = 1.25 # Arbitrarily chosen
  MASTER_NODE_COUNT = 3 # Recommended number in docs
  ```

### Prompt Engineering for LLMs
- **Pattern**: Multi-paragraph prompt templates with XML-tagged sections for structured guidance, layered in increasing specificity so that the most tokens possible can be cached between inference API calls
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
**Observation**: Templates use XML tags for structured sections, Python format strings for parameterization, and explicit behavioral constraints

### String Templates with .format()
- **Pattern**: Multi-line string constants with `.format()` for parameterization
- **Examples**:
  ```python
  OCSF_KNOWLEDGE = """
  <ocsf_event_classes>
  {ocsf_event_classes}
  </ocsf_event_classes>
  """.format(ocsf_event_classes=json.dumps(OCSF_EVENT_CLASSES, indent=4))
  ```
**Observation**: For static templates with dynamic content insertion, use triple-quoted strings with `.format()` called immediately at module level. This pre-renders the template once at import time.

### Inline Comments for Provenance
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
**Observation**: When data is generated or derived from external sources (AI, documentation, conversations), include inline comments documenting the source and method. This aids future maintenance and verification.

---

## 4. Error Handling & Robustness

### Custom Exception Hierarchy
- **Pattern**: Custom exceptions inherit from base Exception with descriptive names
- **Examples**:
  ```python
  class TooMuchTraffic(Exception):
      def __init__(self, expected_traffic: int):
          super().__init__(f"User's expected traffic ({expected_traffic} Gbps) exceeds the limit of a single cluster ({MAX_TRAFFIC})")
  ```

  ```python
  class ExpertInvocationError(Exception):
      pass
  ```

### Exception Naming
- **Pattern**: Descriptive, specific exception names that indicate the problem
- **Examples**: `TooMuchTraffic`, `NotEnoughStorage`, `InvalidCidr`, `FileNotGenerated`, `AssumeRoleNotSupported`, `RESTOperationFailedException`

### Logging Approach
- **Pattern**: Module-level logger instances; consistent use throughout
- **Examples**:
  ```python
  logger = logging.getLogger(__name__)
  ```

  ```python
  logger = logging.getLogger("backend")
  ```

### Custom Logging Formatter with UTC Timestamps
- **Pattern**: Custom formatter for UTC timestamps and invisible Unicode line separators to facilitate downstream automated parsing
- **Examples**:
  ```python
  class LoggingFormatter(logging.Formatter):
      def formatTime(self, record, datefmt=None):
          return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')

  # Invisible Unicode character for log entry boundaries
  LINE_SEP = '\u2063'

  file_formatter = LoggingFormatter(f"%(asctime)s - %(name)s - %(message)s{LINE_SEP}")
  ```

### Log Levels
- **Pattern**: Strategic use of info, debug, warning, error levels
- **Examples**:
  ```python
  logger.info(f"Received heuristic creation request: {request.data}")
  logger.debug(f"Regex value:\n{result.regex.value}")
  logger.error(f"Regex creation failed: {str(e)}")
  logger.exception(e)  # Includes traceback
  ```

---

## 5. Testing Approach

### Test Framework Preferences
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
- **Pattern**: `test_WHEN_<action>_<conditions>_THEN_<expected_result>` for comprehensive context
- **Examples**:
  - `test_WHEN_cmd_cluster_create_called_THEN_cdk_command_correct`
  - `test_WHEN_deploy_called_AND_not_bootstrapped_THEN_executes_command`
  - `test_WHEN_should_proceed_with_operation_AND_abort_usage_THEN_as_expected`
**Observation**: The naming convention makes test purpose immediately clear and provides complete context without needing to read the test body.

### Mocking Strategy
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
- **Pattern**: Use `pytest.raises` context manager for exception verification
- **Examples**:
  ```python
  with pytest.raises(cap.TooMuchTraffic):
      cap.get_capture_node_capacity_plan(cap.MAX_TRAFFIC + 10, azs)

  with pytest.raises(exceptions.CdkDeployFailedUnknown):
      client.deploy(["MyStack"])
  ```

### Module-Level Test Constants
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

## 6. Code Style & Idioms

### Naming Conventions

#### Variables & Functions
- **Pattern**: `snake_case` for variables and functions
- **Examples**: `expected_traffic`, `cluster_name`, `get_capture_node_capacity_plan`

#### Classes
- **Pattern**: `PascalCase` for classes
- **Examples**: `Expert`, `CaptureNodesPlan`, `AwsClientProvider`, `RESTPath`

#### Constants
- **Pattern**: `SCREAMING_SNAKE_CASE` for module-level constants
- **Examples**: `MAX_TRAFFIC`, `MINIMUM_TRAFFIC`, `DEFAULT_SPI_DAYS`, `DEFULT_BOTO_CONFIG` [sic]

#### Private/Internal
- **Pattern**: Leading underscore for internal methods and variables
- **Examples**: `_aws_profile`, `_get_session()`, `_create_regex()`, `_validate()`

### Line Length
- **Pattern**: Generally stays under 120 characters; breaks long strings and method chains
- **Examples**:
  ```python
  command_prefix = get_command_prefix(
      aws_profile=self._aws_env.aws_profile,
      aws_region=self._aws_env.aws_region,
      context=context
  )
  ```

### Import Organization
- **Pattern**: Imports grouped by: stdlib → third-party → local (with blank lines between)
- **Examples**:
  ```python
  import json
  import logging
  from typing import List

  from django.views.decorators.csrf import csrf_exempt
  from langchain_core.messages import HumanMessage
  from rest_framework.views import APIView

  from backend.categorization_expert.expert_def import get_categorization_expert
  from backend.core.ocsf.ocsf_versions import OcsfVersion
  ```

### Comprehensions vs Loops
- **Pattern**: Prefer list comprehensions for simple transformations
- **Examples**:
  ```python
  [pattern.to_json() for pattern in result.patterns]
  ```

### F-Strings
- **Pattern**: Use of f-strings for string formatting
- **Examples**:
  ```python
  logger.info(f"Received heuristic creation request: {request.data}")
  logger.error(f"Invalid heuristic creation request: {request.errors}")
  ```

### Boolean Expressions for Control Flow
- **Pattern**: Break complex boolean logic into simpler expressions with clear variable names for intermediate results
- **Examples**:
  ```python
  one_component_specified = (capture or viewer) and not (capture and viewer)
  no_component_specified = not (capture or viewer)
  if config_version and (not one_component_specified):
      logger.error("If you specify a specific config version...")
  ```

### Conditional Assignment Patterns
- **Pattern**: Use ternary expressions for conditional assignments
- **Examples**:
  ```python
  next_config_version = (
      str(switch_to_version)
      if switch_to_version
      else str(int(cloud_config_details.version.config_version) + 1)
  )
  ```

---

## 7. Dependencies & Tooling

### Standard Library vs Third-Party
- **Pattern**: Leverages stdlib heavily (logging, abc, dataclasses, typing), brings in third-party for specific needs
- **Third-party observed**: Django, DRF, Click, boto3, LangChain, requests

### AWS SDK (boto3) Usage
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
**Observation**: Pattern includes custom exception classes for domain errors, ClientError parsing, pagination handling, and regional API nuances (e.g., us-east-1 special case)

### CLI Framework
- **Pattern**: Uses Click for command-line interfaces
- **Examples**: Extensive use of `@click.command()`, `@click.option()`, `@click.group()`

---

## 8. Design Patterns & Principles

### Dataclass Usage
- **Pattern**: Heavy use of `@dataclass` for data structures; prefers dataclasses over plain classes or dicts
- **Examples**:
  ```python
  @dataclass
  class Expert:
      llm: Runnable[LanguageModelInput, BaseMessage]
      system_prompt_factory: Callable[[Dict[str, Any]], SystemMessage]
      tools: ToolBundle
  ```

  ```python
  @dataclass
  class CaptureNodesPlan:
      instanceType: str
      desiredCount: int
      maxCount: int
      minCount: int
  ```

### Serialization Patterns
- **Pattern**: Dataclasses have `to_dict()` instance methods and `from_dict()` class methods, ternary expressions to conditionally serialize optional fields
- **Examples**:
  ```python
  def to_dict(self) -> Dict[str, any]:
      return {
          "count": self.count,
          "instanceType": self.instanceType,
          "volumeSize": self.volumeSize,
          "mapping": self.mapping.to_dict() if self.mapping else None
      }

  @classmethod
  def from_dict(cls: Type[T_ClusterPlan], input: Dict[str, any]) -> T_ClusterPlan:
      capture_nodes = CaptureNodesPlan(**input["captureNodes"])
      # ...
  ```

### Abstract Base Classes
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

### Client/Provider Pattern
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

### Composition Over Inheritance
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

### Strategy Pattern with Version Selection
- **Pattern**: Functions dispatch to different implementations based on version/flavor enum
- **Examples**:
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
**Observation**: For version-specific or flavor-specific logic, use if-elif chains returning implementation-specific code. Return empty/None for unsupported versions. This pattern allows adding new versions without modifying calling code.

---

## 9. Data Handling

### Data Structure Choices
- **Pattern**: Prefers dataclasses for structured data, dicts for JSON interop
- **Examples**: All data models are dataclasses (Entity, EntityMapping, CaptureNodesPlan, etc.)

### Serialization
- **Confidence**: High
- **Pattern**: `to_dict()` methods for serialization, `from_dict()` class methods for deserialization
- **Examples**: See Design Patterns section

### Dataclasses vs NamedTuples vs Pydantic
- **Pattern**: Uses `@dataclass` from stdlib for data models; Pydantic BaseModel for LangChain tool schemas only

### Nested Dataclass Deserialization
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

### Printable Wrappers with Attribute Filtering
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

### Recursive Data Structures
- **Pattern**: Dataclasses reference themselves for linked structures (with None termination)
- **Examples**:
  ```python
  @dataclass
  class ConfigDetails:
      s3: S3Details
      version: VersionInfo
      previous: ConfigDetails = None  # Recursive reference
  ```

### Immutability
- **Pattern**: Dataclasses are mutable by default; avoid frozen=True except for critical code sections

---

## 10. Async & Concurrency

### Async/Await Usage
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

### Async Wrapper Pattern
- **Pattern**: Sync wrapper function calls `asyncio.run()` for async implementation
- **Examples**:
  ```python
  def perform_inference(llm: Runnable[LanguageModelInput, BaseMessage],
                        batched_tasks: List[InferenceRequest]) -> List[InferenceResult]:
      return asyncio.run(_perform_async_inference(llm, batched_tasks))
  ```

## 11. API Design

### Public vs Private Boundaries
- **Pattern**: Leading underscore (`_`) for private/internal methods
- **Examples**: `_create_regex()`, `_validate()`, `_get_session()`, `_perform_async_inference()`

### Parameter Patterns
- **Pattern**: Explicit parameters preferred; defaults for optional params; kwargs for flexible APIs
- **Examples**:
  ```python
  def __init__(self, aws_profile: str = "default", aws_region: str = None,
               aws_compute=False, assume_role_arn: str=None):
  ```

### Return Value Conventions
- **Pattern**: Returns typed objects (such as dataclasses); uses None for optional returns
- **Examples**: All functions have explicit return types in signatures

### Explicit Over Implicit
- **Pattern**: Explicit parameter passing, explicit imports (no `import *`)
- **Examples**: All imports are explicit; functions take explicit parameters

### Callback/Provider Function Parameters
- **Pattern**: Pass provider functions as parameters for flexibility and testability
- **Examples**:
  ```python
  def _upload_arkime_config_if_necessary(cluster_name: str, bucket_name: str, s3_key: str,
                                         ssm_param: str, archive_provider: Callable[[str], LocalFile],
                                         aws_provider: AwsClientProvider):
      # archive_provider is a function that creates the archive when called
      archive = archive_provider(cluster_name, aws_provider.get_aws_env())
  ```

### Factory Functions that Return Functions
- **Pattern**: Factory functions return parameterized closures for creating prompts/messages
- **Examples**:
  ```python
  def get_analyze_system_prompt_factory(ocsf_version: OcsfVersion, ocsf_event_name: str) -> Callable[[Dict[str, Any]], SystemMessage]:
      def factory(input_entry: str) -> SystemMessage:
          event_schema = get_ocsf_event_schema(ocsf_version, ocsf_event_name, [])
          return SystemMessage(content=analyze_prompt_template.format(...))
      return factory
  ```
  **Observation**: This pattern encapsulates configuration (ocsf_version, event_name) in outer function and allows parameterization (input_entry) in returned closure

### Helper Functions with Underscores
- **Pattern**: Private helper functions prefixed with `_`, often defined at module level
- **Examples**: `_get_pattern_function_name()`, `_get_helper_code()`, `_get_transformer_wrapper_code()`, `_should_proceed_with_operation()`
- **Purpose**: Break down complex command functions into smaller, testable units

---

## 12. Meta Patterns

### Module-Level Constants
- **Pattern**: Constants defined at module top, right after imports
- **Examples**:
  ```python
  MAX_TRAFFIC = 100 # Gbps, scaling limit of a single User Subnet VPC Endpoint
  MINIMUM_TRAFFIC = 0.01 # Gbps; arbitrarily chosen
  CAPACITY_BUFFER_FACTOR = 1.25 # Arbitrarily chosen
  ```

### Factory Functions
- **Confidence**: High
- **Pattern**: `get_*` prefix for factory/provider functions
- **Examples**: `get_regex_expert()`, `get_categorization_expert()`, `get_capture_node_capacity_plan()`, `get_ecs_sys_resource_plan()`

### Context Management
- **Pattern**: Uses context managers (with statements) appropriately
- **Examples**:
  ```python
  with tarfile.open(self._tarball_path, "w:gz") as tar:
      tar.add(self._source_dir_path, arcname=os.path.basename(self._source_dir_path))
  ```

### Equality Methods
- **Pattern**: Custom `__eq__` methods on dataclasses for semantic equality
- **Examples**:
  ```python
  def __eq__(self, other) -> bool:
      return (self.instanceType == other.instanceType and self.desiredCount == other.desiredCount
              and self.maxCount == other.maxCount and self.minCount == other.minCount)
  ```

### Interactive Shell Automation with pexpect
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

### Simple Client Wrappers
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

**Observation**: Pattern includes base_url normalization with rstrip('/'), logging before/after each call, and raise_for_status() for error handling

### String Representations
- **Pattern**: Custom `__str__` methods for human-readable output
- **Examples**:
  ```python
  def __str__(self):
      return json.dumps(self.to_dict())
  ```
