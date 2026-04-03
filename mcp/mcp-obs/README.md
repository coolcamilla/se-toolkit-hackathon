# mcp-obs

MCP server for observability tools (VictoriaLogs and VictoriaTraces).

## Tools

### logs_search
Search logs in VictoriaLogs using LogsQL queries.

### logs_error_count
Count errors per service over a time window.

### traces_list
List recent traces for a service.

### traces_get
Get full details of a specific trace by ID.

## Usage

```bash
# Run directly
python -m mcp_obs

# Or via nanobot MCP server configuration
```

## Environment Variables

- `VICTORIALOGS_URL` — VictoriaLogs endpoint (default: `http://victorialogs:9428`)
- `VICTORIATRACES_URL` — VictoriaTraces endpoint (default: `http://victoriatraces:10428`)
