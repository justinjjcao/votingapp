# Code Review Rubric for `/votes` Page Implementation

## Task Description

> Create a new Flask route in a dedicated web page at the following path: "/votes". This page should be password protected. The page will show a table (in a grid format) with the four restaurants and the vote for each restaurant. The page will also allow a user to vote for the restaurant of their choosing. This page should be modern, rich and following all the latest standards of web user interface developments.

---

## Setup Steps

### Setup A: Environment Preparation
```bash
cd /workspace
pip install -r requirements.txt
```

### Setup B: AWS Credentials
```bash
# Refresh AWS credentials (if using aws-refresh tool)
aws-refresh <account-id>

# Verify credentials
aws sts get-caller-identity
```

### Setup C: DynamoDB Backend
```bash
# Check if table exists
aws dynamodb describe-table --table-name votingapp-restaurants --region us-west-2 2>/dev/null

# If table doesn't exist, create and seed it:
aws dynamodb create-table \
    --table-name votingapp-restaurants \
    --attribute-definitions AttributeName=name,AttributeType=S \
    --key-schema AttributeName=name,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-west-2

aws dynamodb wait table-exists --table-name votingapp-restaurants --region us-west-2

for restaurant in outback bucadibeppo ihop chipotle; do
    aws dynamodb put-item \
        --table-name votingapp-restaurants \
        --item "{\"name\": {\"S\": \"$restaurant\"}, \"restaurantcount\": {\"N\": \"0\"}}" \
        --region us-west-2
done
```

### Setup D: Run the Application
```bash
export DDB_AWS_REGION=us-west-2
export VOTES_PASSWORD=secret123

python3 app.py &
sleep 3

# Verify app is running
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/  # expect: 200
```

### Setup E: Browser Testing
1. Open browser with Developer Tools (F12)
2. Keep Console and Network tabs accessible

---

## Post-Test Cleanup

Run after testing is complete to reset to a clean state:

```bash
# Stop the Flask app
pkill -f "python3 app.py"

# Remove temporary files
rm -f cookies.txt votes_page.html
rm -f /tmp/votes_before.json /tmp/votes_after.json

# Delete DynamoDB table
aws dynamodb delete-table --table-name votingapp-restaurants --region us-west-2

# Wait for table deletion to complete
aws dynamodb wait table-not-exists --table-name votingapp-restaurants --region us-west-2
```

---

## Common Test Helpers

Run these once before tests to set up authentication:

```bash
# Configuration
PASSWORD=${VOTES_PASSWORD:-secret123}
BASE_URL=${BASE_URL:-http://localhost:8080}

# Clean slate
rm -f cookies.txt votes_page.html

# Authenticate and save session
curl -c cookies.txt -b cookies.txt -X POST -d "password=$PASSWORD" \
    "$BASE_URL/votes" -o /dev/null -s

# Fetch authenticated page
curl -c cookies.txt -b cookies.txt "$BASE_URL/votes" -o votes_page.html -s
```

**Expected output after authentication:**
- `cookies.txt` file created with session cookie
- `votes_page.html` contains the authenticated page content

To verify authentication worked, manually inspect `votes_page.html` - it should contain restaurant data visible only to authenticated users.

---

## Test Categories

| Category | Purpose | Run Order |
|----------|---------|-----------|
| **Smoke** | Basic sanity - does it run? | 1st |
| **Functional** | Core requirements met | 2nd |
| **Security** | Auth & vulnerability checks | 3rd |
| **Regression** | Existing features intact | 4th |
| **Error Handling** | Graceful failure behavior | 5th |
| **UX/Polish** | User experience quality | 6th |

**Execution Methods:** Each test specifies how to run it:

| Method | App Running? | Description |
|--------|--------------|-------------|
| `build` | No | Pre-deployment checks: syntax, linting, dependencies, code patterns |
| `api` | Yes | HTTP request/response testing (endpoints, headers, data) |
| `ux` | Yes | Browser-based testing (visual, interaction, DevTools console/network) |

