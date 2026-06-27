"""
JARVIS local proxy server — Security Master Chief of Alexandria.
Serves index.html, proxies /v1/chat to Bifrost, and exposes Porta-Mundi status.
"""
import json
import asyncio
import subprocess
import shutil
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from pathlib import Path

app = FastAPI()
HERE = Path(__file__).parent

# Provider chain: on 429/529/timeout, rotate to next without waiting.
# Each entry is independent — Bifrost for the first two, direct call for opencode.
PROVIDERS = [
    {
        "label": "openrouter",
        "url": "http://localhost:8090/v1/chat/completions",
        "model": "openrouter/anthropic/claude-sonnet-4.6",
    },
    {
        "label": "nim",
        "url": "http://localhost:8090/v1/chat/completions",
        "model": "openai/meta/llama-3.3-70b-instruct",
    },
    {
        "label": "opencode",
        "url": "https://opencode.ai/zen/v1/chat/completions",
        "model": "big-pickle",
    },
]
_ROTATE_CODES = {429, 529}

# Porta-Mundi — 11 defense modules
MODULES = [
    {"id": "zangetsu",   "name": "ZANGETSU",   "role": "Security Guardian",   "port": 7500, "proc": "zangetsu_guardian",    "file": "zangetsu_guardian.py",    "flux": None, "daemon": False},
    {"id": "phoenix",    "name": "PHOENIX",     "role": "Observability",       "port": 8000, "proc": "phoenix_observer",     "file": "phoenix_observer.py",     "flux": 1,    "daemon": True},
    {"id": "sentinelle", "name": "SENTINELLE",  "role": "Perimeter Watch",     "port": 9000, "proc": "zangetsu_security",    "file": "zangetsu_security.py",    "flux": 2,    "daemon": False},
    {"id": "paintshop",  "name": "PAINT SHOP",  "role": "Threat Renderer",     "port": 4141, "proc": "paint_shop",           "file": "paint_shop.py",           "flux": 3,    "daemon": True},
    {"id": "aegis",      "name": "AEGIS",       "role": "Defensive Shield",    "port": 8085, "proc": "alexandria_cyber_gate", "file": "alexandria_cyber_gate.py","flux": 4,    "daemon": True},
    {"id": "chapel",     "name": "CHAPEL XVI",  "role": "Credential Vault",    "port": 6001, "proc": "chapel_xvi_vault",     "file": "chapel_xvi_vault.py",     "flux": 6,    "daemon": False},
    {"id": "labyrinthe", "name": "LABYRINTHE",  "role": "Code Navigation",     "port": None, "proc": "labyrinthe_navigator", "file": "labyrinthe_navigator.py", "flux": None, "daemon": False},
    {"id": "iothackbot", "name": "IOTHACKBOT",  "role": "IoT Penetration",     "port": None, "proc": "iothackbot_agent",     "file": "iothackbot_agent.py",     "flux": None, "daemon": False},
    {"id": "minotaure",  "name": "MINOTAURE",   "role": "Network Honeypot",    "port": None, "proc": "minotaure_gatekeeper", "file": "minotaure_gatekeeper.py", "flux": None, "daemon": False},
    {"id": "alexa",      "name": "ALEXA",       "role": "Infra Orchestration", "port": 5000, "proc": "alexa_api",            "file": "alexa_api.py",            "flux": None, "daemon": True},
    {"id": "serena",     "name": "SERENA",      "role": "Intelligence Agent",  "port": 3011, "proc": "serena_agent",         "file": "serena_agent.py",         "flux": None, "daemon": True},
    {"id": "multilspy",  "name": "MULTILSPY",   "role": "LSP Engine",          "port": 2088, "proc": "multilspy_server",     "file": "multilspy_server.py",     "flux": None, "daemon": True},
    {"id": "tartarus",   "name": "TARTARUS",    "role": "Containment Prison",  "port": 4343, "proc": "tartarus_prison",      "file": "tartarus_prison.py",      "flux": None, "daemon": True},
    {"id": "floatilla",  "name": "FLOATILLA",   "role": "Scout Network",       "port": 4242, "proc": "floatilla_agent",      "file": "floatilla_agent.py",      "flux": None, "daemon": True},
]

