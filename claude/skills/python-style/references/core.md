# Chris's Python Coding Style Guide

This document captures Chris's personal Python coding style based initially on analysis of two production repositories: `github.com/chelma/ocsf-playground` and `github.com/arkime/aws-aio`.

---

## How to Use This Guide

**Philosophy Over Prescription**

These patterns represent preferences and observed practices, not rigid rules. The goal is to embody the engineering judgment behind these choices, not just replicate their surface appearance.

**Guiding Principles:**

1. **Match existing project conventions when they differ** - If you're working in a codebase with established patterns that conflict with this guide, try follow the project's conventions for consistency while respecting the priority levels of the individual guidelines in this style guide.

2. **Adapt to context** - Some patterns documented here are project-specific (e.g., LLM prompt engineering, AWS infrastructure). Apply them when relevant, but don't force-fit them into unrelated contexts.

3. **Suggest improvements when warranted** - If you have strong engineering reasons to deviate from these patterns (performance, security, maintainability, new language features), propose alternatives with clear rationale.

4. **Prioritize signal over noise** - These patterns emerged from production code solving real problems. Understand the "why" behind each pattern before applying it.

**When in doubt:** Favor readability, type safety, explicit behavior, and comprehensive testing.

---

## Priority Levels

Patterns are marked with priority indicators:

- **CRITICAL** - Core principles that should always be followed (e.g., test naming conventions, type hints on public APIs)
- **PREFERRED** - Default choices unless context suggests otherwise (e.g., dataclasses over dicts, pytest over unittest)
- **OBSERVED** - Patterns extracted from analyzed code; useful as reference but highly context-dependent (e.g., `{function}_interactions/` module naming)

---

## Code Organization & Architecture

### Module Organization
- **Priority**: OBSERVED
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
- **Priority**: PREFERRED
- **Pattern**: Dedicated modules for specific responsibilities
- **Examples**:
  - `expert_def.py` - Expert initialization and invocation
  - `task_def.py` - Task data structures
  - `tool_def.py` - LangChain tool definitions
  - `validators.py` - Validation logic

### Package Naming
- **Priority**: CRITICAL
- **Pattern**: `snake_case` for packages/modules, descriptive and specific
- **Examples**: `aws_interactions`, `entities_expert`, `capacity_planning`, `config_wrangling`

---

## Type System & Annotations

### Type Hints Usage
- **Priority**: CRITICAL
- **Pattern**: Comprehensive type hints on function signatures, including return types
- **Examples**:
  ```python
  def get_capture_node_capacity_plan(expected_traffic: float, azs: List[str]) -> CaptureNodesPlan:
  ```

### Custom Types & Type Aliases
- **Priority**: PREFERRED
- **Pattern**: Extensive use of TypeVar for generic type bounds on dataclasses
- **Examples**:
  ```python
  T_ClusterPlan = TypeVar('T_ClusterPlan', bound='ClusterPlan')

  @classmethod
  def from_dict(cls: Type[T_ClusterPlan], input: Dict[str, any]) -> T_ClusterPlan:
  ```

### Typing Module Constructs
- **Priority**: PREFERRED
- **Pattern**: Uses `Dict`, `List`, `Type`, `TypeVar`, `Callable`, `Any` from typing
- **Observation**: Prefers explicit imports from typing module rather than PEP 585 built-in generics
- **Examples**: `from typing import Dict, Any, Callable, Type`

### Runtime Type Checking
- **Priority**: PREFERRED
- **Pattern**: Manual type validation only in critical paths where there is real risk
- **Examples**:
  ```python
  def set_work_item(self, new_work_item: Any):
      if not isinstance(new_work_item, EntityReport):
          raise TypeError("new_work_item must be of type EntityReport")
  ```

### Pydantic for Schema Validation
- **Priority**: OBSERVED
- **Pattern**: Uses Pydantic BaseModel for LangChain tool schemas and structured inputs
- **Examples**:
  ```python
  class EntityInput(BaseModel):
      """A single entity extracted from the data entry"""
      value: str = Field(description="The raw value extracted from the input data...")
      description: str = Field(description="A precise explanation of what the value represents...")
  ```

---

## Documentation Philosophy

