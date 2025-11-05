# Investigation Findings: Summary Generator LLM Work Analysis

## Summary

The summary_generator_tool_def.py file implements a LangChain expert that creates patient event summaries by combining conversation analysis with event logs. The current implementation asks the LLM to perform sorting operations via prompt instructions (line 60 in the template), but the actual sorting is now handled by deterministic Python code (lines 204-208 in tool_def.py). This investigation identifies additional opportunities to move work from the LLM to deterministic code.

## Context from PR #52

**Review comment by chelma (line 110)**:
> "(Non-Blocker) Anything we *can* solve with traditional code, we should solve with traditional code. Reducing the ask of the LLM to the bare minimum increases the odds of success. We could easily perform this sort operation ourselves."

**Status**: The docstring was updated to reflect sorting in descending order, but:
1. The actual sorting happens in `_parse_pharmacy_action_items()` at lines 204-208 (ascending order)
2. The prompt still asks the LLM to sort at line 60 of summarizer_templates.py
3. There's a discrepancy: docstring says descending, code does ascending

## File Structure Analysis

### summary_generator_tool_def.py (263 lines)

**Purpose**: Defines the Pydantic schemas and tool function for the summary generator expert

**Key components**:
- Lines 23-42: `SourceEventInput` schema - captures event citations
- Lines 44-60: `PatientRequestSummaryItemInput` schema
- Lines 61-82: `PharmacyActionSummaryItemInput` schema (includes timestamp field)
- Lines 83-105: `CreatePatientEventsSummaryInput` schema (top-level)
- Lines 107-129: `_parse_source_events()` - converts Pydantic to domain models
- Lines 132-167: `_parse_patient_request_items()` - parses patient items
- Lines 170-208: `_parse_pharmacy_action_items()` - **parses and SORTS pharmacy items**
- Lines 211-251: `create_patient_events_summary()` - main tool function
- Lines 255-262: `create_summary_tool` - StructuredTool definition

### prompting/summarizer_templates.py (66 lines)

**Purpose**: Prompt templates for the summarization expert

**Key sections**:
- Lines 9-23: System prompt - defines expert role
- Lines 26-65: User prompt template with placeholders
- Line 60: **Instructs LLM to sort**: "sorted by date"

## Deterministic Work Already Implemented

### 1. Timestamp-based Sorting (Lines 204-208)

**Current implementation**:
```python
# Sort by timestamp in ascending order
items_with_timestamps.sort(key=lambda x: x[0])
```

**What it does**: Python code sorts pharmacy action items by timestamp after LLM provides them

**Status**: ✅ Already implemented (but prompt still mentions sorting)

### 2. Data Validation and Filtering

**Lines 117-129** (`_parse_source_events`):
- Validates event_type and event_id can be converted to proper types
- Skips invalid source events silently
- Ensures type safety

**Lines 156-165** (`_parse_patient_request_items`):
- Strips whitespace from descriptions
- Filters out items with empty descriptions
- Filters out items with no valid source events

**Lines 194-202** (`_parse_pharmacy_action_items`):
- Strips whitespace from descriptions
- Filters out items with empty descriptions
- Filters out items with no valid source events

**Status**: ✅ Already implemented

## LLM Work Currently Being Asked

Based on the prompt template analysis (summarizer_templates.py):

### 1. Content Analysis (Lines 27-31)
**What LLM does**: Analyze conversation summary and identify unresolved matters
**Can be moved?**: ❌ No - This is semantic understanding, core LLM work

### 2. Event Citation (Line 36, 59)
**What LLM does**: Match conversation event_ids to appropriate summary items
**Can be moved?**: ❌ No - Requires understanding which events relate to which requests

### 3. Summary Item Creation (Lines 46-50)
**What LLM does**: Write 2-4 sentence descriptions of patient requests
**Can be moved?**: ❌ No - Creative writing task, core LLM work

### 4. Pharmacy Action Descriptions (Lines 64-66)
**What LLM does**: Create descriptions of pharmacy actions including dates/times
**Can be moved?**: ⚠️ Partial - Date formatting could be standardized, but description is LLM work

### 5. Event-to-Type Mapping (Lines 62-65)
**What LLM does**: Extract correct event_type field from events
**Can be moved?**: ✅ YES - This is data extraction from structured JSON

### 6. Sorting Pharmacy Actions (Line 60)
**What LLM does**: Asked to sort pharmacy actions by date
**Can be moved?**: ✅ ALREADY DONE - Python code handles this, prompt is outdated

## Opportunities to Move Work to Deterministic Code

### Opportunity 1: Remove Sorting Instruction from Prompt (HIGH PRIORITY)

**Current state**:
- Line 60 in summarizer_templates.py: "sorted by date"
- Python already sorts at lines 204-208
- Asking LLM to do work that Python will override anyway

**Recommendation**: Remove sorting instruction from prompt

