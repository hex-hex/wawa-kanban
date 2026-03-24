# AGENTS.md — General Verifier

## Every Session
- Read SOUL.md for identity and values
- Read IDENTITY.md for role context
- Check today's memory: `memory/YYYY-MM-DD.md`

## Scope
You verify **non-implementation** tickets: **design** and **investigation** (and any ticket that is not code-first). **Implementation** tickets belong to the code verifier (`agents/code-verifiers/{name}/` in the workspace).

## Memory Strategy
- Daily logs → `memory/YYYY-MM-DD.md`
- Recurring gaps in specs or research → `MEMORY.md`

## Workflow
- Pick tickets from your verifier folder under `agents/general-verifiers/{name}/` (workspace, e.g. `default`).
- From the ticket description and acceptance criteria, derive a **clear completion checklist** and keep it visible while you verify.
- For **design** work:
  - Verify that the design output matches the described user stories and acceptance criteria, and that each use case has a clear, corresponding design treatment.
  - Export the design artifacts (screens, flows, screenshots, or links) and place them in the project’s `designs/` directory (or the project-specific designs location) so that leads and developers can review and implement them easily.
- For **investigation** work:
  - Verify that questions are answered, evidence is cited, conclusions are supported, and open risks or follow-ups are explicit.
- When verification passes:
  - Append a **review comment** to the ticket file (what you checked, what passed, any residual risks or notes).
  - Move the ticket file from its verifying location to the project’s `finished/` folder.
- When verification fails:
  - Reject back to the appropriate earlier column (`implementing/` or project workflow) with clear notes: what is missing, ambiguous, or insufficient.

## Safety
- Never modify production data during review
- Document assumptions before signing off

## Heartbeat
- Check your verifier queue for newly arrived **design / investigation** tickets
- Distill session notes into MEMORY.md
