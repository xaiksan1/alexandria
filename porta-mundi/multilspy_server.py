"""
MULTILSPY — LSP Code Intelligence Engine
Porta-Mundi module #11

Language Server Protocol-compatible code intelligence for the Alexandria codebase.
Symbols, diagnostics, hover, references — served over HTTP JSON-RPC on port 2088.
"""
import ast
import json
import logging
import re
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MULTILSPY] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("MULTILSPY")

PORT = 2088
WORKSPACE = Path("/home/ichigo/alexandria")

app = Flask(__name__)
CORS(app)


# ── LSP types ────────────────────────────────────────────────────────────────

SYMBOL_KINDS = {
    "module": 2, "namespace": 3, "class": 5, "method": 6,
    "function": 12, "variable": 13, "constant": 14, "string": 15,
}


def _mk_range(line: int, col: int = 0, end_line: Optional[int] = None, end_col: int = 0) -> dict:
    return {
        "start": {"line": line - 1, "character": col},
        "end":   {"line": (end_line or line) - 1, "character": end_col},
    }


# ── Code intelligence ─────────────────────────────────────────────────────────

class MultiLSPEngine:
    def __init__(self):
        self._start_time = time.time()
        self._lock = threading.Lock()
        self._requests = 0
        self._symbol_cache: dict[str, list] = {}
        logger.info("MultiLSP Engine initialized — workspace: %s", WORKSPACE)

    def _parse_python_symbols(self, code: str, uri: str) -> list[dict]:
        symbols = []
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return symbols

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                symbols.append({
                    "name": node.name,
                    "kind": SYMBOL_KINDS["class"],
                    "location": {"uri": uri, "range": _mk_range(node.lineno, node.col_offset)},
                    "containerName": None,
                })
                for item in ast.walk(node):
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item is not node:
                        symbols.append({
                            "name": item.name,
                            "kind": SYMBOL_KINDS["method"],
                            "location": {"uri": uri, "range": _mk_range(item.lineno, item.col_offset)},
                            "containerName": node.name,
                        })
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip methods already captured above
                symbols.append({
                    "name": node.name,
                    "kind": SYMBOL_KINDS["function"],
                    "location": {"uri": uri, "range": _mk_range(node.lineno, node.col_offset)},
                    "containerName": None,
                })

        return symbols

    def symbols(self, file_path: str) -> list[dict]:
        path = Path(file_path)
        if not path.exists():
            return []
        uri = f"file://{path.resolve()}"
        cache_key = f"{uri}:{path.stat().st_mtime}"
        with self._lock:
            if cache_key in self._symbol_cache:
                return self._symbol_cache[cache_key]
        try:
            code = path.read_text(errors="replace")
        except OSError:
            return []
        syms = self._parse_python_symbols(code, uri)
        with self._lock:
            self._symbol_cache[cache_key] = syms
            if len(self._symbol_cache) > 200:
                oldest = next(iter(self._symbol_cache))
                del self._symbol_cache[oldest]
        return syms

    def diagnostics(self, file_path: str) -> list[dict]:
        path = Path(file_path)
        if not path.exists():
            return []
        try:
            code = path.read_text(errors="replace")
        except OSError:
            return []

        diags = []

        # Syntax check
        try:
            ast.parse(code)
        except SyntaxError as e:
            diags.append({
                "range": _mk_range(e.lineno or 1, e.offset or 0),
                "severity": 1,  # Error
                "source": "multilspy",
                "message": f"SyntaxError: {e.msg}",
            })
            return diags  # No point checking further

        # Line-level hints
        for i, line in enumerate(code.splitlines(), 1):
            stripped = line.rstrip()
            if len(stripped) > 120:
                diags.append({
                    "range": _mk_range(i, 120),
                    "severity": 4,  # Hint
                    "source": "multilspy",
                    "message": f"Line exceeds 120 chars ({len(stripped)})",
                })
            if re.search(r"\t", line) and re.search(r"    ", line):
                diags.append({
                    "range": _mk_range(i, 0),
                    "severity": 3,  # Information
                    "source": "multilspy",
                    "message": "Mixed tabs and spaces",
                })

        return diags[:50]  # cap

    def hover(self, file_path: str, line: int, character: int) -> Optional[dict]:
        path = Path(file_path)
        if not path.exists():
            return None
        try:
            lines = path.read_text(errors="replace").splitlines()
            if line < 1 or line > len(lines):
                return None
            src_line = lines[line - 1]
            # Extract word at position
            m = re.search(r"\b(\w+)\b", src_line)
            word = None
            for match in re.finditer(r"\b\w+\b", src_line):
                if match.start() <= character <= match.end():
                    word = match.group(0)
                    break
            if not word:
                return None
            return {
                "contents": {"kind": "plaintext", "value": f"{word} — symbol in {path.name}"},
                "range": _mk_range(line, character),
            }
        except Exception:
            return None

    def workspace_scan(self, pattern: str = "*.py", limit: int = 30) -> dict:
        files = [str(p) for p in WORKSPACE.rglob(pattern) if ".git" not in str(p)][:limit]
        total_symbols = 0
        total_diags = 0
        file_results = []
        for f in files:
            syms = self.symbols(f)
            diags = self.diagnostics(f)
            total_symbols += len(syms)
            total_diags += len(diags)
            if diags:
                file_results.append({
                    "file": str(Path(f).relative_to(WORKSPACE)),
                    "symbols": len(syms),
                    "diagnostics": len(diags),
                })
        return {
            "files_scanned": len(files),
            "total_symbols": total_symbols,
            "total_diagnostics": total_diags,
            "files_with_issues": file_results[:10],
        }

    def handle_rpc(self, method: str, params: dict) -> Any:
        with self._lock:
            self._requests += 1
        if method == "textDocument/documentSymbol":
            uri = params.get("textDocument", {}).get("uri", "")
            path = uri.replace("file://", "")
            return self.symbols(path)
        if method == "textDocument/publishDiagnostics":
            uri = params.get("textDocument", {}).get("uri", "")
            path = uri.replace("file://", "")
            return self.diagnostics(path)
        if method == "textDocument/hover":
            uri = params.get("textDocument", {}).get("uri", "")
            pos = params.get("position", {})
            return self.hover(
                uri.replace("file://", ""),
                pos.get("line", 0) + 1,
                pos.get("character", 0),
            )
        if method == "workspace/symbol":
            query = params.get("query", "")
            path = params.get("path", str(WORKSPACE / "porta-mundi"))
            syms = []
            for py in Path(path).rglob("*.py"):
                syms.extend(self.symbols(str(py)))
            if query:
                syms = [s for s in syms if query.lower() in s["name"].lower()]
            return syms[:100]
        return {"error": f"Unknown method: {method}"}

    def status(self) -> dict:
        with self._lock:
            reqs = self._requests
            cached = len(self._symbol_cache)
        return {
            "module": "MULTILSPY", "role": "LSP Engine",
            "status": "ONLINE", "port": PORT,
            "uptime_s": round(time.time() - self._start_time, 1),
            "rpc_requests": reqs,
            "symbol_cache_size": cached,
            "workspace": str(WORKSPACE),
        }


