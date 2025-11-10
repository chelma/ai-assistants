"""
Core Task abstraction for LangChain-based multi-expert systems.

A Task encapsulates:
- Work to be performed (input data + work item result)
- Conversation context (LangChain message history)
- Lifecycle methods (get/set work item, serialization)

Tasks are the primary unit of work passed to Experts.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging
from typing import Any, Dict, List

from langchain_core.messages import BaseMessage
from core.inference import InferenceRequest


logger = logging.getLogger(__name__)


@dataclass
class Task(ABC):
    """
    Abstract base class for all Tasks in a multi-expert system.

    A Task represents a unit of work to be performed by an Expert. It manages:
    - Input data (defined by concrete subclasses)
    - Work item (result of Expert invocation)
    - Conversation context (accumulated LangChain messages)

    Concrete Task subclasses must implement:
    - get_work_item() / set_work_item(): Access/update the result
    - get_tool_name(): Name of the tool that produces the work item
    - to_json(): Serialize task state for logging/debugging

    Attributes:
        task_id: Unique identifier for this task instance
        context: List of LangChain messages (SystemMessage, AIMessage, ToolMessage)
                 Accumulates across multiple expert invocations for multi-turn conversations
    """
    task_id: str
    context: List[BaseMessage]

    @abstractmethod
    def get_work_item(self) -> Any:
        """
        Get the work item (result) produced by Expert invocation.

        Returns:
            The work item (typically a dataclass or Pydantic model)
            None if Expert hasn't been invoked yet
        """
        pass

    @abstractmethod
    def set_work_item(self, new_work_item: Any):
        """
        Set the work item (result) after Expert invocation.

        Args:
            new_work_item: The result produced by the Expert's tool

        Raises:
            TypeError: If new_work_item doesn't match expected type
        """
        pass

    @abstractmethod
    def get_tool_name(self) -> str:
        """
        Get the name of the LangChain StructuredTool that produces this Task's work item.

        Returns:
            Tool name (must match the tool name in the Expert's ToolBundle)
        """
        pass

    @abstractmethod
    def to_json(self) -> Dict[str, Any]:
        """
        Serialize Task to JSON for logging, debugging, or persistence.

        Returns:
            Dictionary representation of Task state
        """
        pass

    def to_inference_task(self) -> InferenceRequest:
        """
        Convert Task to InferenceRequest for LLM invocation.

        This method wraps the Task's conversation context into an InferenceRequest,
        which is the input to the inference engine.

        Returns:
            InferenceRequest containing task_id and context
        """
        return InferenceRequest(
            task_id=self.task_id,
            context=self.context
        )