---

## Criteria Summary

| ID | Category | Criteria | Blocking | Weight |
|----|----------|----------|----------|--------|
| **Smoke** |
| SM-1 | Smoke | Application starts without errors | Yes | - |
| SM-2 | Smoke | Route returns valid HTML with HTTP 200 | Yes | - |
| SM-3 | Smoke | No Python syntax errors | Yes | - |
| SM-4 | Smoke | Dependencies available | Yes | - |
| **Functional** |
| FN-1 | Functional | Page displays all restaurants with vote counts | Yes | - |
| FN-2 | Functional | Page provides voting mechanism | Yes | - |
| FN-3 | Functional | Table/grid format display | Yes | - |
| FN-4 | Functional | Vote persists to database and reflects on page | Yes | - |
| **Security** |
| SC-1 | Security | Unauthenticated access blocked | Yes | - |
| SC-2 | Security | Valid credentials grant access | Yes | - |
| SC-3 | Security | Invalid credentials rejected | Yes | - |
| SC-4 | Security | Password not hardcoded, input masked | Yes | - |
| SC-5 | Security | No XSS or NoSQL injection vulnerabilities | Yes | - |
| **Regression** |
| RG-1 | Regression | Existing endpoints still work | Yes | - |
| RG-2 | Regression | CORS headers present | No | 4 |
| RG-3 | Regression | No breaking env var changes | No | 3 |
| **Error Handling** |
| EH-1 | Error Handling | No browser console errors on page load | Yes | - |
| EH-2 | Error Handling | Vote action completes without errors | Yes | - |
| EH-3 | Error Handling | No unhandled exceptions (DB accessible) | No | 5 |
| EH-4 | Error Handling | Graceful error when DB unreachable | No | 4 |
| **UX/Polish** |
| UX-1 | UX/Polish | Clear feedback on failed login | No | 5 |
| UX-2 | UX/Polish | Vote button-restaurant association clear | No | 5 |
| UX-3 | UX/Polish | CSS styling and title tag present | No | 4 |
| UX-4 | UX/Polish | Text is readable | No | 5 |
| UX-5 | UX/Polish | Password configuration documented | No | 4 |
| UX-6 | UX/Polish | Code quality (no debug code, consistent style) | No | 4 |

**Totals:** 25 tests | 15 blocking | 10 non-blocking (43 pts)

---

## Detailed Test Criteria

### 1. Smoke Tests

Run these first. If any fail, stop and fix before proceeding.

#### SM-1: Application starts without errors

| Blocking | Method | Setup |
|----------|--------|-------|
| Yes | api | A, B, C, D |

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/
```
Expected: `200`

**Pass:** App running, responds to requests
**Fail:** Connection refused, HTTP 500

---

#### SM-2: Route returns valid HTML with HTTP 200

| Blocking | Method | Setup |
|----------|--------|-------|
| Yes | api | A, B, C, D |

```bash
# HTTP status (expect: 200)
curl -s -o /dev/null -w "%{http_code}" -b cookies.txt http://localhost:8080/votes

# Content type (expect: text/html)
curl -sI -b cookies.txt http://localhost:8080/votes | grep -i "content-type"

