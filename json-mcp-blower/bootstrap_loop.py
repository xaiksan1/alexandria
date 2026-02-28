#!/usr/bin/env python3
"""
Bootstrap Loop: Exponential MCP generation engine.
Implements fractal growth: Gen N = initial × (growth_rate ^ N)
"""

import json
from pathlib import Path
from mcp_factory import MCPFactory


class BootstrapLoop:
    """Exponential agent generation loop."""

    def __init__(self, schema_path: str = "mcp-schema.json"):
        self.schema_path = Path(schema_path)
        self.factory = MCPFactory(schema_path)
        self.config = self.factory.schema.get("fractal_config", {})

    def calculate_generation_size(self, gen_num: int) -> int:
        """Calculate number of agents for a given generation."""
        initial = self.config.get("initial_generation", 3)
        growth_rate = self.config.get("growth_rate", 2.0)
        return int(initial * (growth_rate ** gen_num))

    def run_bootstrap(self, max_gens: int = None) -> None:
        """Run exponential generation loop."""
        max_gens = max_gens or self.config.get("max_iterations", 10)
        growth_rate = self.config.get("growth_rate", 2.0)

        print(f"🚀 Bootstrap Loop: Exponential Generation")
        print(f"════════════════════════════════════════")
        print(f"Initial: {self.config.get('initial_generation')} agents")
        print(f"Growth Rate: {growth_rate}x per generation")
        print(f"Max Generations: {max_gens}")
        print("")

        total_agents = 0
        total_energy = 0.0

        for gen_num in range(max_gens):
            gen_size = self.calculate_generation_size(gen_num)
            gen_agents = self.factory.create_generation(gen_num, gen_size)

            gen_energy = sum(a.get("energy_cost_kwh", 0) for a in gen_agents)
            total_energy += gen_energy
            total_agents += len(gen_agents)

            print(f"✅ Gen {gen_num}: {len(gen_agents):4d} agents | "
                  f"Energy: {gen_energy:7.1f} kWh | "
                  f"Total: {total_agents:6d} agents")

        print("")
        print(f"🎉 Bootstrap Complete!")
        print(f"   Total Agents: {total_agents:,}")
        print(f"   Total Energy: {total_energy:,.1f} kWh")
        print(f"   Exponential Multiplier: {total_agents / self.config.get('initial_generation'):.0f}x")

        # Save all agents
        self.factory.save_agents()

        # Update schema with status
        self.update_schema(total_agents, total_energy, max_gens)

    def update_schema(self, agent_count: int, energy_cost: float, generations: int) -> None:
        """Update schema with generation status."""
        self.factory.schema["mcp_registry"]["total_agents"] = agent_count
        self.factory.schema["generation_status"]["agents_generated"] = agent_count
        self.factory.schema["generation_status"]["total_energy_cost_kwh"] = energy_cost
        self.factory.schema["generation_status"]["current_generation"] = generations - 1

        with open(self.schema_path, 'w') as f:
            json.dump(self.factory.schema, f, indent=2)


def main():
    """Run bootstrap loop."""
    loop = BootstrapLoop()
    loop.run_bootstrap()


if __name__ == "__main__":
    main()