### When to Add Docstrings
- **Priority**: CRITICAL
- **Pattern**: Add docstrings when:
  - Function complexity is non-trivial (multiple steps, complex logic)
  - Part of a public API that other modules/developers will use
  - Behavior is non-obvious from the function name and signature
  - Function has important side effects or preconditions

- **Pattern**: Skip docstrings when:
  - Function name and type signature are self-documenting
  - Private helper functions with obvious behavior
  - Simple one-line functions or property getters/setters

**Decision Criteria Examples:**

```python
# NEEDS docstring: Complex, non-obvious behavior
def get_ecs_sys_resource_plan(instance_type: str) -> EcsSysResourcePlan:
    """
    Creates a capacity plan for the indicated instance type.
    instance_type: The instance type to plan for
    """

# NO docstring needed: Name and signature are self-documenting
def get_cluster_name(self) -> str:
    return self._cluster_name

# NEEDS docstring: Side effects and expectations
def call_shell_command(command: str, cwd: str = None, env: Dict[str, str] = None,
                       request_response_pairs: List[Tuple[str, str]] = []):
    """
    Execute a command in a child shell process.
    The user can optionally supply a list of request/response pairs to handle command invocations that expect
    a user response. For example:
        call_shell_command('my_shell_command', request_response_pairs=[('Do you really want to?', 'yes')])
    """
```

### Docstring Style
- **Priority**: PREFERRED
- **Pattern**: Simple triple-quoted explanatory comments, not structured docstrings (no Sphinx/Google/NumPy format)

### Comment Style
- **Priority**: CRITICAL
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
- **Priority**: CRITICAL
- **Pattern**: Inline comments explain magic numbers and why values are chosen
- **Examples**:
  ```python
  MINIMUM_TRAFFIC = 0.01 # Gbps; arbitrarily chosen, but will yield a minimal cluster
  CAPACITY_BUFFER_FACTOR = 1.25 # Arbitrarily chosen
  MASTER_NODE_COUNT = 3 # Recommended number in docs
  ```

### Prompt Engineering for LLMs
- **Priority**: OBSERVED
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
- **Priority**: PREFERRED
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
- **Priority**: PREFERRED
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

## Error Handling & Robustness

### Custom Exception Hierarchy
- **Priority**: PREFERRED
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
**Observation**: Custom exceptions are easy to define, make exception handling easier, and make stack traces/logs clearer

### Exception Naming
- **Priority**: CRITICAL
- **Pattern**: Descriptive, specific exception names that indicate the problem
- **Examples**: `TooMuchTraffic`, `NotEnoughStorage`, `InvalidCidr`, `FileNotGenerated`, `AssumeRoleNotSupported`, `RESTOperationFailedException`

### Logging Approach
- **Priority**: CRITICAL
- **Pattern**: Module-level logger instances; consistent use throughout
- **Examples**:
  ```python
  logger = logging.getLogger(__name__)
  ```

  ```python
  logger = logging.getLogger("backend")
  ```

### Custom Logging Formatter with UTC Timestamps
- **Priority**: OBSERVED
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
- **Priority**: PREFERRED
- **Pattern**: Strategic use of info, debug, warning, error levels
- **Examples**:
  ```python
  logger.info(f"Received heuristic creation request: {request.data}")
  logger.debug(f"Regex value:\n{result.regex.value}")
  logger.error(f"Regex creation failed: {str(e)}")
  logger.exception(e)  # Includes traceback
  ```

---

## Code Style & Idioms

### Naming Conventions

#### Variables & Functions
- **Priority**: CRITICAL
- **Pattern**: `snake_case` for variables and functions
- **Examples**: `expected_traffic`, `cluster_name`, `get_capture_node_capacity_plan`

#### Classes
- **Priority**: CRITICAL
- **Pattern**: `PascalCase` for classes
- **Examples**: `Expert`, `CaptureNodesPlan`, `AwsClientProvider`, `RESTPath`

#### Constants
- **Priority**: CRITICAL
- **Pattern**: `SCREAMING_SNAKE_CASE` for module-level constants
- **Examples**: `MAX_TRAFFIC`, `MINIMUM_TRAFFIC`, `DEFAULT_SPI_DAYS`, `DEFAULT_BOTO_CONFIG`

#### Private/Internal
- **Priority**: CRITICAL
- **Pattern**: Leading underscore for internal methods and variables
- **Examples**: `_aws_profile`, `_get_session()`, `_create_regex()`, `_validate()`

