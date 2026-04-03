from fasthtml.common import *
from src.models.kanban import AgentPosition, Ticket, TicketStatus
from src.components.common import CardCloseButton, CardBodyScroll
from src.utils.markdown import md_to_safe_html

_AGENT_POSITION_LABEL: dict[AgentPosition, str] = {
    AgentPosition.DEVELOPER: "Developer",
    AgentPosition.DESIGNER: "Designer",
    AgentPosition.INFO_OFFICER: "Info officer",
    AgentPosition.VERIFIER: "Verifier",
}


def _agent_position_label(position: AgentPosition) -> str:
    return _AGENT_POSITION_LABEL.get(position, position.value.replace("_", " ").title())


def _ticket_card(ticket: Ticket, editable: bool = False, agent_badge=None):
    url = f"/api/ticket/{ticket['id']}?editable=1" if editable else f"/api/ticket/{ticket['id']}"
    locked = ticket.get("locked", False)
    mode_badge = Span(
        ticket["mode"].value.upper(),
        cls="text-xs px-2 py-0.5 rounded bg-slate-600/70 text-slate-300",
    )
    editing_badge = (
        Span(
            "Locked & Editing",
            cls="text-xs px-2 py-0.5 rounded bg-slate-600/90 text-blue-300 border border-blue-500/40",
        )
        if (editable and locked)
        else None
    )
    badges = [b for b in (mode_badge, editing_badge, agent_badge) if b is not None]
    right_badges = Div(*badges, cls="shrink-0 flex items-center gap-1.5 flex-wrap")
    return Div(
        Div(
            Span(
                ticket["id"],
                cls="min-w-0 flex-1 text-xs font-mono text-slate-500 break-all",
            ),
            right_badges,
            cls="flex flex-wrap gap-x-2 gap-y-1 items-start mb-2 min-w-0",
        ),
        Div(
            md_to_safe_html(ticket["title"]),
            cls="font-semibold text-sm mb-2 line-clamp-2 text-slate-100 prose prose-invert prose-sm prose-p:my-1 prose-headings:my-1 prose-headings:text-slate-100 max-w-none",
        ),
        cls="min-w-0 bg-slate-700/95 border border-slate-600/80 rounded-lg p-4 shadow-sm hover:shadow-md hover:-translate-y-0.5 hover:border-slate-500 cursor-pointer transition-all duration-200",
        hx_get=url,
        hx_target="#ticket-modal",
        hx_swap="innerHTML",
    )


def TicketCard(ticket: Ticket):
    return _ticket_card(ticket, editable=False)


def EditableTicketCard(ticket: Ticket):
    """Same as TicketCard but requests modal with Edit Mode button."""
    return _ticket_card(ticket, editable=True)


def UnderGoingTicket(ticket: Ticket, col_id):
    """Card for In Progress / Verifying: shows Position + Agent name as badge when ticket is from agent directory."""
    from src.services.tickets import get_agent_info

    info = get_agent_info(ticket["id"])
    label = f"{_agent_position_label(info[0])}: {info[1]}" if info else None
    if col_id == TicketStatus.IN_PROGRESS and label:
        agent_badge = Span(label, cls="text-xs px-2 py-0.5 rounded bg-blue-500/50 text-blue-300 border border-blue-500/40")
    elif col_id == TicketStatus.VERIFYING and label:
        agent_badge = Span(label, cls="text-xs px-2 py-0.5 rounded bg-violet-500/50 text-violet-300 border border-violet-500/40")
    else:
        agent_badge = None
    return _ticket_card(ticket, editable=False, agent_badge=agent_badge)


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
    close_btn = CardCloseButton(onclick=_modal_close_script())
    if not editable or not ticket:
        return close_btn
    locked = ticket.get("locked", False)
    if locked:
        return (
            Button(
                "Confirm",
                type="submit",
                form="ticket-edit-form",
                aria_label="Confirm",
                cls="shrink-0 px-3 py-1.5 text-sm font-medium bg-emerald-700 text-emerald-50 hover:bg-emerald-600 rounded transition-colors outline-none cursor-pointer",
                hx_post=f"/api/ticket/{ticket['id']}/save",
                hx_swap="none",
            ),
            Button(
                "Save Draft",
                type="button",
                aria_label="Save Draft",
                cls="shrink-0 px-3 py-1.5 text-sm font-medium bg-amber-700 text-amber-50 hover:bg-amber-600 rounded transition-colors outline-none cursor-pointer",
                hx_post=f"/api/ticket/{ticket['id']}/draft",
                hx_include="#ticket-edit-form",
                hx_swap="none",
            ),
            Button(
                "Give Up",
                type="button",
                aria_label="Give Up",
                cls="shrink-0 px-3 py-1.5 text-sm font-medium bg-red-800 text-red-100 hover:bg-red-700 rounded transition-colors outline-none cursor-pointer",
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


def _modal_body(ticket: Ticket, locked: bool):
    """When locked: form with textarea for EasyMDE. Otherwise: read-only markdown."""
    raw_description = ticket.get("description") or ""
    if locked:
        return Form(
            CardBodyScroll(
                Textarea(
                    raw_description,
                    id="ticket-description-editor",
                    name="description",
                    cls="w-full min-h-[200px] p-3 text-gray-100 bg-gray-800 border border-gray-600 rounded font-mono text-sm resize-y",
                ),
            ),
            id="ticket-edit-form",
            hx_post=f"/api/ticket/{ticket['id']}/save",
            hx_swap="none",
        )
    return CardBodyScroll(
        Div(
            md_to_safe_html(raw_description or "No description"),
            cls="text-gray-300 prose prose-invert prose-sm prose-p:text-gray-300 prose-headings:text-gray-100 max-w-none",
        ),
    )


def TicketModal(ticket: Ticket, editable: bool = False):
    header_buttons = _modal_header_buttons(editable, ticket)
    if not isinstance(header_buttons, tuple):
        header_buttons = (header_buttons,)
    locked = ticket.get("locked", False)
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
            _modal_body(ticket, locked),
            cls="bg-gray-700 border border-gray-600 rounded-lg p-6 max-w-2xl w-full max-h-[80vh] flex flex-col shadow-2xl",
        ),
        cls="modal-overlay bg-black/75 fixed inset-0 flex items-center justify-center z-50 modal-animate-in",
        data_ticket_id=ticket["id"],
        data_editable="1" if editable else "0",
        data_locked="1" if locked else "0",
    )
