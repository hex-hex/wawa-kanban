from typing import TypedDict, List, NotRequired
from enum import Enum


class TaskMode(str, Enum):
    IMPLEMENTATION = "implementation"
    INVESTIGATION = "investigation"
    DESIGN = "design"


class TicketStatus(str, Enum):
    TODOS = "todos"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_VERIFICATION = "waiting_for_verification"
    VERIFYING = "verifying"
    FINISHED = "finished"


class AgentPosition(str, Enum):
    DEVELOPER = "developer"
    DESIGNER = "designer"
    TESTER = "tester"


class Ticket(TypedDict):
    id: str
    title: str
    project: str
    description: str
    status: TicketStatus
    mode: TaskMode
    created_at: NotRequired[str]  # ISO format from file birthtime or mtime
    updated_at: NotRequired[str]  # ISO format from file mtime


class Project(TypedDict):
    name: str
    tickets: List[Ticket]


class Agent(TypedDict):
    name: str
    position: AgentPosition
    ticket: Ticket
