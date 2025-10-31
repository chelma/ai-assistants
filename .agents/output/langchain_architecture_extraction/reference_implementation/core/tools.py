"""
Tool bundling abstraction for LangChain-based multi-expert systems.

A ToolBundle wraps one or more LangChain StructuredTools that an Expert can use.
"""
from dataclasses import dataclass
import logging
from typing import List

from langchain_core.tools import StructuredTool


logger = logging.getLogger(__name__)


@dataclass
class ToolBundle:
    """
    A bundle of tools available to an Expert.

    Current pattern: One tool per Expert (one task = one tool call)
    The to_list() method provides consistent interface for LLM.bind_tools()

    Attributes:
        task_tool: The primary StructuredTool for this Expert's task

    Future extension: Add more tools per Expert by adding fields:
        task_tool: StructuredTool
        helper_tools: List[StructuredTool] = field(default_factory=list)

        def to_list(self):
            return [self.task_tool] + self.helper_tools
    """
    task_tool: StructuredTool

    def to_list(self) -> List[StructuredTool]:
        """
        Convert ToolBundle to list of StructuredTools for bind_tools().

        Returns:
            List containing the task_tool (can be extended to include more tools)
        """
        return [self.task_tool]
