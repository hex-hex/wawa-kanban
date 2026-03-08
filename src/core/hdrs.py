from fasthtml.common import Link, Script


def _refresh_via_sse_script():
    return Script(
        """
document.addEventListener('DOMContentLoaded', function() {
  var btn = document.getElementById('btn-refresh');
  var board = document.getElementById('kanban-board');
  if (!btn || !board) return;
  var refreshTimerId = null;
  var INTERVAL_MS = 15000;

  function applyRefresh(payload, forceCloseModal) {
    if (payload.html !== undefined) {
      board.innerHTML = payload.html;
      if (typeof htmx !== 'undefined') htmx.process(board);
    }
    var modal = document.getElementById('ticket-modal');
    var overlay = modal ? modal.querySelector('.modal-overlay') : null;
    if (forceCloseModal) {
      if (modal) { modal.innerHTML = ''; document.dispatchEvent(new CustomEvent('modalClosed')); }
      return;
    }
    var ticketId = overlay ? overlay.getAttribute('data-ticket-id') : null;
    var existingIds = payload.existing_ids || [];
    if (ticketId && existingIds.indexOf(ticketId) >= 0) {
      var editable = overlay ? overlay.getAttribute('data-editable') : '0';
      fetch('/api/ticket/' + ticketId + (editable === '1' ? '?editable=1' : ''))
        .then(function(r) { return r.text(); })
        .then(function(html) {
          if (modal) { modal.innerHTML = html; if (typeof htmx !== 'undefined') htmx.process(modal); }
        })
        .catch(function() {});
    } else if (modal && overlay) {
      modal.innerHTML = '';
      document.dispatchEvent(new CustomEvent('modalClosed'));
    }
  }

  function parseSsePayload(text) {
    var data = '';
    text.split('\\n').forEach(function(line) {
      if (line.indexOf('data: ') === 0) data += line.slice(6) + '\\n';
    });
    data = data.trim();
    if (!data) return null;
    try { return JSON.parse(data); } catch (err) { return null; }
  }

  function doRefresh() {
    if (document.body && document.body.dataset.noAutoRefresh === '1') return;
    fetch('/api/refresh-sse', { headers: { 'Accept': 'text/event-stream' } })
      .then(function(r) { return r.text(); })
      .then(function(text) {
        var payload = parseSsePayload(text);
        if (payload) applyRefresh(payload);
        if (document.body && document.body.dataset.noAutoRefresh === '1') return;
        refreshTimerId = setTimeout(doRefresh, INTERVAL_MS);
        if (typeof window !== 'undefined') window.__refreshTimerId = refreshTimerId;
      })
      .catch(function() {
        if (document.body && document.body.dataset.noAutoRefresh === '1') return;
        refreshTimerId = setTimeout(doRefresh, INTERVAL_MS);
        if (typeof window !== 'undefined') window.__refreshTimerId = refreshTimerId;
      });
  }

  function onRefreshBoard(ev) {
    var closeModal = ev.detail && ev.detail.closeModal;
    fetch('/api/refresh-sse', { headers: { 'Accept': 'text/event-stream' } })
      .then(function(r) { return r.text(); })
      .then(function(text) {
        var payload = parseSsePayload(text);
        if (payload) applyRefresh(payload, !!closeModal);
      })
      .catch(function() {});
  }

  document.addEventListener('refreshBoard', onRefreshBoard);

  document.addEventListener('htmx:afterSwap', function(ev) {
    if (ev.detail && ev.detail.target && ev.detail.target.id === 'ticket-modal') {
      if (refreshTimerId) { clearTimeout(refreshTimerId); refreshTimerId = null; }
    }
  });

  document.addEventListener('modalClosed', function() {
    if (document.body && document.body.dataset.noAutoRefresh === '1') return;
    if (refreshTimerId) clearTimeout(refreshTimerId);
    refreshTimerId = null;
    doRefresh();
  });

  document.addEventListener('keydown', function(ev) {
    if (ev.key !== 'Escape') return;
    var modal = document.getElementById('ticket-modal');
    var o = modal ? modal.querySelector('.modal-overlay') : null;
    if (!o) return;
    o.classList.add('modal-animate-out');
    o.addEventListener('animationend', function f(e) {
      if (e.animationName === 'modalOut') {
        o.removeEventListener('animationend', f);
        o.remove();
        document.dispatchEvent(new CustomEvent('modalClosed'));
      }
    });
  });

  btn.addEventListener('click', function(e) {
    e.preventDefault();
    if (refreshTimerId) clearTimeout(refreshTimerId);
    refreshTimerId = null;
    doRefresh();
  });

  refreshTimerId = setTimeout(doRefresh, INTERVAL_MS);
  if (typeof window !== 'undefined') window.__refreshTimerId = refreshTimerId;
});
""",
        type="text/javascript",
    )


def get_hdrs():
    return (
        Link(rel="stylesheet", href="/static/uno.css", type="text/css"),
        Script(src="https://unpkg.com/htmx.org@2"),
        _refresh_via_sse_script(),
    )
