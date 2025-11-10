"""
Prompt templates for JSON Transformer Expert.

PATTERN DEMONSTRATED: Multi-section prompt templates with XML tags

This file shows prompt template structure:
- XML-style tags (<guidelines>, <source_json>, etc.) for semantic sections
- Explicit constraints and directives ("ALWAYS", "MUST", "NEVER")
- Placeholders for dynamic content ({source_json}, {target_schema})
- Clear goal statement at the top
- Concise final instruction

KEY CONCEPTS:
- XML tags help LLMs understand structure (not required, but helpful)
- Separate guidelines from data sections
- Use imperative language for instructions
- Keep templates focused on single task
- Placeholders match factory function parameters

TEMPLATE BEST PRACTICES:
- Start with role/goal: "You are an AI assistant specialized in..."
- Use <guidelines> for behavioral rules
- Use semantic tags for data sections: <source_json>, <target_schema>
- End with clear call to action: "Create a comprehensive mapping report"
- Avoid redundancy: say it once clearly, not multiple times
"""

# ============================================================================
# MAPPING PHASE TEMPLATE
# ============================================================================

mapping_prompt_template = """You are an AI assistant specialized in analyzing JSON data structures and identifying field mappings.

Your goal is to identify all meaningful field mappings between a source JSON document and a target schema.

<guidelines>
- Analyze the source JSON carefully to understand its structure and semantics
- Identify ALL fields in the source that can map to fields in the target schema
- Provide clear rationale for each mapping explaining the semantic relationship
- Use exact dot-delimited paths (e.g., "user.email", "metadata.timestamp")
- Be thorough - don't skip fields that have valid mappings
</guidelines>

<source_json>
{source_json}
</source_json>

<target_schema>
{target_schema}
</target_schema>

Analyze the source JSON and target schema, then create a comprehensive mapping report.
"""


# ============================================================================
# TRANSFORM PHASE TEMPLATE
# ============================================================================

transform_prompt_template = """You are an AI assistant specialized in generating Python code for JSON transformations.

Your goal is to generate clean, executable Python code that transforms source JSON to match a target schema.

<guidelines>
- Generate syntactically valid Python code
- Define a function: transform(source_json_str: str) -> dict
- The function must parse the JSON string, extract values, and return a dict matching the target schema
- Keep imports minimal - only include what you actually use
- Handle potential missing fields gracefully (use .get() with defaults)
- Follow the identified field mappings exactly
</guidelines>

<source_json>
{source_json}
</source_json>

<target_schema_filtered>
The target schema has been filtered to include only the fields you identified in the mapping phase:
{target_schema_filtered}
</target_schema_filtered>

<field_mappings>
{field_mappings}
</field_mappings>

Generate Python transformation code that implements these mappings.
"""
