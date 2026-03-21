# Wawa Kanban - Engineering Design

## Project Overview

| Aspect | Value |
|--------|-------|
| Type | File-system based kanban board |
| Framework | FastHTML + HTMX + UnoCSS |
| Database | None |
| Data Source | Markdown files in workspace |

## Directory Structure

```
wawa-kanban/
├── app.py                    # Entry point & routing
├── config.py                 # Configuration
│
├── src/                      # Source code
│   ├── core/                 # App initialization
│   │   └── hdrs.py           # Shared headers (CSS, JS)
│   │
│   ├── models/               # Data models
│   │   └── kanban.py         # Kanban, Ticket, Project, Agent structures
│   │
│   ├── services/             # Business logic
│   │   ├── workspace.py      # Frontmatter parse/serialize
│   │   └── tickets.py        # Ticket loading
│   │
│   ├── components/           # UI components
│   │   ├── board.py          # Kanban board
│   │   ├── column.py         # Kanban column
│   │   ├── ticket.py         # Ticket card/modal
│   │   └── common.py         # Shared components
│   │
│   └── routes/               # HTTP endpoints
│       ├── pages.py          # Page routes
│       └── api.py            # API routes
│
├── workspace/                # Kanban data (env: WAWA_WORKSPACE_PATH; local default: fixtures/workspace; Docker image: /app/.workspace)
│   ├── projects/             # Project tickets
│   └── agents/               # Agent tickets (In Progress, Verifying)
│
├── static/                   # CSS assets (uno.css)
├── scripts/                  # Build scripts (build-css.mjs)
│
├── design.md
└── claude.md
```

## Workspace Structure

```
workspace/
├── projects/                         # Project tickets
│   └── {project_id}/                 # e.g. wawa.proj.default
│       ├── todos/                    # TODOS column
│       ├── waiting_for_verification/ # Waiting for Verification column
│       └── finished/                 # Finished column
│
└── agents/                           # Agent tickets (flat dirs, no status subfolders)
    ├── developers/
    │   └── {name}/                   # e.g. default
    │       └── *.md                  # → In Progress column
    ├── designers/
    │   └── {name}/
    │       └── *.md                  # → In Progress column
    └── verifiers/
        ├── code-verifier/            # implementation tickets in Verifying
        │   └── *.md
        └── general-verifier/         # design / investigation tickets in Verifying
            └── *.md
```

**Column loading rules:**

| Column | Source |
|--------|--------|
| TODOS | projects/{project_id}/todos/ |
| IN_PROGRESS | agents/developers/{name}/ + agents/designers/{name}/ (not from projects) |
| WAITING_FOR_VERIFICATION | projects/{project_id}/waiting_for_verification/ |
| VERIFYING | agents/verifiers/code-verifier/ (implementation) and agents/verifiers/general-verifier/ (design, investigation, other) — not from projects |
| FINISHED | projects/{project_id}/finished/ |

Agent tickets show a badge (Position + Agent name, e.g. "Developer: default") derived from the ticket file path at render time.

## Data Structure

### Ticket

Plain dict, no DB. Fields come from frontmatter and file metadata:

```python
{
    "id": str,           # frontmatter["id"] or filename stem
    "title": str,        # frontmatter["title"] or filename stem
    "project": str,      # parsed from filename (project_id)
    "description": str,  # markdown body
    "status": TicketStatus,
    "mode": TaskMode,    # implementation / design / investigation
    "locked": bool,      # True if .md.lock
    "created_at": str,   # ISO from file birthtime
    "updated_at": str,   # ISO from file mtime
}
```

### Ticket File Naming

**One global rule** (all tickets, same format):

Format: `{project_id}.{mode}.{slug}.md`

| Part | Description |
|------|-------------|
| project_id | wawa.proj.{project_name} (e.g. wawa.proj.default) |
| mode | implementation / design / investigation |
| slug | Lowercase, **hyphen-separated** phrase (no dots) |

Example: `wawa.proj.default.implementation.setup-project-structure.md`

Agent tickets use the same format (agent info comes from file path `agents/{type}/{name}/`).

Ticket files can be moved (e.g. via `mv`) between `projects/` and `agents/` folders; the filename stays unchanged. The same file parsed in projects yields project-column status; in agents yields In Progress or Verifying. Parsing logic is identical.

### Ticket Frontmatter

```yaml
---
id: TICKET-001              # optional; fallback: filename stem
title: Task name            # optional; fallback: filename stem
mode: implementation        # implementation | design | investigation
---

# Markdown body

Description content...
```

- **id**: Used for lookup. If missing, filename stem is used.
- **title**: Display title. If missing, filename stem is used.
- **mode**: Task mode; must match one of the parts in filename for parsing.

## Layer Responsibilities

| Layer | Responsibility |
|-------|----------------|
| app.py | Entry point, routes, app setup |
| config.py | Constants (WORKSPACE_PATH, COLUMNS, etc.) |
| src/core/hdrs.py | Shared HTML headers |
| src/models/ | Data structures (TypedDict, Enum) |
| src/services/ | File I/O, ticket loading |
| src/components/ | UI rendering (pure functions) |
| src/routes/ | HTTP handling |

## Extension Points

### Add Column

1. Add `TicketStatus` enum value and entry in `config.COLUMNS`
2. Add to `config.COLUMN_ORDER`
3. Create directory in `workspace/projects/{project_id}/` if project-specific

### Add Ticket Field

1. Update `src/models/kanban.py` Ticket TypedDict
2. Update `src/services/tickets.py` → load and add to ticket dict
3. Update `src/components/ticket.py` → display field

### Add Feature

1. Component in `src/components/`
2. Service in `src/services/`
3. Route in `src/routes/`
