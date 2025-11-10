# Comparison: Old vs. New Issue Draft Approach

## Key Differences

### 1. **Investigation Process References**

**Old approach:**
- References PR #52 review comment and discussion URL
- Mentions "investigation reveals additional opportunities"
- Includes "Investigation identified specific issues in two files"
- References related issues by number

**New approach:**
- No mention of investigation process or research artifacts
- No PR review comment citations
- No "investigation revealed" language
- Focuses purely on observable problems in the system

**Why this matters:** The new approach is standalone - anyone can understand the problem without access to PR history or investigation notes.

---

### 2. **Technical Context Presentation**

**Old approach:**
```markdown
### Current Architecture

The Summary Generator expert follows the LangChain Expert-Task-Tool pattern:
1. **Prompt template** provides instructions to the LLM
2. **Pydantic schemas** define structured output format
...
```

**New approach:**
```markdown
**Example 1: Redundant Sorting Instructions**

The prompt instructs the LLM to sort pharmacy actions by date:
[concrete code example showing the problem]

However, Python code already re-sorts the LLM's output...
```

**Why this matters:** Old approach explains architecture (background knowledge). New approach shows concrete examples of the problem in action.

---

### 3. **Solution Prescription vs. Problem Description**

**Old approach - Prescriptive:**
```markdown
## Opportunities Identified

### Priority 1: Remove Redundant Sorting Instruction (HIGH)
**File**: `prompting/summarizer_templates.py:60`
**Recommendation**: Remove "sorted by date" from line 60 of the prompt template.

### Priority 2: Fix Docstring/Code Mismatch (HIGH)
**File**: `summary_generator_tool_def.py:110`
**Recommendation**: Determine correct sort order and update either docstring or code.
```

Creates a prioritized TODO list with specific files, line numbers, and implementation steps.

**New approach - Problem-focused:**
```markdown
**Example 1: Redundant Sorting Instructions**
[Shows WHAT is wrong]

**Example 2: Error-Prone Field Navigation**
[Shows WHAT is wrong]

**Example 3: Documentation vs. Implementation Mismatch**
[Shows WHAT is wrong]

**Impact:**
[Shows WHY it matters]
```

Describes problems with evidence, explains impact, leaves solution open.

---

### 4. **Acceptance Criteria Structure**

**Old approach:**
```markdown
### Minimum Viable (Must Have)
- [ ] Prompt template no longer instructs LLM to sort pharmacy actions (Priority 1)
- [ ] Docstring and code agree on sort order direction (Priority 2)
- [ ] Unit tests verify sorting behavior matches documentation

### Recommended (Should Have)
- [ ] Events are pre-processed to emphasize `event_type` field (Priority 3)
- [ ] Prompt warnings about event_type vs resource_type confusion are removed

### Optional (Nice to Have)
- [ ] Timestamps are pre-formatted in event JSON (Priority 4)
```

Acceptance criteria are implementation steps tied to the priorities above. Creates a checklist.

**New approach:**
```markdown
**Must have:**
* Prompt no longer instructs LLM to perform operations that Python handles deterministically
* Function docstrings accurately describe implemented behavior
* Existing integration tests pass without modification
* Summary generation quality remains at current baseline

**Should have:**
* Token usage for summary generation reduced by at least 5%
* Unit tests verify deterministic operations are handled by Python code

**Nice to have:**
* Prompt complexity reduced as measured by character count
* Error rate for incorrect event_type usage reduced
```

Acceptance criteria define **outcomes**, not implementation steps. No mention of specific files or priorities.

---

### 5. **File Path References**

**Old approach:**
- "## Opportunities Identified" section includes 4 subsections with explicit file paths
- "## Technical Context" section has "Files to Modify" with line numbers
- "Related Files" section lists secondary files to reference

**New approach:**
- ZERO file paths in the issue body
- ZERO line number references
- Code examples shown inline without attribution

**Why this matters:** Old approach assumes implementer will follow exact file/line prescription. New approach trusts implementer to find the relevant code based on problem description.

---

### 6. **Testing Strategy Inclusion**

