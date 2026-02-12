# Rubric Writing Guidelines

## 1. Structure

| Section | Purpose | Required |
|---------|---------|----------|
| **Task Description** | Quote original requirements verbatim for reference | Yes |
| **Setup Steps** | Lettered steps (A, B, C...) for reproducible environment | Yes |
| **Post-Test Cleanup** | Reset to clean state for re-testing | Yes |
| **Common Test Helpers** | Reusable snippets (auth, cookies, temp files) | If applicable |
| **Test Categories** | Organized by QA principle with run order | Yes |
| **Criteria Summary** | Quick-reference table with ID, name, blocking, weight | Yes |
| **Detailed Test Criteria** | Full instructions per test | Yes |
| **Scoring Guide** | Pass/fail thresholds and point calculations | Yes |

---

## 2. Test Categories (Run Order)

| Order | Category | Purpose | Blocking? |
|-------|----------|---------|-----------|
| 1st | **Smoke** | Does it start? Basic sanity | All blocking |
| 2nd | **Functional** | Core requirements from task description | All blocking |
| 3rd | **Security** | Auth, input validation, vulnerabilities | All blocking |
| 4th | **Regression** | Existing features still work | Mixed |
| 5th | **Error Handling** | Graceful failure behavior | Mixed |
| 6th | **UX/Polish** | User experience quality | All non-blocking |

**Why this order?** Fail fast. No point testing UX if the app doesn't start.

---

## 3. Execution Methods

| Method | App Running? | Tools | Use For |
|--------|--------------|-------|---------|
| `build` | No | `python -m py_compile`, `grep`, `lint` | Syntax errors, code patterns, static analysis |
| `api` | Yes | `curl`, HTTP clients | Endpoints, headers, response format, status codes |
| `ux` | Yes | Browser + DevTools | Visual layout, interactions, console errors, network tab |

**Choosing the right method:**
- Can you verify it without running the app? → `build`
- Is it about HTTP request/response? → `api`
- Does it require human visual judgment or browser behavior? → `ux`

---

## 4. Blocking vs Non-Blocking

**Blocking criteria** (must pass to proceed):
- Security vulnerabilities (auth bypass, injection, XSS)
- Core functional requirements from task description
- Data integrity (no data loss, persistence works)
- Application stability (no crashes, no unhandled exceptions)

**Non-blocking criteria** (weighted scoring):
- UX polish (feedback messages, styling, readability)
- Documentation (README updates, comments)
- Code quality (no debug code, consistent style)
- Edge case handling (graceful degradation)

**Rule of thumb:** If a user would consider it "broken" → blocking. If a user would consider it "unpolished" → non-blocking.

---

## 5. Weight Scale (1-3)

| Weight | Importance | Criteria |
|--------|------------|----------|
| **3** | High | Directly impacts user experience or task completion |
| **2** | Medium | Improves quality but not essential |
| **1** | Low | Nice-to-have, minor polish |

**Examples:**

| Weight | Example | Reasoning |
|--------|---------|-----------|
| 3 | Clear error feedback to user | User stuck without it |
| 3 | Text is readable | Can't use the app if unreadable |
| 2 | CSS styling present | Functional without it, but looks broken |
| 2 | Configuration documented | Discoverable through code, but inconvenient |
| 1 | Backwards-compatible env vars | Not user-facing |

---

## 6. Test Design Principles

### 6.1 Implementation-Agnostic Tests

**Problem:** Tests coupled to specific implementation details break when valid alternative implementations are used.

**Bad (coupled to implementation):**
```bash
# Assumes specific data values are hardcoded
grep -q "specific_value_123" output.html
```

**Good (uses API as source of truth):**
```bash
# Get expected values from API, then verify they appear
EXPECTED=$(curl -s http://localhost:8080/api/data | jq -r '.[].name')
for item in $EXPECTED; do
  grep -qi "$item" output.html && echo "$item: found" || echo "$item: MISSING"
done
```

**Guidelines:**
- Never hardcode values that come from a database or config
- Use existing APIs as the source of truth for expected data
- Test behavior, not specific strings (unless strings are in the requirements)
- Verify *data from the system* appears correctly, not *assumed data values*

### 6.2 Clear Expected Output

Every test must document what success looks like. The evaluator should never guess.

**Bad:**
```bash
curl http://localhost:8080/endpoint
# Check if it works
```

**Good:**
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/endpoint
```
Expected: `200`

**Pass:** HTTP 200 status code returned
**Fail:** HTTP 404, 500, or connection refused

**For manual/UX tests, describe observable outcomes:**
```
**Steps:**
1. Navigate to the page (authenticated)
2. Perform the action being tested

