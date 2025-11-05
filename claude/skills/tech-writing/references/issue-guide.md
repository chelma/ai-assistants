# Issue/Ticket Writing Guide

This document contains line-item preferences for creating GitHub issues, Jira tickets, and similar tracking items. When writing an issue, apply these preferences consistently.

## Analysis Source

This guide was created by analyzing 78 issues authored across two repositories:
- **Time Cop** (9 issues, 2025)
- **AWS-AIO** (69 issues, 2023-2024)

These patterns reflect preferences from 2023-2025, with more recent patterns weighted more heavily.

## Core Principles

### Information Completeness
Issues provide substantial context enabling another engineer to understand the problem space and take action without requiring synchronous communication.

### Objective Tone
Third-person, engineering-focused communication. Avoid personal pronouns, marketing language, or emotional framing.

### Actionable Outcomes
Every issue concludes with clear, testable acceptance criteria that define "done."

### Problem Definition, Not Solution Prescription
Issues describe WHAT is broken and WHY it matters, not HOW to fix it. This preserves implementer agency and prevents premature optimization. Technical context provides facts about the system; acceptance criteria define outcomes, not implementation steps.

## Title Conventions

Use **title tags** to categorize issues:

**Format:** `[TYPE] Brief description`

**Issue types:**
- `[TASK]` - Feature implementation, enhancement, or general work
- `[BUG]` - Something broken or not working as intended

**Examples:**
- ✅ `[TASK] Create Summarization Activity`
- ✅ `[BUG] Ruby Worker image build failing due to missing RBI generation`

**Title content after tag:**
- Keep concise (under 80 characters total if possible)
- Describe the what, not the how
- Use active voice
- No ending punctuation

## Issue Structure

Use this structure for all issues (tasks, bugs, enhancements):

```markdown
## Situation
[Context explaining the current state and why this work is needed]

## Request
[Clear statement of what should be accomplished]

## Acceptance Criteria
* [Specific, testable criterion]
* [Another criterion]
* [Nested details when needed]
    * [Sub-criterion]
```

**Situation section:**
- Provides background and context
- Explains current state and pain points
- May reference related PRs, issues, or conversations
- Can include code examples, error logs, or stack traces for bugs

**Request section:**
- Single paragraph clearly stating the desired outcome
- Focuses on *what* should change, not *how* to do it
- CRITICAL: Do not prescribe implementation steps, specific code changes, or technical approaches
- If extensive investigation informed this issue, distill findings into problem context rather than solution steps
- May reference related issues or documentation

**Acceptance Criteria section:**
- Bullet list of specific, testable conditions
- Each criterion should be independently verifiable
- Use nested bullets for sub-requirements
- Often includes "ASSUME" items for test setup
- Can specify testing scenarios ("When X happens, Y should occur")

## Optional Sections

**Blocked By:**
```markdown
## Blocked By
* https://github.com/owner/repo/issues/123
```
Use when issue cannot proceed until dependencies complete.

**Related Tasks:**
```markdown
## Related Tasks
* https://github.com/owner/repo/issues/456
* https://github.com/owner/repo/issues/789
```
Use to provide context without blocking relationship.

**Notes:**
```markdown
## Notes
[Additional context, discussion points, or caveats]
```
Use for supplementary information that doesn't fit elsewhere.

## Technical Detail Guidelines

### Code References

**Link to specific lines:**
```markdown
See example [here](https://github.com/owner/repo/blob/abc123/path/file.py#L42)
```

**Inline code snippets:**
Use fenced code blocks with language tags:
````markdown
```python
def example():
    pass
```
````

**Error logs:**
Include relevant portions, use code fences:
````markdown
```
Error: building at STEP "RUN bundle exec rake protos:generate": exit status 1
rake aborted!
```
````

### URLs and References

**Format:**
- Bare URLs for GitHub links: `https://github.com/owner/repo/issues/123`
- Markdown links for external resources: `[AWS docs](https://url)`
- Footnote style for multiple references in long issues: `[1]`, `[2]`, etc. with links at bottom

**What to link:**
- Related issues and PRs
- Relevant code locations
- External documentation
- Design documents
- Previous discussions

### Technical Context

**For bugs, include:**
- Steps to reproduce
- Actual vs. expected behavior
- Error messages or stack traces
- Environment details (versions, platforms)
- Code paths involved

