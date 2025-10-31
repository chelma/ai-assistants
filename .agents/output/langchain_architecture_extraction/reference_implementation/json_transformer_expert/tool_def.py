"""
Tool definitions for JSON Transformer Expert.

Defines the Pydantic schemas and StructuredTools for each phase:
1. CreateMappingReport: Mapping phase tool
2. GenerateTransformCode: Transform phase tool
"""
from typing import List
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

from core.tools import ToolBundle
from json_transformer_expert.models import FieldMapping, MappingReport, TransformCode


# ============================================================================
# MAPPING PHASE TOOL
# ============================================================================

class FieldMappingInput(BaseModel):
    """Pydantic schema for a single field mapping."""
    source_path: str = Field(
        description="Dot-delimited path in the source JSON (e.g., 'user.email'). "
                    "Must be an exact path that exists in the source data."
    )
    target_path: str = Field(
        description="Dot-delimited path in the target schema (e.g., 'contact.email_address'). "
                    "Must match a field defined in the target schema."
    )
    rationale: str = Field(
        description="A clear explanation of why this mapping makes sense. "
                    "Explain the semantic relationship between source and target fields."
    )


class CreateMappingReport(BaseModel):
    """Create a report of field mappings between source JSON and target schema."""
    mappings: List[FieldMappingInput] = Field(
        description="List of identified field mappings. Include ALL fields that can be "
                    "meaningfully mapped from source to target."
    )
    data_type_analysis: str = Field(
        description="Brief analysis of the source data type and structure. "
                    "What kind of data is this? (e.g., 'User login event', 'E-commerce transaction')"
    )


def create_mapping_report(
    mappings: List[FieldMappingInput],
    data_type_analysis: str
) -> MappingReport:
    """
    Tool function: Create MappingReport from LLM arguments.

    Converts Pydantic input models to domain dataclasses.
    """
    return MappingReport(
        mappings=[
            FieldMapping(
                source_path=m.source_path,
                target_path=m.target_path,
                rationale=m.rationale
            )
            for m in mappings
        ],
        data_type_analysis=data_type_analysis
    )


# Create the LangChain StructuredTool
create_mapping_report_tool = StructuredTool.from_function(
    func=create_mapping_report,
    name="CreateMappingReport",
    args_schema=CreateMappingReport
)


# ============================================================================
# TRANSFORM PHASE TOOL
# ============================================================================

class GenerateTransformCode(BaseModel):
    """Generate Python code to transform source JSON to target schema format."""
    dependency_setup: str = Field(
        description="Import statements and helper functions needed for the transformation. "
                    "Example: 'import json\\nfrom datetime import datetime'. "
                    "Keep imports minimal - only include what's actually needed."
    )
    transform_logic: str = Field(
        description="Complete Python code defining a 'transform(source_json_str: str) -> dict' function. "
                    "This function must: "
                    "(1) Parse the source JSON string, "
                    "(2) Extract values according to the identified mappings, "
                    "(3) Return a dict matching the target schema structure. "
                    "The code must be syntactically valid and executable."
    )
    rationale: str = Field(
        description="Explanation of the transformation approach. "
                    "Describe any data type conversions, format changes, or special handling."
    )


def generate_transform_code(
    dependency_setup: str,
    transform_logic: str,
    rationale: str
) -> TransformCode:
    """
    Tool function: Create TransformCode from LLM arguments.

    Converts Pydantic input to domain dataclass.
    """
    return TransformCode(
        dependency_setup=dependency_setup,
        transform_logic=transform_logic,
        rationale=rationale
    )


# Create the LangChain StructuredTool
generate_transform_code_tool = StructuredTool.from_function(
    func=generate_transform_code,
    name="GenerateTransformCode",
    args_schema=GenerateTransformCode
)


# ============================================================================
# TOOL BUNDLES
# ============================================================================

def get_mapping_tool_bundle() -> ToolBundle:
    """Get ToolBundle for mapping phase."""
    return ToolBundle(task_tool=create_mapping_report_tool)


def get_transform_tool_bundle() -> ToolBundle:
    """Get ToolBundle for transform phase."""
    return ToolBundle(task_tool=generate_transform_code_tool)
