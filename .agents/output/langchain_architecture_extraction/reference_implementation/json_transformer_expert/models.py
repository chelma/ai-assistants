"""
Domain models for JSON Transformer Expert.

These dataclasses represent the work items produced by each expert phase.
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
