---
name: lms
description: Use LMS MCP tools for live course data
always: true
---

# LMS Skill

You have access to the LMS (Learning Management System) via MCP tools for live course data.

## Available Tools

| Tool | Parameters | Description |
|------|------------|-------------|
| `lms_health` | none | Check if LMS backend is healthy |
| `lms_labs` | none | List all available labs |
| `lms_learners` | none | List all registered learners |
| `lms_pass_rates` | `lab` (required) | Get pass rates with avg score and attempt count per task |
| `lms_timeline` | `lab` (required) | Get submission timeline (date + count) |
| `lms_groups` | `lab` (required) | Get group performance (avg score + student count) |
| `lms_top_learners` | `lab` (required), `limit` (default: 5) | Get top learners by average score |
| `lms_completion_rate` | `lab` (required) | Get completion rate (passed / total) |
| `lms_sync_pipeline` | none | Trigger LMS sync pipeline |

## Strategy

### When lab parameter is needed

Tools requiring a `lab` parameter: `lms_pass_rates`, `lms_timeline`, `lms_groups`, `lms_top_learners`, `lms_completion_rate`.

**Rule:** If the user asks for scores, pass rates, completion, groups, timeline, or top learners **without naming a lab**:

1. Call `lms_labs` first to get available labs
2. If multiple labs exist, ask the user to choose one
3. Use the shared structured-ui skill to present the choice (it will handle display on supported channels)
4. Pass the selected lab value to the requested tool

### Lab labels

- Use each lab's `title` field as the default user-facing label
- If the tool output provides a better identifier (e.g., `lab_id`), use that as the value passed back
- Present labs in a clear, readable format

### Formatting results

- **Percentages:** Format as `XX.X%` (e.g., `75.5%`)
- **Counts:** Use plain integers with optional thousand separators
- **Scores:** Show with 1-2 decimal places
- **Dates:** Use `YYYY-MM-DD` format
- **Tables:** Format tabular data aligned for readability

### Response style

- Keep responses **concise** — lead with the key finding
- Include only relevant numbers; omit empty fields
- If data is empty or unavailable, say so clearly
- Offer follow-up actions when appropriate (e.g., "Would you like to see the timeline for this lab?")

### When asked "what can you do?"

Explain your LMS capabilities clearly:

> I can access live course data from the LMS, including:
> - List available labs and learners
> - Show pass rates, completion rates, and group performance for a specific lab
> - Display submission timelines and top learners
> - Trigger data sync
>
> Just tell me which lab you're interested in, or ask me to show available labs first.

## Example Flows

### Flow 1: User asks for pass rates without specifying lab

```
User: What are the pass rates?
Assistant: [calls lms_labs]
Assistant: Which lab would you like to see pass rates for?
  - Lab 04: Introduction to Testing
  - Lab 05: Advanced Patterns
  [presents choices via structured-ui]
User: [selects Lab 04]
Assistant: [calls lms_pass_rates with lab="lab-04"]
Assistant: Pass rates for Lab 04:
  - Task 1: 85% pass rate, avg score 7.2/10, 120 attempts
  - Task 2: 72% pass rate, avg score 6.8/10, 98 attempts
```

### Flow 2: User asks for top learners with specific lab

```
User: Show top 10 learners for lab-05
Assistant: [calls lms_top_learners with lab="lab-05", limit=10]
Assistant: Top 10 learners for Lab 05:
  1. Alice Chen — 94.5%
  2. Bob Smith — 91.2%
  ...
```

### Flow 3: Data unavailable

```
User: Show completion rate for lab-99
Assistant: [calls lms_completion_rate with lab="lab-99"]
Assistant: No data available for lab-99. Would you like to see available labs?
```
