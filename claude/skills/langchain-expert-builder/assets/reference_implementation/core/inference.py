"""
Inference orchestration for LangChain-based multi-expert systems.

Provides async batch inference infrastructure with synchronous wrapper.
"""
import asyncio
from dataclasses import dataclass
import logging
from typing import List

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import BaseMessage
from langchain_core.runnables import Runnable


logger = logging.getLogger(__name__)


@dataclass
class InferenceRequest:
    """
    Input to the inference engine.

    Attributes:
        task_id: Unique identifier for the task
        context: List of LangChain messages (conversation history)
    """
    task_id: str
    context: List[BaseMessage]

    def to_json(self) -> dict:
        """Serialize for logging/debugging."""
        return {
            "task_id": self.task_id,
            "context": [turn.to_json() for turn in self.context]
        }


@dataclass
class InferenceResult:
    """
    Output from the inference engine.

    Attributes:
        task_id: Unique identifier for the task
        response: LLM's response (typically AIMessage with tool_calls)
    """
    task_id: str
    response: BaseMessage

    def to_json(self) -> dict:
        """Serialize for logging/debugging."""
        return {
            "task_id": self.task_id,
            "response": self.response.to_json()
        }


def perform_inference(
    llm: Runnable[LanguageModelInput, BaseMessage],
    batched_tasks: List[InferenceRequest]
) -> List[InferenceResult]:
    """
    Perform LLM inference on a batch of tasks (synchronous wrapper).

    Args:
        llm: LangChain Runnable (LLM client, typically with tools bound)
        batched_tasks: List of inference requests to process

    Returns:
        List of inference results (same order as input)

    Note: This wraps async inference in asyncio.run() for easier synchronous usage.
    Current usage: invoke_expert() passes single-task batches.
    Future scaling: Can batch multiple tasks for parallel inference.
    """
    return asyncio.run(_perform_async_inference(llm, batched_tasks))


async def _perform_async_inference(
    llm: Runnable[LanguageModelInput, BaseMessage],
    batched_tasks: List[InferenceRequest]
) -> List[InferenceResult]:
    """
    Perform async batch inference with parallel execution.

    Uses asyncio.gather() to run all inference calls concurrently.
    This provides throughput benefits when processing multiple tasks.

    Implementation note:
    Ideally, we'd use provider-native batch APIs (e.g., Bedrock's batch inference),
    but those often use async patterns (S3 results, polling) not directly supported
    by LangChain wrappers. This approach uses parallel ainvoke() as a middle ground.

    Args:
        llm: LangChain Runnable (LLM client)
        batched_tasks: List of inference requests

    Returns:
        List of inference results matching input order
    """
    # Create async invocation for each task
    async_responses = [llm.ainvoke(task.context) for task in batched_tasks]

    # Execute all invocations in parallel
    responses = await asyncio.gather(*async_responses)

    # Package results
    return [
        InferenceResult(task_id=task.task_id, response=response)
        for task, response in zip(batched_tasks, responses)
    ]
