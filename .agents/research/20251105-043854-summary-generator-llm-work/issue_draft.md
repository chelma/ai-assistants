# [TASK] Move deterministic work from Summary Generator LLM to Python code

## Situation

The Summary Generator expert (part of the patient events summarization workflow) currently asks the LLM to perform operations that could be handled by deterministic Python code. This reduces LLM reliability and increases token usage unnecessarily.

Following the PR #52 review comment by @chelma:
> "Anything we *can* solve with traditional code, we should solve with traditional code. Reducing the ask of the LLM to the bare minimum increases the odds of success."

While PR #52 implemented sorting in Python code, the prompt template still instructs the LLM to perform sorting, and investigation reveals additional opportunities to move work from the LLM to deterministic code.

### Current Architecture

The Summary Generator expert follows the LangChain Expert-Task-Tool pattern:

1. **Prompt template** (`prompting/summarizer_templates.py`) provides instructions to the LLM
2. **Pydantic schemas** (`summary_generator_tool_def.py`) define structured output format
3. **Tool function** (`create_patient_events_summary`) converts LLM output to domain models
4. **Parsing functions** perform validation, filtering, and sorting on LLM output

### Problem

The LLM is being asked to perform data extraction and transformation operations that:
- Increase cognitive load (reducing reliability)
- Consume tokens (increasing cost and latency)
- Create opportunities for errors (especially event_type vs resource_type confusion)
- Duplicate work already handled by Python code (sorting)

Investigation identified specific issues in two files:
- `python_worker/time_cop_worker/activities/summarize_patient_events/summary_generator_tool_def.py`
- `python_worker/time_cop_worker/activities/summarize_patient_events/prompting/summarizer_templates.py`

## Request

Reduce the LLM's workload by moving deterministic operations to Python code, allowing the LLM to focus on its core strengths: semantic understanding, content analysis, and natural language generation.

The system should perform data extraction, formatting, and transformation in Python before/after LLM invocation, providing the LLM with pre-processed, clearly structured data.

## Opportunities Identified

### Priority 1: Remove Redundant Sorting Instruction (HIGH)

**File**: `prompting/summarizer_templates.py:60`

**Current state**:
```python
USER_PROMPT_TEMPLATE = """\
...
- **pharmacy_action_summary_items**: Pharmacy actions from filtered events (cite supporting event_ids, sorted by date)
"""
```

**Issue**: The prompt asks the LLM to sort pharmacy actions by date, but Python already handles sorting at `summary_generator_tool_def.py:204-208`:

```python
# Sort by timestamp in ascending order
items_with_timestamps.sort(key=lambda x: x[0])
```

Asking the LLM to sort is redundant and may cause confusion since Python will re-sort the results regardless of LLM output order.

**Recommendation**: Remove "sorted by date" from line 60 of the prompt template.

**Impact**:
- Reduces LLM cognitive load
- Eliminates potential confusion about who handles sorting
- Saves ~10 tokens per invocation

### Priority 2: Fix Docstring/Code Mismatch (HIGH)

**File**: `summary_generator_tool_def.py:110` (docstring) vs line 205 (code)

**Issue**: Documentation contradicts implementation:
- Line 110 docstring: "sorted by the action's date in **descending** order"
- Line 205 code comment: "Sort by timestamp in **ascending** order"

**Recommendation**: Determine correct sort order (chronological ascending likely correct for showing progression) and update either docstring or code to match.

**Impact**:
- Fixes documentation bug
- Prevents developer confusion
- Ensures system behavior matches specification

### Priority 3: Pre-extract event_type Fields (MEDIUM)

**File**: `prompting/summarizer_templates.py:62-65`

**Current state**: The prompt includes extensive warnings about confusing `event_type` with `resource_type`:

```python
**CRITICAL**: For source_events, use EXACT event_type from each event:
- Conversation events: use event_type provided in "Unresolved patient requests" section above
- Supporting events: use event_type field from filtered events ("update", "create", "state_transition")
- NEVER use resource_type values ("Prescription", "Action", "Delivery") as event_type
```

These warnings indicate event_type extraction is a known failure mode. The LLM must navigate JSON structure to distinguish `event_type` from `resource_type`.

**Current event format**:
```json
{
  "event_type": "update",
  "resource_type": "Prescription",
  "id": 123,
  ...many other fields...
}
```

**Recommendation**: Pre-process events in Python to emphasize event_type before sending to LLM:

```python
# Option 1: Flatten and emphasize
{
  "event_id": 123,
  "EVENT_TYPE": "update",  # Capitalized to stand out
  "resource_type": "Prescription",
  ...
}

# Option 2: Create simplified event reference structure
{
  "event_id": 123,
  "type": "update",  # Rename to avoid confusion
  "resource": "Prescription",
  ...
}
```

**Impact**:
- Removes need for ~50 token warning in prompt (lines 62-65)
- Reduces LLM errors from field confusion
- Simplifies event JSON structure explanation
- Estimated 5-10% improvement in event_type citation accuracy
- Saves ~100-500 tokens per invocation (less nested structure to explain)

