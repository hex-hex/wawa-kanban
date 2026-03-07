from typing import TypedDict, List
from enum import Enum


class TicketMode(str, Enum):
    CODE_DEVELOPMENT = "code_development"
    DESIGN = "design"


class Ticket(TypedDict):
    id: str
    title: str
    project: str
    description: str
    status: str
    mode: TicketMode
    priority: str


class Project(TypedDict):
    name: str
    tickets: List[Ticket]


class Agent(TypedDict):
    name: str
    tickets: List[Ticket]
