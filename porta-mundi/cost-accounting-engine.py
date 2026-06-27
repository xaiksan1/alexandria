#!/usr/bin/env python3
"""
ALEXANDRIA COST ACCOUNTING ENGINE
==================================
Real-time Energon tracking for every entity

Tracks:
- ADAM Agents (execution hours, decisions, memory)
- MCP Servers (startup, requests, storage)
- Tools (invocations, output tokens)
- Tasks (agent-hours, tool usage)
- Storage (per GB per day)

Every action has a cost. Every cost is visible.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import hashlib

class CostAccountingEngine:
    """Real-time Energon cost tracking system"""

    def __init__(self, base_path: str = "/home/ichigo/alexandria/ADAM/porta-mundi"):
        self.base_path = Path(base_path)
        self.cost_accounting_dir = self.base_path / "cost-accounting"
        self.entities_dir = self.cost_accounting_dir / "entities"
        self.transactions_dir = self.cost_accounting_dir / "transactions"

        # Load cost framework
        self.framework = self._load_framework()

        # Ensure directories exist
        self.entities_dir.mkdir(parents=True, exist_ok=True)
        self.transactions_dir.mkdir(parents=True, exist_ok=True)

        # Create today's transaction log
        today = datetime.utcnow().strftime("%Y-%m")
        today_dir = self.transactions_dir / today
        today_dir.mkdir(parents=True, exist_ok=True)

    def _load_framework(self) -> Dict:
        """Load cost framework from file"""
        framework_file = self.cost_accounting_dir / "cost-framework.json"
        if framework_file.exists():
            with open(framework_file, 'r') as f:
                return json.load(f)
        return {}

    def record_agent_execution(self, agent_id: str, execution_hours: float,
                              decisions: int, memory_gb: float) -> Dict:
        """Record ADAM agent execution costs"""

        cost_model = self.framework.get("cost_model", {}).get("agents", {})

        costs = {
            "execution": execution_hours * cost_model.get("execution_per_hour", 0.5),
            "decisions": decisions * cost_model.get("decision_per_action", 0.01),
            "memory": memory_gb * cost_model.get("memory_per_gb_per_day", 0.001)
        }

        total_cost = sum(costs.values())

        transaction = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "entity_type": "agent",
            "entity_id": agent_id,
            "event": "execution",
            "execution_hours": execution_hours,
            "decisions": decisions,
            "memory_gb": memory_gb,
            "costs": costs,
            "total_egn": total_cost,
            "hash": self._compute_hash({**costs, "total": total_cost})
        }

        # Save transaction
        self._save_transaction(transaction)

        # Update agent ledger
        self._update_agent_ledger(agent_id, transaction)

        return transaction

    def record_mcp_invocation(self, mcp_id: str, request_count: int,
                             memory_gb: float) -> Dict:
        """Record MCP server costs"""

        cost_model = self.framework.get("cost_model", {}).get("mcp_servers", {})

        costs = {
            "requests": request_count * cost_model.get("per_request", 0.1),
            "memory": memory_gb * cost_model.get("memory_per_gb_per_day", 0.001)
        }

        total_cost = sum(costs.values())

        transaction = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "entity_type": "mcp_server",
            "entity_id": mcp_id,
            "event": "invocation",
            "request_count": request_count,
            "memory_gb": memory_gb,
            "costs": costs,
            "total_egn": total_cost,
            "hash": self._compute_hash({**costs, "total": total_cost})
        }

        self._save_transaction(transaction)
        self._update_entity_ledger("mcp-servers", mcp_id, transaction)

        return transaction

    def record_tool_invocation(self, tool_id: str, invocations: int,
                              output_tokens: int) -> Dict:
        """Record tool usage costs"""

        cost_model = self.framework.get("cost_model", {}).get("tools", {})

        costs = {
            "invocations": invocations * cost_model.get("per_invocation", 0.05),
            "output_tokens": output_tokens * cost_model.get("per_output_token", 0.0001)
        }

        total_cost = sum(costs.values())

        transaction = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "entity_type": "tool",
            "entity_id": tool_id,
            "event": "invocation",
            "invocations": invocations,
            "output_tokens": output_tokens,
            "costs": costs,
            "total_egn": total_cost,
            "hash": self._compute_hash({**costs, "total": total_cost})
        }

        self._save_transaction(transaction)
        self._update_entity_ledger("tools", tool_id, transaction)

        return transaction

    def record_storage_usage(self, storage_id: str, size_gb: float,
                            days: float = 1.0) -> Dict:
        """Record storage costs"""

        cost_model = self.framework.get("cost_model", {}).get("storage", {})
        daily_cost = size_gb * cost_model.get("per_gb_per_day", 0.001)
        total_cost = daily_cost * days

        transaction = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "entity_type": "storage",
            "entity_id": storage_id,
            "event": "daily_charge",
            "size_gb": size_gb,
            "days": days,
            "cost_per_day": daily_cost,
            "total_egn": total_cost,
            "hash": self._compute_hash({"size": size_gb, "cost": total_cost})
        }

        self._save_transaction(transaction)
        self._update_entity_ledger("storage", storage_id, transaction)

        return transaction

    def record_energon_mining(self, kwh: float, efficiency: float = 0.95) -> Dict:
        """Record Energon mining revenue and update sharded master-ledger"""

        revenue_model = self.framework.get("revenue_model", {}).get("mining", {})
        kwh_to_egn = revenue_model.get("kwh_to_egn", 1.0)

        # Account for efficiency loss
        net_egn = kwh * kwh_to_egn * efficiency
        
        transaction = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "entity_type": "mining",
            "entity_id": "mining-revenue",
            "event": "energy_capture",
            "kwh": kwh,
            "efficiency": efficiency,
            "gross_egn": kwh * kwh_to_egn,
            "net_egn": net_egn,
            "hash": self._compute_hash({"kwh": kwh, "egn": net_egn})
        }

        self._save_transaction(transaction)
        
        # --- SHARDED LEDGER INTEGRATION ---
        master_ledger_path = Path("/home/ichigo/alexandria/ADAM/energon-ledger/master-ledger.json")
        if master_ledger_path.exists():
            try:
                with open(master_ledger_path, 'r') as f:
                    master = json.load(f)
                
                # Update master stats
                master["balance_egn"] += net_egn
                master["total_captured_egn"] += net_egn
                master["pending_seal_egn"] += net_egn
                master["last_update"] = datetime.utcnow().isoformat() + "Z"
                
                with open(master_ledger_path, 'w') as f:
                    json.dump(master, f, indent=2)
                
                # Record in current shard
                shards_dir = master_ledger_path.parent / "shards"
                active_shard_path = shards_dir / master["active_shard"]
                if active_shard_path.exists():
                    with open(active_shard_path, 'r') as f:
                        shard = json.load(f)
                    
                    shard["entries"].append(transaction)
                    
                    with open(active_shard_path, 'w') as f:
                        json.dump(shard, f, indent=2)
            except Exception as e:
                print(f"⚠️ Failed to update sharded master: {e}")

        return transaction

    def record_arbitrage_profit(self, arbitrage_spread: float, amount: float) -> Dict:
        """Record financial arbitrage profit"""

        revenue_model = self.framework.get("revenue_model", {}).get("arbitrage", {})
        percentage = revenue_model.get("percentage", 0.002)

        profit = amount * percentage

        transaction = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "entity_type": "arbitrage",
            "entity_id": "financial-arbitrage",
            "event": "spread_capture",
            "amount": amount,
            "spread_percentage": percentage,
            "profit_egn": profit,
            "hash": self._compute_hash({"amount": amount, "profit": profit})
        }

        self._save_transaction(transaction)

        return transaction

    def get_entity_balance(self, entity_type: str, entity_id: str) -> Dict:
        """Get current balance for an entity"""

        ledger_path = self.entities_dir / entity_type / f"{entity_id}.ledger"

        if not ledger_path.exists():
            return {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "total_spent": 0.0,
                "total_earned": 0.0,
                "net_balance": 0.0,
                "transaction_count": 0
            }

        with open(ledger_path, 'r') as f:
            ledger = json.load(f)

        return ledger

    def get_daily_summary(self, date: Optional[str] = None) -> Dict:
        """Get summary of costs/earnings for a day"""

        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")

        year_month = date[:7]
        transactions_file = self.transactions_dir / year_month / f"{date}.transactions"

        if not transactions_file.exists():
            return {
                "date": date,
                "total_costs": 0.0,
                "total_revenue": 0.0,
                "net": 0.0,
                "transactions": []
            }

        with open(transactions_file, 'r') as f:
            transactions = [json.loads(line) for line in f if line.strip()]

        total_costs = sum(t.get("total_egn", 0) for t in transactions
                         if t.get("entity_type") in ["agent", "mcp_server", "tool", "storage"])
        total_revenue = sum(t.get("net_egn", 0) + t.get("profit_egn", 0)
                           for t in transactions
                           if t.get("entity_type") in ["mining", "arbitrage"])

        return {
            "date": date,
            "total_costs": round(total_costs, 4),
            "total_revenue": round(total_revenue, 4),
            "net": round(total_revenue - total_costs, 4),
            "perpetuity_allocation": round((total_revenue - total_costs) * 0.25, 4),
            "transaction_count": len(transactions)
        }

    def get_perpetuity_allocation(self, total_revenue: float) -> Dict:
        """Calculate perpetuity fund allocation"""

        allocation_total = total_revenue * 0.25

        allocation = self.framework.get("perpetuity_allocation", {})

        return {
            "total_allocated": round(allocation_total, 4),
            "education": round(allocation_total * 0.2, 4),  # 5% of 25%
            "fauna": round(allocation_total * 0.2, 4),
            "flora": round(allocation_total * 0.2, 4),
            "environment": round(allocation_total * 0.2, 4),
            "committee": round(allocation_total * 0.2, 4)
        }

    def _save_transaction(self, transaction: Dict) -> None:
        """Save transaction to daily log"""

        today = datetime.utcnow()
        date_str = today.strftime("%Y-%m-%d")
        year_month = today.strftime("%Y-%m")

        transactions_file = self.transactions_dir / year_month / f"{date_str}.transactions"
        transactions_file.parent.mkdir(parents=True, exist_ok=True)

        with open(transactions_file, 'a') as f:
            f.write(json.dumps(transaction) + "\n")

    def _update_agent_ledger(self, agent_id: str, transaction: Dict) -> None:
        """Update agent cost ledger"""

        self._update_entity_ledger("agents", agent_id, transaction)

    def _update_entity_ledger(self, entity_type: str, entity_id: str,
                             transaction: Dict) -> None:
        """Update entity ledger with new transaction"""

        ledger_dir = self.entities_dir / entity_type
        ledger_dir.mkdir(parents=True, exist_ok=True)

        ledger_path = ledger_dir / f"{entity_id}.ledger"

        if ledger_path.exists():
            with open(ledger_path, 'r') as f:
                ledger = json.load(f)
        else:
            ledger = {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "total_spent": 0.0,
                "total_earned": 0.0,
                "transactions": []
            }

        # Update totals based on transaction type
        if transaction["event"] in ["execution", "invocation", "daily_charge"]:
            ledger["total_spent"] += transaction.get("total_egn", 0)
        elif transaction["event"] in ["energy_capture", "spread_capture"]:
            ledger["total_earned"] += transaction.get("net_egn", 0) + transaction.get("profit_egn", 0)

        ledger["net_balance"] = ledger["total_earned"] - ledger["total_spent"]
        ledger["transactions"].append(transaction)
        ledger["last_updated"] = datetime.utcnow().isoformat() + "Z"

        with open(ledger_path, 'w') as f:
            json.dump(ledger, f, indent=2)

    def _compute_hash(self, data: Dict) -> str:
        """Compute SHA256 hash of transaction data"""

        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]


def main():
    """Test the cost accounting engine"""

    engine = CostAccountingEngine()

    print("🔧 ALEXANDRIA COST ACCOUNTING ENGINE")
    print("=" * 50)
    print()

    # Example 1: Agent execution
    print("📊 Recording ADAM-0001 execution...")
    result = engine.record_agent_execution("ADAM-0001",
                                          execution_hours=1.5,
                                          decisions=100,
                                          memory_gb=2.5)
    print(f"   Cost: {result['total_egn']} EGN")
    print()

    # Example 2: Tool invocation
    print("🔨 Recording tool invocation...")
    result = engine.record_tool_invocation("tool-fetch-data",
                                          invocations=50,
                                          output_tokens=5000)
    print(f"   Cost: {result['total_egn']} EGN")
    print()

    # Example 3: Mining revenue
    print("⚡ Recording mining revenue...")
    result = engine.record_energon_mining(kwh=2.5, efficiency=0.95)
    print(f"   Revenue: {result['net_egn']} EGN")
    print()

    # Example 4: Arbitrage profit
    print("💰 Recording arbitrage profit...")
    result = engine.record_arbitrage_profit(arbitrage_spread=0.002,
                                           amount=1000)
    print(f"   Profit: {result['profit_egn']} EGN")
    print()

    # Get agent balance
    print("📈 Agent balance:")
    balance = engine.get_entity_balance("agents", "ADAM-0001")
    print(f"   Spent: {balance.get('total_spent', 0)} EGN")
    print(f"   Balance: {balance.get('net_balance', 0)} EGN")
    print()

    # Get daily summary
    print("📊 Daily summary:")
    summary = engine.get_daily_summary()
    print(f"   Costs: {summary['total_costs']} EGN")
    print(f"   Revenue: {summary['total_revenue']} EGN")
    print(f"   Net: {summary['net']} EGN")
    print(f"   Perpetuity allocation: {summary['perpetuity_allocation']} EGN")
    print()

    print("✅ Cost accounting engine operational")
    print()


if __name__ == "__main__":
    main()
