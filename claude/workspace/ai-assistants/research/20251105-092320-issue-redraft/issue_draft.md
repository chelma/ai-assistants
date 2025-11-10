[TASK] Reduce LLM workload in Summary Generator by moving deterministic operations to Python

## Situation

The Summary Generator expert currently asks the LLM to perform operations that could be handled deterministically by Python code. This reduces reliability and increases token costs.

**Example 1: Redundant Sorting Instructions**

The prompt instructs the LLM to sort pharmacy actions by date:

```
For pharmacy_action_items:
- Create descriptions for pharmacy actions the service agent must take
- Include specific dates/times in descriptions
- Include cite supporting event_ids, sorted by date
```

However, Python code already re-sorts the LLM's output chronologically, making this instruction redundant. The LLM may spend tokens attempting to sort data that will be sorted again anyway.

**Example 2: Error-Prone Field Navigation**

The prompt includes extensive warnings about field confusion:

```
**CRITICAL**: For source_events, use EXACT event_type from each event
- event_type describes what happened: "create", "update", "delete", etc.
- resource_type describes what was affected: "Prescription", "Message", etc.
- NEVER use resource_type values ("Prescription") as event_type
- ALWAYS extract event_type directly from the event JSON
```

These warnings indicate the LLM frequently confuses `event_type` with `resource_type` when navigating the event JSON structure. This is pure data extraction that Python could handle reliably.

**Example 3: Documentation vs. Implementation Mismatch**

The function docstring states pharmacy actions are "sorted by the action's date in descending order" (newest first), but the implementation sorts in ascending order (oldest first):

```python
# Sort by timestamp in ascending order
items_with_timestamps.sort(key=lambda x: x[0])
```

This inconsistency creates confusion about expected behavior.

**Impact:**
- Estimated 5-10% increase in LLM errors due to field confusion
- Approximately 10% unnecessary token usage (150-500 tokens per summary)
- Reduced maintainability from contradictory documentation

## Request

Move deterministic operations from LLM prompt instructions to Python code, allowing the LLM to focus on semantic understanding and content generation tasks it performs best.

## Acceptance Criteria

**Must have:**
* Prompt no longer instructs LLM to perform operations that Python handles deterministically
* Function docstrings accurately describe implemented behavior
* Existing integration tests pass without modification
* Summary generation quality remains at current baseline (manual spot-check of 10+ summaries)

**Should have:**
* Token usage for summary generation reduced by at least 5%
* Unit tests verify deterministic operations are handled by Python code (sorting, field extraction, data validation)

**Nice to have:**
* Prompt complexity reduced as measured by character count or token estimate
* Error rate for incorrect event_type usage reduced (if metrics are tracked)
