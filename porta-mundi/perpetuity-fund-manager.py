#!/usr/bin/env python3
"""
ALEXANDRIA PERPETUITY FUND MANAGER
===================================
Automatic distribution of 25% profits to 5 sectors

Every day:
- 5% → Education (AI ethics, energy-tech training)
- 5% → Fauna (endangered species protection)
- 5% → Flora (reforestation, carbon sequestration)
- 5% → Environment (ozone repair, CO2 capture)
- 5% → Committee (governance & perpetuity)

This ensures Alexandria thrives for 100+ years
regardless of who controls it.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class PerpetuitFundManager:
    """Automated perpetuity fund distribution"""

    def __init__(self, base_path: str = "/home/ichigo/alexandria/ADAM/porta-mundi"):
        self.base_path = Path(base_path)
        self.governance_dir = self.base_path / "governance" / "perpetuity-fund"
        self.financials_dir = self.governance_dir / "financials"

        self.financials_dir.mkdir(parents=True, exist_ok=True)

        # Load fund allocation rules
        self.fund_allocation = self._load_fund_allocation()

    def _load_fund_allocation(self) -> Dict:
        """Load perpetuity fund allocation rules"""

        allocation_file = self.governance_dir / "fund-allocation.json"

        if allocation_file.exists():
            with open(allocation_file, 'r') as f:
                return json.load(f)

        # Default allocation
        return {
            "perpetuity_fund": {
                "total_allocation": "25% of all profits",
                "allocation_by_sector": {
                    "education": {
                        "percentage": 5,
                        "name": "Education & AI Ethics"
                    },
                    "fauna": {
                        "percentage": 5,
                        "name": "Wildlife & Biodiversity"
                    },
                    "flora": {
                        "percentage": 5,
                        "name": "Reforestation & Carbon"
                    },
                    "environment": {
                        "percentage": 5,
                        "name": "Environmental Restoration"
                    },
                    "perpetuity_committee": {
                        "percentage": 5,
                        "name": "Governance & Continuity"
                    }
                }
            }
        }

    def allocate_daily_profits(self, total_revenue: float, total_costs: float) -> Dict:
        """
        Calculate and allocate daily perpetuity funds

        25% of net profit goes to:
        - 5% Education
        - 5% Fauna
        - 5% Flora
        - 5% Environment
        - 5% Committee
        """

        net_profit = total_revenue - total_costs

        if net_profit <= 0:
            return {
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "status": "no_profit",
                "net_profit": net_profit,
                "allocation": None
            }

        perpetuity_total = net_profit * 0.25

        sectors = self.fund_allocation["perpetuity_fund"]["allocation_by_sector"]

        allocation = {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "total_revenue": round(total_revenue, 4),
            "total_costs": round(total_costs, 4),
            "net_profit": round(net_profit, 4),
            "perpetuity_allocation": round(perpetuity_total, 4),
            "sectors": {}
        }

        for sector, details in sectors.items():
            sector_allocation = perpetuity_total * (details["percentage"] / 25)

            allocation["sectors"][sector] = {
                "name": details["name"],
                "percentage_of_perpetuity": details["percentage"],
                "allocated_egn": round(sector_allocation, 4),
                "status": "pending_distribution"
            }

        return allocation

    def distribute_funds(self, allocation: Dict) -> Dict:
        """Distribute funds to each sector"""

        if allocation.get("status") == "no_profit":
            return allocation

        date_str = allocation["date"]
        year_month = date_str[:7]

        # Update each sector's ledger
        for sector, details in allocation["sectors"].items():
            self._record_sector_distribution(sector, details, date_str)

        # Save allocation record
        financials_file = self.financials_dir / f"{date_str}-allocation.json"
        with open(financials_file, 'w') as f:
            json.dump(allocation, f, indent=2)

        allocation["status"] = "distributed"
        return allocation

    def _record_sector_distribution(self, sector: str, details: Dict,
                                   date_str: str) -> None:
        """Record fund distribution to sector"""

        sector_dir = self.governance_dir / "projects" / sector
        sector_dir.mkdir(parents=True, exist_ok=True)

        ledger_file = sector_dir / "ledger.json"

        if ledger_file.exists():
            with open(ledger_file, 'r') as f:
                ledger = json.load(f)
        else:
            ledger = {
                "sector": sector,
                "name": details["name"],
                "total_allocated": 0.0,
                "distributions": [],
                "initiatives": [],
                "impact": {}
            }

        distribution_record = {
            "date": date_str,
            "amount_egn": details["allocated_egn"],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        ledger["total_allocated"] += details["allocated_egn"]
        ledger["distributions"].append(distribution_record)

        with open(ledger_file, 'w') as f:
            json.dump(ledger, f, indent=2)

    def get_sector_balance(self, sector: str) -> Dict:
        """Get current balance for a sector"""

        sector_dir = self.governance_dir / "projects" / sector
        ledger_file = sector_dir / "ledger.json"

        if not ledger_file.exists():
            return {
                "sector": sector,
                "total_allocated": 0.0,
                "distributions": []
            }

        with open(ledger_file, 'r') as f:
            return json.load(f)

    def get_annual_report(self, year: str) -> Dict:
        """Generate annual perpetuity fund report"""

        year_month_pattern = f"{year}-"

        total_by_sector = {}
        all_allocations = []

        for allocation_file in self.financials_dir.glob("*.json"):
            with open(allocation_file, 'r') as f:
                allocation = json.load(f)

            if allocation["date"].startswith(year_month_pattern):
                all_allocations.append(allocation)

                for sector, details in allocation.get("sectors", {}).items():
                    if sector not in total_by_sector:
                        total_by_sector[sector] = 0.0
                    total_by_sector[sector] += details["allocated_egn"]

        grand_total = sum(total_by_sector.values())

        report = {
            "year": year,
            "report_date": datetime.utcnow().isoformat() + "Z",
            "total_allocated": round(grand_total, 4),
            "by_sector": {sector: round(amount, 4)
                         for sector, amount in total_by_sector.items()},
            "allocation_count": len(all_allocations),
            "status": "complete"
        }

        # Save annual report
        report_file = self.governance_dir / "reports" / f"{year}-annual-report.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        return report

    def get_perpetuity_status(self) -> Dict:
        """Get overall perpetuity fund status"""

        status = {
            "status": "active",
            "report_date": datetime.utcnow().isoformat() + "Z",
            "sectors": {}
        }

        sectors = self.fund_allocation["perpetuity_fund"]["allocation_by_sector"]

        for sector in sectors.keys():
            balance = self.get_sector_balance(sector)
            status["sectors"][sector] = {
                "name": balance.get("name"),
                "total_allocated": balance.get("total_allocated", 0.0),
                "distribution_count": len(balance.get("distributions", [])),
                "initiatives": len(balance.get("initiatives", []))
            }

        return status


def main():
    """Test perpetuity fund manager"""

    manager = PerpetuitFundManager()

    print("🏛️  ALEXANDRIA PERPETUITY FUND MANAGER")
    print("=" * 50)
    print()

    # Example daily allocation
    print("💰 Daily allocation (revenue: 100 EGN, costs: 50 EGN)...")
    allocation = manager.allocate_daily_profits(total_revenue=100, total_costs=50)
    print(f"   Net profit: {allocation['net_profit']} EGN")
    print(f"   Perpetuity allocation: {allocation['perpetuity_allocation']} EGN")
    print()

    print("   Sector allocation:")
    for sector, details in allocation["sectors"].items():
        print(f"     • {details['name']}: {details['allocated_egn']} EGN")
    print()

    # Distribute funds
    print("🚀 Distributing funds...")
    result = manager.distribute_funds(allocation)
    print(f"   Status: {result['status']}")
    print()

    # Check sector balances
    print("📊 Sector balances:")
    for sector in ["education", "fauna", "flora", "environment", "perpetuity_committee"]:
        balance = manager.get_sector_balance(sector)
        print(f"   • {sector}: {balance.get('total_allocated', 0)} EGN")
    print()

    # Overall status
    print("📈 Perpetuity fund status:")
    status = manager.get_perpetuity_status()
    for sector, info in status["sectors"].items():
        print(f"   • {info['name']}: {info['total_allocated']} EGN allocated")
    print()

    print("✅ Perpetuity fund manager operational")
    print()


if __name__ == "__main__":
    main()