# Valid HTML structure
grep -c "<html" votes_page.html && grep -c "</html>" votes_page.html
```
Expected:
```
200
Content-Type: text/html; charset=utf-8
1
1
```

**Pass:** HTTP 200, text/html content, valid HTML tags
**Fail:** HTTP 404/500, JSON response, missing HTML structure

---

#### SM-3: No Python syntax errors

| Blocking | Method | Setup |
|----------|--------|-------|
| Yes | build | A |

```bash
python3 -m py_compile app.py && echo "PASS" || echo "FAIL"
```

**Expected output:**
```
PASS
```

**Pass:** No output from py_compile, echo shows PASS
**Fail:** SyntaxError or IndentationError printed

---

#### SM-4: Dependencies available

| Blocking | Method | Setup |
|----------|--------|-------|
| Yes | build | A |

```bash
python3 -c "import app" && echo "PASS" || echo "FAIL: Missing dependency"
```

**Expected output:**
```
PASS
```

**Pass:** Import succeeds silently, echo shows PASS
**Fail:** ModuleNotFoundError with missing package name

---

### 2. Functional Tests

Core feature requirements from the task description.

#### FN-1: Page displays all restaurants with vote counts

| Blocking | Method | Setup |
|----------|--------|-------|
| Yes | ux | A, B, C, D, E |

**Steps:**
1. Get the list of restaurants from API:
   ```bash
   curl -s http://localhost:8080/api/getvotes
   ```
2. Navigate to `/votes` in browser (authenticated)
3. Compare: does the page display each restaurant from the API with its vote count?

**Expected output:**
- API returns list of restaurants with vote counts (e.g., `[{"name": "outback", "value": 5}, ...]`)
- Page displays all restaurants from the API (names may be formatted differently)
- Each restaurant shows a numeric vote count
- Vote counts on page match the API values

**Pass:** All restaurants from API are displayed with matching vote counts
**Fail:** Missing restaurant, missing counts, or counts don't match API

---

#### FN-2: Page provides voting mechanism

| Blocking | Method | Setup |
|----------|--------|-------|
| Yes | ux | A, B, C, D, E |

**Steps:**
1. Navigate to `/votes` page (authenticated)
2. For each restaurant displayed, identify a way to vote (button, link, form, etc.)
3. Click/activate the vote control for one restaurant
4. Observe what happens

**Expected output:**
- Each restaurant has a visible vote control (button, link, or clickable element)
- Clicking the control triggers one of:
  - Page refresh with updated count
  - Inline count update (AJAX)
  - Confirmation message
  - Network request visible in DevTools

**Pass:** Each restaurant has an associated vote control that triggers an action
**Fail:** No way to vote, or vote controls don't respond

---

#### FN-3: Table/grid format display

| Blocking | Method | Setup |
|----------|--------|-------|
| Yes | ux | A, B, C, D, E |

**Steps:**
1. Navigate to `/votes` page (authenticated)
2. Observe the layout of restaurant data

**Expected output:**
- Restaurants and vote counts displayed in a structured layout:
  - Table with rows/columns, OR
  - Grid/card layout, OR
  - Flexbox arrangement with clear alignment
- Each restaurant's name, count, and vote control are visually grouped

**Pass:** Data is visually organized in rows/columns or grid structure
**Fail:** Plain unformatted text, or data displayed as a simple unaligned list

---

#### FN-4: Vote persists to database and reflects on page

| Blocking | Method | Setup |
|----------|--------|-------|
| Yes | ux | A, B, C, D, E |

**Steps:**
1. Get initial vote counts from API:
   ```bash
   curl -s http://localhost:8080/api/getvotes > /tmp/votes_before.json
   cat /tmp/votes_before.json
   ```
2. In browser: vote for any restaurant on `/votes` page. Note which one.
3. Get updated vote counts:
   ```bash
   curl -s http://localhost:8080/api/getvotes > /tmp/votes_after.json
   cat /tmp/votes_after.json
   ```
4. Refresh `/votes` page in browser

**Expected output:**
- Before: `[{"name": "outback", "value": 5}, ...]` (example)
- After: The restaurant you voted for has value increased by 1
- Browser: Refreshed page shows the new count matching API

Example diff:
```
< {"name": "outback", "value": 5}
> {"name": "outback", "value": 6}
```

**Pass:** Voted restaurant's count increased by 1 in API, page reflects new count
**Fail:** Count unchanged, or page shows stale data

---

### 3. Security Tests

Authentication and vulnerability prevention.

#### SC-1: Unauthenticated access blocked

| Blocking | Method | Setup |
|----------|--------|-------|
| Yes | ux | A, B, C, D |

**Steps:**
1. Open a fresh browser window (or clear cookies)
2. Navigate to `/votes` without logging in
3. Examine the page content

**Expected output:**
- Login form or access denied message
- No restaurant names visible
- No vote counts visible
- No voting buttons/controls visible

**Pass:** Page shows only authentication UI, no voting data exposed
**Fail:** Any restaurant names, vote counts, or voting controls visible without authentication

---

#### SC-2: Valid credentials grant access

| Blocking | Method | Setup |
|----------|--------|-------|
| Yes | ux | A, B, C, D, E |

**Steps:**
1. Open DevTools Console, clear it
2. Navigate to `/votes`, enter correct password (from `$VOTES_PASSWORD`), submit
3. Check Console and page content

**Expected output:**
- Console: No red errors
- Page: Displays all restaurants with vote counts
- Page: Shows voting controls for each restaurant
- Refresh: Page still shows data (session persists)

**Pass:** No JS errors, page shows restaurants/votes/buttons, session persists on refresh
**Fail:** JS error on submit, HTTP 500, or correct password rejected

---

#### SC-3: Invalid credentials rejected

| Blocking | Method | Setup |
|----------|--------|-------|
| Yes | ux | A, B, C, D, E |

**Steps:**
1. Open fresh incognito window
2. Navigate to `/votes`
3. Enter wrong password (e.g., `wrongpassword`), submit
4. Examine page content

**Expected output:**
- Page remains on login/auth screen OR shows error message
- No restaurant names visible
- No vote counts visible
- No voting controls visible

**Pass:** Vote data NOT visible after wrong password
**Fail:** Wrong password grants access to restaurant data

---

#### SC-4: Password not hardcoded, input masked

| Blocking | Method | Setup |
|----------|--------|-------|
| Yes | build | None |

```bash
# Password from env var (expect: match found)
grep -n "os.environ\|os.getenv" app.py | grep -i password

