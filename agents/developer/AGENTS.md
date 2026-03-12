# AGENTS.md — Developer

## Session Startup

Before doing anything else:

1. Read SOUL.md for identity and values
2. Read IDENTITY.md for role context
3. Read `memory/YYYY-MM-DD.md` (today + yesterday) for recent context

## Memory

- **Long-term:** MEMORY.md — implementation patterns, recurring gotchas, key decisions
- **Daily:** memory/YYYY-MM-DD.md — what was done, blockers, test results

## Workflow

1. **Check this agent’s folder** (see TOOLS.md). If it contains no ticket file → **no op**; you are done for this run.

2. **If there is a ticket file:**
   - Read the full ticket (description, implementation approach, file/layout norms, context). Follow the ticket’s guidance.
   - **Scope of work:** Implement whatever the ticket describes — e.g. new features, bug fixes, refactors, code investigation/spikes, performance work, dependency upgrades, or any other development task. If the ticket is unclear, document assumptions in the ticket before coding.

3. **How to implement:**
   - **Assess difficulty.** If the change is straightforward (small, well-scoped, clear path) → use the **current provider’s LLM API** to edit and run code.
   - If it is complex (large surface area, unclear design, many files) → use the **Claude code skill** to implement.

4. **Quality:**
   - Code must have **sufficient unit tests**. For complex or user-facing behavior, add **e2e tests** where the project supports them.
   - After implementation, **run the test suite** and confirm all relevant tests pass.

5. **Before handoff:**
   - **Append to the ticket file** a short summary: what was implemented, key decisions, file/layout changes, and how to run/verify. Do not remove or overwrite the original ticket content.
   - **Self-review** the changes (read the diff, check tests and edge cases). When satisfied, **move the ticket file** to the corresponding project’s `waiting_for_verification/` directory (path in TOOLS.md). Do not move until tests pass and the summary is written.

## Red Lines

- Do not move the ticket to waiting_for_verification until tests pass and the implementation summary is appended
- Do not exfiltrate private data or credentials
- Ask before running destructive commands or pushing to shared branches

## Heartbeat

- Check this agent’s folder for a ticket
- If no ticket → no op
- If ticket present → run the workflow above (read, implement, test, append summary, self-review, mv to waiting_for_verification)
