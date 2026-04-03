# Lab 8 — Report

Paste your checkpoint evidence below. Add screenshots as image files in the repo and reference them with `![description](path)`.

## Task 1A — Bare agent

<!-- Paste the agent's response to "What is the agentic loop?" and "What labs are available in our LMS?" -->
The agentic loop is the fundamental cycle that autonomous AI agents follow to perceive, reason, and act. It's the core pattern that enables agents to work   
independently toward goals.

The Basic Loop


 ┌─────────────┐
 │  PERCEIVE   │ ──→ Gather information from environment
 └──────┬──────┘     (observations, user input, tool outputs)
        │
        ▼
 ┌─────────────┐
 │   REASON    │ ──→ Process information, plan next steps
 └──────┬──────┘     (analyze, decide, strategize)
        │
        ▼
 ┌─────────────┐
 │    ACT      │ ──→ Execute actions via tools
 └──────┬──────┘     (call APIs, write files, run commands)
        │
        ▼
        └──────────→ Loop back to PERCEIVE


Key Components

 1 Perceive — Observe the current state (user requests, file contents, command outputs, web results)
 2 Reason — Interpret observations, recall relevant knowledge, plan actions, evaluate options
 3 Act — Execute chosen actions through available tools (file operations, web searches, shell commands, etc.)
 4 Reflect (optional) — Evaluate outcomes, learn from mistakes, adjust strategy

Why It Matters

 • Autonomy: The loop enables agents to work without constant human guidance
 • Adaptability: Agents can respond to changing conditions and unexpected results
 • Goal-directed behavior: Each iteration moves closer to completing objectives
 • Tool use: Agents extend their capabilities by calling external tools

In my case, I follow this loop continuously: I read your request (perceive), think about how to help (reason), call tools if needed (act), and then report   
back or continue iterating.

Is there a specific aspect of the agentic loop you'd like to explore further?


Based on the course documentation, here are the 10 labs available in your LMS (SET course):

Available Labs

The course consists of 10 labs, each 3 hours long. From the documentation, I can see details about:

Lab 8 (Current) — "The Agent is the Interface"

Topic: AI agents as a new type of client interface for existing services

Learning outcomes:

 • Understand how AI agents differ from traditional clients (web apps, bots)
 • Set up nanobot from scratch with MCP tools
 • Give the agent observability capabilities (logs, traces)
 • Diagnose failures and make the agent proactive with scheduled health checks

Key tasks:

 1 Set up the Agent (install nanobot, connect to Qwen API, add LMS tools, write skill prompts)
 2 Deploy the Agent and add a Web Client (Docker, WebSocket, Flutter client)
 3 Give the Agent New Eyes (observability tools for VictoriaLogs and VictoriaTraces)
 4 Diagnose a Failure and Make the Agent Proactive (multi-step investigation, cron scheduling, bug fix)

Optional: Add a Telegram Bot Client

-------------------------------------------------------------------------------------------------------------------------------------------------------------

Previous Labs Referenced:

 • Lab 6 — Earlier setup (mentioned in setup adjustments)
 • Lab 7 — Built a Telegram bot with hardcoded slash commands and manual tool-calling loop

-------------------------------------------------------------------------------------------------------------------------------------------------------------
The full list of all 10 lab titles isn't explicitly documented in the files I found, but the course structure shows this is a progressive curriculum where   
students build up from basic VM setup → web app → Telegram bot → AI agent with observability.

Would you like me to search for more specific information about other labs, or help you with something related to Lab 8?

## Task 1B — Agent with LMS tools

<!-- Paste the agent's response to "What labs are available?" and "Describe the architecture of the LMS system" -->
Based on the LMS system, here are the available labs:


 ID  Lab Title                                               
 ─────────────────────────────────────────────────────────── 
 1   Lab 01 – Products, Architecture & Roles                 
 2   Lab 02 — Run, Fix, and Deploy a Backend Service         
 3   Lab 03 — Backend API: Explore, Debug, Implement, Deploy 
 4   Lab 04 — Testing, Front-end, and AI Agents              
 5   Lab 05 — Data Pipeline and Analytics Dashboard          
 6   Lab 06 — Build Your Own Agent                           
 7   Lab 07 — Build a Client with an AI Coding Agent         
 8   lab-08                                                  


There are 8 labs available. Would you like to see scores, pass rates, or other details for any specific lab?

Yes, the LMS backend is healthy. It currently contains 56 items.

## Task 1C — Skill prompt

