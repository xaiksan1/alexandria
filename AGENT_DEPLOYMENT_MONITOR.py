#!/usr/bin/env python3
"""
ALEXANDRIA AGENT DEPLOYMENT MONITOR
Real-time tracking of 3,069 deployed agents across 10 generations
"""

import json
import subprocess
import time
from pathlib import Path
from datetime import datetime

class AgentDeploymentMonitor:
    def __init__(self):
        self.agents_dir = Path("/home/ichigo/alexandria/json-mcp-blower/agents_exponential")
        self.start_time = datetime.now()

    def get_agent_count(self):
        """Count generated agent configs"""
        try:
            agents = list(self.agents_dir.glob("agent_*.json"))
            return len(agents)
        except:
            return 0

    def get_registry(self):
        """Load agent registry"""
        try:
            registry_path = self.agents_dir / "registry.json"
            if registry_path.exists():
                return json.loads(registry_path.read_text())
        except:
            pass
        return {}

    def get_generation_status(self):
        """Analyze agents by generation"""
        registry = self.get_registry()
        status = {}

        if 'agents' in registry:
            for agent in registry['agents']:
                gen = agent.get('generation', -1)
                if gen not in status:
                    status[gen] = {'total': 0, 'active': 0, 'ports': []}
                status[gen]['total'] += 1
                status[gen]['ports'].append(agent.get('port', 0))

        return status

    def check_process(self, pattern):
        """Check if process is running"""
        try:
            result = subprocess.run(['pgrep', '-f', pattern], capture_output=True)
            return result.returncode == 0
        except:
            return False

    def get_port_status(self):
        """Check listening ports"""
        try:
            result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True)
            ports = []

            for line in result.stdout.split('\n'):
                if 'LISTEN' in line and any(x in line for x in ['50', '51', '52', '53', '54', '55']):
                    parts = line.split()
                    if len(parts) > 3:
                        addr = parts[3]
                        if ':' in addr:
                            port = addr.split(':')[-1]
                            try:
                                ports.append(int(port))
                            except:
                                pass

            return {'total_ports': len(ports), 'port_range': (min(ports) if ports else 0, max(ports) if ports else 0)}
        except:
            return {'total_ports': 0, 'port_range': (0, 0)}

    def get_energy_status(self):
        """Get current energy status"""
        try:
            ledger_path = Path("/home/ichigo/alexandria/ADAM/digital-twin-data/energon_ledger.json")
            if ledger_path.exists():
                data = json.loads(ledger_path.read_text())
                return {
                    'sealed_kwh': data.get('sealed_kwh', 0),
                    'batches': len(data.get('batches', []))
                }
        except:
            pass
        return {'sealed_kwh': 0, 'batches': 0}

    def display_status(self):
        """Display real-time status"""
        subprocess.run(['clear'])

        print("=" * 90)
        print("🚀 ALEXANDRIA AGENT DEPLOYMENT MONITOR - LIVE STATUS")
        print("=" * 90)
        print("Timestamp: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        elapsed = (datetime.now() - self.start_time).total_seconds()
        print("Uptime: " + str(int(elapsed)) + "s")
        print()

        # Agent count
        agent_count = self.get_agent_count()
        print("📊 AGENTS GENERATED: " + str(agent_count) + " / 3,069")
        if agent_count == 3069:
            print("   ✅ FULL DEPLOYMENT COMPLETE")
        else:
            pct = (agent_count / 3069) * 100
            print("   " + str(round(pct, 1)) + "% deployed")
        print()

        # Generation status
        gen_status = self.get_generation_status()
        print("👥 GENERATION STATUS:")
        for gen in sorted(gen_status.keys()):
            info = gen_status[gen]
            status_char = "✅" if info['total'] > 0 else "⏳"
            print("   Gen " + str(gen) + ": " + str(info['total']).rjust(4) + " agents " + status_char)
        print()

        # Port status
        ports = self.get_port_status()
        print("🔌 NETWORK STATUS:")
        print("   Listening Ports: " + str(ports['total_ports']))
        if ports['total_ports'] > 0:
            print("   Port Range: " + str(ports['port_range'][0]) + " - " + str(ports['port_range'][1]))
        print()

        # Energy status
        energy = self.get_energy_status()
        print("⚡ ENERGY STATUS:")
        print("   Sealed: " + "{:,}".format(energy['sealed_kwh']) + " kWh")
        print("   Batches: " + "{:,}".format(energy['batches']))
        print()

        # System status
        print("🎯 SYSTEM COMPONENTS:")
        mining = self.check_process('mining_stats_collector')
        cybergate = self.check_process('alexandria_cyber_gate')
        filmmaker = self.check_process('filmmaker')

        print("   Mining:    " + ("✅ ACTIVE" if mining else "❌ INACTIVE"))
        print("   CyberGate: " + ("✅ ACTIVE" if cybergate else "❌ INACTIVE"))
        print("   Filmmaker: " + ("✅ ACTIVE" if filmmaker else "❌ INACTIVE"))
        print()

        print("=" * 90)
        print("Press Ctrl+C to stop monitoring. Refreshing every 10 seconds...")
        print()

    def run_continuous(self):
        """Run monitoring loop"""
        try:
            while True:
                self.display_status()
                time.sleep(10)
        except KeyboardInterrupt:
            print("\n✅ Monitoring stopped.")
            return

if __name__ == "__main__":
    monitor = AgentDeploymentMonitor()
    monitor.run_continuous()
