"""
Prompt templates for JSON Transformer Expert.

Multi-section templates with XML-style tags for clarity.
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
