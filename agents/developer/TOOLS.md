# TOOLS.md — Developer

## My folder

By default this agent is named **Default Developer** and uses:

- Ticket folder: `workspace/agents/developers/default/`

If the agent name is customized, use:

- Ticket folder: `workspace/agents/developers/{name}/`

In all cases:

- **No ticket file in this folder** → no op.
- **One ticket file** (e.g. `wawa.proj.default.implementation.fix-login-bug.md`) → work on it until done, then move it as below.

## When the ticket is done

Move the ticket file to the **same project’s** `waiting_for_verification/` folder:

- **Path:** `workspace/projects/{project_id}/waiting_for_verification/`
- **project_id** comes from the ticket filename: first part before the first dot-separated `implementation` or `design` or `investigation`.  
  Example: `wawa.proj.default.implementation.fix-login-bug.md` → project_id is `wawa.proj.default` → move to `workspace/projects/wawa.proj.default/waiting_for_verification/`.

Keep the filename unchanged when moving. Do not move until tests pass and you have appended the implementation summary to the ticket file.
