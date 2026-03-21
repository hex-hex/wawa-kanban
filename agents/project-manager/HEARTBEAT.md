# HEARTBEAT.md — Project Manager

Add tasks below for periodic checks. Keep this file empty to skip heartbeat runs.

- [ ] Assign new backlog tickets to developers/designers when an agent is free; route verify work to **code-verifier** vs **general-verifier** per TOOLS.md
- [ ] If no agents are free (each agent folder already has a ticket file): read each busy agent’s logs (last 50 entries); if errors or stuck, report to user
- [ ] Scan all columns for stalled tickets and overdue work
- [ ] Collect development errors and build failures from agent logs/heartbeats
- [ ] Identify and list bottlenecks (blocked tickets, missing deps, unclear requirements)
- [ ] Produce a brief status report for the user: done, in progress, stuck, errors
- [ ] Note today’s assignments and key findings in `memory/YYYY-MM-DD.md`
