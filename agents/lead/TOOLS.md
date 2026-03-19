# TOOLS.md — Team Lead

Reference for ticket naming and content. Use this when creating or editing tickets.

## Workspace layout

- **Projects:** `workspace/projects/{project_id}/` (e.g. `wawa.proj.default`)
- **Project todos:** `workspace/projects/{project_id}/todos/` — create new tickets here
- **project_id** format: `wawa.proj.{project_name}` (e.g. `wawa.proj.default`)

Determine the current project from conversation and context; all new tickets go into that project’s `todos/` folder.

## Ticket file naming

**Format:** `{project_id}.{mode}.{slug}.md`

| Part       | Description |
|-----------|-------------|
| project_id | e.g. `wawa.proj.default` |
| mode       | `implementation` \| `design` \| `investigation` |
| slug       | Lowercase, hyphen-separated phrase (no dots) |

**Example:** `wawa.proj.default.implementation.setup-project-structure.md`

## Ticket modes and content

### Implementation

- **Purpose:** Developer can implement with minimal back-and-forth.
- **Include in the ticket (as much as possible):**
  - **Implementation approach:** Suggested steps, key modules or layers, integration points.
  - **Code and file norms:** Where new code lives, naming, structure, conventions.
  - **Context for investigation:** What to read or explore first (files, docs, patterns), and what “understood enough” means for this task.

### Design

- **Purpose:** Designer knows scope and direction.
- **Include in the ticket:**
  - **User stories:** Who, what goal, in what situation.
  - **Design boundaries:** In scope vs out of scope, constraints (e.g. reuse X, don’t change Y).
  - **Design-language preferences:** Tone (e.g. minimal, playful), patterns to follow or avoid, any reference surfaces.

### Investigation

- **Purpose:** Exploratory work (spike, research).
- **Include:** The question to answer and what “done” looks like (e.g. recommendation, doc, or follow-up tickets).

## Frontmatter

Use YAML frontmatter at the top of each ticket:

```yaml
---
id: TICKET-001              # optional; fallback: filename stem
title: Short task name      # optional; fallback: filename stem
mode: implementation        # implementation | design | investigation
---
```

Then the markdown body with description, approach, boundaries, or user stories as above.
