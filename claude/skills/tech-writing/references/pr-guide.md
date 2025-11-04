# Pull Request Writing Guide

This document contains line-item preferences for creating GitHub pull request descriptions and similar code review requests. When writing a PR, apply these preferences consistently.

## Analysis Source

This guide was created by analyzing 9 pull requests authored in the time-cop repository (July-October 2025). The repository introduced a PR template in October 2025, with preferences weighted toward post-template patterns as they represent the evolved approach while maintaining consistency with pre-template style.

## Core Principles

### Comprehensive Context
Pull requests provide substantial technical detail enabling reviewers to understand the changes, their rationale, and verification approach without requiring synchronous communication.

### Objective Then Personal
Use third-person objective tone when describing changes and rationale. Use first-person when describing testing actions taken ("I ran...", "I confirmed...").

### Evidence-Based Verification
Testing sections include concrete evidence that changes work—command output, screenshots of dashboards, workflow results—not just assertions.

## Standard PR Structure

Use this structure for all pull requests:

```markdown
## Description
[Context explaining why changes were needed and what was accomplished]

## Changes
* [First notable change with technical details]
* [Second notable change]
* [Additional changes as needed]

## Relevant Issues
[Links to related GitHub issues or PRs]

## Commit Checklist
- [ ] [Required verification step]
- [ ] [Another verification step]

## Testing
[Detailed explanation of how changes were tested with evidence]
```

### Description Section

**Purpose:** Explain why the work was needed and what was accomplished.

**Characteristics:**
- Third-person objective tone
- Provides context and rationale for the changes
- Focuses on the WHAT and WHY, not implementation details
- May reference related work, earlier attempts, or design decisions
- Can be single paragraph or bullet list depending on complexity

**Example patterns:**
- "Centralized proto generation across the repo in order to reduce redundant and conflicting behavior."
- "This is a re-commit of an earlier PR with improperly signed commits. It fixes a bug in..."
- "Added Protobuf as a cross-language mechanism for defining Temporal Activities."

### Changes Section

**Purpose:** Itemize the notable modifications made in this PR.

**Formatting:**
- Bullet list of specific changes
- Use inline code (backticks) for technical terms
- Include file paths, command names, function names, service names
- Focus on WHAT changed, providing just enough detail for context
- List changes in logical order (not necessarily chronological)

**Example patterns:**
- "Added `CLAUDE.md` file to provide coding agent context"
- "Converted the Ruby Worker's image build to multi-stage, reducing the final image size by excluding the build toolchain"
- "Updated the Ops Dashboards to display these gauges as Avg/Min/Max"

### Relevant Issues Section

**Purpose:** Link related GitHub issues, PRs, or external references.

**Formatting:**
- Bare GitHub URLs for issues and PRs
- One link per line with bullet point
- Include both issues this PR closes and related context

**Example:**
```markdown
## Relevant Issues
* https://github.com/owner/repo/issues/15
* https://github.com/owner/repo/pull/29
```

### Commit Checklist Section

**Purpose:** Define verification steps that must be completed before merging.

**Characteristics:**
- Checkbox format using `- [ ]` or `- [X]`
- Specific, testable verification steps
- Project-specific validation requirements
- Check boxes when completed, include evidence in Testing section

**Example:**
```markdown
## Commit Checklist
- [X] I have run the Helm Chart tests from a clean state w/ `make clean && make deploy`
- [X] I have confirmed the Temporal workflows kicked off by the Helm Chart tests all succeeded and have attached evidence below in the `Testing` section.
```

### Testing Section

**Purpose:** Convince the reviewer that changes (1) achieve their objective and (2) don't break anything else.

**Characteristics:**
- Detailed explanation of testing approach
- First-person voice ("I ran...", "I tested...", "I confirmed...")
- Actual commands executed (in code blocks)
- Output of important commands (in code blocks)
- Screenshots showing verification
- Multiple testing levels when applicable (unit, integration, end-to-end)

**Structure patterns:**
```markdown
## Testing
* [High-level testing approach - what was tested]
* [Specific test commands or procedures]
* [Results verification]

[Command blocks showing what was run]
[Output blocks showing results]
[Screenshots showing visual verification]
```

