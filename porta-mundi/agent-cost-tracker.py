#!/usr/bin/env python3
"""
AGENT COST TRACKER - Real-time ADAM agent monitoring
Connect Alexandria's cost accounting to live ADAM agents
"""

import json
import os
from datetime import datetime
from pathlib import Path
from cost_accounting_engine import CostAccountingEngine

class AgentCostTracker:
    """Track real ADAM agent execution costs"""

    def __init__(self):
        self.engine = CostAccountingEngine()
        self.agents_dir = Path("/home/ichigo/alexandria/ADAM/agents/active")

    def scan_active_agents(self):
        """Get list of active agents"""
        if not self.agents_dir.exists():
            return []
        return [d.name for d in self.agents_dir.iterdir() if d.is_dir()]

    def track_agent_cost(self, agent_id: str):
        """Track cost for single agent"""
        agent_dir = self.agents_dir / agent_id
        state_file = agent_dir / "state.json"

        if not state_file.exists():
            return None

        with open(state_file, 'r') as f:
            state = json.load(f)

        # Extract metrics
        execution_time = state.get("execution_seconds", 0) / 3600  # Convert to hours
        decisions = state.get("decisions_count", 0)
        memory_usage = state.get("memory_mb", 0) / 1024  # Convert to GB

        # Record cost
        result = self.engine.record_agent_execution(
            agent_id=agent_id,
            execution_hours=execution_time,
            decisions=decisions,
            memory_gb=memory_usage
        )

        return result

    def track_all_agents(self):
        """Track costs for all active agents"""
        agents = self.scan_active_agents()
        results = {}

        for agent_id in agents:
            result = self.track_agent_cost(agent_id)
            if result:
                results[agent_id] = result

        return results

    def get_agent_ranking(self):
        """Get agents ranked by cost"""
        agents = self.scan_active_agents()
        costs = []

        for agent_id in agents:
            balance = self.engine.get_entity_balance("agents", agent_id)
            costs.append({
                "agent_id": agent_id,
                "total_spent": balance.get("total_spent", 0),
                "net_balance": balance.get("net_balance", 0)
            })

        return sorted(costs, key=lambda x: x["total_spent"], reverse=True)


def main():
    tracker = AgentCostTracker()

    print("🤖 AGENT COST TRACKER")
    print("=" * 40)

    # Scan agents
    agents = tracker.scan_active_agents()
    print(f"\n📊 Found {len(agents)} active agents")

    if agents:
        print("\n💰 Tracking costs...")
        results = tracker.track_all_agents()

        print("\n📈 Agent ranking by cost:")
        ranking = tracker.get_agent_ranking()
        for i, agent in enumerate(ranking[:5], 1):
            print(f"  {i}. {agent['agent_id']}: {agent['total_spent']} EGN")
    else:
        print("\n⚠️  No active agents found yet")

if __name__ == "__main__":
    main()