### Line Length
- **Priority**: PREFERRED
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
- **Priority**: CRITICAL
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
- **Priority**: PREFERRED
- **Pattern**: Prefer list comprehensions for simple transformations
- **Examples**:
  ```python
  [pattern.to_json() for pattern in result.patterns]
  ```

### F-Strings
- **Priority**: PREFERRED
- **Pattern**: Use of f-strings for string formatting
- **Examples**:
  ```python
  logger.info(f"Received heuristic creation request: {request.data}")
  logger.error(f"Invalid heuristic creation request: {request.errors}")
  ```

### Boolean Expressions for Control Flow
- **Priority**: PREFERRED
- **Pattern**: Break complex boolean logic into simpler expressions with clear variable names for intermediate results
- **Examples**:
  ```python
  one_component_specified = (capture or viewer) and not (capture and viewer)
  no_component_specified = not (capture or viewer)
  if config_version and (not one_component_specified):
      logger.error("If you specify a specific config version...")
  ```

### Conditional Assignment Patterns
- **Priority**: PREFERRED
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

## Dependencies & Tooling

### Standard Library vs Third-Party
- **Priority**: PREFERRED
- **Pattern**: Leverages stdlib heavily (logging, abc, dataclasses, typing), brings in third-party for specific needs
- **Third-party observed**: Django, DRF, Click, boto3, LangChain, requests

### AWS SDK (boto3) Usage
- **Priority**: OBSERVED
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
- **Priority**: OBSERVED
- **Pattern**: Uses Click for command-line interfaces
- **Examples**: Extensive use of `@click.command()`, `@click.option()`, `@click.group()`

---

## Design Patterns & Principles

### Dataclass Usage
- **Priority**: PREFERRED
- **Pattern**: Heavy use of `@dataclass` for data structures; prefer dataclasses over plain classes or dicts
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
**Observeration**: Dataclasses provide lightweight typing and reduce boilerplate

### Serialization Patterns
- **Priority**: PREFERRED
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
- **Priority**: PREFERRED
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
**Observation**: While we prefer composition over inheritance as a general rule, we use ABCs to create consistent method interfaces and share behavior when that makes sense

### Client/Provider Pattern
- **Priority**: OBSERVED
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
- **Priority**: PREFERRED
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
- **Priority**: PREFERRED
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

## Data Handling

### Data Structure Choices
- **Priority**: PREFERRED
- **Pattern**: Prefers dataclasses for structured data, dicts for JSON interop
- **Examples**: All data models are dataclasses (Entity, EntityMapping, CaptureNodesPlan, etc.)

### Serialization
- **Priority**: PREFERRED
- **Pattern**: `to_dict()` methods for serialization, `from_dict()` class methods for deserialization
- **Examples**: See Design Patterns section

### Dataclasses vs NamedTuples vs Pydantic
- **Priority**: PREFERRED
- **Pattern**: Uses `@dataclass` from stdlib for data models; Pydantic BaseModel for LangChain tool schemas only

### Nested Dataclass Deserialization
- **Priority**: PREFERRED
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
- **Priority**: OBSERVED
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
- **Priority**: PREFERRED
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
- **Priority**: PREFERRED
- **Pattern**: Dataclasses are mutable by default; avoid frozen=True except for critical code sections

---

## API Design

### Public vs Private Boundaries
- **Priority**: CRITICAL
- **Pattern**: Leading underscore (`_`) for private/internal methods
- **Examples**: `_create_regex()`, `_validate()`, `_get_session()`, `_perform_async_inference()`

### Parameter Patterns
- **Priority**: PREFERRED
- **Pattern**: Explicit parameters preferred; defaults for optional params; kwargs for flexible APIs
- **Examples**:
  ```python
  def __init__(self, aws_profile: str = "default", aws_region: str = None,
               aws_compute=False, assume_role_arn: str=None):
  ```

### Return Value Conventions
- **Priority**: CRITICAL
- **Pattern**: Returns typed objects (such as dataclasses); uses None for optional returns
- **Examples**: All functions have explicit return types in signatures

### Explicit Over Implicit
- **Priority**: CRITICAL
- **Pattern**: Explicit parameter passing, explicit imports (no `import *`)
- **Examples**: All imports are explicit; functions take explicit parameters

