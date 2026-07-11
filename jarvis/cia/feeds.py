"""
CIA Feeds — live cybersecurity intelligence from multiple sources.
Sources: NVD/NIST, CISA KEV, SANS ISC, Exploit-DB, HackerNews Security
"""
import asyncio
import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
CISA_KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
SANS_RSS = "https://isc.sans.edu/rssfeed.xml"
EXPLOIT_DB_RSS = "https://www.exploit-db.com/rss.xml"
HN_SECURITY = "https://hn.algolia.com/api/v1/search?tags=story&query=cybersecurity+vulnerability&hitsPerPage=15"

NVD_API_KEY = os.environ.get("NVD_API_KEY")

TIMEOUT = httpx.Timeout(15.0)
RETRY_ATTEMPTS = 3
RETRY_BASE_DELAY = 2.0


async def _with_retry(fn, *args, attempts: int = RETRY_ATTEMPTS, **kwargs):
    """Retry a coroutine-returning call with exponential backoff on transient HTTP errors."""
    last_exc: Exception | None = None
    for attempt in range(attempts):
        try:
            return await fn(*args, **kwargs)
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            last_exc = exc
            if attempt < attempts - 1:
                await asyncio.sleep(RETRY_BASE_DELAY * (2 ** attempt))
    raise last_exc


async def fetch_nvd_cves(limit: int = 20, window_days: int = 30) -> list[dict[str, Any]]:
    """Top recent CVEs from NVD with CVSS >= 7.0, published in the last `window_days` days."""
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=window_days)
    fmt = "%Y-%m-%dT%H:%M:%S.000"
    params = {
        "resultsPerPage": limit,
        "startIndex": 0,
        "cvssV3Severity": "HIGH",
        "noRejected": "",
        "pubStartDate": start.strftime(fmt),
        "pubEndDate": now.strftime(fmt),
    }
    headers = {"apiKey": NVD_API_KEY} if NVD_API_KEY else {}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(NVD_URL, params=params, headers=headers)
        r.raise_for_status()
        data = r.json()

    results = []
    for item in data.get("vulnerabilities", []):
        cve = item.get("cve", {})
        metrics = cve.get("metrics", {})
        score = None
        for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            if key in metrics and metrics[key]:
                score = metrics[key][0].get("cvssData", {}).get("baseScore")
                break
        desc = next(
            (d["value"] for d in cve.get("descriptions", []) if d["lang"] == "en"),
            "No description",
        )
        results.append({
            "id": cve.get("id"),
            "published": cve.get("published", "")[:10],
            "score": score,
            "description": desc[:300],
            "url": f"https://nvd.nist.gov/vuln/detail/{cve.get('id')}",
        })
    return results


async def fetch_cisa_kev(limit: int = 15) -> list[dict[str, Any]]:
    """CISA Known Exploited Vulnerabilities — actively exploited in the wild."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(CISA_KEV_URL)
        r.raise_for_status()
        data = r.json()

    vulns = sorted(
        data.get("vulnerabilities", []),
        key=lambda v: v.get("dateAdded", ""),
        reverse=True,
    )[:limit]

    return [
        {
            "id": v.get("cveID"),
            "product": v.get("product"),
            "vendor": v.get("vendorProject"),
            "description": v.get("shortDescription", "")[:250],
            "date_added": v.get("dateAdded"),
            "due_date": v.get("dueDate"),
            "ransomware": v.get("knownRansomwareCampaignUse", "Unknown"),
        }
        for v in vulns
    ]


async def fetch_sans_isc() -> list[dict[str, Any]]:
    """SANS Internet Storm Center — daily threat diary."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(SANS_RSS)
        r.raise_for_status()
        xml = r.text

    root = ET.fromstring(xml)
    ns = {"dc": "http://purl.org/dc/elements/1.1/"}
    items = []
    for item in root.findall(".//item")[:10]:
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        desc = item.findtext("description", "")
        desc_clean = re.sub(r"<[^>]+>", "", desc)[:300]
        pub = item.findtext("pubDate", "")
        items.append({"title": title, "link": link, "summary": desc_clean, "published": pub})
    return items


async def fetch_exploit_db() -> list[dict[str, Any]]:
    """Exploit-DB latest public exploits."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(EXPLOIT_DB_RSS, follow_redirects=True)
        r.raise_for_status()
        xml = r.text

    root = ET.fromstring(xml)
    items = []
    for item in root.findall(".//item")[:10]:
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        desc = item.findtext("description", "")
        desc_clean = re.sub(r"<[^>]+>", "", desc)[:200]
        items.append({"title": title, "link": link, "description": desc_clean})
    return items


async def fetch_hackernews_security() -> list[dict[str, Any]]:
    """HackerNews top security stories."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(HN_SECURITY)
        r.raise_for_status()
        data = r.json()

    return [
        {
            "title": h.get("title"),
            "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
            "points": h.get("points", 0),
            "comments": h.get("num_comments", 0),
            "author": h.get("author"),
        }
        for h in data.get("hits", [])
        if h.get("title")
    ]


async def collect_all() -> dict[str, Any]:
    """Gather all CIA feeds concurrently."""
    results = await asyncio.gather(
        _with_retry(fetch_nvd_cves),
        _with_retry(fetch_cisa_kev),
        _with_retry(fetch_sans_isc),
        _with_retry(fetch_exploit_db),
        _with_retry(fetch_hackernews_security),
        return_exceptions=True,
    )
    keys = ("nvd_cves", "cisa_kev", "sans_isc", "exploit_db", "hackernews")
    data: dict[str, Any] = {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "sources": {},
    }
    for key, result in zip(keys, results):
        if isinstance(result, Exception):
            data["sources"][key] = {"error": str(result), "items": []}
        else:
            data["sources"][key] = {"items": result, "count": len(result)}
    return data