### Priority 4: Pre-format Timestamps (LOW)

**Files**:
- `summary_generator_tool_def.py:77-80` (Pydantic schema requires datetime)
- `prompting/summarizer_templates.py:66-67` (instructs LLM to format dates)

**Current state**: LLM must:
1. Provide timestamp in datetime format (Pydantic validation)
2. Format dates in descriptions: "Start with On [date], ..."

**Recommendation**: Pre-format timestamps in event JSON:

```python
{
  "event_id": 123,
  "timestamp": "2025-11-04T15:30:00Z",
  "formatted_date": "November 4, 2025",  # Human-readable
  "formatted_datetime": "November 4, 2025 at 3:30 PM"  # With time
}
```

Then update Pydantic schema to accept pre-formatted strings instead of requiring LLM to format dates.

**Impact**:
- Ensures consistent date formatting across all summaries
- Reduces LLM cognitive load
- Small token savings (~5-10 tokens)
- Eliminates date formatting errors

## Acceptance Criteria

### Minimum Viable (Must Have)
- [ ] Prompt template no longer instructs LLM to sort pharmacy actions (Priority 1)
- [ ] Docstring and code agree on sort order direction (Priority 2)
- [ ] Unit tests verify sorting behavior matches documentation
- [ ] Existing integration tests pass without modification

### Recommended (Should Have)
- [ ] Events are pre-processed to emphasize `event_type` field before LLM sees them (Priority 3)
- [ ] Prompt warnings about event_type vs resource_type confusion are removed or reduced
- [ ] Unit tests verify event_type is correctly extracted in all scenarios
- [ ] Token usage for summary generation is reduced by at least 5%

### Optional (Nice to Have)
- [ ] Timestamps are pre-formatted in event JSON (Priority 4)
- [ ] Pydantic schema accepts formatted date strings instead of requiring datetime
- [ ] Date formatting is consistent across all generated summaries

## Technical Context

### Files to Modify

**Primary changes**:
1. `python_worker/time_cop_worker/activities/summarize_patient_events/prompting/summarizer_templates.py`
   - Line 60: Remove "sorted by date" instruction
   - Lines 62-65: Remove or simplify event_type warnings (if Priority 3 implemented)
   - Lines 66-67: Remove date formatting instruction (if Priority 4 implemented)

2. `python_worker/time_cop_worker/activities/summarize_patient_events/summary_generator_tool_def.py`
   - Line 110: Fix docstring to match code (or vice versa)
   - Lines 77-80: Update schema if pre-formatted timestamps implemented

**Secondary changes** (if Priority 3 implemented):
3. Event filtering logic (wherever events are prepared before being passed to prompt factory)
   - Add pre-processing step to emphasize event_type field
   - Consider creating simplified event representation for LLM consumption

### Related Files

Reference files for understanding the expert pattern:
- `summary_generator_expert_def.py` - Expert definition and LLM configuration
- `summary_generator_task_def.py` - Task definition for conversation context
- `summary_models.py` - Domain models (SourceEvent, SummaryItem, etc.)

### Testing Strategy

**Unit tests**:
- Verify `_parse_pharmacy_action_items` sorts correctly and matches docstring
- Verify prompt template does not contain "sorted by date" instruction
- Verify event_type extraction works correctly (if Priority 3 implemented)

**Integration tests**:
- Existing Helm chart tests should pass without modification
- Temporal workflows for patient summarization should succeed
- Generated summaries should maintain quality (manual review of sample outputs)

**Validation**:
- Compare token usage before/after changes (expect 5-10% reduction if all priorities implemented)
- Monitor event_type citation errors in production (expect reduction if Priority 3 implemented)
- Verify date formatting consistency (if Priority 4 implemented)

## Benefits

### Reliability
- Reduces LLM cognitive load by ~5-10% (fewer instructions, clearer data)
- Eliminates known failure mode (event_type vs resource_type confusion)
- Ensures consistent sorting behavior (Python guarantees, LLM does not)

### Performance
- Reduces token usage by ~160-560 tokens per invocation (5-10% reduction)
- Slightly faster LLM inference (fewer tokens to process)
- Lower cost per summary generation

### Maintainability
- Fixes documentation bug (docstring/code mismatch)
- Clearer separation of concerns (Python: data transformation, LLM: semantic understanding)
- Easier to test and validate deterministic operations

## References

**PR #52 Review Comment**: https://github.com/scriptdash/time-cop/pull/52#discussion_r2492265894

**Related Issue**: ISSUE-44 (context for PR #52 changes)

**LangChain Expert Pattern**: This follows the Expert-Task-Tool architecture where:
- Tool schemas define structured output
- Prompt templates provide instructions
- Tool functions convert LLM output to domain models
- Best practice: Minimize LLM work to semantic tasks, maximize deterministic preprocessing/postprocessing
