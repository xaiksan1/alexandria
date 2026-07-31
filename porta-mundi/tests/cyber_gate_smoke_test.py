#!/usr/bin/env python3
"""Cyber-Gate smoke test — what REALLY happens when there's an intruder.

Does not mock anything. Talks to the real, live pm2 services
(cyber-gate :8085, phoenix :8000, paint-shop :4141) exactly the way a real
event would reach them, and instantiates the same defensive classes
(Minotaure, Zangetsu security layer, NmapScanner) the live process uses —
same code, same venv (ADAM/.venv, the interpreter cyber-gate actually runs
under) — so a failure here is a failure that would happen for real.

Run:  ADAM/.venv/bin/python3 porta-mundi/tests/cyber_gate_smoke_test.py

Exit code 0 only if nothing FAILed. WARN findings (detection gaps found,
not defects in this test) do not fail the run but ARE printed loudly —
read them, they're the point of this test.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

RESULTS: list[tuple[str, str, str]] = []  # (status, name, detail)


def record(status: str, name: str, detail: str = "") -> None:
    RESULTS.append((status, name, detail))
    icon = {"PASS": "\033[32mPASS\033[0m", "WARN": "\033[33mWARN\033[0m", "FAIL": "\033[31mFAIL\033[0m"}[status]
    print(f"[{icon}] {name}" + (f" — {detail}" if detail else ""))


def http(method: str, url: str, body: dict | None = None, timeout: float = 5) -> tuple[int, dict | str]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                  headers={"Content-Type": "application/json"} if data else {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw.decode(errors="replace")
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw.decode(errors="replace")
    except Exception as e:
        return -1, str(e)


# ─────────────────────────────────────────────────────────────────────────
print("=" * 72)
print(" 1. LIVE SERVICE HEALTH — is the gate actually up, not just 'online' in pm2")
print("=" * 72)

for name, url in [("Phoenix", "http://127.0.0.1:8000/health"),
                   ("Paint Shop", "http://127.0.0.1:4141/health"),
                   ("Cyber-Gate", "http://127.0.0.1:8085/status")]:
    status, body = http("GET", url)
    if status == 200:
        record("PASS", f"{name} reachable", str(body)[:100])
    else:
        record("FAIL", f"{name} reachable", f"status={status} body={body}")

# ─────────────────────────────────────────────────────────────────────────
print()
print("=" * 72)
print(" 2. SOURCE-DISCLOSURE REGRESSION — the 2026-07-25 fix, checked live, today")
print("=" * 72)

status, body = http("GET", "http://127.0.0.1:8085/aegis.py")
if status == 404:
    record("PASS", "GET /aegis.py returns 404 (not the signing module's source)")
else:
    record("FAIL", "GET /aegis.py did NOT 404", f"status={status} — SOURCE DISCLOSURE REGRESSION, body starts: {str(body)[:200]}")

status, body = http("HEAD", "http://127.0.0.1:8085/aegis.py")
if status != 200:
    record("PASS", f"HEAD /aegis.py rejected (status={status}, not a file leak)")
else:
    record("FAIL", "HEAD /aegis.py returned 200", "possible source disclosure via HEAD")

# ─────────────────────────────────────────────────────────────────────────
print()
print("=" * 72)
print(" 3. DIRECT THREAT PIPELINE — POST /api/threat, the real")
print("    Sentinelle -> Paint Shop -> Aegis -> Bounty Hunters -> Chapel XVI chain")
print("=" * 72)

clean_event = {"source": "203.0.113.10", "message": "GET /favicon.ico HTTP/1.1", "severity": "LOW"}
status, body = http("POST", "http://127.0.0.1:8085/api/threat", clean_event)
if status == 200 and isinstance(body, dict) and body.get("verdict") == "clean":
    stages = body.get("stages", {})
    downstream_ran = any(k in stages for k in ("paint_shop", "aegis", "bounty_hunters"))
    if not downstream_ran:
        record("PASS", "Benign traffic verdict=clean, downstream stages correctly skipped",
               f"stages={list(stages.keys())}")
    else:
        record("WARN", "Benign traffic ran downstream stages it shouldn't have", str(stages)[:200])
else:
    record("FAIL", "Clean-event pipeline call", f"status={status} body={str(body)[:300]}")

known_attack_event = {"source_ip": "198.51.100.77", "message": "' OR '1'='1' -- attempted sql injection on /login"}
status, body = http("POST", "http://127.0.0.1:8085/api/threat", known_attack_event)
if status == 200 and isinstance(body, dict) and body.get("verdict") not in ("clean", None):
    stages = body.get("stages", {})
    have_all = all(k in stages for k in ("sentinelle", "paint_shop", "aegis", "bounty_hunters", "chapel_xvi"))
    if have_all and "error" not in stages.get("paint_shop", {}):
        record("PASS", "Known-signature attack (SQLi) ran the FULL real pipeline",
               f"verdict={body['verdict']}, aegis_sig={stages['aegis'].get('signature', '')[:24]}..., "
               f"ioc_tracked={stages['bounty_hunters'].get('ioc')}, "
               f"chapel_seal={stages['chapel_xvi'].get('hash', '')[:20]}...")
    else:
        record("WARN", "Known-signature attack did not fully complete the pipeline", str(stages)[:400])
else:
    record("FAIL", "Known-attack pipeline call", f"status={status} body={str(body)[:300]}")

# The load-bearing finding: Sentinelle only matches ~15 hardcoded substrings.
# A real, novel attack that doesn't contain one of those literal strings
# never trips "threat", and the ENTIRE downstream chain (forensics, signing,
# IOC tracking, sealing) never runs for it — sealed as "clean" instead.
novel_attack_event = {
    "source_ip": "198.51.100.200",
    "message": "POST /api/v2/users/9183/impersonate with a forged JWT bearing alg=none",
}
status, body = http("POST", "http://127.0.0.1:8085/api/threat", novel_attack_event)
if status == 200 and isinstance(body, dict):
    if body.get("verdict") == "clean":
        record("WARN",
               "DETECTION GAP: a real attack pattern with no hardcoded-signature substring "
               "is sealed as 'clean' — Sentinelle only does literal substring matching "
               "(sql injection/union select/../nmap/etc.), it does not reason about novel attacks",
               f"event={novel_attack_event['message']!r} -> verdict=clean, no forensics/signing/IOC-tracking ran")
    else:
        record("PASS", "Novel-looking attack still correctly flagged", f"verdict={body.get('verdict')}")
else:
    record("FAIL", "Novel-attack pipeline call", f"status={status} body={str(body)[:300]}")

# ─────────────────────────────────────────────────────────────────────────
print()
print("=" * 72)
print(" 4. HONEYPOT PATH — Minotaure triggers Phoenix, does Paint Shop actually")
print("    watermark it the way the 'residual pixel tracer' design assumes?")
print("=" * 72)

from minotaure_gatekeeper import MinotaureGatekeeper  # noqa: E402

minotaure = MinotaureGatekeeper()
minotaure.generate_labyrinth(complexity=6)
challenge = minotaure.challenge_intruder("192.0.2.55")
record("PASS", "Minotaure.challenge_intruder() ran", f"challenge_id={challenge['challenge_id']}")

print("    waiting 10s for Paint Shop's background poller (runs every 8s)...")
time.sleep(10)

status, renders = http("GET", "http://127.0.0.1:4141/renders?limit=20")
found = False
if status == 200 and isinstance(renders, list):
    found = any(r.get("source") == "minotaure" for r in renders)
if found:
    record("PASS", "Honeypot event WAS watermarked by Paint Shop's auto-poller")
else:
    record("WARN",
           "DETECTION GAP: the honeypot challenge (severity=MEDIUM, score 50) was NOT "
           "auto-watermarked — Paint Shop's background poller only renders events with "
           "threat_score >= 75 (HIGH/CRITICAL). A destroyed/triggered Minotaure honeypot at "
           "MEDIUM severity leaves NO residual-pixel tracer via this path, so Bounty Hunters "
           "has nothing to pick up unless something calls POST /api/threat or /render directly.",
           f"paint_shop /renders in the last 20 had 'minotaure' as source: {found}")

# ─────────────────────────────────────────────────────────────────────────
print()
print("=" * 72)
print(" 5. ZANGETSU SECURITY LAYER — is the incident-response code real, does it work")
print("=" * 72)

try:
    from zangetsu_guardian import ZangetsuSecurityLayer, AccessLevel, OperationType
    from zangetsu_security import WhiteHatCybersecurity, IncidentSeverity

    zsl = ZangetsuSecurityLayer()

    # (a) Does check_operation() actually look at WHICH resource is targeted,
    # or only at role+operation? A "developer" is legitimately allowed to
    # WRITE — the question is whether writing to /etc/passwd is treated any
    # differently than writing to a scratch file.
    ctx_dev = zsl.create_security_context(user_id="smoke-test", role="developer", access_level=AccessLevel.AUTHORIZED)
    allowed_sensitive, _ = zsl.check_operation(ctx_dev, OperationType.WRITE, resource="/etc/passwd")
    allowed_scratch, _ = zsl.check_operation(ctx_dev, OperationType.WRITE, resource="/tmp/scratch.txt")
    if allowed_sensitive and allowed_scratch:
        record("WARN",
               "AUTHORIZATION GAP: check_operation() never inspects the 'resource' argument — "
               "a role authorized to WRITE is allowed to write to /etc/passwd exactly as freely "
               "as a scratch file. The access-control model is role+operation only, with zero "
               "resource-sensitivity awareness.",
               f"developer WRITE /etc/passwd -> allowed={allowed_sensitive}; "
               f"developer WRITE /tmp/scratch.txt -> allowed={allowed_scratch}")
    elif not allowed_sensitive:
        record("PASS", "check_operation() correctly distinguishes a sensitive resource")
    else:
        record("FAIL", "check_operation() inconsistent resource handling",
               f"sensitive={allowed_sensitive} scratch={allowed_scratch}")

    # (b) _check_authorization compares AccessLevel by `.value >= .value`, i.e.
    # a lexicographic STRING comparison ("authenticated" < "public" < "restricted"
    # alphabetically), not by intended privilege ordinal. A guest granted the
    # objectively-higher AUTHENTICATED tier should clear a PUBLIC requirement;
    # if the string-compare bug is real, it won't.
    ctx_guest_pub = zsl.create_security_context(user_id="u1", role="guest", access_level=AccessLevel.PUBLIC)
    ctx_guest_auth = zsl.create_security_context(user_id="u2", role="guest", access_level=AccessLevel.AUTHENTICATED)
    if ctx_guest_pub.is_authorized and not ctx_guest_auth.is_authorized:
        record("WARN",
               "PRIVILEGE-ORDERING BUG: _check_authorization compares AccessLevel.value as raw "
               "strings ('authenticated' < 'public' alphabetically), not by intended privilege "
               "rank. A guest with the objectively-higher AUTHENTICATED access level is "
               "incorrectly DENIED authorization while PUBLIC (the intended lowest tier) passes.",
               f"guest+PUBLIC.is_authorized={ctx_guest_pub.is_authorized}, "
               f"guest+AUTHENTICATED.is_authorized={ctx_guest_auth.is_authorized}")
    else:
        record("PASS", "AccessLevel comparison behaves as an ordinal, not raw string compare")

    whc = WhiteHatCybersecurity()
    incident = whc.create_incident("test-agent-001", IncidentSeverity.HIGH, "policy_violation",
                                    "smoke-test simulated incident")
    actions = whc.recommend_remediation(incident)
    procedure = whc.execute_remediation(incident, actions)
    if incident.is_resolved and procedure.execution_status == "completed":
        record("PASS", "WhiteHatCybersecurity full incident lifecycle ran end to end",
               f"recommended={[a.value for a in actions]}, results={procedure.results}")
    else:
        record("WARN", "Incident remediation did not fully complete", f"status={procedure.execution_status}, results={procedure.results}")
except Exception as e:
    record("FAIL", "Zangetsu security layer instantiation/lifecycle", f"{type(e).__name__}: {e}")

# ─────────────────────────────────────────────────────────────────────────
print()
print("=" * 72)
print(" 6. NMAP SCANNER — white-hat guard: refuses public targets, allows local")
print("=" * 72)

try:
    from nmap_scanner import NmapScanner

    scanner = NmapScanner()
    result = scanner.scan("8.8.8.8", ports="80")
    if result.get("error") == "refused":
        record("PASS", "NmapScanner refused a public target (8.8.8.8)", str(result))
    else:
        record("FAIL", "NmapScanner did NOT refuse a public target", str(result))

    result = scanner.scan("127.0.0.1", ports="80")
    if "error" not in result:
        record("PASS", "NmapScanner accepted localhost and returned a real scan result",
               f"keys={list(result.keys())}")
    else:
        record("WARN", "NmapScanner rejected localhost or errored", str(result))
except Exception as e:
    record("FAIL", "NmapScanner instantiation/scan", f"{type(e).__name__}: {e}")

# ─────────────────────────────────────────────────────────────────────────
print()
print("=" * 72)
print(" SUMMARY")
print("=" * 72)
n_pass = sum(1 for s, _, _ in RESULTS if s == "PASS")
n_warn = sum(1 for s, _, _ in RESULTS if s == "WARN")
n_fail = sum(1 for s, _, _ in RESULTS if s == "FAIL")
print(f"PASS={n_pass}  WARN={n_warn}  FAIL={n_fail}")
if n_warn:
    print("\nWARN = real detection gaps found in the live system, not test defects:")
    for s, name, detail in RESULTS:
        if s == "WARN":
            print(f"  - {name}\n      {detail}")

sys.exit(1 if n_fail else 0)
