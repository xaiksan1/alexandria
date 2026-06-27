"""
SERENA — Intelligence Agent
Porta-Mundi module #10

Semantic code analysis, anomaly detection, UI serving.
Connects to Bifrost for LLM inference.
REST API + UI on port 3001.
"""
import json
import logging
import re
import time
import ast
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional
import httpx
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SERENA] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("SERENA")

PORT = 3011
BIFROST_URL = "http://localhost:8090/v1/chat/completions"
BIFROST_MODEL = "openrouter/anthropic/claude-sonnet-4.6"
PORTA_DIR = Path(__file__).parent
UI_DIR = Path(__file__).parent.parent / "ui" / "serena"

app = Flask(__name__)
CORS(app)


class SerenaIntelligence:
    def __init__(self):
        self._start_time = time.time()
        self._analyses = 0
        self._lock = threading.Lock()
        logger.info("Serena Intelligence initialized — semantic scalpel ready")

    # ── Static pattern analysis (no LLM needed) ──────────────────────────────

    _SUSPICIOUS = [
        (r"eval\s*\(", "HIGH", "eval() detected — possible code injection"),
        (r"exec\s*\(", "HIGH", "exec() detected — arbitrary code execution risk"),
        (r"os\.system\s*\(", "MEDIUM", "os.system() — prefer subprocess with args list"),
        (r"shell\s*=\s*True", "MEDIUM", "shell=True in subprocess — injection risk"),
        (r"pickle\.load", "HIGH", "pickle.load() — unsafe deserialization"),
        (r"__import__\s*\(", "MEDIUM", "Dynamic import — review intent"),
        (r"input\s*\(", "LOW", "input() — validate if from untrusted source"),
        (r"open\s*\(.+['\"]w", "LOW", "File write — ensure path is controlled"),
        (r"ANTHROPIC_API_KEY", "CRITICAL", "Hardcoded API key pattern detected"),
        (r"password\s*=\s*['\"].+['\"]", "CRITICAL", "Hardcoded password detected"),
    ]

    def analyze_code(self, code: str, filename: str = "<unknown>") -> dict:
        issues = []

        # Pattern scan
        for pattern, severity, desc in self._SUSPICIOUS:
            for m in re.finditer(pattern, code, re.IGNORECASE):
                line = code[:m.start()].count("\n") + 1
                issues.append({
                    "line": line, "severity": severity,
                    "description": desc, "match": m.group(0),
                })

        # AST metrics (Python only)
        metrics = {}
        if filename.endswith(".py") or not filename.endswith((
            ".js", ".ts", ".json", ".yaml", ".yml", ".md", ".html"
        )):
            try:
                tree = ast.parse(code)
                funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
                imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
                metrics = {
                    "functions": len(funcs),
                    "classes": len(classes),
                    "imports": len(imports),
                    "lines": len(code.splitlines()),
                    "complexity_hint": "high" if len(funcs) > 20 else "medium" if len(funcs) > 8 else "low",
                }
            except SyntaxError as e:
                issues.append({"line": e.lineno, "severity": "HIGH",
                               "description": f"Syntax error: {e.msg}", "match": ""})

        with self._lock:
            self._analyses += 1

        critical = sum(1 for i in issues if i["severity"] == "CRITICAL")
        high = sum(1 for i in issues if i["severity"] == "HIGH")

        return {
            "filename": filename,
            "ts": datetime.now().isoformat(),
            "issues": sorted(issues, key=lambda x: ["CRITICAL","HIGH","MEDIUM","LOW"].index(x["severity"])),
            "summary": {
                "total_issues": len(issues),
                "critical": critical, "high": high,
                "medium": sum(1 for i in issues if i["severity"] == "MEDIUM"),
                "low": sum(1 for i in issues if i["severity"] == "LOW"),
            },
            "verdict": "CRITICAL" if critical else "HIGH" if high else "CLEAN",
            "metrics": metrics,
        }

    def scan_directory(self, path: str, pattern: str = "*.py", limit: int = 20) -> dict:
        root = Path(path)
        if not root.exists():
            return {"error": f"Path not found: {path}"}
        files = list(root.rglob(pattern))[:limit]
        results = []
        for f in files:
            try:
                code = f.read_text(errors="replace")
                r = self.analyze_code(code, f.name)
                if r["summary"]["total_issues"] > 0:
                    results.append({"file": str(f.relative_to(root)), **r})
            except Exception:
                pass
        return {
            "path": path, "pattern": pattern,
            "files_scanned": len(files),
            "files_with_issues": len(results),
            "results": results,
        }

    def llm_analyze(self, code: str, question: str = "") -> Optional[str]:
        prompt = question or "Analyze this code for security vulnerabilities and bad practices. Be concise."
        try:
            resp = httpx.post(
                BIFROST_URL,
                json={
                    "model": BIFROST_MODEL,
                    "max_tokens": 600,
                    "messages": [
                        {"role": "system", "content": "You are Serena, an elite code security analyst. Be precise and concise."},
                        {"role": "user", "content": f"{prompt}\n\n```\n{code[:4000]}\n```"},
                    ],
                },
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning("Bifrost unavailable: %s", e)
            return None

    def status(self) -> dict:
        return {
            "module": "SERENA", "role": "Intelligence Agent",
            "status": "ONLINE", "port": PORT,
            "uptime_s": round(time.time() - self._start_time, 1),
            "analyses_run": self._analyses,
            "ui_available": (UI_DIR / "semantic_scalpel.html").exists(),
            "bifrost": BIFROST_URL,
        }


serena = SerenaIntelligence()


@app.get("/")
def index():
    ui_file = UI_DIR / "semantic_scalpel.html"
    if ui_file.exists():
        return send_file(str(ui_file))
    st = serena.status()
    return Response(
        f"<html><body><pre>{json.dumps(st, indent=2)}</pre></body></html>",
        mimetype="text/html",
    )


@app.get("/health")
def health():
    return jsonify({"status": "ok", "module": "SERENA", "port": PORT})


@app.get("/status")
def status():
    return jsonify(serena.status())


@app.post("/analyze")
def analyze():
    body = request.get_json(force=True, silent=True) or {}
    code = body.get("code", "")
    filename = body.get("filename", "code.py")
    use_llm = body.get("llm", False)
    question = body.get("question", "")

    if not code:
        return jsonify({"error": "code field required"}), 400

    result = serena.analyze_code(code, filename)

    if use_llm:
        llm_output = serena.llm_analyze(code, question)
        result["llm_analysis"] = llm_output

    return jsonify(result)


@app.post("/scan")
def scan():
    body = request.get_json(force=True, silent=True) or {}
    path = body.get("path", str(PORTA_DIR))
    pattern = body.get("pattern", "*.py")
    limit = min(int(body.get("limit", 20)), 50)
    return jsonify(serena.scan_directory(path, pattern, limit))


def get_module_status() -> dict:
    return serena.status()


if __name__ == "__main__":
    logger.info("SERENA activating on port %d", PORT)
    logger.info("Semantic Scalpel UI: %s", "available" if (UI_DIR / "semantic_scalpel.html").exists() else "not found")
    logger.info("Bifrost LLM: %s", BIFROST_URL)
    app.run(host="0.0.0.0", port=PORT, debug=False)