PORTA_DIR = Path("/home/ichigo/alexandria/porta-mundi")


async def _port_open(port: int) -> bool:
    try:
        _, w = await asyncio.wait_for(
            asyncio.open_connection("127.0.0.1", port), timeout=0.6
        )
        w.close()
        return True
    except Exception:
        return False


def _proc_running(proc: str) -> bool:
    try:
        r = subprocess.run(["pgrep", "-f", proc], capture_output=True, timeout=2)
        return r.returncode == 0
    except Exception:
        return False


def _file_exists(module: dict) -> bool:
    f = module.get("file")
    if not f:
        return False
    return (PORTA_DIR / f).exists()


@app.get("/")
async def index():
    return FileResponse(HERE / "index.html")


@app.get("/health")
async def health():
    try:
        async with httpx.AsyncClient(timeout=3) as c:
            r = await c.get("http://localhost:8090/health")
            bstatus = r.json().get("status", "ok")
        return {"status": "ok", "bifrost": bstatus, "providers": [p["label"] for p in PROVIDERS]}
    except Exception as e:
        return JSONResponse({"status": "degraded", "bifrost": str(e)}, status_code=503)


@app.get("/porta-mundi/status")
async def porta_status():
    port_checks = {
        m["id"]: _port_open(m["port"]) if m["port"] else asyncio.sleep(0, result=False)
        for m in MODULES
    }
    port_results = {k: await v for k, v in port_checks.items()}

    results = []
    for m in MODULES:
        port_ok = port_results[m["id"]]
        proc_ok = _proc_running(m["proc"])
        file_ok = _file_exists(m)

        if port_ok:
            status = "active"
        elif proc_ok:
            status = "degraded"
        elif file_ok:
            status = "dormant"
        else:
            status = "offline"

        results.append({
            "id": m["id"], "name": m["name"], "role": m["role"],
            "status": status, "port": m["port"], "flux": m["flux"],
            "port_ok": port_ok, "proc_ok": proc_ok,
        })
    return results


async def _start_module(module_id: str) -> dict:
    module = next((m for m in MODULES if m["id"] == module_id), None)
    if not module:
        return {"id": module_id, "status": "error", "error": "unknown module"}

    file = module.get("file")
    if not file:
        return {"id": module_id, "status": "no_file", "error": "no launch script (not yet implemented)"}

    script = PORTA_DIR / file
    if not script.exists():
        return {"id": module_id, "status": "error", "error": f"script not found: {script}"}

    proc_name = module["proc"]
    if _proc_running(proc_name):
        return {"id": module_id, "status": "already_running"}

    if not shutil.which("pm2"):
        return {"id": module_id, "status": "error", "error": "pm2 not found in PATH"}

    cmd = ["pm2", "start", str(script), "--name", proc_name, "--interpreter", "/usr/bin/python3",
           "--cwd", str(PORTA_DIR)]
    # Only real daemon servers (aegis, alexa) get auto-restart; diagnostic scripts exit cleanly
    if not module.get("daemon"):
        cmd.append("--no-autorestart")

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15, cwd=str(PORTA_DIR))
        if r.returncode != 0:
            return {"id": module_id, "status": "error", "error": (r.stderr or r.stdout).strip()}
        return {"id": module_id, "status": "started", "proc": proc_name}
    except Exception as e:
        return {"id": module_id, "status": "error", "error": str(e)}


@app.post("/porta-mundi/start/{module_id}")
async def porta_start(module_id: str):
    return await _start_module(module_id)


