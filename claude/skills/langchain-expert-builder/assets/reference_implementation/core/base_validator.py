"""
Base validator infrastructure for expert validation.

PATTERN DEMONSTRATED: Dependency-Injected Validation

This module provides an abstract base class for validators that can be dependency-injected
into expert classes, enabling independent testing and cleaner separation of concerns.

KEY CONCEPTS:
- Validators are pure functions: take result + task context, return ValidationReport
- Validators are optional: Experts can have validation or not (property returns None)
- Validators are testable in isolation: No need to invoke LLM to test validation logic
- Validators are composable: Could chain validators or create conditional validators

WHEN TO USE THIS PATTERN:
- Expert outputs need domain-specific validation beyond Pydantic schema validation
- Validation logic is complex enough to warrant separate testing
- Want to enable validation retry loops (LLM self-correction)
- Different experts need different validation rules

WHEN NOT TO USE:
- Simple experts where Pydantic schema validation is sufficient
- Validation logic is trivial (2-3 line checks)
- Prototyping where separation of concerns adds unnecessary complexity

DESIGN CHOICE: Abstract base class with dependency injection
- Rationale: Enables optional validation, testability, clear interface contract
- Trade-off: Slightly more setup (create validator class) vs inline validation
- Alternative: Validation logic embedded in expert invoke() (harder to test, less flexible)

TYPICAL USAGE PATTERN:

    # 1. Define domain-specific validator
    class MyValidator(BaseValidator):
        def validate(self, result: MyResult, task: MyTask) -> ValidationReport:
            report = ValidationReport(...)
            # Perform validation checks
            if some_check_fails:
                report.passed = False
                report.report_entries.append("Error details")
            return report

    # 2. Expert declares validator via property
    class MyExpert(BaseExpert):
        @property
        def validator(self) -> Optional[BaseValidator]:
            return MyValidator()  # or None for no validation

    # 3. Base expert invokes validator automatically during invoke()
    # (No additional code needed - validation happens in base invoke() method)
"""

from typing import TypeVar
from core.validation_report import ValidationReport

# Type variables for generic task and result types
TaskType = TypeVar('TaskType')
ResultType = TypeVar('ResultType')


class BaseValidator:
    """
    Abstract base validator that can be injected into expert classes.

    Validators are responsible ONLY for validation - they should NOT have side effects
    like modifying tasks, logging (beyond what ValidationReport handles), or making
    external calls.

    Validators should be pure functions that:
    1. Accept result and task as inputs
    2. Perform validation checks
    3. Return ValidationReport with detailed findings
    4. NOT modify inputs or cause side effects

    This purity enables:
    - Independent testing (no mocks needed for LLM, logging, etc.)
    - Easy composition (chain validators, conditional validators)
    - Clear separation of concerns (validation vs orchestration)
    """

    def validate(self, result: ResultType, task: TaskType) -> ValidationReport:
        """
        Validate the result without modifying the task.

        This method should:
        1. Perform any necessary validation checks on the result
        2. Use task as read-only context (e.g., checking result references valid task data)
        3. Return a ValidationReport with validation results
        4. NOT modify the task or result (pure function)

        Args:
            result: The result from LLM tool execution to validate
            task: The task object (read-only, used for validation context like available IDs)

        Returns:
            ValidationReport with validation results and detailed error messages.
            If report.passed is True, validation succeeded.
            If report.passed is False, report.report_entries contains error messages
            that can be fed back to LLM for self-correction in retry loops.

        Example implementation:

            def validate(self, result: CodeGenResult, task: CodeGenTask) -> ValidationReport:
                report = ValidationReport(
                    input=task.to_json(),
                    output={},
                    report_entries=[],
                    passed=True
                )

                # Syntax validation
                try:
                    compile(result.generated_code, '<string>', 'exec')
                except SyntaxError as e:
                    report.passed = False
                    report.report_entries.append(f"Syntax error: {e}")

                # Semantic validation
                if result.function_name not in result.generated_code:
                    report.passed = False
                    report.report_entries.append(
                        f"Generated code must define function '{result.function_name}'"
                    )

                return report
        """
        raise NotImplementedError("Subclasses must implement validate()")
