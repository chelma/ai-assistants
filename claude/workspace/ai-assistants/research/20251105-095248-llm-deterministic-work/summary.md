# Research Summary: Moving Deterministic Work Out of LLM Prompts

**Repository**: time-cop (scriptdash/time-cop)
**PR Reference**: #52
**Review Comment**: @chelma noted that deterministic operations (sorting) should be handled by Python code, not LLM prompts

## Investigation Summary

Examined the Summary Generator expert implementation to identify where the LLM is being asked to perform operations that could be handled deterministically by Python code.

### Key Findings

1. **Redundant Sorting Instruction**
   - Prompt template instructs LLM to sort pharmacy actions by date
   - Python code already re-sorts the output after LLM generates it
   - File: `prompting/summarizer_templates.py:60` and `summary_generator_tool_def.py:204-208`

2. **Error-Prone Field Navigation**
   - Extensive warnings throughout prompts to prevent LLM from confusing `event_type` vs `resource_type` fields
   - LLM navigates raw event JSON to extract field values
   - Warnings present in both prompt template (`summarizer_templates.py:62-65`) and tool schema (`summary_generator_tool_def.py:34-41`)
   - Pure data extraction task that Python could handle reliably

### Architecture Context

The system uses a two-expert LangChain workflow:
1. **Conversation Analyzer Expert**: Analyzes patient conversations, identifies unresolved matters
2. **Summary Generator Expert**: Creates summary items by combining conversation context with filtered events

Both experts use the Expert-Task-Tool pattern from the langchain-expert-builder skill, where Pydantic schemas enforce structured output from the LLM.

### Deliverable

Created GitHub issue draft following tech-writing skill guidelines:
- Clear problem definition with code references
- PR context explaining team philosophy
- File paths and line numbers as breadcrumbs
- Outcome-based acceptance criteria (not implementation prescription)
- No investigation artifacts or "Recommendation" sections

## Files Created

- `issue_draft.md` - GitHub issue ready for submission
- `summary.md` - This investigation summary