**For features, include:**
- Use case or user need
- Related existing functionality
- Technical constraints
- Scaling considerations

## Distilling Investigation Findings

When creating an issue after extensive investigation, provide technical context that helps understand the problem while avoiding solution prescription.

### Technical Context to Include (Breadcrumbs)

**Concrete examples with locations:**
- Code snippets showing the problem with file paths and line numbers
- Error messages or logs with stack traces
- Specific instances demonstrating the pattern
- Example: `summary_generator_tool_def.py:204-208` shows the sorting implementation

**Project context:**
- PR comments or review feedback that motivated this investigation
- Links to related issues, previous discussions, or design documents
- Team philosophy or principles relevant to understanding why this matters
- Example: "Following PR #52 review comment by @username: [quote]"

**Impact metrics:**
- Token usage, error rates, performance degradation
- Cost implications, reliability concerns
- Maintenance burden or technical debt

**System architecture facts:**
- How components interact relevant to this issue
- Technology stack or patterns in use (LangChain, Expert-Task-Tool, etc.)
- Constraints or design decisions that affect the problem

**Key principle:** Provide breadcrumbs to investigate further. File references, line numbers, and PR links help the implementer understand WHERE and WHY, without prescribing HOW to fix.

### What NOT to Include

**Investigation process artifacts:**
- References to local research directories (`.agents/research/`)
- Tool names used during investigation (grep, codebase-researcher, etc.)
- "I found..." or "Investigation revealed..." language
- Your personal investigation methodology

**Prescriptive solutions:**
- "Recommendation:" subsections telling how to fix each problem
- Priority rankings for suggested solutions (HIGH/MEDIUM/LOW)
- Implementation checklists or "Files to Modify" sections
- Acceptance criteria tied to specific implementation approaches
- "Option 1 / Option 2" code examples showing how to solve it

### Example - Too prescriptive (implementation TODO list):

```markdown
## Opportunities Identified

### Priority 1: Remove Redundant Sorting Instruction (HIGH)
**File**: `prompting/summarizer_templates.py:60`

**Recommendation**: Remove "sorted by date" from line 60 of the prompt template.

**Impact**: Reduces LLM cognitive load, saves ~10 tokens per invocation.

### Priority 2: Fix Docstring/Code Mismatch (HIGH)
**File**: `summary_generator_tool_def.py:110`

**Recommendation**: Update docstring to match code implementation.

## Files to Modify

1. `prompting/summarizer_templates.py`
   - Line 60: Remove "sorted by date" instruction
   - Lines 62-65: Remove event_type warnings

2. `summary_generator_tool_def.py`
   - Line 110: Fix docstring

## Acceptance Criteria
- [ ] Line 60 of prompt template updated (Priority 1)
- [ ] Docstring matches implementation (Priority 2)
```

**Problems with this approach:**
- Priority rankings prescribe which solutions to implement
- "Recommendation:" sections tell the implementer how to solve each issue
- "Files to Modify" creates an implementation checklist
- Acceptance criteria tied to specific line changes, not outcomes
- Reads like a TODO list, not a problem definition

### Example - Good balance (problem with breadcrumbs):

```markdown
## Situation

The Summary Generator expert currently asks the LLM to perform operations that could be handled deterministically by Python code. This reduces reliability and increases token costs.

Following PR #52 review comment by @chelma:
> "Anything we *can* solve with traditional code, we should solve with traditional code. Reducing the ask of the LLM to the bare minimum increases the odds of success."

While PR #52 implemented sorting in Python code, investigation reveals the prompt template still instructs the LLM to perform sorting, plus additional opportunities exist.

**Problem 1: Redundant Sorting Instruction**

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

The LLM instruction is redundant and may cause confusion since Python will re-sort regardless.

**Problem 2: Error-Prone Field Navigation**

The prompt at `prompting/summarizer_templates.py:62-65` includes extensive warnings:

```python
**CRITICAL**: For source_events, use EXACT event_type from each event
- NEVER use resource_type values ("Prescription") as event_type
```

These warnings indicate the LLM frequently confuses fields when navigating event JSON - a pure data extraction task Python could handle reliably.

**Problem 3: Documentation Mismatch**

The docstring at `summary_generator_tool_def.py:110` states pharmacy actions are "sorted by the action's date in descending order", but the implementation at line 204 sorts ascending. This creates confusion about expected behavior.

## Request

Reduce the LLM's workload by moving deterministic operations to Python code, allowing the LLM to focus on semantic understanding and content generation.

## Acceptance Criteria

* Prompt no longer instructs LLM to perform operations that Python handles deterministically
* Function docstrings accurately describe implemented behavior
* Token usage for summary generation reduced by at least 5%
* Existing integration tests pass without modification
* Unit tests verify deterministic operations handled by Python code
```

