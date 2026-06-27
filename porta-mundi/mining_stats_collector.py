#!/usr/bin/env python3
"""
Mining Statistics Collector
Monitors mining performance and updates statistics
"""
import json
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path

class MiningStatsCollector:
    def __init__(self, interval=30):
        self.interval = interval
        self.ledger_path = Path("/home/ichigo/alexandria/ADAM/digital-twin-data/adam_task_ledger.json")
        self.energon_path = Path("/home/ichigo/alexandria/ADAM/digital-twin-data/energon_ledger.json")
        
    def collect_stats(self):
        """Collect mining and system statistics"""
        try:
            stats = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "mining_active": True,
                "interval": self.interval
            }
            
            # Try to read existing ledgers
            if self.ledger_path.exists():
                with open(self.ledger_path, 'r') as f:
                    task_data = json.load(f)
                    stats["tasks"] = len(task_data.get("batches", []))
            
            if self.energon_path.exists():
                with open(self.energon_path, 'r') as f:
                    energon_data = json.load(f)
                    stats["sealed_kwh"] = energon_data.get("sealed_kwh", 0)
            
            print(f"[{stats['timestamp']}] Mining stats collected: {stats}")
            return stats
            
        except Exception as e:
            print(f"Error collecting stats: {e}")
            return None
    
    def run(self):
        """Run the collector loop"""
        print(f"Mining Statistics Collector started (interval={self.interval}s)")
        try:
            while True:
                self.collect_stats()
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print("\nMining Statistics Collector stopped")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=30, help="Collection interval in seconds")
    args = parser.parse_args()
    
    collector = MiningStatsCollector(interval=args.interval)
    collector.run()
