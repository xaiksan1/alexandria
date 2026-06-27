"""
CIA Publisher — builds HTML intelligence reports and publishes via Pagecast.
"""
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PAGECAST_DIR = Path(os.getenv("PAGECAST_DIR", "/home/michaellefebvre416/alexandria/cia/pagecast"))
REPORTS_DIR = Path(os.getenv("CIA_REPORTS_DIR", "/home/michaellefebvre416/alexandria/cia/reports"))


def _threat_color(level: str) -> str:
    return {"LOW": "#22c55e", "MEDIUM": "#f59e0b", "HIGH": "#f97316", "CRITICAL": "#ef4444"}.get(
        level, "#6b7280"
    )


def build_report(intel: dict[str, Any], analysis: dict[str, Any]) -> str:
    """Build a self-contained HTML intelligence report."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    threat_level = analysis.get("threat_level", "UNKNOWN")
    color = _threat_color(threat_level)

    nvd = intel["sources"].get("nvd_cves", {}).get("items", [])
    kev = intel["sources"].get("cisa_kev", {}).get("items", [])
    sans = intel["sources"].get("sans_isc", {}).get("items", [])
    hn = intel["sources"].get("hackernews", {}).get("items", [])

    top_threats_html = "".join(
        f"""<div class="threat-card">
          <span class="badge" style="background:{_threat_color(t.get('severity','MEDIUM'))}">{t.get('severity','?')}</span>
          <strong>{t.get('id','')}</strong>
          <p>{t.get('description','')[:200]}</p>
          <em>Action: {t.get('action','')}</em>
        </div>"""
        for t in analysis.get("top_threats", [])
    )

    critical_cves_html = "".join(
        f"<li><strong>{c.get('id')}</strong> (score {c.get('score','?')}) — {c.get('why_critical','')}</li>"
        for c in analysis.get("critical_cves", [])
    )

    recs_html = "".join(
        f"<li>{r}</li>" for r in analysis.get("recommendations", [])
    )

    attack_vectors_html = "".join(
        f'<span class="tag">{v}</span>' for v in analysis.get("attack_vectors", [])
    )

    nvd_rows = "".join(
        f"<tr><td><a href='{c['url']}' target='_blank'>{c['id']}</a></td>"
        f"<td><span class='score'>{c.get('score','?')}</span></td>"
        f"<td>{c.get('description','')[:120]}...</td>"
        f"<td>{c.get('published','')}</td></tr>"
        for c in nvd[:12]
    )

    kev_rows = "".join(
        f"<tr><td>{k['id']}</td><td>{k.get('vendor','')} {k.get('product','')}</td>"
        f"<td>{k.get('date_added','')}</td>"
        f"<td style='color:{'#ef4444' if k.get('ransomware')=='Known' else '#6b7280'}'>"
        f"{k.get('ransomware','')}</td></tr>"
        for k in kev[:10]
    )

    sans_items = "".join(
        f"<li><a href='{i['link']}' target='_blank'>{i['title']}</a><br><small>{i.get('summary','')[:150]}</small></li>"
        for i in sans[:6]
    )

    hn_items = "".join(
        f"<li><a href='{i['url']}' target='_blank'>{i['title']}</a> "
        f"<small>({i.get('points',0)} pts)</small></li>"
        for i in hn[:8]
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CIA Intel Report — {ts}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #0f172a; color: #e2e8f0; padding: 20px; }}
  h1 {{ color: #60a5fa; font-size: 1.8rem; margin-bottom: 4px; }}
  h2 {{ color: #94a3b8; font-size: 1.1rem; margin: 20px 0 10px; border-bottom: 1px solid #334155; padding-bottom: 6px; }}
  .header {{ display: flex; align-items: center; gap: 20px; margin-bottom: 24px; }}
  .threat-level {{ background: {color}; color: #fff; font-weight: 700; padding: 8px 20px; border-radius: 8px; font-size: 1.2rem; }}
  .summary {{ background: #1e293b; padding: 16px; border-radius: 8px; border-left: 4px solid {color}; margin-bottom: 20px; line-height: 1.6; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }}
  .card {{ background: #1e293b; padding: 16px; border-radius: 8px; }}
  .threat-card {{ background: #1e293b; padding: 12px; border-radius: 6px; margin-bottom: 8px; border-left: 3px solid #334155; }}
  .threat-card p {{ margin: 6px 0; font-size: 0.9rem; color: #94a3b8; }}
  .threat-card em {{ font-size: 0.85rem; color: #60a5fa; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; color: #fff; margin-right: 8px; font-weight: 600; }}
  .tag {{ display: inline-block; background: #334155; padding: 4px 10px; border-radius: 20px; margin: 3px; font-size: 0.8rem; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
  th {{ background: #0f172a; color: #64748b; padding: 8px; text-align: left; }}
  td {{ padding: 8px; border-bottom: 1px solid #1e293b; }}
  tr:hover {{ background: #1e293b; }}
  .score {{ background: #dc2626; color: #fff; padding: 2px 6px; border-radius: 4px; font-weight: 600; font-size: 0.8rem; }}
  a {{ color: #60a5fa; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  ul {{ padding-left: 20px; line-height: 1.8; }}
  .footer {{ text-align: center; color: #334155; margin-top: 30px; font-size: 0.8rem; }}
</style>
</head>
<body>
<div class="header">
  <div>
    <h1>CIA — Cybersecurity Intelligence Report</h1>
    <p style="color:#64748b">{ts} · Alexandria Anima Mundi</p>
  </div>
  <div class="threat-level">THREAT: {threat_level}</div>
</div>

<div class="summary">{analysis.get('summary','')}</div>

<h2>Top Threats</h2>
{top_threats_html}

<div class="grid">
  <div class="card">
    <h2 style="margin-top:0">Critical CVEs to Patch</h2>
    <ul>{critical_cves_html}</ul>
  </div>
  <div class="card">
    <h2 style="margin-top:0">Immediate Actions</h2>
    <ul>{recs_html}</ul>
  </div>
</div>

<h2>Trending Attack Vectors</h2>
<div style="margin-bottom:20px">{attack_vectors_html}</div>

<h2>NVD — High Severity CVEs</h2>
<table>
  <tr><th>CVE ID</th><th>Score</th><th>Description</th><th>Published</th></tr>
  {nvd_rows}
</table>

<h2>CISA Known Exploited Vulnerabilities</h2>
<table>
  <tr><th>CVE</th><th>Product</th><th>Date Added</th><th>Ransomware</th></tr>
  {kev_rows}
</table>

<div class="grid" style="margin-top:20px">
  <div class="card">
    <h2 style="margin-top:0">SANS ISC Diary</h2>
    <ul>{sans_items}</ul>
  </div>
  <div class="card">
    <h2 style="margin-top:0">HackerNews Security</h2>
    <ul>{hn_items}</ul>
  </div>
</div>

<div class="footer">Generated by CIA — Cybersecurity Intelligence Agentic · Alexandria Anima Mundi</div>
</body>
</html>"""


def save_report(html: str, filename: str | None = None) -> Path:
    """Save report to disk."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if not filename:
        filename = f"cia-report-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}.html"
    path = REPORTS_DIR / filename
    path.write_text(html)
    return path


def publish_via_pagecast(report_path: Path) -> dict[str, Any]:
    """Publish the report to Cloudflare Pages via pagecast CLI."""
    if not PAGECAST_DIR.exists():
        return {"error": "pagecast not installed", "path": str(report_path)}
    try:
        result = subprocess.run(
            ["node", ".", "publish", str(report_path)],
            cwd=str(PAGECAST_DIR),
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = result.stdout + result.stderr
        # Extract URL from output
        import re
        urls = re.findall(r"https://[^\s]+\.pages\.dev[^\s]*", output)
        return {
            "published": result.returncode == 0,
            "url": urls[0] if urls else None,
            "output": output[:500],
            "local_path": str(report_path),
        }
    except Exception as e:
        return {"error": str(e), "local_path": str(report_path)}