@app.post("/porta-mundi/start-all")
async def porta_start_all():
    results = []
    for m in MODULES:
        results.append(await _start_module(m["id"]))
    return results


@app.post("/v1/chat")
async def proxy_chat(request: Request):
    """
    Accepts {system, messages, max_tokens} from browser.
    Streams from Bifrost. On 429/529/timeout, rotates to next provider immediately.
    """
    body = await request.json()
    system = body.get("system", "")
    messages = body.get("messages", [])
    max_tokens = body.get("max_tokens", 400)

    openai_messages = []
    if system:
        openai_messages.append({"role": "system", "content": system})
    openai_messages.extend(messages)

    headers = {"Content-Type": "application/json"}

    async def stream_bifrost():
        for i, provider in enumerate(PROVIDERS):
            is_last = i == len(PROVIDERS) - 1
            payload = json.dumps({
                "model": provider["model"],
                "max_tokens": max_tokens,
                "stream": True,
                "messages": openai_messages,
            }).encode()

            try:
                async with httpx.AsyncClient(timeout=120) as client:
                    async with client.stream(
                        "POST", provider["url"],
                        content=payload, headers=headers
                    ) as resp:
                        if resp.status_code in _ROTATE_CODES:
                            if not is_last:
                                yield f"data: {{\"_jarvis_switch\": \"{PROVIDERS[i+1]['label']}\"}}\n\n".encode()
                                continue
                            yield f"data: {{\"error\": \"All providers rate-limited ({resp.status_code})\"}}\n\ndata: [DONE]\n\n".encode()
                            return
                        async for chunk in resp.aiter_bytes():
                            yield chunk
                        return

            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                if not is_last:
                    yield f"data: {{\"_jarvis_switch\": \"{PROVIDERS[i+1]['label']}\"}}\n\n".encode()
                    continue
                yield f"data: {{\"error\": \"All providers unreachable: {type(exc).__name__}\"}}\n\ndata: [DONE]\n\n".encode()

    return StreamingResponse(stream_bifrost(), media_type="text/event-stream")


# ── GhostDesk integration ──
GHOSTDESK_MCP = "http://localhost:3000/mcp"
_gd_sid: str | None = None
_gd_lock = asyncio.Lock()


def _sse_result(text: str) -> dict:
    for line in text.splitlines():
        if line.startswith("data:"):
            raw = line[5:].strip()
            if raw and raw != "[DONE]":
                try:
                    ev = json.loads(raw)
                    if "method" not in ev:  # skip notification frames
                        return ev
                except Exception:
                    pass
    return {}


