"""
CIA Agent — Instant-Lee powered analysis of threat intelligence feeds.
Calls Instant-Lee MCP server to generate structured threat assessments.
"""
import json
import os
from typing import Any

import httpx

INSTANT_LEE_URL = os.getenv("INSTANT_LEE_URL", "http://localhost:4112")
BIFROST_URL = os.getenv("BIFROST_URL", "http://localhost:8090")
BIFROST_MODEL = os.getenv("BIFROST_MODEL", "openrouter/anthropic/claude-sonnet-4.6")

TIMEOUT = httpx.Timeout(60.0)


async def analyze_threats(intel: dict[str, Any]) -> dict[str, Any]:
    """
    Pass collected intel to Bifrost LLM for structured threat analysis.
    Returns: summary, top_threats, attack_vectors, recommendations
    """
    nvd = intel["sources"].get("nvd_cves", {}).get("items", [])
    kev = intel["sources"].get("cisa_kev", {}).get("items", [])
    sans = intel["sources"].get("sans_isc", {}).get("items", [])
    exploits = intel["sources"].get("exploit_db", {}).get("items", [])
    hn = intel["sources"].get("hackernews", {}).get("items", [])

    prompt = f"""You are the CIA (Cybersecurity Intelligence Agentic) analyst for Alexandria.

Analyze the following live threat intelligence and return a JSON object with:
- "threat_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
- "summary": 2-3 sentence executive summary
- "top_threats": list of 5 most critical threats (each: id, severity, description, action)
- "attack_vectors": trending attack methods (list of strings)
- "critical_cves": top 3 CVEs to patch immediately (each: id, score, why_critical)
- "recommendations": 5 immediate actions for security teams

INTEL DATA:
=== NVD HIGH CVEs ({len(nvd)} items) ===
{json.dumps(nvd[:10], indent=2)}

=== CISA Known Exploited ({len(kev)} items) ===
{json.dumps(kev[:8], indent=2)}

=== SANS ISC Diary ===
{json.dumps([{"title": i["title"], "summary": i["summary"][:150]} for i in sans[:5]], indent=2)}

=== Exploit-DB Latest ===
{json.dumps([{"title": i["title"]} for i in exploits[:8]], indent=2)}

=== HackerNews Security ===
{json.dumps([{"title": i["title"], "points": i["points"]} for i in hn[:8]], indent=2)}

Return ONLY valid JSON, no markdown."""

    payload = {
        "model": BIFROST_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 2000,
    }

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.post(f"{BIFROST_URL}/v1/chat/completions", json=payload)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"].strip()

    # Strip markdown code fences if present
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    content = content.strip()

    return json.loads(content)


async def generate_rules_brief(intel: dict[str, Any]) -> str:
    """Generate a brief for agentsync — what rules to update."""
    kev = intel["sources"].get("cisa_kev", {}).get("items", [])
    nvd = intel["sources"].get("nvd_cves", {}).get("items", [])

    prompt = f"""Based on this threat intel, generate a brief security rules update note.
Format as markdown with:
- New CVEs requiring WAF rules
- Attack patterns to add to YARA/Sigma rules
- IP/domain patterns to blocklist

CVEs: {json.dumps([c['id'] for c in nvd[:5]])}
CISA KEV products: {json.dumps([f"{k['vendor']} {k['product']}" for k in kev[:5]])}

Keep it under 300 words."""

    payload = {
        "model": BIFROST_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 500,
    }

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.post(f"{BIFROST_URL}/v1/chat/completions", json=payload)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
