"""Brief routes — PDF export and public share links.

PDF uses fpdf2 (pure Python, zero system dependencies, works on Windows).
"""

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.db import client as db

router = APIRouter(tags=["briefs"])


# ── PDF generation (fpdf2) ────────────────────────────────────────────────────

def _generate_pdf(mission: dict, brief: dict) -> bytes:
    from fpdf import FPDF

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

    target = mission.get("target", "")
    mission_type = mission.get("mission_type", "").replace("_", " ").upper()
    mission_id = str(mission.get("id", ""))
    score = brief.get("market_move_score", 0)
    move = (brief.get("recommended_move") or "MONITOR").upper()
    confidence = brief.get("confidence_score", 0)
    headline = action_pack.get("headline", "")
    situation = action_pack.get("situation", "")
    rationale = action_pack.get("commander_rationale", "")
    immediate = actions.get("immediate") or []
    this_week = actions.get("this_week") or []
    watch = actions.get("watch") or []
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_margins(20, 20, 20)

    # ── Header bar ───────────────────────────────────────────────────────────
    pdf.set_fill_color(15, 15, 15)
    pdf.rect(0, 0, 210, 22, style="F")
    pdf.set_font("Courier", "B", 14)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(20, 6)
    pdf.cell(80, 10, "WAR ROOM AI", ln=False)
    pdf.set_font("Courier", "", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.set_xy(110, 6)
    pdf.cell(80, 5, "EXECUTIVE BATTLE BRIEF", align="R", ln=False)
    pdf.set_xy(110, 11)
    pdf.cell(80, 5, generated_at, align="R")
    pdf.set_xy(20, 22)

    # ── Mission metadata ──────────────────────────────────────────────────────
    pdf.ln(4)
    pdf.set_font("Courier", "", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 5, f"TARGET: {target}   |   MISSION: {mission_type}   |   ID: {mission_id[:8].upper()}", ln=True)
    pdf.ln(3)

    # Divider
    pdf.set_draw_color(60, 60, 60)
    pdf.set_line_width(0.3)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(5)

    # ── Score + Move block ────────────────────────────────────────────────────
    y_start = pdf.get_y()
    pdf.set_fill_color(20, 20, 20)
    pdf.rect(20, y_start, 170, 28, style="F")

    # Score
    pdf.set_xy(28, y_start + 4)
    pdf.set_font("Courier", "", 7)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(30, 4, "MARKET MOVE SCORE", ln=True)
    pdf.set_xy(28, y_start + 9)
    score_color = (239, 68, 68) if score >= 80 else (245, 158, 11) if score >= 60 else (200, 200, 200)
    pdf.set_font("Courier", "B", 26)
    pdf.set_text_color(*score_color)
    pdf.cell(30, 14, str(score))

    # Move
    pdf.set_xy(80, y_start + 4)
    pdf.set_font("Courier", "", 7)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(40, 4, "RECOMMENDED MOVE", ln=True)
    pdf.set_xy(80, y_start + 10)
    pdf.set_font("Courier", "B", 14)
    pdf.set_text_color(245, 158, 11)
    pdf.cell(50, 10, move)

    # Confidence
    pdf.set_xy(140, y_start + 4)
    pdf.set_font("Courier", "", 7)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(40, 4, "CONFIDENCE", ln=True)
    pdf.set_xy(140, y_start + 9)
    pdf.set_font("Courier", "B", 16)
    pdf.set_text_color(200, 200, 200)
    pdf.cell(40, 10, f"{confidence}/100")

    pdf.set_xy(20, y_start + 30)
    pdf.ln(3)

    # ── Situation ─────────────────────────────────────────────────────────────
    if headline:
        pdf.set_font("Courier", "", 7)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 4, "SITUATION", ln=True)
        pdf.ln(1)
        pdf.set_font("Courier", "B", 10)
        pdf.set_text_color(230, 230, 230)
        pdf.multi_cell(0, 5, headline)
        if situation:
            pdf.ln(1)
            pdf.set_font("Courier", "", 9)
            pdf.set_text_color(160, 160, 160)
            pdf.multi_cell(0, 5, situation)
        pdf.ln(4)

    # Divider
    pdf.set_draw_color(60, 60, 60)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(5)

    # ── Action Pack (3 columns) ───────────────────────────────────────────────
    col_w = 53
    col_gap = 5
    col_x = [20, 20 + col_w + col_gap, 20 + (col_w + col_gap) * 2]
    col_colors = [(239, 68, 68), (245, 158, 11), (56, 189, 248)]
    col_labels = ["IMMEDIATE", "THIS WEEK", "WATCH"]
    col_items = [immediate, this_week, watch]

    top_y = pdf.get_y()

    for i, (x, color, label, items) in enumerate(zip(col_x, col_colors, col_labels, col_items)):
        pdf.set_xy(x, top_y)
        pdf.set_font("Courier", "B", 7)
        pdf.set_text_color(*color)
        pdf.cell(col_w, 4, label, ln=True)
        pdf.set_xy(x, top_y + 5)
        pdf.set_font("Courier", "", 8)
        pdf.set_text_color(160, 160, 160)
        if not items:
            pdf.set_xy(x, pdf.get_y())
            pdf.cell(col_w, 5, "-", ln=True)
        else:
            for item in items:
                pdf.set_xy(x, pdf.get_y())
                # Arrow prefix
                pdf.set_text_color(*color)
                pdf.cell(4, 5, ">")
                pdf.set_text_color(160, 160, 160)
                pdf.multi_cell(col_w - 4, 5, item)

    # Move cursor below all columns (estimate).
    max_items = max(len(immediate), len(this_week), len(watch), 1)
    pdf.set_xy(20, top_y + 6 + max_items * 12)
    pdf.ln(6)

    # ── Rationale ─────────────────────────────────────────────────────────────
    if rationale:
        pdf.set_draw_color(60, 60, 60)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(4)
        pdf.set_font("Courier", "", 7)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 4, "COMMANDER RATIONALE", ln=True)
        pdf.ln(1)
        pdf.set_font("Courier", "", 8)
        pdf.set_text_color(150, 150, 150)
        pdf.multi_cell(0, 5, rationale)
        pdf.ln(4)

    # ── Bright Data usage ─────────────────────────────────────────────────────
    if product_counts:
        pdf.set_draw_color(60, 60, 60)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(4)
        pdf.set_font("Courier", "", 7)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 4, "POWERED BY BRIGHT DATA — INTELLIGENCE SOURCES", ln=True)
        pdf.ln(2)
        card_w = 32
        bx = 20
        for prod, info in sorted(product_counts.items()):
            pdf.set_fill_color(20, 20, 20)
            pdf.rect(bx, pdf.get_y(), card_w, 14, style="F")
            pdf.set_xy(bx + 2, pdf.get_y() + 1)
            pdf.set_font("Courier", "", 6)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(card_w - 4, 4, prod.replace("_", " ").upper()[:12])
            pdf.set_xy(bx + 2, pdf.get_y())
            ok_color = (34, 197, 94) if info["ok"] == info["count"] else (245, 158, 11)
            pdf.set_font("Courier", "B", 12)
            pdf.set_text_color(*ok_color)
            pdf.cell(card_w - 4, 8, str(info["count"]))
            bx += card_w + 3

    # ── Footer ─────────────────────────────────────────────────────────────────
    pdf.set_y(-20)
    pdf.set_draw_color(60, 60, 60)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("Courier", "I", 7)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"Generated by War Room AI · Powered by Bright Data · {generated_at}", align="C")

    return bytes(pdf.output())


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/missions/{mission_id}/brief/pdf")
async def download_brief_pdf(mission_id: str) -> Response:
    """Render the battle brief as a downloadable PDF via fpdf2."""
    mission = await db.aget_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    brief = await db.aget_brief_by_mission(mission_id)
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not ready yet")

    try:
        pdf_bytes = await asyncio.to_thread(_generate_pdf, mission, brief)
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="PDF generation unavailable. Run: uv add fpdf2",
        )

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