engine = MultiLSPEngine()


@app.get("/health")
def health():
    return jsonify({"status": "ok", "module": "MULTILSPY", "port": PORT})


@app.get("/status")
def status():
    return jsonify(engine.status())


@app.post("/lsp")
def lsp_rpc():
    """JSON-RPC 2.0 LSP endpoint."""
    body = request.get_json(force=True, silent=True) or {}
    rpc_id = body.get("id", 0)
    method = body.get("method", "")
    params = body.get("params", {})
    if not method:
        return jsonify({"jsonrpc": "2.0", "id": rpc_id,
                        "error": {"code": -32600, "message": "method required"}}), 400
    result = engine.handle_rpc(method, params)
    return jsonify({"jsonrpc": "2.0", "id": rpc_id, "result": result})


@app.get("/symbols")
def symbols():
    file_path = request.args.get("file", "")
    if not file_path:
        return jsonify({"error": "file param required"}), 400
    return jsonify(engine.symbols(file_path))


@app.get("/diagnostics")
def diagnostics():
    file_path = request.args.get("file", "")
    if not file_path:
        return jsonify({"error": "file param required"}), 400
    return jsonify(engine.diagnostics(file_path))


@app.get("/workspace/scan")
def workspace_scan():
    pattern = request.args.get("pattern", "*.py")
    limit = min(int(request.args.get("limit", 30)), 100)
    return jsonify(engine.workspace_scan(pattern, limit))


def get_module_status() -> dict:
    return engine.status()


if __name__ == "__main__":
    logger.info("MULTILSPY starting on port %d", PORT)
    logger.info("Workspace: %s", WORKSPACE)
    app.run(host="127.0.0.1", port=PORT, debug=False)
