from src.models.kanban import Project, Agent


class Repository:
    _instance: "Repository | None" = None

    def __new__(cls) -> "Repository":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._projects: list[Project] = []
            cls._instance._agents: list[Agent] = []
        return cls._instance

    @property
    def projects(self) -> list[Project]:
        return self._projects

    @property
    def agents(self) -> list[Agent]:
        return self._agents

    def clear(self) -> None:
        self._projects.clear()
        self._agents.clear()


repository = Repository()