**Example:**
```markdown
## Testing
* Ran all three worker types (python, ruby, dispatcher) locally and in loose containers.
* Executed `make cleanup && make deploy` and confirmed the Temporal workflows were successful

[command output showing test results]

<img width="2559" height="532" alt="Screenshot 2025-10-28 at 10 34 42 AM" src="..." />
```

## Visual Elements in PRs

### When to Include Screenshots

Include screenshots to provide visual evidence that changes work correctly. Common scenarios:

- **Dashboard/UI changes:** Show the new or modified interface
- **Workflow verification:** Show successful execution in monitoring tools
- **Before/after comparisons:** Demonstrate improvement or fix
- **Test results:** Show passing tests or successful deployments
- **Multiple related views:** Show different aspects of the same feature

### Screenshot Guidelines

**Placement:**
- Always in the Testing section
- After textual explanation of what was verified
- Group related screenshots together

**Labeling:**
- Use backtick-enclosed labels before screenshots to identify what they show
- Labels should be descriptive: `` `Python Worker` ``, `` `Ruby Ops Dashboard` ``
- For multiple screenshots, use consistent labeling convention

**Format:**
```markdown
`Label describing screenshot`
<img width="2559" height="1336" alt="Screenshot 2025-07-29 at 5 33 26 AM" src="..." />
```

**Alt text:**
- Use descriptive timestamps: "Screenshot YYYY-MM-DD at HH:MM:SS AM/PM"
- Provides context about when verification occurred

**What to show:**
- Full desktop screenshots showing complete context
- Dashboard views with relevant metrics/status visible
- UI states that prove functionality works
- Test output or workflow execution results
- Error states if demonstrating a fix

### Example Screenshot Usage

Simple case (single screenshot):
```markdown
* Confirmed the test Workflows were successful in the Temporal dashboard
<img width="2473" height="1292" alt="Screenshot 2025-10-02 at 9 52 51 AM" src="..." />
```

Complex case (multiple related screenshots):
```markdown
* Reviewed the Ops Dashboards to see the new metrics/graphs and compared to Temporal Dashboard

`Python Worker`
<img width="2557" height="1336" alt="Screenshot 2025-07-31 at 9 31 16 AM" src="..." />

`Ruby Worker`
<img width="2555" height="1335" alt="Screenshot 2025-07-31 at 9 31 06 AM" src="..." />
```

Organized testing (multiple verification types):
```markdown
* Reviewed the Grafana Dashboards for the Python and Ruby Workers

`Python Ops Dashboard`
<img width="2559" height="1336" alt="..." src="..." />

`Ruby Ops Dashboard`
<img width="2557" height="1333" alt="..." src="..." />

* Checked in the Grafana Loki Dashboard for the raw logs I expected:

`Mixed Workflow Test logs`
<img width="2555" height="1332" alt="..." src="..." />

`Python Workflow Test logs`
<img width="2555" height="1331" alt="..." src="..." />
```

## Writing Style

### Voice and Tone

**Description and Changes sections - use third-person:**
- ✅ "Centralized proto generation across the repo..."
- ✅ "Added Protobuf as a cross-language mechanism..."
- ✅ "Fixed a bug where we were not getting..."
- ❌ NOT "I centralized..." or "We added..."

**Testing section - use first-person:**
- ✅ "I ran the Helm Chart tests..."
- ✅ "I confirmed the workflows were successful..."
- ✅ "I reviewed the dashboards..."
- ❌ NOT "The tests were run..." or "Dashboards were reviewed..."

**Maintain objectivity:**
- Focus on technical facts and verification
- Avoid marketing language or superlatives
- Present clear cause-and-effect relationships
- Explain trade-offs when relevant

### Technical Detail Guidelines

**Code blocks for commands:**
```markdown
```bash
make cleanup && make deploy
```
```

**Inline code for technical terms:**
- Commands: `` `make deploy` ``, `` `temporal workflow start` ``
- File paths: `` `.agents/README.md` ``, `` `protos/` ``
- Functions/methods: `` `WorkflowDemoMixed` ``
- Service names: `` `protoc-gen-rbi` ``
- Configuration values: `` `latest` ``

