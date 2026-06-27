"""
CIA Router — FastAPI endpoints for JARVIS CIA tab.
"""
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse

from .feeds import collect_all
from .agent import analyze_threats, generate_rules_brief
from .publisher import build_report, save_report, publish_via_pagecast

router = APIRouter(prefix="/v1/cia", tags=["CIA"])

# In-memory cache — refreshed on demand or by scheduler
_cache: dict[str, Any] = {}
_lock = asyncio.Lock()


async def _get_or_refresh() -> dict[str, Any]:
    global _cache
    async with _lock:
        if not _cache:
            _cache = await collect_all()
    return _cache


@router.get("/status")
async def cia_status():
    """CIA module health + last collection timestamp."""
    return {
        "module": "CIA",
        "status": "online",
        "last_collected": _cache.get("collected_at"),
        "sources_loaded": list(_cache.get("sources", {}).keys()),
    }


@router.post("/refresh")
async def cia_refresh():
    """Force refresh of all intel feeds."""
    global _cache
    _cache = await collect_all()
    return {
        "refreshed_at": _cache["collected_at"],
        "counts": {k: v.get("count", 0) for k, v in _cache["sources"].items()},
    }


@router.get("/threats")
async def cia_threats():
    """SSE stream: collect feeds + AI analysis in real time."""

    async def stream():
        yield f"data: {json.dumps({'step': 'collecting', 'msg': 'Fetching live threat feeds...'})}\n\n"

        try:
            intel = await collect_all()
            global _cache
            _cache = intel

            counts = {k: v.get("count", 0) for k, v in intel["sources"].items()}
            yield f"data: {json.dumps({'step': 'feeds_done', 'counts': counts})}\n\n"

            yield f"data: {json.dumps({'step': 'analyzing', 'msg': 'CIA Agent analyzing threats...'})}\n\n"

            analysis = await analyze_threats(intel)

            yield f"data: {json.dumps({'step': 'complete', 'analysis': analysis, 'intel': intel})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'step': 'error', 'error': str(e)})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.get("/cves")
async def cia_cves():
    """Latest high-severity CVEs."""
    intel = await _get_or_refresh()
    return {
        "nvd": intel["sources"].get("nvd_cves", {}).get("items", []),
        "cisa_kev": intel["sources"].get("cisa_kev", {}).get("items", []),
        "collected_at": intel.get("collected_at"),
    }


@router.get("/news")
async def cia_news():
    """Security news: SANS ISC + HackerNews."""
    intel = await _get_or_refresh()
    return {
        "sans_isc": intel["sources"].get("sans_isc", {}).get("items", []),
        "hackernews": intel["sources"].get("hackernews", {}).get("items", []),
        "exploits": intel["sources"].get("exploit_db", {}).get("items", []),
        "collected_at": intel.get("collected_at"),
    }


@router.post("/report")
async def cia_report():
    """Generate + publish HTML intelligence report via Pagecast."""

    async def stream():
        yield f"data: {json.dumps({'step': 'collecting'})}\n\n"
        intel = await collect_all()
        global _cache
        _cache = intel

        yield f"data: {json.dumps({'step': 'analyzing'})}\n\n"
        analysis = await analyze_threats(intel)

        yield f"data: {json.dumps({'step': 'building_report'})}\n\n"
        html = build_report(intel, analysis)
        report_path = save_report(html)

        yield f"data: {json.dumps({'step': 'publishing'})}\n\n"
        pub = publish_via_pagecast(report_path)

        yield f"data: {json.dumps({'step': 'done', 'result': pub})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.get("/rules-brief")
async def cia_rules_brief():
    """AI-generated security rules update brief."""
    intel = await _get_or_refresh()
    brief = await generate_rules_brief(intel)
    return {"brief": brief, "generated_at": datetime.now(timezone.utc).isoformat()}