**Impact**:
- Reduces cognitive load on LLM
- Eliminates confusion (LLM might spend tokens trying to sort)
- Makes it clear Python handles ordering

**File**: `prompting/summarizer_templates.py:60`

### Opportunity 2: Pre-extract event_type Fields (MEDIUM PRIORITY)

**Current state**:
- Prompt gives LLM raw event JSON (line 50)
- LLM must navigate JSON structure to find event_type vs resource_type
- Lines 62-65 provide extensive warnings about confusing these fields
- This is pure data extraction, not semantic understanding

**Recommendation**: Pre-process events to extract event_type in a clear format

**Example transformation**:
```python
# Current: LLM gets raw event JSON
{
  "event_type": "update",
  "resource_type": "Prescription",
  "id": 123,
  ...lots of other fields...
}

# Better: Pre-format with clear event_type annotation
{
  "event_id": 123,
  "EVENT_TYPE": "update",  # <-- Emphasized
  "resource_type": "Prescription",
  ...
}
```

**Impact**:
- Reduces prompt complexity (remove lines 62-65 warnings)
- Reduces LLM errors (event_type confusion is a known issue based on warning)
- Saves tokens (less explanation needed)
- Improves reliability (less ambiguity)

### Opportunity 3: Pre-format Timestamps (LOW PRIORITY)

**Current state**:
- Lines 77-80: LLM must provide timestamp in datetime format
- Lines 64-66: LLM must format dates in descriptions ("On [date], ...")

**Recommendation**: Pre-format timestamps in events to consistent human-readable format

**Example**:
```python
# Add to each event:
{
  "event_id": 123,
  "timestamp": "2025-11-04T15:30:00Z",
  "formatted_date": "November 4, 2025 at 3:30 PM"  # <-- Pre-formatted
}
```

**Impact**:
- Ensures consistent date formatting across summaries
- Reduces LLM cognitive load
- Small token savings

### Opportunity 4: Docstring vs Implementation Mismatch (HIGH PRIORITY - BUG)

**Issue identified**:
- Line 110 docstring says "sorted by the action's date in descending order"
- Line 205 code says `# Sort by timestamp in ascending order`
- These contradict each other

**Recommendation**: Determine correct sort order and fix mismatch

**Questions to resolve**:
1. Should pharmacy actions be shown newest-first (descending) or oldest-first (ascending)?
2. Update either code or docstring to match
3. Consider: Service agents likely want chronological order (ascending) to see progression

## Impact Analysis

### Token Savings

**Current prompt size estimate** (from template):
- System prompt: ~150 tokens
- User prompt base: ~200 tokens
- Event definitions: ~500 tokens (varies)
- Events JSON: ~2000-5000 tokens (varies by patient)
- **Total**: ~3000-6000 tokens per invocation

**Savings from recommendations**:
- Remove sorting instruction (Opp 1): ~10 tokens
- Remove event_type warnings (Opp 2): ~50 tokens
- Simplified event JSON (Opp 2): ~100-500 tokens (less nested structure to explain)
- **Total savings**: ~160-560 tokens per invocation (5-10% reduction)

### Reliability Improvements

**Error reduction**:
- **Opportunity 1**: Eliminates potential LLM confusion about sorting responsibility
- **Opportunity 2**: Major - event_type confusion is explicitly warned against in prompt (lines 62-65), indicating this is a known failure mode
- **Opportunity 4**: Fixes bug where documentation and behavior disagree

**Success rate impact**: Estimated 5-10% improvement in correct event_type usage based on:
- Explicit warnings in prompt indicate this is a problem area
- Simplifying data extraction reduces opportunities for mistakes

## Code References

### Sorting Implementation
- **File**: `summary_generator_tool_def.py`
- **Lines**: 182-208
- **Function**: `_parse_pharmacy_action_items()`
- **What it does**: Creates list of (timestamp, SummaryItem) tuples, sorts by timestamp (ascending), returns items without timestamps

### Prompt Sorting Instruction
- **File**: `prompting/summarizer_templates.py`
- **Line**: 60
- **Text**: "cite supporting event_ids, sorted by date"

### Event Type Warnings
- **File**: `prompting/summarizer_templates.py`
- **Lines**: 62-65
- **Purpose**: Warn LLM not to confuse event_type with resource_type

### Docstring Mismatch
- **File**: `summary_generator_tool_def.py`
- **Line**: 110 (docstring) vs Line 205 (code comment)
- **Issue**: Ascending vs descending disagreement

## Next Steps

1. Create GitHub issue documenting these opportunities
2. Prioritize:
   - HIGH: Fix docstring/code mismatch (Opp 4)
   - HIGH: Remove sorting instruction from prompt (Opp 1)
   - MEDIUM: Pre-extract event_type fields (Opp 2)
   - LOW: Pre-format timestamps (Opp 3)
