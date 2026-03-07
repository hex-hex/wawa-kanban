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
- **Never use inline style.** Use only `cls` (UnoCSS/Tailwind classes) or custom classes in `static/kanban.css`. Do not add `style=` to elements.
- **CSS not applied or class missing from `static/uno.css`?** The CSS build may not have run. Remind the user to run `npm run build:css` (one-off) or `npm run dev:css` (watch), or run it for them: `npm run build:css`.

## Testing

- Any test that asserts page/UI display (what the user sees) must be an **e2e test** (HTTP request against the app), not a unit test (e.g. rendering a single component to string).

## Page Layout

- **Root** (`index_page`): `Titled( Div( cls="bg-gray-900 min-h-screen text-gray-100" ) )` → full-page wrapper; children: `_main_content()`, `Div(id="ticket-modal")`.
- **Main content** (`_main_content`): `Div(id="main-content")` → no width constraint; children: **NavBar**, **Container** (id="kanban-board").
- **NavBar**: Outer `sticky top-0 bg-gray-800 px-6 py-3 z-50`. Inner content: `max-w-7xl mx-auto px-4` (content max 80rem, centered) + `flex justify-between` (title left, select + Refresh right).
- **Container** (kanban wrapper): Default `w-full p-6 mt-8`; for board we add `px-0 overflow-x-auto` so the board is full width with no horizontal padding.
- **KanbanBoard**: Outer div: scroll container `overflow-x-auto w-full max-w-full`. Inner div: flex row `flex flex-nowrap gap-4 pb-4 w-full` + `min-w-[...]` so columns fill width and scroll on small screens.
- **KanbanColumn**: Each column `flex flex-col flex-1 min-w-52`; header uses column color classes from `static/kanban.css`; body scrollable with `overflow-y-auto max-h-[calc(100vh-200px)] min-h-[120px] flex-1`.

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
