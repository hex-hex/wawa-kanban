from fasthtml.common import *
from src.models.kanban import Ticket


def TicketCard(ticket: Ticket):
    return Div(
        Div(
            Span(ticket["id"], cls="text-xs font-mono text-gray-400"),
            Span(
                ticket["mode"].value.upper(),
                cls="text-xs px-2 py-0.5 rounded bg-gray-600 text-gray-300",
            ),
            cls="flex justify-between items-center mb-2",
        ),
        Div(
            ticket["title"], cls="font-semibold text-sm mb-2 line-clamp-2 text-gray-200"
        ),
        cls=(
            "bg-gray-700 rounded-lg p-3 shadow-sm border border-gray-600 "
            "hover:shadow-md hover:-translate-y-0.5 cursor-pointer transition-all duration-200"
        ),
        hx_get=f"/api/ticket/{ticket['id']}",
        hx_target="#ticket-modal",
        hx_swap="innerHTML",
    )


def TicketModal(ticket: Ticket):
    return Div(
        Div(
            Div(
                H2(ticket["title"], cls="text-xl font-bold mb-4 text-gray-100"),
                Div(
                    Span(
                        ticket["mode"].value.upper(),
                        cls="px-2 py-0.5 rounded text-xs font-medium bg-gray-600 text-gray-300",
                    ),
                    Span(ticket["id"], cls="ml-2 font-mono text-sm text-gray-400"),
                    cls="flex items-center gap-2 mb-4",
                ),
                Hr(cls="my-4 border-gray-600"),
                Div(
                    ticket["description"] or "No description",
                    cls="text-gray-300 whitespace-pre-wrap",
                ),
                cls="bg-gray-800 rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto",
            ),
            cls="fixed inset-0 bg-black/70 flex items-center justify-center z-50",
            onclick="if(event.target === this) this.remove()",
        ),
        onclick="if(event.target.id === 'ticket-modal') this.remove()",
        id="ticket-modal",
        cls="fixed inset-0 bg-black/70 flex items-center justify-center z-50",
    )
