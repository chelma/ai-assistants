"""
Custom exceptions for validation errors.

These exceptions provide semantic clarity for different failure modes
when validating LLM-generated code or structured output.
"""


class PythonLogicInvalidSyntaxError(Exception):
    """
    Raised when LLM-generated Python code has syntax errors.

    Example:
        exec(llm_code)  # SyntaxError
        → raise PythonLogicInvalidSyntaxError("Syntax error: invalid syntax on line 5")
    """
    pass


class PythonLogicNotInModuleError(Exception):
    """
    Raised when expected function/class is missing from LLM-generated module.

    Example:
        module = load_code(llm_code)
        if not hasattr(module, 'transform'):
            raise PythonLogicNotInModuleError("Missing 'transform' function")
    """
    pass


class PythonLogicNotExecutableError(Exception):
    """
    Raised when expected function exists but is not callable.

    Example:
        if not callable(module.transform):
            raise PythonLogicNotExecutableError("'transform' must be callable")
    """
    pass
