# Project Setup

## Start Development Server

```bash
uv run app.py
```

The app runs on http://localhost:5020

## CSS Development

Build CSS once:
```bash
npm run build:css
```

Watch mode (auto-rebuild on Python file changes):
```bash
npm run dev:css
```

## Project Structure

- `app.py` - FastHTML application entry point
- `uno.config.ts` - UnoCSS configuration
- `scripts/build-css.mjs` - Extracts cls/class from Python files and generates CSS
- `static/uno.css` - Generated CSS file (referenced by app.py)

## Coding Rules

- All text displayed on web pages must be in English

## Testing

- Any test that asserts page/UI display (what the user sees) must be an **e2e test** (HTTP request against the app), not a unit test (e.g. rendering a single component to string).

## Kanban Board

### Workspace Structure
```
workspace/projects/wawa_proj_default/
├── project.md
├── backlog/        # Tickets waiting to be picked up
├── implementing/   # Tickets currently being worked on
├── verifying/     # Tickets awaiting verification
└── finished/      # Completed tickets
```

### Ticket Format
Each ticket is a markdown file with frontmatter:
```markdown
---
id: TICKET-001
title: Ticket title
priority: high|medium|low
created: 2024-01-01
---

# Description

Ticket content here...
```