async def _gd_init(client: httpx.AsyncClient) -> str:
    r = await client.post(
        GHOSTDESK_MCP,
        json={"jsonrpc": "2.0", "id": 0, "method": "initialize",
              "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                         "clientInfo": {"name": "jarvis", "version": "1"}}},
        headers={"Content-Type": "application/json",
                 "Accept": "application/json, text/event-stream"},
    )
    return r.headers.get("mcp-session-id") or ""


async def _gd_call(tool: str, arguments: dict) -> dict:
    global _gd_sid
    hdrs = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": tool, "arguments": arguments}}
    async with httpx.AsyncClient(timeout=30) as c:
        if not _gd_sid:
            async with _gd_lock:
                if not _gd_sid:
                    _gd_sid = await _gd_init(c)
        r = await c.post(GHOSTDESK_MCP, json=payload,
                         headers={**hdrs, "mcp-session-id": _gd_sid or ""})
        if r.status_code in (400, 404):
            async with _gd_lock:
                _gd_sid = await _gd_init(c)
            r = await c.post(GHOSTDESK_MCP, json=payload,
                             headers={**hdrs, "mcp-session-id": _gd_sid or ""})
        ev = _sse_result(r.text)
        if "error" in ev:
            err = ev["error"]
            raise RuntimeError(err.get("message", str(err)) if isinstance(err, dict) else str(err))
        return ev.get("result", {})


@app.get("/v1/desktop/status")
async def desktop_status():
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            await _gd_init(c)
        return {"status": "online", "port": 3000}
    except Exception as e:
        return JSONResponse({"status": "offline", "error": str(e)}, status_code=503)


@app.get("/v1/desktop/screenshot")
async def desktop_screenshot():
    try:
        result = await _gd_call("screen_shot", {})
        for item in result.get("content", []):
            if item.get("type") == "image":
                return {"image": f"data:{item['mimeType']};base64,{item['data']}"}
        return JSONResponse({"error": "no image in response"}, status_code=500)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/v1/desktop/exec")
async def desktop_exec(request: Request):
    body = await request.json()
    command = body.get("command", "").strip()
    if not command:
        return JSONResponse({"error": "command required"}, status_code=400)
    try:
        result = await _gd_call("exec_shell", {"command": command})
        texts = [c["text"] for c in result.get("content", []) if c.get("type") == "text"]
        raw = "\n".join(texts)
        try:
            parsed = json.loads(raw)
            stdout = parsed.get("stdout", "")
            stderr = parsed.get("stderr", "")
            output = (stdout + ("\n" + stderr if stderr else "")).rstrip()
            is_error = parsed.get("returncode", 0) != 0 or parsed.get("timed_out", False)
        except Exception:
            output = raw
            is_error = result.get("isError", False)
        return {"output": output, "isError": is_error}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/v1/desktop/apps")
async def desktop_apps():
    try:
        result = await _gd_call("app_list", {})
        texts = [c["text"] for c in result.get("content", []) if c.get("type") == "text"]
        return {"apps": "\n".join(texts)}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/v1/desktop/tool")
async def desktop_tool(request: Request):
    body = await request.json()
    tool = body.get("tool", "")
    args = body.get("args", {})
    if not tool:
        return JSONResponse({"error": "tool required"}, status_code=400)
    try:
        return await _gd_call(tool, args)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ---------------------------------------------------------------------------
# Bug Bounty Hunter — /v1/bounty/*
# All tools stream stdout via SSE so the UI can show live output.
# ---------------------------------------------------------------------------

GOBIN = "/home/ichigo/go/bin"
LOCAL_BIN = "/home/ichigo/.local/bin"

# Allowed tools with their absolute paths — never shell-expand user input.
BOUNTY_TOOLS: dict[str, str] = {
    "subfinder":   f"{GOBIN}/subfinder",
    "dnsx":        f"{GOBIN}/dnsx",
    "katana":      f"{GOBIN}/katana",
    "gau":         f"{GOBIN}/gau",
    "waybackurls": f"{GOBIN}/waybackurls",
    "nuclei":      f"{GOBIN}/nuclei",
    "ffuf":        f"{GOBIN}/ffuf",
    "gobuster":    f"{GOBIN}/gobuster",
    "hakrawler":   f"{GOBIN}/hakrawler",
    "httpx":       f"{LOCAL_BIN}/httpx",
    "sqlmap":      f"{LOCAL_BIN}/sqlmap",
    "nmap":        "/usr/bin/nmap",
    "nikto":       "/usr/bin/nikto",
    "masscan":     "/usr/bin/masscan",
}


def _validate_target(target: str) -> bool:
    """Accept domains and IPs only — no shell metacharacters."""
    import re
    return bool(re.fullmatch(r"[a-zA-Z0-9._\-/]+", target))


async def _stream_tool(cmd: list[str]):
    """Run cmd and yield each stdout line as an SSE data event."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    assert proc.stdout is not None
    async for line in proc.stdout:
        yield f"data: {line.decode(errors='replace').rstrip()}\n\n"
    await proc.wait()
    yield "data: [DONE]\n\n"


@app.get("/v1/bounty/tools")
async def bounty_tools():
    """List available tools and whether their binary exists."""
    return {
        name: {"path": path, "available": Path(path).exists()}
        for name, path in BOUNTY_TOOLS.items()
    }


@app.post("/v1/bounty/recon")
async def bounty_recon(request: Request):
    """Subdomain discovery: subfinder → dnsx → httpx pipeline, streamed."""
    body = await request.json()
    target = body.get("target", "").strip()
    if not target or not _validate_target(target):
        return JSONResponse({"error": "invalid target"}, status_code=400)

    async def _run():
        yield f"data: [RECON] Starting recon on {target}\n\n"
        # subfinder
        yield f"data: [subfinder] Enumerating subdomains...\n\n"
        async for chunk in _stream_tool([BOUNTY_TOOLS["subfinder"], "-d", target, "-silent"]):
            yield chunk
        # httpx probe
        yield f"data: [httpx] Probing live hosts...\n\n"
        async for chunk in _stream_tool([
            BOUNTY_TOOLS["httpx"], "-l", "/dev/stdin",
            "-title", "-status-code", "-silent",
        ]):
            yield chunk

    return StreamingResponse(_run(), media_type="text/event-stream")


@app.post("/v1/bounty/scan")
async def bounty_scan(request: Request):
    """Port + vuln scan: nmap then nuclei, streamed."""
    body = await request.json()
    target = body.get("target", "").strip()
    if not target or not _validate_target(target):
        return JSONResponse({"error": "invalid target"}, status_code=400)

    async def _run():
        yield f"data: [SCAN] Starting scan on {target}\n\n"
        yield f"data: [nmap] Port scanning...\n\n"
        async for chunk in _stream_tool([
            BOUNTY_TOOLS["nmap"], "-sV", "--open", "-T4", target,
        ]):
            yield chunk
        yield f"data: [nuclei] Running vulnerability templates...\n\n"
        async for chunk in _stream_tool([
            BOUNTY_TOOLS["nuclei"], "-u", f"https://{target}",
            "-severity", "medium,high,critical", "-silent",
        ]):
            yield chunk

    return StreamingResponse(_run(), media_type="text/event-stream")


@app.post("/v1/bounty/fuzz")
async def bounty_fuzz(request: Request):
    """Directory fuzzing with ffuf, streamed."""
    body = await request.json()
    target = body.get("target", "").strip()
    wordlist = body.get("wordlist", "/usr/share/wordlists/dirb/common.txt")
    if not target or not _validate_target(target):
        return JSONResponse({"error": "invalid target"}, status_code=400)
    if not Path(wordlist).exists():
        return JSONResponse({"error": f"wordlist not found: {wordlist}"}, status_code=400)

    async def _run():
        yield f"data: [FUZZ] Fuzzing {target}\n\n"
        async for chunk in _stream_tool([
            BOUNTY_TOOLS["ffuf"],
            "-u", f"https://{target}/FUZZ",
            "-w", wordlist,
            "-mc", "200,301,302,403",
            "-t", "50",
        ]):
            yield chunk

    return StreamingResponse(_run(), media_type="text/event-stream")


@app.post("/v1/bounty/crawl")
async def bounty_crawl(request: Request):
    """URL crawl + wayback machine URLs."""
    body = await request.json()
    target = body.get("target", "").strip()
    if not target or not _validate_target(target):
        return JSONResponse({"error": "invalid target"}, status_code=400)

    async def _run():
        yield f"data: [CRAWL] Crawling {target}\n\n"
        yield f"data: [gau] Fetching known URLs from AlienVault + Wayback...\n\n"
        async for chunk in _stream_tool([BOUNTY_TOOLS["gau"], target]):
            yield chunk
        yield f"data: [katana] Active crawl...\n\n"
        async for chunk in _stream_tool([
            BOUNTY_TOOLS["katana"], "-u", f"https://{target}", "-silent", "-depth", "3",
        ]):
            yield chunk

    return StreamingResponse(_run(), media_type="text/event-stream")
