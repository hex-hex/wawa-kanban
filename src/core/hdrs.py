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

  function updateBoardFromSse(text) {
    var data = '';
    text.split('\\n').forEach(function(line) {
      if (line.indexOf('data: ') === 0) data += line.slice(6) + '\\n';
    });
    data = data.trim();
    if (!data) return;
    try {
      var payload = JSON.parse(data);
      if (payload.html !== undefined) {
        board.innerHTML = payload.html;
        if (typeof htmx !== 'undefined') htmx.process(board);
      }
    } catch (err) {}
  }

  function doRefresh() {
    if (document.body && document.body.dataset.noAutoRefresh === '1') return;
    fetch('/api/refresh-sse', { headers: { 'Accept': 'text/event-stream' } })
      .then(function(r) { return r.text(); })
      .then(function(text) {
        updateBoardFromSse(text);
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

  function refreshBoardAndCloseModal() {
    fetch('/api/refresh-sse', { headers: { 'Accept': 'text/event-stream' } })
      .then(function(r) { return r.text(); })
      .then(function(text) {
        updateBoardFromSse(text);
        var modal = document.getElementById('ticket-modal');
        if (modal) modal.innerHTML = '';
      })
      .catch(function() {});
  }

  document.addEventListener('refreshBoard', refreshBoardAndCloseModal);

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
