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

    DESIGN PHILOSOPHY:

    The narrow-scope philosophy (each expert has one specialized task) typically means
    one tool per expert. However, multi-tool experts are appropriate when a single
    specialized prompt could produce different but closely related outputs.

    WHEN TO USE MULTIPLE TOOLS:
    - Validation-aware generation: generate_code vs revise_code (with validation feedback)
    - Confidence-based results: high_confidence_result vs low_confidence_result
    - Retry strategies: submit_solution vs request_clarification

    WHEN NOT TO USE MULTIPLE TOOLS:
    - Fundamentally different tasks (create separate experts instead)
    - Different prompts required (violates narrow-scope principle)
    - Different LLM configs needed (temp=0 vs temp=1 → separate experts)

    See langchain_guide.md "Multi-Tool Experts" section for detailed guidance.

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
