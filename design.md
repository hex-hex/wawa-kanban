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
│   │   └── hdrs.py          # Shared headers (CSS, JS)
│   │
│   ├── models/              # Data models
│   │   └── kanban.py        # Kanban, Column, Ticket structures
│   │
│   ├── services/            # Business logic
│   │   ├── workspace.py     # File operations
│   │   └── tickets.py      # Ticket loading
│   │
│   ├── components/         # UI components
│   │   ├── board.py        # Kanban board
│   │   ├── ticket.py       # Ticket card/modal
│   │   └── common.py       # Shared components
│   │
│   └── routes/              # HTTP endpoints
│       ├── pages.py         # Page routes
│       └── api.py           # API routes
│
├── app.py                    # Entry point (imports from src/)
│
├── workspace/                # Kanban data (md files)
├── static/                  # CSS assets
├── scripts/                 # Build scripts
│
├── design.md
└── claude.md
```

## Layer Responsibilities

| Layer | Responsibility |
|-------|----------------|
| `app.py` | Entry point, routes, app setup |
| `config.py` | Constants only |
| `src/core/hdrs.py` | Shared HTML headers |
| `src/models/` | Data structures |
| `src/services/` | File I/O, data loading |
| `src/components/` | UI rendering (pure functions) |
| `src/routes/` | HTTP handling |

## Data Structure

Use plain dictionaries instead of dataclasses (no DB ORM pattern):

```python
# ticket as dict
{
    "id": "TICKET-001",
    "title": "Task name",
    "priority": "high",
    "created": "2024-01-01",
    "column": "backlog",
    "body": "description",
    "filename": "wawa.proj.default.implementation.setup-project-structure.md"
}
```

### Ticket File Naming

Format: `{project_id}.{phase}.{slug}.md`

| Part | Example | Description |
|------|---------|-------------|
| project_id | wawa.proj.default | Project identifier (dot-separated) |
| phase | implementation / design / investigation | Task phase |
| slug | setup-project-structure | Lowercase, hyphen-separated descriptive phrase |

Example: `wawa.proj.default.design.dashboard-layout.md`

## Extension Points

### Add Column
1. Add to `config.COLUMNS`
2. Create directory in `workspace/`

### Add Ticket Field
1. Update `src/services/tickets.py` → add key to dict
2. Update `src/components/ticket.py` → display field

### Add Feature
1. Component in `src/components/`
2. Service in `src/services/`
3. Route in `src/routes/`

## Next Steps

Confirm this structure, then I will:
1. Delete any created src files
2. Rebuild app.py with clean structure
