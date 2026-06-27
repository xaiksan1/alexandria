#!/usr/bin/env python3
"""
PORTA-MUNDI — Repo Quarantine Scanner
Phoenix Module: Clone → Analyse → Verdict

Usage:
    python3 porta-mundi/repo_quarantine.py <git_url_or_local_path>

Verdict:
    TRUSTED     → score < 20  — safe to use
    MONITORED   → score 20-49 — use with caution
    QUARANTINED → score >= 50 — do not install
"""

import json, math, os, re, shutil, subprocess, sys, tempfile, time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ADAM_ROOT = Path(__file__).parent.parent
TRUST_LEDGER = ADAM_ROOT / "SELF" / "trust_ledger.json"
SCAN_RESULTS_DIR = Path(__file__).parent / "quarantine_reports"

SCANNABLE_EXTENSIONS = {
    ".py",".js",".ts",".mjs",".cjs",".sh",".bash",
    ".json",".yaml",".yml",".toml",".env",".cfg",
    ".rb",".go",".rs",".php",".java",".kt",".md",".txt",
}

SKIP_DIRS = {
    "node_modules",".git","__pycache__","dist","build",
    "target",".cache","vendor","venv",".venv","env",".tox",
}

IOC_PATTERNS = [
    {"id":"OBF-001","name":"eval(base64_decode)","pattern":re.compile(r'eval\s*\(\s*(base64|b64|atob)',re.I),"severity":25,"description":"Obfuscated code execution"},
    {"id":"OBF-002","name":"exec(compile())","pattern":re.compile(r'exec\s*\(\s*compile\s*\(',re.I),"severity":20,"description":"Dynamic compilation + execution"},
    {"id":"OBF-003","name":"exec(__import__)","pattern":re.compile(r'exec\s*\(\s*__import__',re.I),"severity":20,"description":"Hidden import via exec"},
    {"id":"OBF-004","name":"chr() chain","pattern":re.compile(r'chr\(\d+\)\s*\+\s*chr\(\d+\)\s*\+\s*chr\(\d+\)'),"severity":15,"description":"String obfuscation via char codes"},
    {"id":"PER-001","name":"PATH modification","pattern":re.compile(r'(os\.environ|PATH)\s*[+=].*?(site-packages|\.local)',re.I),"severity":15,"description":"Modifies system PATH"},
    {"id":"PER-002","name":"crontab injection","pattern":re.compile(r'crontab\s*-[le]|/etc/cron',re.I),"severity":20,"description":"Writes to crontab"},
    {"id":"PER-003","name":"systemd service write","pattern":re.compile(r'/etc/systemd/system|systemctl\s+enable',re.I),"severity":20,"description":"Installs systemd service"},
    {"id":"PER-004","name":"shell profile write","pattern":re.compile(r'(~/\.bashrc|~/\.profile|~/.zshrc|/etc/rc\.local)',re.I),"severity":15,"description":"Modifies shell startup"},
    {"id":"PER-005","name":"SSH authorized_keys","pattern":re.compile(r'authorized_keys|ssh_config',re.I),"severity":30,"description":"Modifies SSH keys — backdoor"},
    {"id":"NET-001","name":"Hardcoded IP","pattern":re.compile(r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b'),"severity":8,"description":"Hardcoded IP address"},
    {"id":"NET-002","name":"POST secrets externally","pattern":re.compile(r'requests\.(post|put)\s*\(.*?(password|token|key|secret|api_key)',re.I|re.S),"severity":20,"description":"Sends secrets to external endpoint"},
    {"id":"NET-003","name":"Exfil service URL","pattern":re.compile(r'(pastebin\.com|ngrok|webhook\.site|discord\.com/api/webhooks)',re.I),"severity":25,"description":"Sends data to exfiltration service"},
    {"id":"DOR-001","name":"Long sleep (>1 day)","pattern":re.compile(r'sleep\s*\(\s*(\d{5,})\s*\)',re.I),"severity":15,"description":"Long sleep — dormant activation"},
    {"id":"DOR-002","name":"Date/weekday trigger","pattern":re.compile(r'(datetime\.now|date\.today)\(\).*?(weekday|month|day)\s*[=!><]+\s*\d',re.I),"severity":10,"description":"Time-based conditional"},
    {"id":"STG-001","name":"Zero-width chars","pattern":re.compile(r'[\u200b\u200c\u200d\ufeff\u2060\u200e\u200f]'),"severity":20,"description":"Hidden steganography (Ghost Protocol pattern)"},
    {"id":"STG-002","name":"Large base64 blob","pattern":re.compile(r'[A-Za-z0-9+/]{200,}={0,2}'),"severity":10,"description":"Large base64 block — verify payload"},
    {"id":"ESC-001","name":"Non-interactive sudo","pattern":re.compile(r'sudo\s+-n\s|SUDO_ASKPASS',re.I),"severity":18,"description":"Non-interactive sudo — priv escalation"},
    {"id":"ESC-002","name":"chmod 777","pattern":re.compile(r'chmod\s+(777|a\+rwx)',re.I),"severity":12,"description":"World-writable permissions"},
    {"id":"ESC-003","name":"setuid/setgid","pattern":re.compile(r'(os\.setuid|os\.setgid|setresuid|prctl)',re.I),"severity":20,"description":"UID/GID manipulation"},
]

def calculate_entropy(data):
    if not data: return 0.0
    freq = defaultdict(int)
    for ch in data: freq[ch] += 1
    n = len(data)
    return -sum((c/n)*math.log2(c/n) for c in freq.values())

def find_high_entropy_strings(content, min_length=20, threshold=4.5):
    findings = []
    for match in re.finditer(r'["\']([A-Za-z0-9+/=_\-]{%d,})["\']' % min_length, content):
        s = match.group(1)
        e = calculate_entropy(s)
        if e >= threshold:
            findings.append({"string": s[:60]+"…" if len(s)>60 else s, "entropy": round(e,2)})
    return findings

def iter_scannable_files(repo_path):
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            fpath = Path(root) / fname
            if fpath.suffix.lower() in SCANNABLE_EXTENSIONS:
                try:
                    yield fpath, fpath.read_text(encoding="utf-8", errors="ignore")
                except (PermissionError, OSError):
                    pass

def scan_repo(repo_path):
    findings, entropy_hits = [], []
    total_files = total_lines = 0
    file_scores = defaultdict(int)

    for fpath, content in iter_scannable_files(repo_path):
        total_files += 1
        total_lines += content.count("\n")
        rel = str(fpath.relative_to(repo_path))

        for ioc in IOC_PATTERNS:
            for match in ioc["pattern"].finditer(content):
                line_no = content[:match.start()].count("\n") + 1
                findings.append({
                    "ioc_id": ioc["id"], "name": ioc["name"],
                    "description": ioc["description"], "severity": ioc["severity"],
                    "file": rel, "line": line_no,
                    "snippet": content[max(0,match.start()-30):match.end()+30].strip()[:120],
                })
                file_scores[rel] += ioc["severity"]

        for hit in find_high_entropy_strings(content):
            entropy_hits.append({"file": rel, **hit})

    raw_score = sum(f["severity"] for f in findings)
    entropy_score = min(len(entropy_hits) * 3, 30)
    total_score = raw_score + entropy_score

    seen, deduped = set(), []
    for f in findings:
        key = (f["ioc_id"], f["file"])
        if key not in seen:
            seen.add(key)
            deduped.append(f)

    return {
        "total_files_scanned": total_files,
        "total_lines": total_lines,
        "ioc_findings": deduped,
        "entropy_hits": entropy_hits[:20],
        "top_suspicious_files": sorted(file_scores.items(), key=lambda x: -x[1])[:10],
        "raw_score": raw_score,
        "entropy_score": entropy_score,
        "total_score": total_score,
    }

def verdict(score):
    if score < 20:   return "TRUSTED",     "\033[92m"
    elif score < 50: return "MONITORED",   "\033[93m"
    else:            return "QUARANTINED", "\033[91m"

def write_trust_ledger(source, result, v_label):
    if not TRUST_LEDGER.exists(): return
    try:
        ledger = json.loads(TRUST_LEDGER.read_text())
        if "repos" not in ledger: ledger["repos"] = {}
        ledger["repos"][source] = {
            "verdict": v_label, "score": result["total_score"],
            "scanned_at": datetime.now().isoformat(),
            "ioc_count": len(result["ioc_findings"]),
            "top_iocs": [f["ioc_id"] for f in result["ioc_findings"][:5]],
        }
        TRUST_LEDGER.write_text(json.dumps(ledger, indent=2))
    except Exception as e:
        print(f"  [warn] trust ledger: {e}")

R="\033[0m"; B="\033[1m"; D="\033[2m"

def print_report(source, result, elapsed):
    v_label, v_color = verdict(result["total_score"])
    print(f"\n{'═'*60}")
    print(f"{B}  PORTA-MUNDI — Repo Quarantine Scanner (Phoenix){R}")
    print(f"{'═'*60}")
    print(f"  Repo   : {source}")
    print(f"  Files  : {result['total_files_scanned']} / {result['total_lines']} lines")
    print(f"  IOCs   : {len(result['ioc_findings'])} unique findings")
    print(f"  Score  : {result['raw_score']} (IOC) + {result['entropy_score']} (entropy) = {B}{result['total_score']}{R}")
    print(f"\n  Verdict: {v_color}{B}{v_label}{R}")
    print(f"{'─'*60}")

    if result["ioc_findings"]:
        print(f"\n  {B}IOC Findings (sorted by severity):{R}")
        for f in sorted(result["ioc_findings"], key=lambda x: -x["severity"])[:15]:
            c = "\033[91m" if f["severity"]>=20 else "\033[93m" if f["severity"]>=10 else D
            print(f"  {c}[{f['ioc_id']}] +{f['severity']:2d}{R}  {f['name']}")
            print(f"       {D}{f['file']}:{f['line']} → {f['snippet'][:80]}{R}")

    if result["top_suspicious_files"]:
        print(f"\n  {B}Top suspicious files:{R}")
        for fname, score in result["top_suspicious_files"][:5]:
            print(f"  +{score:3d}  {fname}")

    if result["entropy_hits"]:
        print(f"\n  {B}High-entropy strings (top 5):{R}")
        for h in result["entropy_hits"][:5]:
            print(f"  {D}H={h['entropy']}  {h['file']}  →  {h['string'][:60]}{R}")

    print(f"\n  Elapsed: {elapsed:.1f}s")
    print(f"{'═'*60}\n")

def generate_certificate(source: str, result: dict, v_label: str, scan_id: str, elapsed: float) -> str:
    """Generate ISO-PHOENIX certificate — human-readable audit stamp."""
    now = datetime.now()
    ts_iso = now.strftime("%Y-%m-%dT%H:%M:%S") + " EDT"

    threat_level = {
        "TRUSTED":     "ALPHA-ZERO  (Safe for Sandbox Exit)",
        "MONITORED":   "BETA-ONE    (Conditional — Review Required)",
        "QUARANTINED": "GAMMA-RED   (Threat Detected — Do Not Deploy)",
    }[v_label]

    clearance = {
        "TRUSTED":     "GRANTED",
        "MONITORED":   "CONDITIONAL",
        "QUARANTINED": "DENIED",
    }[v_label]

    verdict_line = {
        "TRUSTED":     "[ ✓ ] PORTA-MUNDI : PHOENIX ZERO-TRUST CERTIFICATE",
        "MONITORED":   "[ ⚠ ] PORTA-MUNDI : PHOENIX CONDITIONAL CERTIFICATE",
        "QUARANTINED": "[ ✗ ] PORTA-MUNDI : PHOENIX THREAT DETECTED",
    }[v_label]

    ioc_summary = (
        f"0 (No IOCs detected)"
        if not result["ioc_findings"]
        else f"{len(result['ioc_findings'])} — {', '.join(set(f['ioc_id'] for f in result['ioc_findings'][:5]))}"
    )

    entropy_summary = (
        f"0 (No hidden payloads / Ghost Protocol patterns)"
        if not result["entropy_hits"]
        else f"{result['entropy_score']} pts — {len(result['entropy_hits'])} high-entropy strings detected"
    )

    top_iocs_block = ""
    if result["ioc_findings"]:
        top_iocs_block = "\n  [ TOP IOCs ]\n"
        for f in sorted(result["ioc_findings"], key=lambda x: -x["severity"])[:5]:
            top_iocs_block += f"  {f['ioc_id']:10s} +{f['severity']:2d}  {f['name']} ({f['file']}:{f['line']})\n"
        top_iocs_block += "━" * 72 + "\n"

    cert = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
           {verdict_line}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  TARGET      : {source}
  TIMESTAMP   : {ts_iso}
  SCAN_ID     : {scan_id}
  ENGINE      : Porta-Mundi Quarantine Scanner v1.0 / ADAM Trust Ledger
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [ METRICS ]
  Files Analyzed    : {result['total_files_scanned']}
  Lines of Code     : {result['total_lines']:,}
  Scan Duration     : {elapsed:.1f}s
  Entropy Score     : {entropy_summary}
  Malicious IOCs    : {ioc_summary}
  Total Risk Score  : {result['total_score']} / 100+
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{top_iocs_block}  [ VERDICT ]
  Status            : {v_label}
  Threat Level      : {threat_level}
  Clearance         : {clearance}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
       "By the authority of the AlexandrIA Trust Ledger."
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Audit trail: quarantine_reports/{scan_id}.json
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".strip()
    return cert


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    source = sys.argv[1]
    tmp_dir = None
    t0 = time.time()

    if source.startswith("http") or source.startswith("git@"):
        print(f"  [phoenix] Cloning to isolated sandbox…")
        tmp_dir = tempfile.mkdtemp(prefix="phoenix_quarantine_")
        repo_path = Path(tmp_dir) / "repo"
        proc = subprocess.run(
            ["git", "clone", "--depth=1", "--quiet", source, str(repo_path)],
            capture_output=True, text=True
        )
        if proc.returncode != 0:
            print(f"  [error] Clone failed: {proc.stderr}")
            sys.exit(1)
        print(f"  [phoenix] Clone complete. Scanning…")
    else:
        repo_path = Path(source).expanduser().resolve()
        if not repo_path.exists():
            print(f"  [error] Path not found: {repo_path}")
            sys.exit(1)
        print(f"  [phoenix] Scanning: {repo_path}")

    try:
        result = scan_repo(repo_path)
        elapsed = time.time() - t0
        v_label, _ = verdict(result["total_score"])

        print_report(source, result, elapsed)
        write_trust_ledger(source, result, v_label)

        SCAN_RESULTS_DIR.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = re.sub(r'[^a-zA-Z0-9_-]', '_', Path(source).name or "repo")
        scan_id = f"PHOENIX-{ts}_{name}"

        # JSON report (machine-readable)
        rpath = SCAN_RESULTS_DIR / f"{ts}_{name}_{v_label}.json"
        rpath.write_text(json.dumps({
            "source": source, "verdict": v_label, "scan_id": scan_id,
            "scanned_at": datetime.now().isoformat(), **result
        }, indent=2, default=str))

        # ISO-PHOENIX certificate (human-readable audit stamp)
        cert = generate_certificate(source, result, v_label, scan_id, elapsed)
        cert_path = SCAN_RESULTS_DIR / f"{ts}_{name}_{v_label}.CERTIFICATE.txt"
        cert_path.write_text(cert)
        print(cert)
        print(f"  JSON    : {rpath}")
        print(f"  Cert    : {cert_path}\n")

        sys.exit(0 if v_label=="TRUSTED" else 1 if v_label=="MONITORED" else 2)
    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)

if __name__ == "__main__":
    main()
