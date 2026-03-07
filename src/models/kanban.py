from typing import TypedDict, List


class Ticket(TypedDict):
    project: str
    description: str
    status: str


class Project(TypedDict):
    name: str
    tickets: List[Ticket]


class Agent(TypedDict):
    name: str
    tickets: List[Ticket]
