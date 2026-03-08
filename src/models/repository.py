from src.models.kanban import Project, Agent


class Repository:
    _instance: "Repository | None" = None

    def __new__(cls) -> "Repository":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._projects: list[Project] = []
            cls._instance._agents: list[Agent] = []
            cls._instance._current_project_index: int | None = None
        return cls._instance

    @property
    def projects(self) -> list[Project]:
        return self._projects

    @property
    def agents(self) -> list[Agent]:
        return self._agents

    @property
    def current_project(self) -> Project | None:
        """One of the projects in _projects; None if empty or not set."""
        if not self._projects:
            return None
        i = self._current_project_index
        if i is None or not (0 <= i < len(self._projects)):
            return None
        return self._projects[i]

    @current_project.setter
    def current_project(self, project: Project | None) -> None:
        """Set current by Project reference."""
        if project is None:
            return
        try:
            self._current_project_index = self._projects.index(project)
        except ValueError:
            pass

    def set_current_by_name(self, name: str) -> None:
        """Set current project by name."""
        for i, p in enumerate(self._projects):
            if p["name"] == name:
                self._current_project_index = i
                return

    def clear(self) -> None:
        self._projects.clear()
        self._agents.clear()
        self._current_project_index = None


repository = Repository()
