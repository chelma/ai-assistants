"""
Domain models for JSON Transformer Expert.

PATTERN DEMONSTRATED: Domain dataclasses as work items

These dataclasses represent the work items produced by each expert phase:
- FieldMapping: Single field mapping (source path → target path + rationale)
- MappingReport: Collection of mappings + analysis (output of mapping phase)
- TransformCode: Python code with imports + logic (output of transform phase)

KEY CONCEPTS:
- All models are dataclasses with type hints (no BaseModel/Pydantic here)
- Every model has to_json() for serialization
- Models are pure data containers (no business logic)
- Separate from Pydantic schemas used in tools (conversion happens in tool functions)

DESIGN CHOICE: Domain models vs Pydantic models
- Domain models (dataclasses): Internal representation, easy to work with
- Pydantic models (in tool_def.py): LLM interface, validation schema
- Tool functions bridge the gap by converting Pydantic → dataclass
"""
from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass
class FieldMapping:
    """
    A mapping between source JSON field and target schema field.

    Attributes:
        source_path: Dot-delimited path in source JSON (e.g., "user.email")
        target_path: Dot-delimited path in target schema (e.g., "contact.email_address")
        rationale: Explanation of why this mapping makes sense
    """
    source_path: str
    target_path: str
    rationale: str

    def to_json(self) -> Dict[str, str]:
        return {
            "source_path": self.source_path,
            "target_path": self.target_path,
            "rationale": self.rationale
        }


@dataclass
class MappingReport:
    """
    Result of the mapping phase: identified field mappings between source and target.

    Attributes:
        mappings: List of identified field mappings
        data_type_analysis: Brief description of the source data type
    """
    mappings: List[FieldMapping]
    data_type_analysis: str

    def to_json(self) -> Dict[str, Any]:
        return {
            "mappings": [m.to_json() for m in self.mappings],
            "data_type_analysis": self.data_type_analysis
        }


@dataclass
class TransformCode:
    """
    Result of the transform phase: Python code to perform the transformation.

    Attributes:
        dependency_setup: Import statements and helper functions
        transform_logic: Main transform() function that converts source to target
        rationale: Explanation of the transformation approach
    """
    dependency_setup: str
    transform_logic: str
    rationale: str

    def to_json(self) -> Dict[str, str]:
        return {
            "dependency_setup": self.dependency_setup,
            "transform_logic": self.transform_logic,
            "rationale": self.rationale
        }
