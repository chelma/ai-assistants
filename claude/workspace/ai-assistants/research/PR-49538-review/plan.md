# Research Plan: PR #49538 Security Review

**Workspace**: scriptdash
**Project Root**: ~/workspace/claude/scriptdash
**Research Objective**: Comprehensive security review of mass hash syntax conversion commit
**Started**: 2025-12-04

## Investigation Scope

**Commit**: a4e39d0a1099b7ff62d4d25cd78182acd73f1431
**Author**: Sierra Brown <sierra@alto.com>
**Date**: Wed Dec 3 12:32:29 2025 -0800
**Message**: "feat: sc-3963 enforce hash shorthand syntax across codebase"

**Stats**:
- Files changed: 4,830 (includes numstat metadata)
- Total diff lines: 206,215
- Expected changes: +:28,362 / -:28,373 (nearly symmetric)

**Additional note from commit message**: "Also removes orphaned sig declarations found during cleanup."

## Key Questions

1. **Pattern Compliance**: Do all changes match the expected `=>` to `:` conversion pattern?
2. **Logic Preservation**: Are there any modifications beyond pure syntax conversion?
3. **Malicious Code**: Are there any backdoors, credentials, or suspicious code injections?
4. **Statistical Anomalies**: Are there outlier files with unusual change patterns?
5. **Orphaned Sig Removals**: What are the "orphaned sig declarations" and are they legitimate?
6. **Edge Cases**: Are there incorrect conversions in strings, comments, or special contexts?

## Investigation Strategy

### Phase 1: Statistical Overview
- Extract numstat for all files
- Calculate change distribution (insertions, deletions per file)
- Identify statistical outliers (>2 std dev from mean)
- Flag non-symmetric changes (insertions != deletions for hash conversion should be ~equal)

### Phase 2: Keyword Scanning
Search full diff for suspicious patterns:
- **Credentials**: password, secret, api_key, token, auth, credential
- **Execution**: eval, exec, system, backticks, %x, spawn, `
- **Network**: http://, https://, curl, wget, Net::HTTP, URI.open
- **Encoding**: base64, Base64, decode64, encode64
- **File ops**: File.write, File.delete, FileUtils.rm, chmod, chown
- **Reflection**: send, instance_eval, class_eval, define_method
- **Suspicious**: lambda, proc, const_get, method_missing

### Phase 3: Chunked Diff Analysis
- Read diff in ~1500 line chunks
- Verify each file's changes match expected pattern
- Flag ANY deviations for detailed review
- Focus on exception-based reporting

### Phase 4: "Orphaned Sig" Investigation
- Identify all lines removing `sig` declarations
- Verify they are truly orphaned (no corresponding method)
- Ensure no legitimate signatures removed

### Phase 5: Spot-Check Sampling
- Randomly sample 20 files across directories
- Manually verify conversions are purely syntactic
- Check for any subtle logic changes

## Expected Deliverables

1. **summary.md** - Executive summary with risk assessment
2. **statistics.txt** - Statistical analysis of changes
3. **pattern_violations.md** - Files with unexpected patterns (or "NONE FOUND")
4. **suspicious_code.md** - Malicious/suspicious code (or "NONE FOUND")
5. **outliers.md** - Statistical outliers requiring explanation (or "NONE FOUND")
6. **orphaned_sigs.md** - Analysis of removed sig declarations
7. **sample_analysis.md** - Spot-check results

## Success Criteria

- All 4,830 files accounted for
- Exception-based findings (only deviations documented)
- Clear severity ratings for any issues
- Statistical analysis complete
- Orphaned sig removals validated
- Spot-check sampling performed (n=20)