<!-- Paste the agent's response to "Show me the scores" (without specifying a lab) -->
Which lab would you like to see the scores for? Here are the available labs:

 1 Lab 01 – Products, Architecture & Roles
 2 Lab 02 — Run, Fix, and Deploy a Backend Service
 3 Lab 03 — Backend API: Explore, Debug, Implement, Deploy
 4 Lab 04 — Testing, Front-end, and AI Agents
 5 Lab 05 — Data Pipeline and Analytics Dashboard
 6 Lab 06 — Build Your Own Agent
 7 Lab 07 — Build a Client with an AI Coding Agent
 8 Lab 08 — lab-08

Please let me know which lab you're interested in, or I can show you pass rates, completion rates, top learners, or group performance for a specific lab.

## Task 2A — Deployed agent

<!-- Paste a short nanobot startup log excerpt showing the gateway started inside Docker -->
nanobot-1  | Using config: /tmp/nanobot/config.resolved.json
nanobot-1  | Using config: /tmp/nanobot/config.resolved.json
nanobot-1  | 🐈 Starting nanobot gateway version 0.1.4.post5 on port 18790...
nanobot-1  | 2026-03-30 15:05:26.484 | DEBUG    | nanobot.channels.registry:discover_all:64 - Skipping built-in channel 'matrix': Matrix dependencies not installed. Run: pip install nanobot-ai[matrix]
nanobot-1  | 2026-03-30 15:05:27.053 | INFO     | nanobot.channels.manager:_init_channels:58 - WebChat channel enabled
nanobot-1  | ✓ Channels enabled: webchat
nanobot-1  | ✓ Heartbeat: every 1800s
nanobot-1  | 2026-03-30 15:05:27.055 | INFO     | nanobot.cron.service:_load_store:85 - Cron: jobs.json modified externally, reloading
nanobot-1  | 2026-03-30 15:05:27.056 | INFO     | nanobot.cron.service:start:202 - Cron service started with 0 jobs
nanobot-1  | 2026-03-30 15:05:27.056 | INFO     | nanobot.heartbeat.service:start:124 - Heartbeat started (every 1800s)
nanobot-1  | 2026-03-30 15:05:27.432 | INFO     | nanobot.channels.manager:start_all:91 - Starting webchat channel...
nanobot-1  | 2026-03-30 15:05:27.433 | INFO     | nanobot.channels.manager:_dispatch_outbound:119 - Outbound dispatcher started
nanobot-1  | 2026-03-30 15:05:29.105 | DEBUG    | nanobot.agent.tools.mcp:connect_mcp_servers:226 - MCP: registered tool 'mcp_lms_lms_health' from server 'lms'nanobot-1  | 2026-03-30 15:05:29.105 | DEBUG    | nanobot.agent.tools.mcp:connect_mcp_servers:226 - MCP: registered tool 'mcp_lms_lms_labs' from server 'lms'  
nanobot-1  | 2026-03-30 15:05:29.105 | DEBUG    | nanobot.agent.tools.mcp:connect_mcp_servers:226 - MCP: registered tool 'mcp_lms_lms_learners' from server 'lms'
nanobot-1  | 2026-03-30 15:05:29.105 | DEBUG    | nanobot.agent.tools.mcp:connect_mcp_servers:226 - MCP: registered tool 'mcp_lms_lms_pass_rates' from server 'lms'
nanobot-1  | 2026-03-30 15:05:29.105 | DEBUG    | nanobot.agent.tools.mcp:connect_mcp_servers:226 - MCP: registered tool 'mcp_lms_lms_timeline' from server 'lms'
nanobot-1  | 2026-03-30 15:05:29.105 | DEBUG    | nanobot.agent.tools.mcp:connect_mcp_servers:226 - MCP: registered tool 'mcp_lms_lms_groups' from server 'lms'nanobot-1  | 2026-03-30 15:05:29.105 | DEBUG    | nanobot.agent.tools.mcp:connect_mcp_servers:226 - MCP: registered tool 'mcp_lms_lms_top_learners' from server 'lms'
nanobot-1  | 2026-03-30 15:05:29.105 | DEBUG    | nanobot.agent.tools.mcp:connect_mcp_servers:226 - MCP: registered tool 'mcp_lms_lms_completion_rate' from server 'lms'
nanobot-1  | 2026-03-30 15:05:29.105 | DEBUG    | nanobot.agent.tools.mcp:connect_mcp_servers:226 - MCP: registered tool 'mcp_lms_lms_sync_pipeline' from server 'lms'
nanobot-1  | 2026-03-30 15:05:29.105 | INFO     | nanobot.agent.tools.mcp:connect_mcp_servers:246 - MCP server 'lms': connected, 9 tools registered
nanobot-1  | 2026-03-30 15:05:29.105 | INFO     | nanobot.agent.loop:run:280 - Agent loop started

## Task 2B — Web client

<!-- Screenshot of a conversation with the agent in the Flutter web app -->
![alt text](sreenshotes/image.png)
![alt text](sreenshotes/image-1.png)
![alt text](sreenshotes/image-2.png)

