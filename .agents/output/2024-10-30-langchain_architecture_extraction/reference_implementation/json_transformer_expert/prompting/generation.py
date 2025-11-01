"""
Prompt generation (factory pattern) for JSON Transformer Expert.

PATTERN DEMONSTRATED: Prompt factory functions with progressive detail loading

This file shows how to create system prompt factories that:
1. Return a callable that takes dynamic inputs
2. Generate SystemMessage with formatted template
3. Support progressive detail loading (reduce context in later phases)

PROGRESSIVE DETAIL LOADING EXAMPLE:
- Mapping phase: Full source + full target schema (~5000 tokens)
- Transform phase: Full source + FILTERED target schema (~1500 tokens)
  → 70% token reduction by filtering to only mapped paths

KEY CONCEPTS:
- Factory functions enable late binding (inputs provided at invocation time)
- Inner function captures template via closure
- Progressive detail: Later phases use results from earlier phases to filter context
- SystemMessage wraps the formatted prompt string

WHY FACTORY PATTERN?
- Separates prompt logic from Expert creation
- Easy to test prompt generation independently
- Supports dynamic context injection (e.g., fetching schemas, filtering data)
- Enables progressive detail loading without complex state management
"""
import json
from typing import Callable, List

from langchain_core.messages import SystemMessage

from json_transformer_expert.prompting.templates import (
    mapping_prompt_template,
    transform_prompt_template
)


def get_mapping_system_prompt_factory() -> Callable[[str, str], SystemMessage]:
    """
    Create factory for mapping phase system prompts.

    The factory takes source_json and target_schema at invocation time.

    Returns:
        Factory function: (source_json, target_schema) -> SystemMessage
    """
    def factory(source_json: str, target_schema: str) -> SystemMessage:
        return SystemMessage(
            content=mapping_prompt_template.format(
                source_json=source_json,
                target_schema=target_schema
            )
        )

    return factory


def get_transform_system_prompt_factory() -> Callable[[str, str, List[dict]], SystemMessage]:
    """
    Create factory for transform phase system prompts.

    Demonstrates PROGRESSIVE DETAIL LOADING:
    - Takes field_mappings from mapping phase
    - Filters target_schema to only include mapped paths
    - Reduces token count and focuses LLM on relevant schema subset

    Returns:
        Factory function: (source_json, target_schema, field_mappings) -> SystemMessage
    """
    def factory(source_json: str, target_schema: str, field_mappings: List[dict]) -> SystemMessage:
        # TODO: In production, implement actual schema filtering logic here
        # For now, we'll just note that target_schema would be filtered
        # to only include the paths present in field_mappings
        #
        # Example filtering logic:
        # mapped_paths = {m['target_path'] for m in field_mappings}
        # target_schema_filtered = filter_schema(target_schema, mapped_paths)
        target_schema_filtered = f"{target_schema}\n\n(In production: Filter to only include paths from mappings)"

        return SystemMessage(
            content=transform_prompt_template.format(
                source_json=source_json,
                target_schema_filtered=target_schema_filtered,
                field_mappings=json.dumps(field_mappings, indent=2)
            )
        )

    return factory
