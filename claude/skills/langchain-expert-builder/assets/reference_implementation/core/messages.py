"""
Message type abstractions for LLM interactions.

PATTERN DEMONSTRATED: Framework Independence via Message Abstraction Layer

This module provides framework-agnostic message types to avoid direct dependencies on
LangChain's message classes throughout domain code. This allows easy switching between
different LLM providers or frameworks.

KEY CONCEPTS:
- Domain code uses our message types (SystemMessage, HumanMessage, AIMessage, ToolMessage)
- Conversion to/from LangChain messages happens only at boundaries (when calling LLM)
- Framework-specific types (LangChain, LiteLLM, etc.) are isolated to conversion functions

WHEN TO USE THIS PATTERN:
- Building expert systems that may need to switch LLM providers
- Creating reusable components across multiple projects with different LLM frameworks
- Wanting clean domain types without framework leakage
- Need to serialize conversation history independent of LLM provider

WHEN NOT TO USE:
- Simple scripts with single LLM provider that won't change
- Prototyping where framework independence isn't a concern
- Projects deeply integrated with LangChain-specific features

DESIGN CHOICE: Simple dataclasses over framework types
- Rationale: Enables framework portability, clean serialization, type safety
- Trade-off: Requires conversion at boundaries (minimal overhead)
- Alternative: Use LangChain types directly (couples domain code to framework)
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

# Import LangChain types only for conversion functions
import langchain_core.messages as lc_messages


class MessageRole(Enum):
    """Role of the message in the conversation."""
    SYSTEM = "system"
    HUMAN = "human"
    AI = "ai"
    TOOL = "tool"


@dataclass
class BaseMessage:
    """
    Base class for all message types.

    Framework-agnostic representation of conversation messages.
    Subclasses implement to_langchain() for boundary conversion.
    """
    content: str
    role: MessageRole

    def to_langchain(self) -> lc_messages.BaseMessage:
        """Convert to LangChain message format for LLM invocation."""
        raise NotImplementedError("Subclasses must implement to_langchain()")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization/logging."""
        return {
            "role": self.role.value,
            "content": self.content
        }


@dataclass
class SystemMessage(BaseMessage):
    """System message providing instructions or context to the LLM."""

    def __init__(self, content: str):
        super().__init__(content=content, role=MessageRole.SYSTEM)

    def to_langchain(self) -> lc_messages.SystemMessage:
        """Convert to LangChain SystemMessage."""
        return lc_messages.SystemMessage(content=self.content)


@dataclass
class HumanMessage(BaseMessage):
    """Human/user message in the conversation."""

    def __init__(self, content: str):
        super().__init__(content=content, role=MessageRole.HUMAN)

    def to_langchain(self) -> lc_messages.HumanMessage:
        """Convert to LangChain HumanMessage."""
        return lc_messages.HumanMessage(content=self.content)


@dataclass
class AIMessage(BaseMessage):
    """
    AI/assistant message in the conversation.

    Optionally includes tool_calls when LLM invokes structured tools.
    """
    tool_calls: Optional[List[Dict[str, Any]]] = None

    def __init__(self, content: str, tool_calls: Optional[List[Dict[str, Any]]] = None):
        super().__init__(content=content, role=MessageRole.AI)
        self.tool_calls = tool_calls

    def to_langchain(self) -> lc_messages.AIMessage:
        """Convert to LangChain AIMessage."""
        return lc_messages.AIMessage(
            content=self.content,
            tool_calls=self.tool_calls or []
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization/logging."""
        result = super().to_dict()
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        return result


@dataclass
class ToolMessage(BaseMessage):
    """
    Tool execution result message.

    Sent back to LLM after a tool call to provide execution results.
    """
    tool_call_id: str
    name: str

    def __init__(self, content: str, tool_call_id: str, name: str):
        super().__init__(content=content, role=MessageRole.TOOL)
        self.tool_call_id = tool_call_id
        self.name = name

    def to_langchain(self) -> lc_messages.ToolMessage:
        """Convert to LangChain ToolMessage."""
        return lc_messages.ToolMessage(
            content=self.content,
            tool_call_id=self.tool_call_id,
            name=self.name
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization/logging."""
        result = super().to_dict()
        result["tool_call_id"] = self.tool_call_id
        result["name"] = self.name
        return result


# Conversion utilities for boundary crossing

def from_langchain(lc_msg: lc_messages.BaseMessage) -> BaseMessage:
    """
    Convert a LangChain message to our framework-agnostic message type.

    USAGE: Call this when receiving responses from LLM to convert back to domain types.

    Args:
        lc_msg: LangChain message to convert

    Returns:
        Our framework-agnostic message type

    Raises:
        ValueError: If message type is not recognized
    """
    if isinstance(lc_msg, lc_messages.SystemMessage):
        return SystemMessage(content=lc_msg.content)
    elif isinstance(lc_msg, lc_messages.HumanMessage):
        return HumanMessage(content=lc_msg.content)
    elif isinstance(lc_msg, lc_messages.AIMessage):
        tool_calls = None
        if hasattr(lc_msg, 'tool_calls') and lc_msg.tool_calls:
            tool_calls = lc_msg.tool_calls
        return AIMessage(content=lc_msg.content, tool_calls=tool_calls)
    elif isinstance(lc_msg, lc_messages.ToolMessage):
        return ToolMessage(
            content=lc_msg.content,
            tool_call_id=lc_msg.tool_call_id,
            name=lc_msg.name
        )
    else:
        raise ValueError(f"Unsupported LangChain message type: {type(lc_msg)}")


def to_langchain_messages(messages: List[BaseMessage]) -> List[lc_messages.BaseMessage]:
    """
    Convert a list of our messages to LangChain messages.

    USAGE: Call this before invoking LLM with conversation context.

    Args:
        messages: List of our framework-agnostic message types

    Returns:
        List of LangChain messages ready for LLM invocation
    """
    return [msg.to_langchain() for msg in messages]


def from_langchain_messages(lc_messages_list: List[lc_messages.BaseMessage]) -> List[BaseMessage]:
    """
    Convert a list of LangChain messages to our message types.

    Args:
        lc_messages_list: List of LangChain messages

    Returns:
        List of our framework-agnostic message types
    """
    return [from_langchain(msg) for msg in lc_messages_list]