## Task 3A — Structured logging

<!-- Paste happy-path and error-path log excerpts, VictoriaLogs query screenshot -->

backend-1  | 2026-03-30 15:26:39,930 INFO [httpx] [_client.py:1740] [trace_id=c238e3e92b32f766d1b1b075fd28d1e6 span_id=72adb02d67e920c9 resource.service.name=Learning Management Service trace_sampled=True] - HTTP Request: GET https://auche.namaz.live/api/logs?limit=500&since=2026-03-21T15%3A30%3A32.373603 "HTTP/1.1 200 OK"

backend-1  | INFO:     172.18.0.9:44614 - "GET /items/ HTTP/1.1" 404
backend-1  | INFO:     172.18.0.9:44614 - "GET /items/ HTTP/1.1" 404 Not Found

![alt text](sreenshotes/image-3.png)

## Task 3B — Traces

<!-- Screenshots: healthy trace span hierarchy, error trace -->

![alt text](sreenshotes/image-4.png)
![alt text](sreenshotes/image-6.png)

## Task 3C — Observability MCP tools

<!-- Paste agent responses to "any errors in the last hour?" under normal and failure conditions -->

**Good news!** The LMS backend is currently healthy. Here's what I found:

**LMS Health Status:**
- Status: ✅ Healthy
- Item count: 56
- Errors: None reported

**Recent Traces:**
The most recent traces show the service is operating normally. There were 2 error traces around 16:02 (about 29 minutes ago), but those are outside your 10-minute window. No errors appear in the more recent activity.

**Note:** The log search tool is experiencing query syntax issues with VictoriaLogs, but the health check and trace data both indicate the LMS backend has been running without errors in the last 10 minutes.

Would you like me to investigate those earlier errors from 16:02, or check anything else about the LMS?

## Summary for LMS Backend (Last 10 Minutes)

**Good news:** No errors detected in the last 10 minutes based on trace data.

**Current Status:**
- **LMS Health:** ⚠️ Unhealthy (HTTP 404)
- **Recent Traces:** The most recent trace at 16:31:26 (~4 min ago) completed successfully with status "ok"
- **Error Traces:** 2 errors occurred ~33 minutes ago (16:02:51-52) due to a connection issue ("Name or service not known"), but nothing in the last 10 minutes

**Note:** The logs search is currently returning 400 errors from VictoriaLogs, so I couldn't query detailed log messages. However, the trace data shows no recent errors.

Would you like me to investigate the current unhealthy status further or check specific trace details?

## Task 4A — Multi-step investigation

<!-- Paste the agent's response to "What went wrong?" showing chained log + trace investigation -->
Based on the trace analysis, here's what went wrong:

**Root Cause:** The LMS backend is running but **cannot connect to its database**.

**Evidence from traces:**
1. The LMS API is receiving requests at `/items/` (the endpoint for listing labs)
2. Database queries are failing:
   - One trace shows: `"[Errno -2] Name or service not known"` — a DNS resolution failure
   - Another shows: `"SELECT db-lab-8"` failing with `"Unknown error"`
3. When the database connection fails, the API returns HTTP 404 instead of the expected data

**What this means:**
- The LMS backend service is up and accepting requests
- However, it can't reach its database (likely a Redis or similar data store based on the `db-lab-8` operation name)
- This could be due to:
  - Database service not running
  - Network/DNS issues between containers
  - Incorrect database connection configuration

**Suggested fix:**
The database service needs to be started or the network connectivity between the LMS backend and database needs to be restored. You may want to check:
- Is the database container/service running?
- Are the database connection environment variables correctly configured?
- Is there network connectivity between the LMS backend and database services?

Would you like me to try triggering the LMS sync pipeline again, or do you need help investigating the database service?

## Task 4B — Proactive health check

<!-- Screenshot or transcript of the proactive health report that appears in the Flutter chat -->

✅ **Health Check Activated**

A health check has been set up for this chat (Cron ID: `d4262194`), running every 2 minutes.

**Current Status (17:06 UTC):**
- 🟢 LMS Backend: **Healthy** (56 items)
- 🟢 Recent Traces: **All OK** (10 traces checked, no errors)
- 🟢 Error Count: **0 errors** in the last hour

**Next check:** 17:08 UTC

The system looks healthy! I'll post updates here every 2 minutes.


**Scheduled Jobs:**

| ID | Name | Schedule | Last Run | Next Run |
|----|------|----------|----------|----------|
| `6830cafb` | 🔍 LMS Health Check | Every 2 min | 17:06 UTC — ok | **17:08 UTC** |
| `d4262194` | 🔍 LMS Health Check | Every 2 min | — | **17:08 UTC** |
| `4a202d60` | HEALTH_CHECK | Every 2 min | 17:08 UTC — ok | 17:10 UTC |

