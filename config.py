from pathlib import Path

WORKSPACE_PATH = Path("workspace/projects/wawa.proj.default")

COLUMNS = {
    "todos": {"name": "Todos", "color": "#6B7280"},
    "waiting_for_test": {"name": "Waiting for Test", "color": "#F59E0B"},
    "finished": {"name": "Finished", "color": "#10B981"},
}

PRIORITY_COLORS = {
    "high": "#EF4444",
    "medium": "#F59E0B",
    "low": "#9CA3AF",
}

APP_TITLE = "Wawa Kanban"
