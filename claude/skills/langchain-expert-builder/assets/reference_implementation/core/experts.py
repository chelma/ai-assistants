"""
Core Expert abstraction for LangChain-based multi-expert systems.

An Expert encapsulates:
- An LLM client (with tools bound)
- A system prompt factory (generates prompts dynamically)
- A tool bundle (structured output schema)

This module is framework-agnostic and can be used with any LangChain-compatible LLM provider.
"""
from dataclasses import dataclass
import json
import logging
from typing import Any, Callable, Dict

from botocore.config import Config
from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage
from langchain_core.runnables import Runnable

from core.tools import ToolBundle
from core.tasks import Task
from core.inference import perform_inference


logger = logging.getLogger(__name__)

# AWS Bedrock-specific: Boto config for resilience to throttling and long inference times
# Adjust or remove this if using a different LLM provider
DEFAULT_BOTO_CONFIG = Config(
    read_timeout=120,  # Wait 2 minutes for a response from the LLM
    retries={
        'max_attempts': 20,  # Retry up to 20 times
        'mode': 'adaptive'   # Use adaptive retry strategy for better throttling handling
    }
)


@dataclass
class Expert:
    """
    An Expert represents a complete LLM inference capability.

    Attributes:
        llm: LangChain Runnable (typically an LLM with tools bound via bind_tools())
        system_prompt_factory: Function that generates SystemMessage based on task input
        tools: ToolBundle containing the structured output tool(s)
    """
    llm: Runnable[LanguageModelInput, BaseMessage]
    system_prompt_factory: Callable[[Dict[str, Any]], SystemMessage]
    tools: ToolBundle


class ExpertInvocationError(Exception):
    """Raised when LLM fails to produce expected tool call during expert invocation."""
    pass


def invoke_expert(expert: Expert, task: Task) -> Task:
    """
    Invoke an Expert on a Task, updating the Task with the LLM's structured output.

    This function orchestrates the full Expert invocation lifecycle:
    1. Convert Task to InferenceRequest (wraps conversation context)
    2. Perform LLM inference (async batch-ready)
    3. Validate that LLM produced a tool call
    4. Execute the tool with LLM's arguments
    5. Update Task with work item result
    6. Append AIMessage and ToolMessage to Task context

    Args:
        expert: The Expert to invoke
        task: The Task to perform (will be mutated)

    Returns:
        The updated Task (same object, mutated)

    Raises:
        ExpertInvocationError: If LLM doesn't produce a tool call
    """
    logger.debug(f"Initial Task: {json.dumps(task.to_json(), indent=4)}")

    # Step 1: Convert task to inference request
    inference_task = task.to_inference_task()

    # Step 2: Perform inference (forces tool call via bind_tools())
    inference_result = perform_inference(expert.llm, [inference_task])[0]
    logger.debug(f"Inference Result: {json.dumps(inference_result.to_json(), indent=4)}")

    # Step 3: Validate tool call exists
    if not isinstance(inference_result.response, AIMessage) or not inference_result.response.tool_calls:
        raise ExpertInvocationError(
            f"The LLM did not create a tool call for the task. "
            f"Final LLM message: {inference_result.response.content}"
        )

    # Step 4: Append LLM response to context
    task.context.append(inference_result.response)

    # Step 5: Execute tool with LLM arguments
    # Use last tool call if LLM produced multiple (allows for "thinking" tool calls)
    tool_call = inference_result.response.tool_calls[-1]
    result = expert.tools.task_tool(tool_call["args"])
    task.set_work_item(result)

    # Step 6: Append tool execution to context
    task.context.append(
        ToolMessage(
            name=task.get_tool_name(),
            content="Executed the expert task",
            tool_call_id=tool_call["id"]
        )
    )

    logger.debug(f"Updated Task: {json.dumps(task.to_json(), indent=4)}")

    return task
