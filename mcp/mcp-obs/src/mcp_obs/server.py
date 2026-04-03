"""
MCP server for observability tools (VictoriaLogs and VictoriaTraces).
"""

from mcp.server.fastmcp import FastMCP
import httpx
from typing import Optional
from datetime import datetime, timedelta

mcp = FastMCP("mcp-obs")

# Default URLs - can be overridden via environment variables
VICTORIALOGS_URL = "http://victorialogs:9428"
VICTORIATRACES_URL = "http://victoriatraces:10428"


@mcp.tool()
async def logs_search(
    query: str,
    limit: int = 100,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> list[dict]:
    """
    Search logs in VictoriaLogs using LogsQL.

    Args:
        query: LogsQL query string (e.g., 'service.name:"Learning Management Service" severity:ERROR')
        limit: Maximum number of log entries to return
        start_time: Start time in RFC3339 format (e.g., '2026-03-30T10:00:00Z'). Defaults to 1 hour ago.
        end_time: End time in RFC3339 format. Defaults to now.

    Returns:
        List of log entries with fields: timestamp, severity, message, service, trace_id, etc.
    """
    # Build time range
    if not start_time:
        start_time = (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z"
    if not end_time:
        end_time = datetime.utcnow().isoformat() + "Z"

    # Build query with time range
    time_query = f"_time:{start_time},{end_time} {query}"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{VICTORIALOGS_URL}/select/logsql/query",
            params={"query": time_query, "limit": limit},
            timeout=30.0,
        )
        response.raise_for_status()

        # VictoriaLogs returns JSON with fields
        data = response.json()
        return _parse_logs_response(data)


@mcp.tool()
async def logs_error_count(
    service: Optional[str] = None,
    hours: int = 1,
) -> list[dict]:
    """
    Count errors per service over a time window.

    Args:
        service: Filter by service name (optional). If not specified, returns all services.
        hours: Time window in hours (default: 1)

    Returns:
        List of dicts with 'service' and 'count' fields.
    """
    start_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat() + "Z"
    end_time = datetime.utcnow().isoformat() + "Z"

    # Build query for errors
    if service:
        query = f'_time:{start_time},{end_time} severity:ERROR service.name:"{service}"'
    else:
        query = f"_time:{start_time},{end_time} severity:ERROR"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{VICTORIALOGS_URL}/select/logsql/query",
            params={"query": query, "limit": 10000},
            timeout=30.0,
        )
        response.raise_for_status()

        data = response.json()
        logs = _parse_logs_response(data)

        # Count by service
        counts: dict[str, int] = {}
        for log in logs:
            svc = log.get("service", "unknown")
            counts[svc] = counts.get(svc, 0) + 1

        return [{"service": svc, "count": cnt} for svc, cnt in sorted(counts.items(), key=lambda x: -x[1])]


@mcp.tool()
async def traces_list(
    service: str = "Learning Management Service",
    limit: int = 20,
) -> list[dict]:
    """
    List recent traces for a service from VictoriaTraces.

    Args:
        service: Service name to filter traces (default: "Learning Management Service")
        limit: Maximum number of traces to return

    Returns:
        List of trace summaries with: trace_id, start_time, duration, span_count, status
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{VICTORIATRACES_URL}/select/jaeger/api/traces",
            params={"service": service, "limit": limit},
            timeout=30.0,
        )
        response.raise_for_status()

        data = response.json()
        traces_data = data.get("data", [])

        result = []
        for trace in traces_data:
            trace_id = trace.get("traceID", "")
            spans = trace.get("spans", [])

            # Find root span (no references or parent)
            root_span = None
            for span in spans:
                if not span.get("references"):
                    root_span = span
                    break

            if not root_span and spans:
                root_span = spans[0]

            # Calculate duration and status
            duration_ms = root_span.get("duration", 0) / 1000 if root_span else 0
            start_time = root_span.get("startTime", 0) / 1000 if root_span else 0

            # Check for errors
            has_error = any(
                tag.get("key") == "error" and tag.get("value") == "true"
                for span in spans
                for tag in span.get("tags", [])
            )

            result.append({
                "trace_id": trace_id,
                "start_time": datetime.fromtimestamp(start_time / 1000).isoformat() if start_time else None,
                "duration_ms": round(duration_ms, 2),
                "span_count": len(spans),
                "status": "error" if has_error else "ok",
                "service": service,
            })

        return result


@mcp.tool()
async def traces_get(trace_id: str) -> dict:
    """
    Get full details of a specific trace by ID.

    Args:
        trace_id: The trace ID to fetch

    Returns:
        Full trace details with spans, operations, durations, and error information.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{VICTORIATRACES_URL}/select/jaeger/api/traces/{trace_id}",
            timeout=30.0,
        )
        response.raise_for_status()

        data = response.json()
        traces_data = data.get("data", [])

        if not traces_data:
            return {"error": f"Trace {trace_id} not found"}

        trace = traces_data[0]
        return _parse_trace(trace)


