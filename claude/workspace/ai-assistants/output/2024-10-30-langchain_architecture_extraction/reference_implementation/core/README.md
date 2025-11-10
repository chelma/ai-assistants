# Core Abstractions

This directory contains the reusable foundation for LangChain-based multi-expert systems.

## Files

- **`experts.py`**: Expert dataclass + invoke_expert() orchestration
- **`tasks.py`**: Task abstract base class for work items
- **`tools.py`**: ToolBundle for wrapping LangChain StructuredTools
- **`inference.py`**: Async batch inference with synchronous wrapper
- **`validation_report.py`**: ValidationReport for accumulating validation results

## Usage

Copy this entire `core/` directory to your project. These files are framework-agnostic and ready to run with any LangChain-compatible LLM provider.

See `../json_transformer_expert/` for a complete example of how to build concrete Experts, Tasks, and Tools using these abstractions.

**Note on validation exceptions:** Domain-specific validation exceptions should be defined in your expert's `validators.py` module. See `json_transformer_expert/validators.py` for an example of custom exceptions for Python code validation.
