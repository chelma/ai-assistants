[TASK] Move deterministic work out of LLM prompts in Summary Generator

## Situation

The Summary Generator expert currently asks the LLM to perform operations that could be handled deterministically by Python code. This reduces reliability and increases token costs.

Following PR #52 review comment by @chelma:
> "Anything we *can* solve with traditional code, we should solve with traditional code. Reducing the ask of the LLM to the bare minimum increases the odds of success. We could easily perform this sort operation ourselves."

While PR #52 implemented sorting in Python code (`summary_generator_tool_def.py:204-208`), investigation reveals the prompt template still instructs the LLM to perform sorting. Additional analysis identified further opportunities to reduce the LLM's workload by moving deterministic operations to application code.

**Redundant Sorting Instruction**

The prompt at `prompting/summarizer_templates.py:60` instructs the LLM to sort pharmacy actions by date:

```python
- **pharmacy_action_summary_items**: Pharmacy actions from filtered events
  (cite supporting event_ids, sorted by date)
```

However, Python already re-sorts the output at `summary_generator_tool_def.py:204-208`:

```python
# Sort by timestamp in ascending order
items_with_timestamps.sort(key=lambda x: x[0])
```

The LLM instruction is redundant and may cause confusion since Python will re-sort regardless of the LLM's ordering.

**Error-Prone Field Navigation**

The prompt at `prompting/summarizer_templates.py:62-65` includes extensive warnings to prevent the LLM from confusing fields when navigating event JSON:

```python
**CRITICAL**: For source_events, use EXACT event_type from each event
- Conversation events: use event_type provided in "Unresolved patient requests" section above
- Supporting events: use event_type field from filtered events ("update", "create", "state_transition")
- NEVER use resource_type values ("Prescription", "Action", "Delivery") as event_type
```

These warnings indicate the LLM frequently confuses `event_type` and `resource_type` fields when navigating event JSON - a pure data extraction task that Python could handle reliably. The tool schema at `summary_generator_tool_def.py:34-41` also includes similar warnings in the field descriptions:

```python
event_type: str = Field(
    description=(
        "The type of the source event that is being cited. The event_type field is in the list of event types defined in # Event Types"
    )
)
```

The extensive warnings across both the prompt template and tool schema suggest this is a recurring error pattern that would be eliminated by extracting `event_type` values in Python before presenting them to the LLM.

## Request

Reduce the LLM's workload by moving deterministic operations to Python code, allowing the LLM to focus on semantic understanding (identifying relevant events and generating natural language summaries) rather than data extraction and ordering operations.

## Acceptance Criteria

* LLM prompts no longer instruct the LLM to perform sorting operations
* LLM prompts no longer require the LLM to navigate raw event JSON to extract `event_type` values
* Function docstrings accurately describe implemented behavior
* Token usage for summary generation activity reduced by at least 5% compared to current implementation
* Existing integration tests pass without modification
* Unit tests verify deterministic operations are handled by Python code

## Related Tasks

* PR #52: https://github.com/scriptdash/time-cop/pull/52 (Initial sorting implementation)