**Why this works:**
- Provides PR context explaining team philosophy and why this matters
- File paths and line numbers help implementer locate the problems
- Code snippets show WHAT is wrong with specific examples
- Describes the problem without prescribing HOW to fix it
- Acceptance criteria define outcomes, not implementation steps
- No "Recommendation:" sections or priority rankings

## Writing Style

### Voice and Tone

**Use third-person descriptive:**
- ✅ "The system currently uses..."
- ✅ "Users expect X to destroy everything"
- ❌ NOT "We need to..."
- ❌ NOT "I think we should..."

**Use imperative for requests:**
- ✅ "Update the behavior to..."
- ✅ "Add a way to..."
- ✅ "Enable users to..."

**Maintain objectivity:**
- Focus on technical facts
- Avoid emotional language
- No marketing superlatives
- Present tense for current state, future tense for desired state

### Sentence Structure

**Keep focused and direct:**
- One idea per sentence when possible
- Use bullets for lists of related items
- Use paragraphs for explanatory context
- Break complex information into digestible chunks

### Completeness vs. Brevity

**Provide enough context to:**
- Understand why the work is needed
- Begin implementation without synchronous conversation
- Make informed technical decisions
- Verify completion

**Omit:**
- Implementation details (unless critical to understanding)
- Obvious information the team already knows
- Speculation about unrelated future work
- Personal opinions not grounded in technical requirements

## Acceptance Criteria Best Practices

### Characteristics of Good Criteria

**Specific and testable:**
- ✅ "GitHub should prevent merges if the Helm Chart deployment fails"
- ❌ NOT "GitHub checks should work properly"

**Independently verifiable:**
- Each criterion can be checked without depending on others
- Someone other than the author can verify completion

**Complete:**
- Cover all aspects of the request
- Include both positive cases (what should work) and negative cases (what should be prevented)

### Formatting Acceptance Criteria

**Use bullet lists:**
```markdown
## Acceptance Criteria
* First criterion
* Second criterion
    * Nested detail for second
    * Another nested detail
* Third criterion
```

**Specify testing scenarios:**
```markdown
## Acceptance Criteria
* ASSUME - a pre-seeded local database with test data
* When a user hits the endpoint, X should happen
    * The system performs Y using Z
    * Each request is validated
* After completing the operation, A should be true
```

**For multi-step workflows:**
```markdown
## Acceptance Criteria
* User able to perform step 1
* User able to perform step 2
* User able to perform step 3
* Demonstrate end-to-end workflow completion
```

### Optional vs. Required Criteria

**Mark optional items:**
```markdown
* Required criterion
* Another required criterion
* OPTIONAL: Provide a "force" option to skip manual approval
```

## Issue Types and Patterns

### Bug Reports

**Structure:** Situation + Request + Acceptance Criteria

**Situation should include:**
- What is broken
- How it manifests (error messages, logs, unexpected behavior)
- Impact or consequences
- Steps to reproduce if applicable

**Example pattern:**
```markdown
## Description
Image build for the Ruby Workers is currently failing because [reason].
See PR: [link]

Logs:
```
[error output]
```

## Acceptance Criteria
* [What should be fixed]
```

### Feature Requests / Tasks

**Structure:** Situation + Request + Acceptance Criteria

**Situation should include:**
- Current limitations or gaps
- Why this feature is needed
- User impact or use cases

**Request should include:**
- Clear statement of desired functionality
- May reference similar features or approaches

**Example pattern:**
```markdown
## Situation
Currently, consumers interact with X using Y.  This has some consequences - Z.
We should utilize W instead.

## Request
Add a [new capability] so consumers can [achieve outcome].

## Acceptance Criteria
* [Specific functional requirement]
* [Another requirement with details]
    * [Sub-requirement]
* [Testing or documentation requirement]
```

### Enhancement Tracking

**Structure:** Description + Related Tasks OR just a list

