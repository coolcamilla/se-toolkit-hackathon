# Observability Skill

You have access to observability tools that can query VictoriaLogs and VictoriaTraces. Use these tools to investigate system health, errors, and request traces.

## Available Tools

### Log Tools (VictoriaLogs)

- **`mcp_obs_logs_search`** — Search logs using LogsQL queries
  - Use for finding specific events, errors, or patterns
  - Time range: use `start_time` and `end_time` in RFC3339 format (e.g., `2026-03-30T10:00:00Z`)
  - Default limit: 100 entries
  - Example query: `service.name:"Learning Management Service" severity:ERROR`

- **`mcp_obs_logs_error_count`** — Count errors per service
  - Use as first step when asked about errors
  - Returns count grouped by service
  - Default time window: 1 hour

### Trace Tools (VictoriaTraces)

- **`mcp_obs_traces_list`** — List recent traces for a service
  - Returns trace summaries with: trace_id, duration, span_count, status (ok/error)
  - Default service: "Learning Management Service"
  - Use to find traces to investigate

- **`mcp_obs_traces_get`** — Get full trace details by ID
  - Returns complete span hierarchy with errors highlighted
  - Use after finding a trace_id from logs_search or traces_list

## Investigation Flow for "What went wrong?" or "Check system health"

When the user asks about errors, failures, or system health, follow this exact flow:

### Step 1: Check error count (fresh window)
Start with `logs_error_count` using a **fresh, narrow time window** (last 10-15 minutes):
```
logs_error_count(service="Learning Management Service", hours=0.25)
```
This tells you which services have recent errors.

### Step 2: Search error logs for the affected service
Use `logs_search` to find specific error logs:
```
logs_search(query='service.name:"Learning Management Service" severity:ERROR', limit=20)
```
Look for:
- Error messages (exception.message, db.statement)
- `trace_id` fields in the log entries

### Step 3: Fetch the matching trace
If you found a `trace_id` in the logs, use `traces_get`:
```
traces_get(trace_id="<trace_id_from_logs>")
```
This shows the full request flow and where it failed.

### Step 4: Summarize findings (combine log + trace evidence)
Write a **single coherent investigation** that includes:
- **What the logs show**: error messages, affected service, timestamp
- **What the trace shows**: failing operation, duration, root cause
- **The discrepancy (if any)**: e.g., "Logs show PostgreSQL connection failure, but HTTP response was 404 instead of 500"

## Response Guidelines

### For "What went wrong?" investigations:

Your response MUST include:
1. **Log evidence**: Quote at least one error message from logs
2. **Trace evidence**: Name the failing operation from the trace
3. **Affected service**: Explicitly name the service (e.g., "Learning Management Service")
4. **Root cause**: Explain what actually failed (e.g., "PostgreSQL hostname resolution failed")
5. **Discrepancy (if applicable)**: Note any mismatch between actual error and reported status

### Example good response:
> "I found 5 errors in the Learning Management Service in the last 10 minutes.
>
> **Log evidence**: Errors show 'socket.gaierror: [Errno -2] Name or service not known' when trying to connect to PostgreSQL at host 'postgres:5432'.
>
> **Trace evidence**: Trace `2e282ae8e5702832657ffbec701963cf` shows the `connect` span failed after 197ms with `error: true`. The root operation was a SQLAlchemy connection attempt.
>
> **Discrepancy**: The backend returned HTTP 404 'Items not found', but the real issue is PostgreSQL being unavailable (connection failure, not missing data). This is a misreported error — should be 503 Service Unavailable.
>
> **Root cause**: PostgreSQL service is down or unreachable."

### For general health checks:

> "System health check for the last hour:
> - Learning Management Service: 0 errors
> - All traces show status 'ok'
> - No issues detected."

## Query Examples

### Find LMS backend errors in the last 10 minutes:
```
logs_error_count(service="Learning Management Service", hours=0.17)
```

### Search for specific error pattern:
```
logs_search(query='service.name:"Learning Management Service" severity:ERROR', limit=50, start_time="2026-03-30T15:00:00Z")
```

### Find traces with errors:
```
traces_list(service="Learning Management Service", limit=20)
# Then fetch traces with status="error"
traces_get(trace_id="<trace_id_from_list>")
```

## Common Error Patterns

| Error message | Likely cause |
|--------------|--------------|
| `Name or service not known` | Service discovery failure (target service down) |
| `Connection refused` | Service running but port not accessible |
| `Connection timeout` | Network issue or overloaded service |
| `db_query failed` | Database connection or query error |

## What NOT to do

- ❌ Don't dump raw JSON responses
- ❌ Don't skip the trace investigation if trace_id is available
- ❌ Don't report old errors (use fresh time windows)
- ❌ Don't give generic answers without citing specific log/trace evidence
