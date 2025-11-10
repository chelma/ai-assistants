# Research Plan: Summary Generator LLM Work Analysis

**Workspace**: ai-assistants
**Project Root**: /Users/chris.helma/workspace/personal/ai-assistants
**Created**: 2025-11-05 04:38:54
**Research Directory**: `~/.claude/workspace/ai-assistants/research/20251105-043854-summary-generator-llm-work/`

## Research Objective

Analyze the summary_generator_tool_def.py file to identify work currently being asked of the LLM that could be handled by deterministic Python code, with a focus on sorting operations mentioned in PR #52 review comments.

## Key Questions

1. What is the current structure of the summary generator expert's prompt?
2. What data transformation operations is the LLM being asked to perform?
3. What sorting operations are mentioned around line 110 (per review comment)?
4. What filtering or data manipulation is being asked of the LLM?
5. What operations could be moved to deterministic code before/after LLM invocation?
6. What would be the impact on prompt complexity and token usage?

## Investigation Scope

**Primary file**:
- `/Users/chris.helma/workspace/personal/time-cop/python_worker/time_cop_worker/activities/summarize_patient_events/summary_generator_tool_def.py`

**Context files** (if needed):
- Related expert definition files
- Prompt templates
- Task definitions
- Validation logic

## Expected Deliverables

1. **findings.md** - Detailed analysis of current implementation with code references
2. **issue_draft.md** - GitHub issue following tech-writing guidelines that:
   - Explains the problem (LLM doing deterministic work)
   - References specific code sections
   - Explains why this matters (reliability, token usage)
   - Provides specific recommendations
   - Includes acceptance criteria

## Skills Loaded

- ✅ python-style - For Python code analysis
- ✅ langchain-expert-builder - For understanding LangChain expert patterns
- ✅ tech-writing - For GitHub issue creation

## Investigation Strategy

1. **Phase 1**: Setup & Planning (current)
2. **Phase 2**: Reconnaissance - Use Explore to understand file structure and related files
3. **Phase 3**: Deep Investigation - Read primary file and analyze prompt structure
4. **Phase 4**: Analysis - Identify LLM work vs deterministic work opportunities
5. **Phase 5**: Deliverable Creation - Create GitHub issue draft
6. **Phase 6**: Summary & Handoff - Return concise findings to main session
