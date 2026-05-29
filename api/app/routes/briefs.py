"""Brief routes — PDF export and public share links."""

import io
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, JSONResponse

from app.db import client as db

router = APIRouter(tags=["briefs"])

# ── HTML template for PDF ─────────────────────────────────────────────────────

_PDF_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Courier New', monospace;
    background: #0a0a0a;
    color: #d4d4d4;
    padding: 48px;
    font-size: 11px;
    line-height: 1.6;
  }
  .header {
    border-bottom: 1px solid #404040;
    padding-bottom: 16px;
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }
  .logo { font-size: 16px; font-weight: bold; color: #ffffff; letter-spacing: 2px; }
  .logo span { color: #ff4444; }
  .meta { text-align: right; color: #666; font-size: 9px; letter-spacing: 1px; }
  .section-label {
    font-size: 8px;
    letter-spacing: 2px;
    color: #555;
    text-transform: uppercase;
    margin-bottom: 6px;
  }
  .score-block {
    display: flex;
    align-items: center;
    gap: 32px;
    margin-bottom: 24px;
    padding: 16px;
    border: 1px solid #333;
    background: #111;
  }
  .score-num { font-size: 48px; font-weight: bold; color: #f59e0b; }
  .move-badge {
    font-size: 14px;
    font-weight: bold;
    letter-spacing: 3px;
    color: #f59e0b;
    border: 1px solid #92400e;
    padding: 6px 16px;
    background: #111;
  }
  .confidence { color: #666; font-size: 10px; }
  .situation { margin-bottom: 24px; }
  .headline { font-size: 14px; color: #fff; font-weight: bold; margin-bottom: 8px; }
  .situation-body { color: #999; }
  .actions-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 16px;
    margin-bottom: 24px;
  }
  .action-col { border: 1px solid #333; padding: 12px; background: #111; }
  .action-label { font-size: 8px; letter-spacing: 2px; margin-bottom: 8px; }
  .immediate .action-label { color: #ef4444; }
  .this-week .action-label { color: #f59e0b; }
  .watch .action-label { color: #38bdf8; }
  .action-item { color: #aaa; margin-bottom: 4px; padding-left: 12px; position: relative; }
  .action-item::before { content: '→'; position: absolute; left: 0; }
  .rationale {
    border-top: 1px solid #333;
    padding-top: 16px;
    margin-bottom: 24px;
    color: #777;
  }
  .bd-section {
    border: 1px solid #2d2d2d;
    padding: 12px;
    background: #0d0d0d;
    margin-bottom: 24px;
  }
  .bd-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin-top: 8px; }
  .bd-card { border: 1px solid #2a2a2a; padding: 8px; text-align: center; }
  .bd-product { font-size: 8px; letter-spacing: 1px; color: #555; margin-bottom: 4px; }
  .bd-count { font-size: 18px; font-weight: bold; color: #d4d4d4; }
  .bd-status-ok { color: #22c55e; }
  .bd-status-empty { color: #f59e0b; }
  .footer {
    border-top: 1px solid #333;
    padding-top: 12px;
    color: #444;
    font-size: 9px;
    display: flex;
    justify-content: space-between;
  }
</style>
</head>
<body>

<div class="header">
  <div>
    <div class="logo">WAR ROOM <span>AI</span></div>
    <div style="font-size:9px;color:#555;margin-top:4px;letter-spacing:1px;">
      EXECUTIVE BATTLE BRIEF
    </div>
  </div>
  <div class="meta">
    <div>{{ mission_type | upper | replace("_", " ") }}</div>
    <div>{{ target }}</div>
    <div>{{ generated_at }}</div>
    <div>MISSION {{ mission_id[:8] | upper }}</div>
  </div>
</div>

<!-- Score & Move -->
<div class="score-block">
  <div>
    <div class="section-label">Market Move Score</div>
    <div class="score-num">{{ market_move_score }}</div>
  </div>
  <div>
    <div class="section-label">Recommended Move</div>
    <div class="move-badge">{{ recommended_move | upper }}</div>
  </div>
  <div>
    <div class="section-label">Confidence</div>
    <div class="confidence" style="font-size:20px;">{{ confidence_score }}/100</div>
  </div>
</div>

<!-- Situation -->
{% if headline %}
<div class="situation">
  <div class="section-label">Situation</div>
  <div class="headline">{{ headline }}</div>
  {% if situation_body %}<div class="situation-body">{{ situation_body }}</div>{% endif %}
</div>
{% endif %}

<!-- Action Pack -->
<div class="actions-grid">
  <div class="action-col immediate">
    <div class="action-label">Immediate</div>
    {% for item in immediate %}
    <div class="action-item">{{ item }}</div>
    {% endfor %}
    {% if not immediate %}<div style="color:#333;">—</div>{% endif %}
  </div>
  <div class="action-col this-week">
    <div class="action-label">This Week</div>
    {% for item in this_week %}
    <div class="action-item">{{ item }}</div>
    {% endfor %}
    {% if not this_week %}<div style="color:#333;">—</div>{% endif %}
  </div>
  <div class="action-col watch">
    <div class="action-label">Watch</div>
    {% for item in watch %}
    <div class="action-item">{{ item }}</div>
    {% endfor %}
    {% if not watch %}<div style="color:#333;">—</div>{% endif %}
  </div>
</div>

<!-- Rationale -->
{% if rationale %}
<div class="rationale">
  <div class="section-label" style="margin-bottom:6px;">Commander Rationale</div>
  {{ rationale }}
</div>
{% endif %}

<!-- Bright Data usage -->
{% if bd_calls %}
<div class="bd-section">
  <div class="section-label">Powered by Bright Data — Intelligence Sources</div>
  <div class="bd-grid">
    {% for product, count, status in bd_calls %}
    <div class="bd-card">
      <div class="bd-product">{{ product }}</div>
      <div class="bd-count {% if status == 'ok' %}bd-status-ok{% elif status == 'empty' %}bd-status-empty{% endif %}">
        {{ count }}
      </div>
    </div>
    {% endfor %}
  </div>
</div>
{% endif %}

<div class="footer">
  <span>Generated by War Room AI · Powered by Bright Data</span>
  <span>{{ generated_at }}</span>
</div>

</body>
</html>"""


def _build_pdf_context(mission: dict, brief: dict) -> dict:
    """Assemble template variables from mission + brief dicts."""
    action_pack = brief.get("action_pack") or {}
    actions = action_pack.get("actions") or {}
    bd_raw: list[dict] = brief.get("bright_data_calls") or []

    # Aggregate BD calls by product.
    product_counts: dict[str, dict] = {}
    for call in bd_raw:
        prod = call.get("product", "unknown")
        if prod not in product_counts:
            product_counts[prod] = {"count": 0, "ok": 0}
        product_counts[prod]["count"] += 1
        if call.get("ok"):
            product_counts[prod]["ok"] += 1

    bd_calls = [
        (prod, info["count"], "ok" if info["ok"] == info["count"] else "empty")
        for prod, info in sorted(product_counts.items())
    ]

    return {
        "mission_id": str(mission.get("id", "")),
        "mission_type": mission.get("mission_type", ""),
        "target": mission.get("target", ""),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "market_move_score": brief.get("market_move_score", 0),
        "recommended_move": (brief.get("recommended_move") or "MONITOR").upper(),
        "confidence_score": brief.get("confidence_score", 0),
        "headline": action_pack.get("headline", ""),
        "situation_body": action_pack.get("situation", ""),
        "immediate": actions.get("immediate") or [],
        "this_week": actions.get("this_week") or [],
        "watch": actions.get("watch") or [],
        "rationale": action_pack.get("commander_rationale", ""),
        "bd_calls": bd_calls,
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/missions/{mission_id}/brief/pdf")
async def download_brief_pdf(mission_id: str) -> Response:
    """Render the battle brief as a downloadable PDF via WeasyPrint."""
    mission = await db.aget_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    brief = await db.aget_brief_by_mission(mission_id)
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not ready yet")

    try:
        from jinja2 import Template
        import weasyprint
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"PDF generation unavailable: {exc}. Run: uv add weasyprint jinja2",
        )

    template = Template(_PDF_TEMPLATE)
    html = template.render(**_build_pdf_context(mission, brief))

    pdf_bytes = weasyprint.HTML(string=html).write_pdf()
    target_slug = mission.get("target", "brief").replace(".", "-").replace("/", "-")
    filename = f"warroom-brief-{target_slug}-{mission_id[:8]}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/missions/{mission_id}/brief/share")
async def share_brief(mission_id: str) -> dict:
    """Mark a brief as publicly shared. Returns the public share URL."""
    mission = await db.aget_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    brief = await db.aget_brief_by_mission(mission_id)
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not ready yet")

    await db.amark_brief_shared(mission_id)
    return {"share_url": f"/share/{mission_id}"}


@router.get("/share/{mission_id}")
async def get_shared_brief(mission_id: str) -> dict:
    """Public read-only endpoint for a shared battle brief."""
    mission = await db.aget_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Not found")
    brief = await db.aget_brief_by_mission(mission_id)
    if not brief:
        raise HTTPException(status_code=404, detail="Not found")
    return {"mission": mission, "brief": brief}
