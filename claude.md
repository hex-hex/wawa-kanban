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

- **以不手写 inline style 为准。** No inline styles: do not use `style=` on any element. Use only `cls` (UnoCSS utility classes) for styling.
- All text displayed on web pages must be in English.
- **禁止使用手写的 CSS。** Do not add or maintain hand-written CSS (e.g. in `static/kanban.css` or any `.css` file). All styling must come from `cls` in Python and the generated `static/uno.css` (run `npm run build:css` or `npm run dev:css`).
- **CSS not applied or class missing from `static/uno.css`?** The CSS build may not have run. Remind the user to run `npm run build:css` (one-off) or `npm run dev:css` (watch), or run it for them: `npm run build:css`.

## Testing

- Any test that asserts page/UI display (what the user sees) must be an **e2e test** (HTTP request against the app), not a unit test (e.g. rendering a single component to string).

## Page Layout

- **app.py**: `fast_app(pico=False)` — Pico CSS must be disabled to avoid max-width/centering that restricts layout.
- **Root** (`index_page`): `Titled( Div(id="wawa-app" cls="bg-gray-950 min-h-screen text-gray-100") )` → full-page wrapper; children: `_main_content()`, `Div(id="ticket-modal")`.
- **Main content** (`_main_content`): `Div(id="main-content" cls="w-full")` → full width; children: **NavBar**, **Div**(id="kanban-board" cls="w-full overflow-x-auto").
- **Preflights** (uno.config.ts): Override `main.container`, `html`, `body` for full viewport width; no side or top margin/padding. E2E `test_layout_full_width_no_side_margins` verifies this.
- **KanbanBoard**: Outer `overflow-x-auto w-full max-w-full`. Inner flex row `flex flex-nowrap gap-4 pb-4 w-full min-w-[...]` so columns fill width and scroll on small screens.
- **KanbanColumn**: Each column `flex flex-col flex-1 min-w-52`; header uses Uno color classes via `cls` (e.g. `bg-{uno_color}-500/20 border-{uno_color}-500`); body scrollable with `overflow-y-auto max-h-[calc(100vh-200px)] min-h-[120px] flex-1`.

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
