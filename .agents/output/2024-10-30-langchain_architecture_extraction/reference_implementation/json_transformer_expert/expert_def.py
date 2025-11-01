"""
Expert factory functions for JSON Transformer.

Demonstrates the two-phase pattern with contrasting LLM configurations:
1. Mapping Expert: Creative analysis (temp=1, thinking enabled)
2. Transform Expert: Deterministic code generation (temp=0, thinking disabled)

TODO: Replace the LLM configuration with your actual provider setup.
      The pattern shown here is AWS Bedrock-specific but the concepts apply universally.
"""
import logging

from core.experts import Expert
from json_transformer_expert.tool_def import (
    get_mapping_tool_bundle,
    get_transform_tool_bundle
)
from json_transformer_expert.prompting.generation import (
    get_mapping_system_prompt_factory,
    get_transform_system_prompt_factory
)

# TODO: Import your LLM client
# from langchain_aws import ChatBedrockConverse  # AWS Bedrock
# from langchain_openai import ChatOpenAI        # OpenAI
# from langchain_anthropic import ChatAnthropic  # Anthropic direct


logger = logging.getLogger(__name__)


def get_mapping_expert() -> Expert:
    """
    Create Expert for mapping phase (creative analysis).

    LLM Configuration:
    - Temperature: 1 (creative, exploratory)
    - Extended thinking: Enabled (for complex reasoning)
    - Max tokens: High (detailed analysis)

    This configuration is suitable for:
    - Open-ended analysis tasks
    - Complex reasoning and exploration
    - Discovering relationships and patterns
    """
    logger.info("Building mapping expert")

    # Get tool bundle for mapping phase
    tool_bundle = get_mapping_tool_bundle()

    # TODO: Replace with your LLM configuration
    # Example for AWS Bedrock:
    # from langchain_aws import ChatBedrockConverse
    # from botocore.config import Config
    #
    # llm = ChatBedrockConverse(
    #     model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    #     temperature=1,  # Creative analysis
    #     max_tokens=30000,
    #     region_name="us-west-2",
    #     additional_model_request_fields={
    #         "thinking": {
    #             "type": "enabled",
    #             "budget_tokens": 30000
    #         }
    #     },
    #     config=Config(
    #         read_timeout=120,
    #         retries={'max_attempts': 20, 'mode': 'adaptive'}
    #     )
    # )
    #
    # # Bind tools to LLM (forces structured output)
    # llm_w_tools = llm.bind_tools(tool_bundle.to_list())
    #
    # return Expert(
    #     llm=llm_w_tools,
    #     system_prompt_factory=get_mapping_system_prompt_factory(),
    #     tools=tool_bundle
    # )

    raise NotImplementedError(
        "Replace this with your LLM configuration. "
        "See comments above for AWS Bedrock example."
    )


def get_transform_expert() -> Expert:
    """
    Create Expert for transform phase (deterministic code generation).

    LLM Configuration:
    - Temperature: 0 (deterministic, consistent)
    - Extended thinking: Disabled (straightforward task)
    - Max tokens: Moderate (code generation)

    This configuration is suitable for:
    - Code generation tasks
    - Deterministic transformations
    - Tasks where consistency is critical
    """
    logger.info("Building transform expert")

    # Get tool bundle for transform phase
    tool_bundle = get_transform_tool_bundle()

    # TODO: Replace with your LLM configuration
    # Example for AWS Bedrock:
    # from langchain_aws import ChatBedrockConverse
    # from botocore.config import Config
    #
    # llm = ChatBedrockConverse(
    #     model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    #     temperature=0,  # Deterministic code generation
    #     max_tokens=16000,
    #     region_name="us-west-2",
    #     additional_model_request_fields={
    #         "thinking": {
    #             "type": "disabled"  # Not needed for straightforward code generation
    #         }
    #     },
    #     config=Config(
    #         read_timeout=120,
    #         retries={'max_attempts': 20, 'mode': 'adaptive'}
    #     )
    # )
    #
    # # Bind tools to LLM (forces structured output)
    # llm_w_tools = llm.bind_tools(tool_bundle.to_list())
    #
    # return Expert(
    #     llm=llm_w_tools,
    #     system_prompt_factory=get_transform_system_prompt_factory(),
    #     tools=tool_bundle
    # )

    raise NotImplementedError(
        "Replace this with your LLM configuration. "
        "See comments above for AWS Bedrock example."
    )