**Output blocks for results:**
```markdown
```
NAME: time-cop-stack
LAST DEPLOYED: Tue Oct 28 09:50:36 2025
STATUS: deployed
Phase: Succeeded
```
```

### Completeness vs. Brevity

**Include enough detail to:**
- Understand why changes were made
- Identify what specifically changed
- Verify changes work correctly
- Assess impact on existing functionality

**Omit:**
- Implementation minutiae (that's what code review is for)
- Obvious information reviewers already know
- Speculation about future work unrelated to this PR
- Lengthy justifications for standard practices

## Working with Templates

When a repository has a PR template:

1. **Follow the template structure** - Use the sections it defines
2. **Apply these preferences within template constraints:**
   - Maintain objective tone in description sections
   - Provide substantial technical detail
   - Include concrete testing evidence
   - Use inline code and proper formatting
3. **Don't leave template placeholders** - Replace all `< >` placeholders with actual content
4. **Add optional sections if valuable** - Notes, additional context, related work

When template sections differ from these preferences, prioritize the template structure while applying the writing style and completeness principles defined here.

## Examples

### Good Example: Post-Template PR with Multiple Changes

```markdown
## Description
Centralized proto generation across the repo in order to reduce redundant and conflicting behavior. The best place to understand the changes made, quickly, are the `.agent` plan and implementation files (see Changes below).

## Changes
* Added a `CLAUDE.md` file to provide coding agent context
* Added a `.agents/` directory to create a place for instructions for how humans and AI should collaborate when making changes in the repo
* Created an implementation plan w/ Claude Code for the centralization feature (see `.agents/tasks/centralize_protobuf_generation_plan.md`)
* Added `protos/` directory to contain the centralized generation behavior
* Made the Dispatcher and Python images multi-stage to reduce image size

## Relevant Issues
* https://github.com/scriptdash/time-cop/issues/15

## Commit Checklist
- [X] I have run the Helm Chart tests from a clean state w/ `make clean && make deploy`
- [X] I have confirmed the Temporal workflows kicked off by the Helm Chart tests all succeeded

## Testing
* Ran all three worker types (python, ruby, dispatcher) locally and in loose containers.
* Executed `make cleanup && make deploy` and confirmed the Temporal workflows were successful

[command output]

<img width="2559" height="532" alt="Screenshot 2025-10-28 at 10 34 42 AM" src="..." />
```

### Good Example: Bug Fix with Visual Evidence

```markdown
## Description
This is a re-commit of an earlier PR with improperly signed commits. It fixes a bug in the Ruby Worker image build process caused by a missing protoc plugin.

## Changes
* Add `protoc-gen-rbi` plugin to the Ruby Worker Containerfile so the image build works like local builds
* Converted the Ruby Worker's image build to multi-stage, reducing the final image size by excluding the build toolchain

## Relevant Issues
* https://github.com/scriptdash/time-cop/issues/28
* https://github.com/scriptdash/time-cop/pull/29

## Testing
* Ran `make cleanup && make deploy` successfully
* Confirmed the test Workflows were successful in the Temporal dashboard
<img width="2473" height="1292" alt="Screenshot 2025-10-02 at 9 52 51 AM" src="..." />
```

### Good Example: Complex Testing with Multiple Screenshots

```markdown
## Description
* Updated the Python and Ruby Workers to emit Prometheus custom histograms for the duration of executed Workflows and Activities.
* Updated the Ops Dashboards to display these gauges as Avg/Min/Max.
* There's still room for improvement in these dashboards but I'd prefer to revisit later rather invest more time now; we're at the 80/20 point on this one IMO.

## Testing
* Repeatedly ran make deploy or make update-dashboards, make expose, kicked off workflows manually using the Temporal CLI, and then make cleanup.
* Reviewed the Ops Dashboards to see the new metrics/graphs and compared to Temporal Dashboard

`Python Worker`
<img width="2557" height="1336" alt="Screenshot 2025-07-31 at 9 31 16 AM" src="..." />

`Ruby Worker`
<img width="2555" height="1335" alt="Screenshot 2025-07-31 at 9 31 06 AM" src="..." />
```
