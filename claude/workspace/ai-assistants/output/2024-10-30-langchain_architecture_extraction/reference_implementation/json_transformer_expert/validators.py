"""
Validation for LLM-generated transform code.

PATTERN DEMONSTRATED: Multi-stage validation with ValidationReport

This file shows how to validate LLM-generated Python code through progressive stages:
1. Syntax validation (can Python parse it?)
2. Loading validation (does it define expected functions?)
3. Invocation validation (does it run without errors?)
4. Output validation (does output match expected structure?)

KEY CONCEPTS:
- ValidationReport accumulates results across stages
- Custom exceptions (PythonLogicInvalidSyntaxError, etc.) provide semantic clarity
- Each stage builds on previous stage (early exit on failure)
- report.append_entry() provides dual logging (logger + report entries)
- Use ModuleType to create isolated namespace for exec()

WHEN TO USE THIS PATTERN:
- Validating LLM-generated code (Python, SQL, regex, etc.)
- Multi-stage validation where later stages depend on earlier stages
- Need structured validation reports for debugging or user feedback
- Want to distinguish between different failure modes (syntax vs logic vs runtime)

DESIGN CHOICE: Why custom exceptions?
- Semantic clarity: "PythonLogicNotInModuleError" vs generic "ValueError"
- Enables precise error handling downstream
- Self-documenting: exception name explains what went wrong
"""
import logging
from types import ModuleType
from typing import Dict, Any

from core.validation_report import ValidationReport
from json_transformer_expert.models import TransformCode


logger = logging.getLogger(__name__)


# ============================================================================
# CUSTOM EXCEPTIONS FOR PYTHON CODE VALIDATION
# ============================================================================

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


class TransformCodeValidator:
    """
    Validates LLM-generated Python transformation code.

    Demonstrates the multi-stage validation pattern used throughout the architecture.
    """

    def __init__(self, source_json: str, transform_code: TransformCode):
        self.source_json = source_json
        self.transform_code = transform_code

    def validate(self) -> ValidationReport:
        """
        Run full validation pipeline.

        Returns:
            ValidationReport with passed=True if all stages succeed, False otherwise
        """
        report = ValidationReport(
            input=self.source_json,
            output={},
            report_entries=[],
            passed=False
        )

        try:
            # Stage 1: Syntax validation
            transform_func = self._validate_syntax(report)

            # Stage 2: Invocation validation
            output = self._validate_invocation(transform_func, report)

            # Stage 3: Output validation
            self._validate_output(output, report)

            # If we made it here, all stages passed
            report.passed = True
            report.append_entry("✓ Validation complete - all stages passed", logger.info)

        except Exception as e:
            report.passed = False
            report.append_entry(f"✗ Validation failed: {str(e)}", logger.error)

        return report

    def _validate_syntax(self, report: ValidationReport):
        """
        Stage 1: Validate Python syntax and load the module.

        Raises:
            PythonLogicInvalidSyntaxError: If code has syntax errors
            PythonLogicNotInModuleError: If 'transform' function is missing
            PythonLogicNotExecutableError: If 'transform' is not callable
        """
        report.append_entry("Stage 1: Validating syntax...", logger.info)

        # Create isolated module namespace
        transform_module = ModuleType("transform")

        # Execute code in module namespace
        try:
            full_code = f"{self.transform_code.dependency_setup}\n\n{self.transform_code.transform_logic}"
            exec(full_code, transform_module.__dict__)
        except SyntaxError as e:
            raise PythonLogicInvalidSyntaxError(f"Syntax error: {str(e)}")

        report.append_entry("  ✓ Code is syntactically valid", logger.info)

        # Validate module structure
        if not hasattr(transform_module, "transform"):
            raise PythonLogicNotInModuleError("Missing 'transform' function")

        if not callable(transform_module.transform):
            raise PythonLogicNotExecutableError("'transform' must be callable")

        report.append_entry("  ✓ Module structure valid (transform function exists)", logger.info)

        return transform_module.transform

    def _validate_invocation(self, transform_func, report: ValidationReport) -> Dict[str, Any]:
        """
        Stage 2: Invoke the transform function with source JSON.

        Raises:
            Exception: If transform function raises any error
        """
        report.append_entry("Stage 2: Invoking transform function...", logger.info)

        try:
            output = transform_func(self.source_json)
            report.append_entry(f"  ✓ Function executed without errors", logger.info)
            return output
        except Exception as e:
            report.append_entry(f"  ✗ Function raised exception: {str(e)}", logger.error)
            raise

    def _validate_output(self, output: Any, report: ValidationReport):
        """
        Stage 3: Validate the output structure.

        Basic validation: Check that output is a dict.
        In production, you'd validate against target schema here.
        """
        report.append_entry("Stage 3: Validating output structure...", logger.info)

        if not isinstance(output, dict):
            raise ValueError(f"Output must be dict, got {type(output).__name__}")

        report.append_entry(f"  ✓ Output is dict with {len(output)} keys", logger.info)

        # TODO: In production, add recursive schema validation here
        # (See reference_implementation patterns for recursive validation pattern)

        report.output = output