def _parse_logs_response(data: dict) -> list[dict]:
    """Parse VictoriaLogs response into structured log entries."""
    logs = []

    # VictoriaLogs returns data in various formats
    # Try to extract log entries
    if isinstance(data, dict):
        hits = data.get("hits", [])
        for hit in hits:
            log_entry = {}
            fields = hit.get("fields", {})

            # Extract common fields
            log_entry["timestamp"] = hit.get("timestamp") or fields.get("_time")
            log_entry["severity"] = fields.get("severity") or fields.get("level")
            log_entry["message"] = fields.get("message") or hit.get("message", "")
            log_entry["service"] = fields.get("service.name") or fields.get("service")
            log_entry["trace_id"] = fields.get("trace_id") or fields.get("traceID")
            log_entry["span_id"] = fields.get("span_id") or fields.get("spanID")
            log_entry["event"] = fields.get("event")

            # Copy all fields for completeness
            log_entry["fields"] = fields

            logs.append(log_entry)

    return logs


def _parse_trace(trace: dict) -> dict:
    """Parse VictoriaTraces response into structured trace details."""
    trace_id = trace.get("traceID", "")
    spans = trace.get("spans", [])
    processes = trace.get("processes", {})

    # Get service name from process
    service_name = "unknown"
    for proc_id, proc in processes.items():
        if proc.get("serviceName"):
            service_name = proc["serviceName"]
            break

    # Build span hierarchy
    span_map = {span["spanID"]: span for span in spans}
    root_spans = []
    child_spans: dict[str, list] = {}

    for span in spans:
        refs = span.get("references", [])
        parent_ref = next((r for r in refs if r.get("refType") == "CHILD_OF"), None)

        if parent_ref:
            parent_id = parent_ref.get("spanID")
            if parent_id:
                if parent_id not in child_spans:
                    child_spans[parent_id] = []
                child_spans[parent_id].append(span)
        else:
            root_spans.append(span)

    # Check for errors
    has_error = False
    error_spans = []
    for span in spans:
        for tag in span.get("tags", []):
            if tag.get("key") == "error" and tag.get("value") == "true":
                has_error = True
                error_spans.append({
                    "span_id": span["spanID"],
                    "operation": span.get("operationName", "unknown"),
                    "error_message": _get_error_message(span),
                })
                break

    # Calculate total duration
    total_duration = 0
    for span in spans:
        duration = span.get("duration", 0)
        if duration > total_duration:
            total_duration = duration

    return {
        "trace_id": trace_id,
        "service": service_name,
        "duration_ms": round(total_duration / 1000, 2),
        "span_count": len(spans),
        "has_error": has_error,
        "error_spans": error_spans,
        "root_spans": [
            {
                "span_id": s["spanID"],
                "operation": s.get("operationName", "unknown"),
                "duration_ms": round(s.get("duration", 0) / 1000, 2),
                "tags": _extract_tags(s),
            }
            for s in root_spans
        ],
        "all_spans": [
            {
                "span_id": s["spanID"],
                "operation": s.get("operationName", "unknown"),
                "duration_ms": round(s.get("duration", 0) / 1000, 2),
                "has_error": any(
                    t.get("key") == "error" and t.get("value") == "true"
                    for t in s.get("tags", [])
                ),
            }
            for s in spans
        ],
    }


def _get_error_message(span: dict) -> str:
    """Extract error message from span logs."""
    for log in span.get("logs", []):
        for field in log.get("fields", []):
            if field.get("key") == "exception.message":
                return field.get("value", "")
    return "Unknown error"


def _extract_tags(span: dict) -> dict:
    """Extract tags from span into a dict."""
    tags = {}
    for tag in span.get("tags", []):
        key = tag.get("key", "unknown")
        value = tag.get("value", "")
        tags[key] = value
    return tags
