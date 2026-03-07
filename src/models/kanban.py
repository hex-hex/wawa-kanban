from typing import TypedDict, List
from enum import Enum


class TaskMode(str, Enum):
    IMPLEMENTATION = "implementation"
    INVESTIGATION = "investigation"
    DESIGN = "design"


class AgentPosition(str, Enum):
    DEVELOPER = "developer"
    DESIGNER = "designer"
    TESTER = "tester"


class Ticket(TypedDict):
    id: str
    title: str
    project: str
    description: str
    status: str
    mode: TaskMode


class Project(TypedDict):
    name: str
    tickets: List[Ticket]


class Agent(TypedDict):
    name: str
    position: AgentPosition
    ticket: Ticket