**Old approach:**
Includes extensive "## Testing Strategy" section:
```markdown
**Unit tests**:
- Verify `_parse_pharmacy_action_items` sorts correctly
- Verify prompt template does not contain "sorted by date"

**Integration tests**:
- Existing Helm chart tests should pass
- Temporal workflows should succeed

**Validation**:
- Compare token usage before/after (expect 5-10% reduction)
```

**New approach:**
Testing strategy embedded in acceptance criteria:
```markdown
**Must have:**
* Existing integration tests pass without modification
* Summary generation quality remains at current baseline (manual spot-check)

**Should have:**
* Unit tests verify deterministic operations are handled by Python code
```

**Why this matters:** Old approach prescribes HOW to test. New approach defines WHAT should be verified as outcomes.

---

### 7. **Benefits Section**

**Old approach:**
Has explicit "## Benefits" section with subsections:
```markdown
### Reliability
- Reduces LLM cognitive load by ~5-10%
- Eliminates known failure mode

### Performance
- Reduces token usage by ~160-560 tokens
- Slightly faster LLM inference

### Maintainability
- Fixes documentation bug
- Clearer separation of concerns
```

**New approach:**
Benefits integrated into "Situation" section as **Impact**:
```markdown
**Impact:**
- Estimated 5-10% increase in LLM errors due to field confusion
- Approximately 10% unnecessary token usage (150-500 tokens per summary)
- Reduced maintainability from contradictory documentation
```

**Why this matters:** Old approach sells the solution. New approach explains the problem's consequences.

---

## Summary of Philosophy Shift

| Aspect | Old Approach | New Approach |
|--------|-------------|--------------|
| **Orientation** | Solution-focused (HOW to fix) | Problem-focused (WHAT is wrong) |
| **Structure** | Investigation findings → Opportunities → Implementation | Problem examples → Impact → Desired outcome |
| **Prescription** | Explicit (files, lines, priorities) | Implicit (outcomes, not steps) |
| **Context** | Architectural background + process | Concrete examples + impact |
| **Acceptance Criteria** | Implementation checklist | Outcome verification |
| **Assumptions** | Implementer follows prescription | Implementer understands problem and chooses approach |
| **Longevity** | Brittle (file paths may change) | Durable (problem description remains valid) |
| **Agency** | Low (step-by-step TODO) | High (problem + constraints, implementer decides) |

---

## What Makes the New Approach Better

### 1. Standalone Readability
Anyone reading the new issue can understand the problem without:
- Access to codebase
- Knowledge of investigation process
- PR history or review comments
- Research artifacts

### 2. Preserves Implementer Agency
The old approach essentially says: "I've investigated and here's the solution - just execute these 4 priorities."

The new approach says: "Here are 3 concrete examples showing a pattern of problems. The impact is X. Make it so the impact doesn't happen anymore."

### 3. Survives Codebase Evolution
File paths and line numbers become stale quickly. Problem descriptions remain relevant.

### 4. Focuses on Outcomes
New approach emphasizes what success looks like ("token usage reduced by 5%", "integration tests pass") rather than implementation steps.

### 5. More Professional Tone
Old approach reads like internal research notes. New approach reads like a professional issue any team member could understand and act on.

---

## What Was Lost (Intentionally)

The new approach deliberately **omits**:

1. **Architectural context** - LangChain Expert-Task-Tool pattern explanation
2. **Related files** - List of secondary files to reference
3. **Explicit priorities** - HIGH/MEDIUM/LOW ranking of opportunities
4. **Prescriptive recommendations** - Specific code changes per opportunity
5. **Detailed testing strategy** - Explicit test cases and validation steps
6. **References section** - PR links, related issues

These omissions are **intentional**. They represent:
- Process artifacts (how we discovered this)
- Implementation guidance (how to fix it)
- Context that couples the issue to a specific moment in time

The new issue is **more abstract** and **more durable** because it describes the problem space, not the solution space.

---

## Key Lesson

The updated tech-writing guidance emphasizes:

> "Issues describe WHAT is broken and WHY it matters, not HOW to fix it. This preserves implementer agency and prevents premature optimization."

The old draft was essentially a **research report disguised as an issue**. It documented findings and recommended solutions.

The new draft is a **problem statement**. It describes what's wrong, provides concrete evidence, explains impact, and defines success criteria - then trusts the implementer to choose the best approach.
