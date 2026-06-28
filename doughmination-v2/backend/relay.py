"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
Tunnel via SSH
(`ssh -L 9091:localhost:9091 host`) if accessing remotely.
"""

import sqlite3
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse

from helper import DB_PATH, LogQuery


app = FastAPI(
    title="Visitor Log Relay",
    description="Browse visitor_logs.db",
    docs_url="/docs",
    redoc_url=None,
)

_query = LogQuery(db_path=DB_PATH)


# ---------------------------------------------------------------------------
# JSON API
# ---------------------------------------------------------------------------

@app.get("/api/stats")
def api_stats():
    try:
        conn = sqlite3.connect(_query.db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM visitor_logs")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT ip_address) FROM visitor_logs")
        unique_ips = cur.fetchone()[0]
        cur.execute(
            "SELECT COUNT(*) FROM visitor_logs "
            "WHERE unix_timestamp > strftime('%s', 'now') - 86400"
        )
        last_24h = cur.fetchone()[0]
        cur.execute(
            "SELECT path, COUNT(*) c FROM visitor_logs "
            "GROUP BY path ORDER BY c DESC LIMIT 10"
        )
        top_paths = [{"path": r[0], "count": r[1]} for r in cur.fetchall()]
        conn.close()
        return {
            "total_visits": total,
            "unique_ips": unique_ips,
            "last_24h": last_24h,
            "top_paths": top_paths,
        }
    except sqlite3.OperationalError as e:
        raise HTTPException(500, f"DB error: {e}")


@app.get("/api/recent")
def api_recent(limit: int = Query(100, ge=1, le=1000)):
    conn = sqlite3.connect(_query.db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT id, timestamp, ip_address, method, path, response_code, "
        "user_agent, referer FROM visitor_logs "
        "ORDER BY unix_timestamp DESC LIMIT ?",
        (limit,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


@app.get("/api/by-ip/{ip}")
def api_by_ip(ip: str):
    return _query.find_by_ip(ip)


@app.get("/api/by-path")
def api_by_path(q: str = Query(..., min_length=1)):
    return _query.find_by_path(q)


@app.get("/api/suspicious")
def api_suspicious():
    return _query.find_suspicious_patterns()


@app.get("/api/entry/{entry_id}")
def api_entry(entry_id: int):
    conn = sqlite3.connect(_query.db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM visitor_logs WHERE id = ?", (entry_id,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        raise HTTPException(404, "Entry not found")
    return dict(row)


# ---------------------------------------------------------------------------
# HTML UI (single page, vanilla JS, no build step)
# ---------------------------------------------------------------------------

INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Visitor Log Relay</title>
<style>
  :root { color-scheme: dark light; }
  body { font: 14px/1.4 system-ui, sans-serif; margin: 0; padding: 16px;
         background: #0e0f12; color: #e6e7eb; }
  h1 { margin: 0 0 8px; font-size: 18px; }
  .stats { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 12px; }
  .stat { background: #1a1c22; border: 1px solid #272a32; border-radius: 8px;
          padding: 8px 12px; min-width: 120px; }
  .stat .n { font-size: 22px; font-weight: 600; }
  .stat .l { font-size: 11px; opacity: 0.7; text-transform: uppercase; letter-spacing: 0.05em; }
  .controls { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; align-items: center; }
  input, select, button { font: inherit; padding: 6px 10px; border-radius: 6px;
                          border: 1px solid #2c2f38; background: #1a1c22;
                          color: inherit; }
  button { cursor: pointer; }
  button.primary { background: #3a5fcf; border-color: #3a5fcf; }
  table { width: 100%; border-collapse: collapse; background: #14161b;
          border: 1px solid #272a32; border-radius: 8px; overflow: hidden; }
  th, td { padding: 6px 10px; text-align: left; border-bottom: 1px solid #1f2229;
           font-size: 13px; vertical-align: top; }
  th { background: #1a1c22; font-weight: 600; }
  tr:hover { background: #181a20; cursor: pointer; }
  td.ip { font-family: ui-monospace, monospace; }
  td.path { font-family: ui-monospace, monospace; max-width: 320px;
            overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .code-2xx { color: #6ee787; }
  .code-3xx { color: #f0c674; }
  .code-4xx, .code-5xx { color: #ff6b6b; }
  .top-paths { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; }
  .top-paths span { background: #1a1c22; border: 1px solid #272a32;
                    border-radius: 4px; padding: 2px 6px; font-size: 12px;
                    font-family: ui-monospace, monospace; }
  details { margin-top: 12px; }
  pre { background: #1a1c22; border: 1px solid #272a32; padding: 8px;
        border-radius: 6px; overflow: auto; max-height: 60vh; font-size: 12px; }
  .hint { opacity: 0.6; font-size: 12px; margin-left: auto; }
  .empty { opacity: 0.6; text-align: center; padding: 32px; }
</style>
</head>
<body>
  <h1>Visitor Log Relay</h1>

  <div class="stats" id="stats"></div>

  <div class="controls">
    <select id="mode">
      <option value="recent">Recent</option>
      <option value="ip">By IP</option>
      <option value="path">By path</option>
      <option value="suspicious">Suspicious patterns</option>
    </select>
    <input id="filter" placeholder="filter value" style="min-width: 220px;" />
    <input id="limit" type="number" value="100" min="1" max="1000" style="width: 80px;" />
    <button class="primary" id="go">Load</button>
    <span class="hint">click any row for full details</span>
  </div>

  <div id="results"></div>

  <details>
    <summary>Selected entry</summary>
    <pre id="detail">(click a row)</pre>
  </details>

<script>
const $ = (id) => document.getElementById(id);

async function loadStats() {
  try {
    const s = await fetch('/api/stats').then(r => r.json());
    const top = (s.top_paths || []).map(p =>
      `<span title="${p.count} visits">${escapeHtml(p.path || '(none)')} · ${p.count}</span>`
    ).join('');
    $('stats').innerHTML = `
      <div class="stat"><div class="n">${s.total_visits}</div><div class="l">total</div></div>
      <div class="stat"><div class="n">${s.unique_ips}</div><div class="l">unique IPs</div></div>
      <div class="stat"><div class="n">${s.last_24h}</div><div class="l">last 24h</div></div>
      <div class="stat" style="flex:1; min-width: 280px;">
        <div class="l">top paths</div>
        <div class="top-paths">${top || '<span>(none)</span>'}</div>
      </div>`;
  } catch (e) {
    $('stats').innerHTML = `<div class="stat"><div class="l">stats unavailable</div></div>`;
  }
}

function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, c =>
    ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function codeClass(code) {
  if (!code) return '';
  if (code < 300) return 'code-2xx';
  if (code < 400) return 'code-3xx';
  if (code < 500) return 'code-4xx';
  return 'code-5xx';
}

function renderRows(rows) {
  if (!rows || !rows.length) {
    $('results').innerHTML = '<div class="empty">no results</div>';
    return;
  }
  const head = `<tr>
    <th>id</th><th>time</th><th>ip</th><th>method</th>
    <th>path</th><th>code</th><th>user agent</th></tr>`;
  const body = rows.map(r => `
    <tr data-id="${r.id}">
      <td>${r.id}</td>
      <td>${escapeHtml(r.timestamp || '')}</td>
      <td class="ip">${escapeHtml(r.ip_address || '')}</td>
      <td>${escapeHtml(r.method || '')}</td>
      <td class="path" title="${escapeHtml(r.path || '')}">${escapeHtml(r.path || '')}</td>
      <td class="${codeClass(r.response_code)}">${escapeHtml(r.response_code ?? '')}</td>
      <td class="path" title="${escapeHtml(r.user_agent || '')}">${escapeHtml(r.user_agent || '')}</td>
    </tr>`).join('');
  $('results').innerHTML = `<table><thead>${head}</thead><tbody>${body}</tbody></table>`;
  $('results').querySelectorAll('tr[data-id]').forEach(tr => {
    tr.addEventListener('click', () => loadDetail(tr.dataset.id));
  });
}

function renderSuspicious(rows) {
  if (!rows || !rows.length) {
    $('results').innerHTML = '<div class="empty">no suspicious activity in the last hour</div>';
    return;
  }
  const head = `<tr><th>ip</th><th>visits</th><th>first</th><th>last</th></tr>`;
  const body = rows.map(r => `
    <tr><td class="ip">${escapeHtml(r.ip_address)}</td>
        <td>${r.visit_count}</td>
        <td>${escapeHtml(r.first_visit)}</td>
        <td>${escapeHtml(r.last_visit)}</td></tr>`).join('');
  $('results').innerHTML = `<table><thead>${head}</thead><tbody>${body}</tbody></table>`;
}

async function loadDetail(id) {
  try {
    const e = await fetch(`/api/entry/${id}`).then(r => r.json());
    $('detail').textContent = JSON.stringify(e, null, 2);
  } catch (err) {
    $('detail').textContent = String(err);
  }
}

async function go() {
  const mode = $('mode').value;
  const filter = $('filter').value.trim();
  const limit = parseInt($('limit').value || '100', 10);
  let url;
  if (mode === 'recent') url = `/api/recent?limit=${limit}`;
  else if (mode === 'ip') url = `/api/by-ip/${encodeURIComponent(filter)}`;
  else if (mode === 'path') url = `/api/by-path?q=${encodeURIComponent(filter)}`;
  else if (mode === 'suspicious') url = `/api/suspicious`;

  $('results').innerHTML = '<div class="empty">loading...</div>';
  try {
    const rows = await fetch(url).then(r => r.json());
    if (mode === 'suspicious') renderSuspicious(rows);
    else renderRows(rows);
  } catch (e) {
    $('results').innerHTML = `<div class="empty">error: ${escapeHtml(e.message)}</div>`;
  }
}

$('go').addEventListener('click', go);
$('filter').addEventListener('keydown', e => { if (e.key === 'Enter') go(); });
$('mode').addEventListener('change', () => {
  const needsFilter = ['ip', 'path'].includes($('mode').value);
  $('filter').style.display = needsFilter ? '' : 'none';
});
$('mode').dispatchEvent(new Event('change'));

loadStats();
go();
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index():
    return INDEX_HTML


@app.get("/healthz")
def healthz():
    return JSONResponse({"ok": True, "db": str(_query.db_path)})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # 127.0.0.1 only by design — logs contain sensitive headers/cookies.
    # Use SSH tunneling for remote access.
    uvicorn.run(app, host="127.0.0.1", port=9091)
