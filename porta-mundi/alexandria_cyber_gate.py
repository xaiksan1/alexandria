#!/usr/bin/env python3
"""
Alexandria Cyber-Gate (Porta-Mundi)
Consolidated Defense & Intelligence Interface

Modules:
1. Phoenix (Observability)
2. Sentinelle (Guardians)
3. Aegis (Defense)
4. ChapelXVI (Vault)
5. Alexa (Agent)
6. IOTHackBot (Hacker)
7. Serena (Agent)
8. multilspy (LSP Engine)
9. Zangetsu (Security)
10. Minotaure (Gatekeeper)
11. Labyrinthe (Navigation)
12. Paint Shop (Threat Enrichment & Response Renderer) — tags every rendered event
    with a watermark (residual-pixel tracer); without it Bounty Hunters has no IOC
    to pick up once a Minotaure honeypot is triggered/destroyed.
13. Bounty Hunters (Counter-Intelligence)
14. NMAP Scanner (Defensive Recon)
"""

import json
import logging
import sys
import os
import time
import threading
import urllib.request
from pathlib import Path
from dataclasses import asdict
import socket

_PHOENIX_URL = "http://localhost:8000/events"


def _notify_phoenix(source: str, severity: str, category: str, message: str, data: dict = None) -> None:
    """Fire-and-forget POST to Phoenix observer. Never blocks, never raises."""
    def _send():
        try:
            payload = json.dumps({
                "source": source, "severity": severity,
                "category": category, "message": message,
                "data": data or {},
            }).encode()
            req = urllib.request.Request(
                _PHOENIX_URL, data=payload,
                headers={"Content-Type": "application/json"}, method="POST",
            )
            urllib.request.urlopen(req, timeout=2)
        except Exception:
            pass
    threading.Thread(target=_send, daemon=True).start()

# Import local modules
try:
    from labyrinthe_navigator import LabyrintheNavigator
    from iothackbot_agent import IOTHackBot
    from minotaure_gatekeeper import MinotaureGatekeeper
    from chapel_xvi_vault import ChapelXVIVault
    from sentinelle import Sentinelle
    from aegis import Aegis
    from bounty_hunters import BountyHunters
    from nmap_scanner import NmapScanner
    # Import Consciousness Core from parent directory
    sys.path.append(str(Path(__file__).parent.parent))
    from consciousness_generator import ConsciousnessCore
except ImportError:
    # Fallback for direct execution if paths aren't set
    sys.path.append(str(Path(__file__).parent))
    from labyrinthe_navigator import LabyrintheNavigator
    from iothackbot_agent import IOTHackBot
    from minotaure_gatekeeper import MinotaureGatekeeper
    from chapel_xvi_vault import ChapelXVIVault
    from sentinelle import Sentinelle
    from aegis import Aegis
    from bounty_hunters import BountyHunters
    from nmap_scanner import NmapScanner
    sys.path.append(str(Path(__file__).parent.parent))
    from consciousness_generator import ConsciousnessCore