### Callback/Provider Function Parameters
- **Priority**: PREFERRED
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
- **Priority**: PREFERRED
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
- **Priority**: PREFERRED
- **Pattern**: Private helper functions prefixed with `_`, often defined at module level
- **Examples**: `_get_pattern_function_name()`, `_get_helper_code()`, `_get_transformer_wrapper_code()`, `_should_proceed_with_operation()`
- **Purpose**: Break down complex command functions into smaller, testable units

---

## Meta Patterns

### Module-Level Constants
- **Priority**: CRITICAL
- **Pattern**: Constants defined at module top, right after imports
- **Examples**:
  ```python
  MAX_TRAFFIC = 100 # Gbps, scaling limit of a single User Subnet VPC Endpoint
  MINIMUM_TRAFFIC = 0.01 # Gbps; arbitrarily chosen
  CAPACITY_BUFFER_FACTOR = 1.25 # Arbitrarily chosen
  ```

### Factory Functions
- **Priority**: PREFERRED
- **Pattern**: `get_*` prefix for factory/provider functions
- **Examples**: `get_regex_expert()`, `get_categorization_expert()`, `get_capture_node_capacity_plan()`, `get_ecs_sys_resource_plan()`

### Context Management
- **Priority**: PREFERRED
- **Pattern**: Uses context managers (with statements) appropriately
- **Examples**:
  ```python
  with tarfile.open(self._tarball_path, "w:gz") as tar:
      tar.add(self._source_dir_path, arcname=os.path.basename(self._source_dir_path))
  ```

### Equality Methods
- **Priority**: PREFERRED
- **Pattern**: Custom `__eq__` methods on dataclasses for semantic equality
- **Examples**:
  ```python
  def __eq__(self, other) -> bool:
      return (self.instanceType == other.instanceType and self.desiredCount == other.desiredCount
              and self.maxCount == other.maxCount and self.minCount == other.minCount)
  ```

### Interactive Shell Automation with pexpect
- **Priority**: OBSERVED
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
- **Priority**: PREFERRED
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
- **Priority**: PREFERRED
- **Pattern**: Custom `__str__` methods for human-readable output
- **Examples**:
  ```python
  def __str__(self):
      return json.dumps(self.to_dict())
  ```

---

## When to Deviate From This Guide

These patterns emerged from solving specific problems in specific contexts. Deviate when:

### Team/Project Conventions Differ
- If working in an established codebase with different conventions (e.g., Google-style docstrings, 88-char line length from Black), **follow the existing style** for consistency
- Propose style guide adoption only if the team is open to it

### Domain Requirements Differ
- **Performance-critical code**: Frozen dataclasses, specialized data structures, avoiding comprehensions in hot paths
- **Security-sensitive code**: More defensive programming, comprehensive input validation, audit logging
- **Public libraries**: More comprehensive docstrings, semantic versioning, deprecation warnings

### Better Engineering Solution Exists
**When to propose alternatives:**
- Clear performance or security improvements
- Significant reduction in complexity
- Better testability or maintainability
- Leveraging new language features (Python 3.10+ pattern matching, 3.9+ type hints)

**How to propose:**
- Explain the engineering trade-off clearly
- Reference the pattern you're deviating from
- Document why the deviation is justified

### Examples of Valid Deviations:

```python
# DEVIATION: Using frozen dataclass for immutability guarantee
# Reason: This config is shared across threads and must be immutable
@dataclass(frozen=True)
class ThreadSafeConfig:
    max_retries: int
    timeout: float

# DEVIATION: Using structured docstring format
# Reason: This is a public library; users need comprehensive API docs
def process_data(input: DataFrame, filters: List[str]) -> DataFrame:
    """
    Process input data with specified filters.

    Args:
        input: Input DataFrame to process
        filters: List of filter expressions in SQL WHERE clause format

    Returns:
        Filtered and processed DataFrame

    Raises:
        ValueError: If filters contain invalid SQL syntax
    """

# DEVIATION: Using PEP 585 built-in generics instead of typing module
# Reason: Python 3.9+ project, modern syntax is clearer
def merge_configs(configs: list[dict[str, Any]]) -> dict[str, Any]:
    # Note: Guide prefers typing.List and typing.Dict, but this is valid for 3.9+
```

The goal is **engineering judgment**, not blind pattern-matching.