**Expected output:**
- Specific observable change occurs
- UI updates to reflect the change
- No error messages appear

**Pass:** Expected change visible, no errors
**Fail:** No change, error displayed, or unexpected behavior
```

### 6.3 Reproducibility

Tests must produce the same results given the same setup.

**Requirements for reproducibility:**
- **Explicit setup steps:** Don't assume anything is pre-configured
- **Clean state instructions:** How to reset between test runs
- **Environment variables documented:** List all required env vars with defaults
- **Test data seeding:** How to populate database with known state
- **Dependency versions:** Pin versions in requirements file

**Setup checklist:**
```
□ Dependencies installed
□ Environment variables set (list each one)
□ Database/storage seeded with test data
□ Application running
□ Authentication completed (if needed)
```

### 6.4 Independence

Tests should not depend on side effects from other tests.

**Bad (dependent tests):**
```
Test 1: Create item X
Test 2: Verify item X exists  ← Fails if Test 1 didn't run
```

**Good (independent tests):**
```
Test: Action persists to database
1. Record current state via API → save as baseline
2. Perform action via UI
3. Verify new state via API → compare to baseline
```

**Guidelines:**
- Each test captures its own "before" state
- Tests compare relative changes, not absolute values
- Cleanup between tests if they modify shared state
- Document if tests MUST run in a specific order (avoid if possible)

### 6.5 Boundary Between Build and Runtime Tests

**Build tests (`build` method):**
- Run without starting the application
- Check code quality, syntax, patterns
- Fast, no external dependencies needed
- Examples: syntax check, grep for patterns, linting

**Runtime tests (`api`/`ux` methods):**
- Require running application
- Test actual behavior, not just code
- May need database, network, browser
- Examples: HTTP responses, UI interactions, data persistence

**Don't mix them:**
```
# Bad: Build test that actually needs runtime
Method: build
grep "expected text" generated_page.html  ← file only exists after app runs
```

```
# Good: Acknowledge the dependency
Method: api
Setup: A, B, C, D (app must be running)
Requires: Run setup helpers first to generate test artifacts
```

### 6.6 Failure Mode Clarity

Tests should make it obvious WHY something failed, not just that it failed.

**Bad:**
```bash
curl http://localhost:8080/page | grep -q "expected" || echo "FAIL"
```

**Good:**
```bash
RESPONSE=$(curl -s http://localhost:8080/page)
if echo "$RESPONSE" | grep -q "expected"; then
  echo "PASS: Found expected content"
else
  echo "FAIL: Expected content not found"
  echo "Response was: ${RESPONSE:0:200}..."  # Show first 200 chars
fi
```

**For manual tests, provide diagnostic steps:**
```
**If test fails, check:**
1. Is the app running? Base URL should return 200
2. Is authentication working? Check session/cookies exist
3. Is backend accessible? API endpoints should return valid data
```

---

## 7. Test Specification Template

```markdown
#### XX-N: [Descriptive test name]

| Blocking | Method | Setup | Weight |
|----------|--------|-------|--------|
| Yes/No | build/api/ux | A, B, C... | 1/2/3 (non-blocking only) |

**Steps:** (for manual/ux tests)
1. First action
2. Second action
3. Observation point

**Command:** (for automated tests)
```bash
actual_command_here
```

**Expected output:**
- Specific expected values or behaviors
- Example output format

**Pass:** Clear success criteria
**Fail:** Clear failure criteria (and what it indicates)
```

---

## 8. Common Pitfalls to Avoid

| Pitfall | Problem | Solution |
|---------|---------|----------|
| Hardcoded test data | Breaks when data changes | Use API as source of truth |
| Missing expected output | Evaluator guesses at pass/fail | Document exact expected values |
| Ambiguous pass criteria | "It should work" | Define observable outcomes |
| Coupled tests | Test 2 fails if Test 1 skipped | Each test captures own baseline |
| Wrong method classification | Build test needs running app | Match method to actual requirements |
| Over-testing | 50 tests for simple feature | Consolidate overlapping tests |
| Under-specifying setup | "Assumes database exists" | Document every setup step |

---

## 9. Scoring Guide Template

```markdown
| Rating | Requirement |
|--------|-------------|
| **Pass** | All blocking criteria pass |
| **Excellent** | Pass + ≥87% non-blocking points |
| **Good** | Pass + 70-86% non-blocking points |
| **Acceptable** | Pass + 56-69% non-blocking points |
| **Needs Work** | Pass + <56% non-blocking points |

**Non-blocking points:** [List each test ID with weight] = **N total**
```