**Use for:**
- Collecting related improvement ideas
- Tracking V2 feature sets
- Ongoing refinement areas

**Example:**
```markdown
## Description
This task is to capture ideas for improvements to the `config-*` commands.

* `config-list`
    * Filtering config by version
    * Limiting responses
* `config-pull`
    * Pull both capture and viewer simultaneously

## Related Tasks
* [link]
* [link]
```

## Working with Templates

Many repositories have issue templates. When templates exist:

1. **Use the template structure** - Don't fight it
2. **Apply these preferences within template constraints:**
   - Maintain objective tone
   - Provide substantial context
   - Ensure acceptance criteria are specific and testable
   - Use inline code and links appropriately
3. **Fill all template sections** - Don't leave placeholders
4. **Add optional sections** if they add value (Related Tasks, Notes, etc.)

## Title Length and Formatting

**Keep titles concise:**
- Aim for under 80 characters (including tag)
- Summarize the core issue, not implementation details

**Use backticks for technical terms:**
- ✅ `` `cluster-destroy` hangs on Capture ASG deletion``
- ✅ `` `config-update` can deploy a specific `--config-version` ``

**Avoid redundant prefixes:**
- ❌ "Issue with cluster-destroy hanging"
- ✅ "cluster-destroy hangs on Capture ASG deletion"

## Examples

### Good Example: Task with Clear Structure

```markdown
[TASK] Create Summarization Activity

## Situation
Per the latest commit on the Summarization workflow (see: [PR link]), we have a Workflow that will be kicked off when a message is sent to a locally running instance. However, the stubbed summary is the same for every patient and message sent.

## Request
Enable automated summary generation for the patient message history and context.

## Acceptance Criteria
* ASSUME - a pre-seeded local database with test data
* When a user hits a locally-running app with a message, a summary appears
    * Summary generation is performed using OpenAI and Langchain
    * Summary generation is single-turn
    * API Key is safely piped via ENV variables
    * Works when running as: loose application, standalone container, via Helm Chart
* After generating the summary, validation occurs and exceptions thrown on failure
* Unit tests added with mocked inference API
* README(s) updated for any additional setup steps
```

### Good Example: Bug Report

```markdown
[BUG] Ruby Worker image build failing due to missing RBI generation

## Description
Image build for the Ruby Workers is currently failing because we automated RBI creation for protobuf-generated types for loose processes, but did not update the image build process. See PR: [link]

Logs:
```
[full error output with stack trace]
```

## Acceptance Criteria
* Image build completes successfully
* RBI generation works in both local and container contexts
```

### Good Example: Simple Enhancement

```markdown
Make VPC Flow Logs optional

## Description
Currently, VPC Flow logs are enabled by default for the Capture and Viewer VPCs with 10 year retention. This can get expensive. We should make this optional.

## Acceptance Criteria
* Flow logs and retention period optional/configurable
```

### Anti-Pattern: Vague Request

```markdown
Fix the build

## Description
The build is broken and we need to fix it.

## Acceptance Criteria
* Build works
```

**Problems:**
- No context about what is broken or why
- No technical details (error messages, logs)
- Acceptance criteria is not specific or testable

### Anti-Pattern: Implementation Prescription

```markdown
Refactor authentication to use OAuth2 library

## Description
We should refactor the authentication code to use the OAuth2 library instead of our custom implementation.

## Acceptance Criteria
* Code uses OAuth2 library
```

**Problems:**
- Prescribes implementation (how) instead of describing need (what/why)
- No explanation of why change is needed
- No user-facing or technical justification
- Doesn't describe actual requirements

**Why this is problematic:**
- Implementation may change by the time issue is worked
- Better solutions may exist that weren't considered during initial analysis
- Issue becomes a TODO list instead of a problem definition
- Reduces implementer's creative problem-solving and agency
- Creates false sense that solution is validated when only problem has been identified

**Better version:**
```markdown
Improve authentication security and maintainability

## Situation
The custom authentication implementation has known security gaps and requires significant maintenance. Industry-standard OAuth2 would provide better security guarantees and reduce maintenance burden.

## Request
Update the authentication system to meet current security standards and reduce maintenance overhead.

## Acceptance Criteria
* Authentication meets OWASP security guidelines
* Supports standard OAuth2 flows (authorization code, refresh tokens)
* Reduces custom auth code by at least 50%
* Existing users can authenticate without migration
* Documentation updated
```

