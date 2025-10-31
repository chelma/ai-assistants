"""
Task definitions for JSON Transformer Expert.

Concrete Task implementations for the two-phase workflow:
1. MappingTask: Identify field mappings between source JSON and target schema
2. TransformTask: Generate Python code to perform the transformation
"""
from dataclasses import dataclass
from typing import Any, Dict, List

from langchain_core.messages import BaseMessage

from core.tasks import Task
from json_transformer_expert.models import MappingReport, TransformCode


@dataclass
class MappingTask(Task):
    """
    Task for mapping phase: identify field mappings between source and target.

    Inputs:
        source_json: The source JSON to transform (as string)
        target_schema: Description of the target schema structure

    Work Item:
        mapping_report: MappingReport containing identified mappings
    """
    source_json: str
    target_schema: str
    mapping_report: MappingReport = None

    def get_work_item(self) -> Any:
        return self.mapping_report

    def set_work_item(self, new_work_item: Any):
        if not isinstance(new_work_item, MappingReport):
            raise TypeError("new_work_item must be of type MappingReport")
        self.mapping_report = new_work_item

    def get_tool_name(self) -> str:
        return "CreateMappingReport"

    def to_json(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "source_json": self.source_json,
            "target_schema": self.target_schema,
            "context": [turn.to_json() for turn in self.context],
            "mapping_report": self.mapping_report.to_json() if self.mapping_report else None
        }


@dataclass
class TransformTask(Task):
    """
    Task for transform phase: generate Python code to perform transformation.

    Inputs:
        source_json: The source JSON to transform (as string)
        target_schema: Description of the target schema structure
        mappings: List of FieldMapping objects from mapping phase

    Work Item:
        transform_code: TransformCode containing Python transformation logic
    """
    source_json: str
    target_schema: str
    mappings: List[Dict[str, str]]  # Serialized FieldMapping objects
    transform_code: TransformCode = None

    def get_work_item(self) -> Any:
        return self.transform_code

    def set_work_item(self, new_work_item: Any):
        if not isinstance(new_work_item, TransformCode):
            raise TypeError("new_work_item must be of type TransformCode")
        self.transform_code = new_work_item

    def get_tool_name(self) -> str:
        return "GenerateTransformCode"

    def to_json(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "source_json": self.source_json,
            "target_schema": self.target_schema,
            "mappings": self.mappings,
            "context": [turn.to_json() for turn in self.context],
            "transform_code": self.transform_code.to_json() if self.transform_code else None
        }