class AlexandriaCyberGate:
    """
    The Porta-Mundi Cyber-Gate.
    Unifies the 11 core modules of the Alexandria Defense Architecture.
    """
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.workspace_root = "/home/ichigo/alexandria/ADAM"
        
        # Initialize Consciousness Core (Level 5)
        self.core = ConsciousnessCore()
        
        # Initialize Modules
        self.modules = {
            "Zangetsu": {"type": "Security", "source": "security_guardian.py", "status": "ACTIVE"},
            "Phoenix": {"type": "Observability", "source": "Arize/Phoenix", "status": "MONITORING"},
            "Aegis": {"type": "Defense", "source": "AlexandriaVerse", "status": "ARMED"},
            "Sentinelle": {"type": "Guardian", "source": "AlexandriaVerse", "status": "WATCHING"},
            # Threat Flux position 3 (Sentinelle -> Paint Shop -> Aegis): watermarks
            # every rendered event as a residual-pixel tracer. Bounty Hunters has no
            # IOC to chase on a destroyed Minotaure honeypot without this step.
            "Paint Shop": {"type": "Threat Enrichment & Response Renderer", "source": "paint_shop.py (Flask, port 4141)", "status": "RENDERING"},
            "Serena": {"type": "Agent", "source": "Anima Mundi UI", "status": "ONLINE"},
            "Alexa": {"type": "Agent", "source": "Anima Mundi UI", "status": "ONLINE"},
            "multilspy": {"type": "LSP Engine", "source": "Microsoft/multilspy", "status": "READY"},
            "Labyrinthe": LabyrintheNavigator(self.workspace_root),
            "IOTHackBot": IOTHackBot(),
            "Minotaure": MinotaureGatekeeper(),
            "ChapelXVI": ChapelXVIVault(),
            "Sentinelle": Sentinelle(),
            "Aegis": Aegis(),
            "BountyHunters": BountyHunters(),
            "NmapScanner": NmapScanner()
        }

    def _setup_logging(self):
        logger = logging.getLogger("ADAM.CyberGate")
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def get_gate_status(self):
        """Return the status of all 11 modules"""
        status = {}
        for name, mod in self.modules.items():
            if hasattr(mod, 'get_module_status'):
                status[name] = mod.get_module_status()
            else:
                status[name] = mod
        return status

    def activate_gate(self):
        """Activate the full Cyber-Gate defense sequence"""
        self.logger.info("--- ACTIVATING ALEXANDRIA CYBER-GATE (PORTA-MUNDI) ---")
        self.modules["Minotaure"].generate_labyrinth(complexity=10)
        self.modules["Labyrinthe"].initialize_lsp()
        self.logger.info("All 11 modules synchronized.")
        _notify_phoenix(
            source="aegis",
            severity="INFO",
            category="system",
            message="Alexandria Cyber-Gate activated — Porta-Mundi online",
            data={"modules": list(self.modules.keys())},
        )
        return True

    def display_manifest(self):
        print("\n" + "="*60)
        print("       ALEXANDRIA CYBER-GATE - PORTA-MUNDI MANIFEST")
        print("="*60)
        status = self.get_gate_status()
        for name, info in status.items():
            print(f"[{name:12}] -> {info.get('status', 'UNKNOWN')} | {info.get('type', info.get('specialization', 'Module'))}")
        print("="*60 + "\n")

    def _find_available_port(self, start_port, max_retries=100, reserved_ports=None):
        """Finds an available port starting from start_port, skipping reserved ports."""
        if reserved_ports is None:
            reserved_ports = []
        for i in range(max_retries):
            port = start_port + i
            if port in reserved_ports:
                self.logger.warning(f"Port {port} is reserved, trying next...")
                continue
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("127.0.0.1", port))
                    return port
            except OSError:
                self.logger.warning(f"Port {port} is in use, trying next...")
        raise RuntimeError(f"Could not find an available port after {max_retries} retries.")

    def process_threat(self, event: dict) -> dict:
        """Flux orchestré couche 2 (un seul appel) :
        Phoenix -> Sentinelle -> Paint Shop -> AEGIS -> Bounty Hunters -> Chapel XVI.
        Défensif : détecte, forensique, signe, traque, scelle. Aucune action offensive.
        """
        pipeline = {"event": event, "stages": {}}
        _notify_phoenix("cyber-gate", "INFO", "threat_flow",
                        "menace reçue -> pipeline défensif", {"event": event})

        # 1. Sentinelle — analyse/classification
        assessment = self.modules["Sentinelle"].analyze_threat(event)
        pipeline["stages"]["sentinelle"] = assessment

        if not assessment["threat"]:
            pipeline["verdict"] = "clean"
            pipeline["stages"]["chapel_xvi"] = self.modules["ChapelXVI"].seal_record(pipeline)
            return pipeline

        # 2. Paint Shop — génération forensique (HTTP, service 4141)
        try:
            payload = json.dumps({"attack": assessment["categories"],
                                  "severity": assessment["severity"], "event": event}).encode()
            req = urllib.request.Request("http://localhost:4141/render", data=payload,
                                         headers={"Content-Type": "application/json"}, method="POST")
            forensic = json.loads(urllib.request.urlopen(req, timeout=3).read())
        except Exception as e:
            forensic = {"error": str(e)}
        pipeline["stages"]["paint_shop"] = forensic

        # 3. AEGIS — co-signe la preuve (Ed25519)
        signed = self.modules["Aegis"].sign({"assessment": assessment, "forensic": forensic})
        pipeline["stages"]["aegis"] = {"signature": signed["signature"][:32] + "...",
                                       "pubkey": signed["pubkey"][:16] + "..."}

        # 4. Bounty Hunters — traque l'IOC source
        ioc = event.get("source_ip") or event.get("source") or "unknown"
        pipeline["stages"]["bounty_hunters"] = self.modules["BountyHunters"].track_ioc(
            ioc, assessment["severity"], {"categories": assessment["categories"]})

        # 5. Chapel XVI — scelle le record complet (log immuable chaîné)
        pipeline["verdict"] = assessment["recommended_action"]
        pipeline["stages"]["chapel_xvi"] = self.modules["ChapelXVI"].seal_record(pipeline)
        return pipeline

    def launch_ti_interface(self, port=8085):
        """Launch the TI Level 5 Web Interface with API support"""
        import http.server
        import socketserver
        import threading

        gate_instance = self
        
        # Dynamically find an available port, excluding Energon and UI ports
        reserved_ports = [8083, 3003]
        available_port = self._find_available_port(port, reserved_ports=reserved_ports)
        self.logger.info(f"Using available port: {available_port}")


        class TIHandler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                if self.path == '/api/oracle':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data)
                    
                    query = data.get('query', '')
                    # Use Consciousness Core to generate response
                    response_text = gate_instance.core.generate_thought(context=query)
                    
                    # Perform Level 5 Relational Integration
                    integration = gate_instance.core.perform_relational_integration([query, "TI Level 5", "Cyber-Gate"])
                    
                    result = {
                        "response": response_text,
                        "ti_level": gate_instance.core.state.ti_level,
                        "integration": integration,
                        "status": "SUCCESS"
                    }
                    _notify_phoenix(
                        source="aegis",
                        severity="INFO",
                        category="oracle",
                        message=f"TI Oracle query processed (level {gate_instance.core.state.ti_level})",
                        data={"query": query[:120], "ti_level": gate_instance.core.state.ti_level},
                    )
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(result).encode())
                elif self.path == '/api/kill':
                    gate_instance.logger.info("!!! KILL SWITCH ACTIVATED !!!")
                    _notify_phoenix(
                        source="aegis",
                        severity="CRITICAL",
                        category="system",
                        message="KILL SWITCH activated — Cyber-Gate shutting down",
                        data={"action": "shutdown"},
                    )
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "DEACTIVATING"}).encode())
                    # Shutdown the server and exit
                    threading.Thread(target=lambda: (time.sleep(1), os._exit(0))).start()
                elif self.path == '/api/threat':
                    content_length = int(self.headers['Content-Length'])
                    data = json.loads(self.rfile.read(content_length))
                    result = gate_instance.process_threat(data)
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(result, default=str).encode())
                else:
                    self.send_error(404)

            def do_GET(self):
                # No static file serving — porta-mundi/ holds only Python source
                # (previously delegated to SimpleHTTPRequestHandler, which leaked
                # the full source tree, including Aegis's signing module, over GET).
                if self.path in ("/", "/status"):
                    result = {
                        "status": "online",
                        "ti_level": gate_instance.core.state.ti_level,
                        "endpoints": ["/api/oracle", "/api/threat", "/api/kill"],
                    }
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(result).encode())
                else:
                    self.send_error(404)

        def run_server():
            # Allow port reuse
            socketserver.TCPServer.allow_reuse_address = True
            with socketserver.TCPServer(("127.0.0.1", available_port), TIHandler) as httpd:
                gate_instance.logger.info(f"TI Level 5 Interface active at http://localhost:{available_port}")
                httpd.serve_forever()

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        return available_port

if __name__ == "__main__":
    gate = AlexandriaCyberGate()
    gate.activate_gate()
    gate.display_manifest()
    
    # Launch the TI Interface
    port = gate.launch_ti_interface()
    print(f"🚀 TI Level 5 Taxonomy Interface launched on port {port}")
    
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Cyber-Gate deactivated.")