# Input field masked (expect: type="password")
grep -iE 'type=["\']password["\']' votes_page.html
```
Expected:
```
42:    password = os.environ.get('VOTES_PASSWORD', 'default')
<input type="password" name="password" ...>
```

**Pass:** Password from env var, input is `type="password"`
**Fail:** Hardcoded password, `type="text"` for password field

---

#### SC-5: No XSS or NoSQL injection vulnerabilities

| Blocking | Method | Setup |
|----------|--------|-------|
| Yes | build | None |

**Steps:**
1. Check for unsafe Jinja2 patterns:
   ```bash
   grep -c "| safe" templates/*.html 2>/dev/null || echo "0"
   ```
2. Check for input validation on restaurant names:
   ```bash
   grep -n "if.*restaurant.*in\|VALID_RESTAURANTS" app.py
   ```

**Expected output:**
- `| safe` count: 0 (or only used on non-user-input)
- Restaurant validation: Shows line with whitelist check like `if restaurant in VALID_RESTAURANTS`

**Pass:** Jinja2 auto-escaping (default), restaurant names validated against whitelist
**Fail:** `| safe` on user input, unvalidated input in DB queries

---

### 4. Regression Tests

Ensure existing functionality still works.

#### RG-1: Existing endpoints still work

| Blocking | Method | Setup |
|----------|--------|-------|
| Yes | api | A, B, C, D |

```bash
# Homepage
curl -s http://localhost:8080/ | grep -ci "voting"

# API getvotes - verify format and count
API_RESPONSE=$(curl -s http://localhost:8080/api/getvotes)
echo "$API_RESPONSE" | grep -o '"value"' | wc -l

# Individual vote endpoints - get restaurant names from API
RESTAURANTS=$(echo "$API_RESPONSE" | grep -oE '"name":\s*"[^"]+"' | cut -d'"' -f4)
for r in $RESTAURANTS; do
  RESP=$(curl -s "http://localhost:8080/api/$r")
  echo "$RESP" | grep -qE "^[0-9]+$" && echo "$r: OK" || echo "$r: FAIL"
done
```

**Expected output:**
```
1
4
outback: OK
bucadibeppo: OK
ihop: OK
chipotle: OK
```
(Restaurant names will match whatever is in the database)

**Pass:** Homepage contains "voting", API returns 4 restaurants with "value" keys, individual endpoints return numbers
**Fail:** Any endpoint 404/500, wrong response format, or homepage requires auth

---

#### RG-2: CORS headers present

| Blocking | Method | Setup | Weight |
|----------|--------|-------|--------|
| No | api | A, B, C, D | 4 |

```bash
curl -sI http://localhost:8080/api/getvotes | grep -i "access-control"
```
Expected: `Access-Control-Allow-Origin: *`

**Pass:** CORS header present
**Fail:** No CORS headers

---

#### RG-3: No breaking env var changes

| Blocking | Method | Setup | Weight |
|----------|--------|-------|--------|
| No | build | None | 3 |

```bash
# Hard-required vars with no default (expect: 0 - codebase uses getenv)
grep -c 'os\.environ\[' app.py || echo "0"

# Existing env vars still present (expect: >= 2)
grep -cE "DDB_AWS_REGION|DDB_TABLE_NAME" app.py

# New password var has default (expect: shows getenv with default)
grep -E 'os\.environ\.get|os\.getenv' app.py | grep -i password
```
Expected:
```
0
2
    password = os.environ.get('VOTES_PASSWORD', 'default')
```

**Pass:** No new hard-required vars, existing vars present, password has default
**Fail:** New `os.environ[VAR]` without default, existing var removed

---

### 5. Error Handling Tests

Graceful behavior under normal and failure conditions.

#### EH-1: No browser console errors on page load

| Blocking | Method | Setup |
|----------|--------|-------|
| Yes | ux | A, B, C, D, E |

**Steps:**
1. Open DevTools → Console tab → Clear
2. Open DevTools → Network tab → Check "Disable cache" → Clear
3. Navigate to `http://localhost:8080/votes`
4. Authenticate if prompted
5. Check both tabs

**Expected output:**
- Console: Empty or only info/debug messages (no red errors)
- Network: All resources return 200 (no 404/500 status codes)

**Pass:** Console has no red errors, Network has no 404/500
**Fail:** Any `Uncaught` error, any resource 404

---

#### EH-2: Vote action completes without errors

| Blocking | Method | Setup |
|----------|--------|-------|
| Yes | ux | A, B, C, D, E |

**Steps:**
1. On `/votes` page (authenticated), clear Console and Network
2. Click any vote button
3. Check Console and Network

**Expected output:**
- Console: No new red errors after click
- Network: Vote request returns 200, 302, or 303

**Pass:** No JS errors, vote request returns success status
**Fail:** JS error on click, HTTP 500 on vote

---

#### EH-3: No unhandled exceptions (DB accessible)

| Blocking | Method | Setup | Weight |
|----------|--------|-------|--------|
| No | ux | A, B, C, D | 5 |

**Steps:**
1. Make API request:
   ```bash
   curl -s http://localhost:8080/api/getvotes
   ```
2. Check application logs for exceptions

**Expected output:**
- API returns valid JSON: `[{"name": "...", "value": ...}, ...]`
- App logs: No Python tracebacks or exception messages

**Pass:** All requests succeed, no exceptions in app logs
**Fail:** Exceptions logged (even if not user-visible)

---

#### EH-4: Graceful error when DB unreachable

| Blocking | Method | Setup | Weight |
|----------|--------|-------|--------|
| No | ux | A, B, D (skip C) | 4 |

**Steps:**
1. Start app with invalid table name:
   ```bash
   export DDB_TABLE_NAME=nonexistent-table
   python3 app.py &
   sleep 3
   ```
2. Make request:
   ```bash
   curl -s http://localhost:8080/api/getvotes
   ```

**Expected output:**
- User-friendly error message, e.g., "Service unavailable" or custom error page
- NOT a raw Python traceback

**Pass:** User-friendly error message displayed
**Fail:** Raw traceback visible, `botocore.exceptions` in response

---

### 6. UX/Polish Tests

User experience and code quality (all non-blocking).

#### UX-1: Clear feedback on failed login

| Blocking | Method | Setup | Weight |
|----------|--------|-------|--------|
| No | ux | A, B, C, D, E | 5 |

**Steps:** After entering wrong password (from SC-3), check for error indication.

**Pass:** Error message visible ("Invalid password", red border, etc.)
**Fail:** No feedback, user can't tell login failed

---

#### UX-2: Vote button-restaurant association clear

| Blocking | Method | Setup | Weight |
|----------|--------|-------|--------|
| No | ux | A, B, C, D, E | 5 |

**Steps:**
1. On `/votes` page, verify each vote button is clearly associated with its restaurant (same row, labeled, or visually grouped)
2. Click a button → verify feedback (count updates, message, page refresh)

**Pass:** Clear button-restaurant association AND visible feedback
**Fail:** Ambiguous which button is for which restaurant, OR no feedback

---

#### UX-3: CSS styling and title tag present

| Blocking | Method | Setup | Weight |
|----------|--------|-------|--------|
| No | build | None | 4 |

```bash
# CSS present (expect: >= 1)
grep -ciE "<style|stylesheet|bootstrap|tailwind" votes_page.html

# Title present (expect: non-empty)
grep -oiE "<title>.+</title>" votes_page.html
```
Expected:
```
1
<title>Restaurant Votes</title>
```

**Pass:** Has CSS styling and meaningful `<title>`
**Fail:** No CSS (browser defaults), missing/empty title

---

#### UX-4: Text is readable

| Blocking | Method | Setup | Weight |
|----------|--------|-------|--------|
| No | ux | A, B, C, D, E | 5 |

**Visual check on `/votes` page:**
- Can you read restaurant names, vote counts, button labels?
- Is contrast sufficient? Font size reasonable?

**Pass:** All text legible without straining
**Fail:** Invisible text, too small, cut off

---

#### UX-5: Password configuration documented

| Blocking | Method | Setup | Weight |
|----------|--------|-------|--------|
| No | build | None | 4 |

```bash
grep -iE "password|votes_password|authentication" README.md app.py 2>/dev/null | head -5
```

**Pass:** Documentation mentions env var name, default, or setup
**Fail:** No mention of password configuration

---

#### UX-6: Code quality (no debug code, consistent style)

| Blocking | Method | Setup | Weight |
|----------|--------|-------|--------|
| No | build | None | 4 |

```bash
# Debug code (expect: 0 or only legitimate logging)
grep -cn "print(\|console.log" app.py templates/*.html 2>/dev/null

# Incomplete markers (expect: 0)
grep -cin "TODO\|FIXME\|HACK\|XXX" app.py
```

**Pass:** No debug prints, no TODO markers, consistent style
**Fail:** Debug statements left in, mixed tabs/spaces

---

## Scoring Guide

| Rating | Requirement |
|--------|-------------|
| **Pass** | All 15 blocking criteria pass |
| **Excellent** | Pass + ≥37 non-blocking points (87%+) |
| **Good** | Pass + 31-36 points (71-86%) |
| **Acceptable** | Pass + 24-30 points (56-70%) |
| **Needs Work** | Pass + <24 points (<56%) |

**Non-blocking points:** RG-2(4) + RG-3(3) + EH-3(5) + EH-4(4) + UX-1(5) + UX-2(5) + UX-3(4) + UX-4(5) + UX-5(4) + UX-6(4) = **43 total**