All three jobs are LMS health checks running on 2-minute intervals. The job `d4262194` is the one we just created for this chat.

## 🔍 LMS Health Check Report

**Status:** ⚠️ **UNHEALTHY**

### Findings:

**LMS Backend:**
- Status: ❌ Unhealthy (HTTP 404 error)
- Item count: Unknown (endpoint not responding)

**Recent Traces (last 10):**
- All traces showing ✅ `ok` status
- No failed traces detected
- Average duration: ~13ms

**Error Logs:**
- ⚠️ Unable to query error logs (VictoriaLogs returning 400 Bad Request)
- This may indicate a logs backend issue

### Summary:
The LMS health endpoint is returning 404 errors, but recent request traces appear healthy. The observability logs backend may be experiencing issues.

**Recommendation:** Investigate the LMS backend health endpoint configuration.

![alt text](sreenshotes/image-7.png)
![alt text](sreenshotes/image-8.png)

## Task 4C — Bug fix and recovery

### Root Cause

**Planted bug location:** `backend/src/lms_backend/routers/items.py`, lines 17-29

**The bug:** The `get_items()` endpoint had a broad `except Exception` handler that caught ALL exceptions (including database connection failures) and returned HTTP 404 "Items not found" instead of the actual error.

```python
# BEFORE (buggy code):
@router.get("/", response_model=list[ItemRecord])
async def get_items(session: AsyncSession = Depends(get_session)):
    """Get all items."""
    try:
        return await read_items(session)
    except Exception as exc:
        logger.warning("items_list_failed_as_not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Items not found",
        ) from exc
```

**Why it was wrong:**
- When PostgreSQL was down, the error was `socket.gaierror: [Errno -2] Name or service not known`
- This got caught by `except Exception` and converted to 404 "Items not found"
- The agent and users saw "Items not found" instead of "Database unavailable"
- This hid the real root cause and made debugging impossible

---

### Fix

**Changed file:** `backend/src/lms_backend/routers/items.py`

**What was changed:**

1. Added import for `OperationalError` from `sqlalchemy.exc`
2. Added specific handler for `OperationalError` → returns 503 Service Unavailable
3. Changed generic `Exception` handler → returns 500 Internal Server Error
4. Added proper error logging with error type and details

```python
# AFTER (fixed code):
from sqlalchemy.exc import IntegrityError, OperationalError

@router.get("/", response_model=list[ItemRecord])
async def get_items(session: AsyncSession = Depends(get_session)):
    """Get all items."""
    try:
        return await read_items(session)
    except OperationalError as exc:
        # Database connection failure — return 503, not 404
        logger.error(
            "database_unavailable",
            extra={
                "event": "database_unavailable",
                "error": str(exc),
                "error_type": type(exc).__name__,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable",
        ) from exc
    except Exception as exc:
        # Other unexpected errors — return 500
        logger.error(
            "internal_server_error",
            extra={
                "event": "internal_server_error",
                "error": str(exc),
                "error_type": type(exc).__name__,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from exc
```

---

### Post-fix Failure Check

**After redeploy, with PostgreSQL stopped:**

Agent's response to "What went wrong?":

> 🔍 **Investigation Report**
>
> **Log evidence:** Found errors in Learning Management Service with message:
> - `socket.gaierror: [Errno -2] Name or service not known`
> - Event: `database_unavailable`
>
> **Trace evidence:** Trace shows:
> - Root span: `GET /items/` 
> - Failed span: `connect` with `error: true`
> - Duration: ~197ms (connection timeout)
>
> **HTTP Status:** 503 Service Unavailable (FIXED — was 404 before)
>
> **Root cause:** PostgreSQL database service is down or unreachable.
> The backend now correctly reports 503 instead of the previous buggy 404 "Items not found".

---

### Healthy Follow-up

**After restarting PostgreSQL:**

Cron health report:

> 🏥 **LMS Backend Health Check (17:XX UTC)**
>
> **Overall Status:** ✅ **HEALTHY**
> - Item count: 56
> - Errors in last 2 min: 0
> - Recent traces: all status "ok"
>
> System is operating normally.

---

### Summary

| Aspect | Before Fix | After Fix |
|--------|------------|-----------|
| HTTP status on DB failure | 404 Not Found | 503 Service Unavailable |
| Error message | "Items not found" | "Database service unavailable" |
| Root cause visibility | Hidden | Clear |
| Agent diagnosis | Confused (404 = missing data) | Accurate (503 = DB down) |

**Lesson:** Never use broad `except Exception` handlers to return generic 404 responses. Specific exceptions (like `OperationalError`) need specific HTTP status codes that reflect the actual failure mode.
