from pathlib import Path

WORKSPACE_PATH = Path("workspace/projects/wawa_proj_default")

COLUMNS = {
    "backlog": {"name": "Backlog", "color": "#6B7280"},
    "implementing": {"name": "Implementing", "color": "#3B82F6"},
    "verifying": {"name": "Verifying", "color": "#F59E0B"},
    "finished": {"name": "Finished", "color": "#10B981"},
}

PRIORITY_COLORS = {
    "high": "#EF4444",
    "medium": "#F59E0B",
    "low": "#9CA3AF",
}

APP_TITLE = "Wawa Kanban"
