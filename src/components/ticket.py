from fasthtml.common import *
from src.models.kanban import Ticket
from src.utils.markdown import md_to_safe_html


def _ticket_card(ticket: Ticket, editable: bool = False):
    url = f"/api/ticket/{ticket['id']}?editable=1" if editable else f"/api/ticket/{ticket['id']}"
    locked = ticket.get("locked", False)
    mode_badge = Span(
        ticket["mode"].value.upper(),
        cls="text-xs px-2 py-0.5 rounded bg-slate-600/70 text-slate-300",
    )
    editing_badge = (
        Span("EDITING", cls="text-xs px-2 py-0.5 rounded bg-amber-800 text-gray-300")
        if (editable and locked)
        else None
    )
    right_badges = (
        Div(mode_badge, editing_badge, cls="flex items-center gap-1.5")
        if editing_badge
        else mode_badge
    )
    return Div(
        Div(
            Span(ticket["id"], cls="text-xs font-mono text-slate-500"),
            right_badges,
            cls="flex justify-between items-center mb-2",
        ),
        Div(
            md_to_safe_html(ticket["title"]),
            cls="font-semibold text-sm mb-2 line-clamp-2 text-slate-100 prose prose-invert prose-sm prose-p:my-1 prose-headings:my-1 prose-headings:text-slate-100 max-w-none",
        ),
        cls="bg-slate-700/95 border border-slate-600/80 rounded-lg p-4 shadow-sm hover:shadow-md hover:-translate-y-0.5 hover:border-slate-500 cursor-pointer transition-all duration-200",
        hx_get=url,
        hx_target="#ticket-modal",
        hx_swap="innerHTML",
    )


def TicketCard(ticket: Ticket):
    return _ticket_card(ticket, editable=False)


def EditableTicketCard(ticket: Ticket):
    """Same as TicketCard but requests modal with Edit Mode button."""
    return _ticket_card(ticket, editable=True)


def _modal_close_script():
    """Run dismiss animation then remove overlay. Call from close button."""
    return (
        "var o=this.closest('.modal-overlay');"
        "if(o){o.classList.add('modal-animate-out');"
        "o.addEventListener('animationend',function f(ev){"
        "if(ev.animationName==='modalOut'){o.removeEventListener('animationend',f);o.remove();"
        "document.dispatchEvent(new CustomEvent('modalClosed'));}});}"
    )


def _modal_header_buttons(editable: bool, ticket: Ticket | None = None):
    close_btn = Button(
        "Close",
        type="button",
        aria_label="Close",
        cls="shrink-0 px-3 py-1.5 text-sm font-medium bg-gray-700 text-gray-300 hover:text-gray-100 hover:bg-gray-600 rounded transition-colors outline-none cursor-pointer",
        onclick=_modal_close_script(),
    )
    if not editable or not ticket:
        return close_btn
    locked = ticket.get("locked", False)
    if locked:
        return (
            Button(
                "Save",
                type="button",
                aria_label="Save",
                cls="shrink-0 px-3 py-1.5 text-sm font-medium bg-green-900 text-green-200 hover:bg-green-800 rounded transition-colors outline-none cursor-pointer",
                hx_post=f"/api/ticket/{ticket['id']}/save",
                hx_swap="none",
            ),
            Button(
                "Give Up",
                type="button",
                aria_label="Give Up",
                cls="shrink-0 px-3 py-1.5 text-sm font-medium bg-red-900 text-red-200 hover:bg-red-800 rounded transition-colors outline-none cursor-pointer",
                hx_post=f"/api/ticket/{ticket['id']}/unlock",
                hx_swap="none",
            ),
            close_btn,
        )
    return (
        Button(
            "Lock & Edit",
            type="button",
            aria_label="Lock & Edit",
            cls="shrink-0 px-3 py-1.5 text-sm font-medium bg-blue-600 text-white hover:bg-blue-500 rounded transition-colors outline-none cursor-pointer",
            hx_post=f"/api/ticket/{ticket['id']}/lock",
            hx_swap="none",
        ),
        close_btn,
    )


def TicketModal(ticket: Ticket, editable: bool = False):
    header_buttons = _modal_header_buttons(editable, ticket)
    if not isinstance(header_buttons, tuple):
        header_buttons = (header_buttons,)
    return Div(
        Div(
            Div(
                H2(ticket["title"], cls="text-xl font-bold text-gray-100 flex-1 min-w-0 pr-2"),
                Div(*header_buttons, cls="flex items-center gap-2 shrink-0"),
                cls="flex items-center justify-between gap-2 mb-4",
            ),
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
                md_to_safe_html(ticket["description"] or "No description"),
                cls="text-gray-300 prose prose-invert prose-sm prose-p:text-gray-300 prose-headings:text-gray-100 max-w-none",
            ),
            cls="bg-gray-700 border border-gray-600 rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto shadow-2xl",
        ),
        cls="modal-overlay bg-black/75 fixed inset-0 flex items-center justify-center z-50 modal-animate-in",
        data_ticket_id=ticket["id"],
        data_editable="1" if editable else "0",
    )
