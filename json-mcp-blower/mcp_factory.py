#!/usr/bin/env python3
"""
MCP Factory: Creates Claude agent instances from schema templates.
Part of JSON-MCP-Blower exponential agent generation system.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class MCPFactory:
    """Factory for creating MCP instances."""

    def __init__(self, schema_path: str = "mcp-schema.json"):
        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()
        self.agents = []

    def _load_schema(self) -> Dict:
        """Load MCP schema."""
        if self.schema_path.exists():
            with open(self.schema_path) as f:
                return json.load(f)
        return {"mcp_registry": {}, "agent_specializations": []}

    def create_agent(self, specialization: Dict, generation: int = 0) -> Dict:
        """Create a single MCP agent instance."""
        agent_id = str(uuid.uuid4())[:8]

        return {
            "id": f"agent_{agent_id}",
            "specialization_id": specialization.get("id"),
            "name": specialization.get("name"),
            "role": specialization.get("role"),
            "purpose": specialization.get("purpose"),
            "generation": generation,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "status": "initialized",
            "tools": specialization.get("tools", []),
            "energy_cost_kwh": specialization.get("energy_cost_kwh", 0.5),
            "metrics": {
                "tasks_completed": 0,
                "success_rate": 0.0,
                "average_response_time_ms": 0
            }
        }

    def create_generation(self, generation_num: int, count: int) -> List[Dict]:
        """Create a generation of agents."""
        specializations = self.schema.get("agent_specializations", [])
        if not specializations:
            print("⚠️  No specializations defined in schema")
            return []

        agents = []
        for i in range(count):
            # Distribute agents across specializations
            spec_idx = i % len(specializations)
            spec = specializations[spec_idx]
            agent = self.create_agent(spec, generation=generation_num)
            agents.append(agent)

        self.agents.extend(agents)
        return agents

    def save_agents(self, output_dir: str = "agents"):
        """Save agents to JSON files."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Save individual agent files
        for agent in self.agents:
            agent_file = output_path / f"{agent['id']}.json"
            with open(agent_file, 'w') as f:
                json.dump(agent, f, indent=2)

        # Save registry
        registry_file = output_path / "registry.json"
        with open(registry_file, 'w') as f:
            json.dump({
                "total_agents": len(self.agents),
                "agents": [a["id"] for a in self.agents],
                "created_at": datetime.utcnow().isoformat() + "Z"
            }, f, indent=2)

        print(f"✅ Saved {len(self.agents)} agents to {output_dir}/")

    def display_summary(self):
        """Display generation summary."""
        if not self.agents:
            print("❌ No agents generated")
            return

        print(f"\n📊 Agent Generation Summary")
        print("════════════════════════════════════════")
        print(f"Total Agents: {len(self.agents)}")

        # Count by role
        roles = {}
        for agent in self.agents:
            role = agent.get("role", "unknown")
            roles[role] = roles.get(role, 0) + 1

        print("\nBy Role:")
        for role, count in sorted(roles.items()):
            print(f"  {role.capitalize()}: {count}")

        # Energy summary
        total_energy = sum(a.get("energy_cost_kwh", 0) for a in self.agents)
        print(f"\nTotal Energy Cost: {total_energy:.2f} kWh")


def main():
    """Main entry point."""
    factory = MCPFactory()

    # Create first generation
    print("🏭 MCP Factory: Creating Agent Swarm")
    print("════════════════════════════════════════")

    gen0_count = 3
    gen0 = factory.create_generation(0, gen0_count)
    print(f"✅ Generation 0: {len(gen0)} agents created")

    # Display and save
    factory.display_summary()
    factory.save_agents()


if __name__ == "__main__":
    main()
