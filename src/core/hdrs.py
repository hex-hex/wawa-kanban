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

  document.addEventListener('htmx:beforeSwap', function(ev) {
    if (ev.detail && ev.detail.target && ev.detail.target.id === 'ticket-modal') {
      if (window.__ticketEasyMDE) {
        window.__ticketEasyMDE.toTextArea();
        window.__ticketEasyMDE = null;
      }
    }
  });

  document.addEventListener('htmx:afterSwap', function(ev) {
    if (ev.detail && ev.detail.target && ev.detail.target.id === 'ticket-modal') {
      if (refreshTimerId) { clearTimeout(refreshTimerId); refreshTimerId = null; }
      var overlay = document.querySelector('#ticket-modal .modal-overlay');
      var textarea = document.getElementById('ticket-description-editor');
      if (overlay && overlay.getAttribute('data-locked') === '1' && textarea && typeof EasyMDE !== 'undefined') {
        window.__ticketEasyMDE = new EasyMDE({
          element: textarea,
          autofocus: false,
          spellChecker: false,
          status: false,
          minHeight: '200px',
          maxHeight: 'calc(80vh - 220px)',
          toolbar: ['bold', 'italic', 'heading', '|', 'quote', 'unordered-list', 'ordered-list', '|', 'link', 'code', 'table', '|', 'preview', 'side-by-side', 'fullscreen', '|', 'guide']
        });
      }
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
        Link(
            rel="stylesheet",
            href="https://cdn.jsdelivr.net/npm/easymde@2.18.0/dist/easymde.min.css",
            type="text/css",
        ),
        Script(src="https://unpkg.com/htmx.org@2"),
        Script(src="https://cdn.jsdelivr.net/npm/easymde@2.18.0/dist/easymde.min.js"),
        _refresh_via_sse_script(),
    )
