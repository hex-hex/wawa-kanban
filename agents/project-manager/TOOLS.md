# TOOLS.md — Project Manager

Environment notes for assignment and monitoring.

## Free vs busy agent

-- **Free:** The agent’s folder (e.g. `agents/developers/default/`, `agents/designers/default/`, `agents/verifiers/default/`) **contains no ticket file** (no `.md` file matching the ticket naming rule). You can assign a new ticket there.
- **Busy (not free):** The agent’s folder **already contains a ticket file**. Do not assign another; at most one ticket per agent at a time.

## Board Structure

- `backlog/` — unassigned tickets
- `implementing/` — in progress (developer)
- `verifying/` — awaiting verification (verifier)
- `finished/` — done

Tickets are markdown files with frontmatter: `id`, `title`, `priority`, `created`, etc.

## Where to Look

- **Agent logs:** Each agent (developer/designer/verifier) may have session or run logs. When checking busy agents, read the **last 50 entries**; look for errors, build failures, and “stuck” (no progress, blocked, waiting). If found, report to the user: which agent, which ticket, what error or stuck signal.
- Board state: scan columns for dwell time; long dwell = stalled or blocked.
- `MEMORY.md` and daily `memory/` for assignment history and recurring issues.
