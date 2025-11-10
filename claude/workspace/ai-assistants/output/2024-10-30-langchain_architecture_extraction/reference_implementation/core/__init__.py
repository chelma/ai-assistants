"""
Core abstractions for LangChain-based multi-expert systems.

This package provides the foundational abstractions:
- Expert: LLM + prompt factory + tools
- Task: Work item + conversation context
- ToolBundle: Structured output tools
- Inference: Async batch inference
- ValidationReport: Validation result accumulation
"""

from core.experts import Expert, ExpertInvocationError, invoke_expert
from core.tasks import Task
from core.tools import ToolBundle
from core.inference import InferenceRequest, InferenceResult, perform_inference
from core.validation_report import ValidationReport

__all__ = [
    # Expert abstractions
    "Expert",
    "ExpertInvocationError",
    "invoke_expert",
    # Task abstractions
    "Task",
    # Tool abstractions
    "ToolBundle",
    # Inference
    "InferenceRequest",
    "InferenceResult",
    "perform_inference",
    # Validation
    "ValidationReport",
]
