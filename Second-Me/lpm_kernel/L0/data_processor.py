#!/usr/bin/env python3
"""
L0: Raw Data Processing
Collects and organizes unstructured source data for training.
"""

import json
from pathlib import Path
from datetime import datetime


class L0DataProcessor:
    """Process raw data for L0 layer."""

    def __init__(self, data_dir: str = "L0-raw-data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.processed_data = {
            "identity": [],
            "code": [],
            "projects": [],
            "patterns": [],
            "communication": []
        }

    def scan_data_directory(self) -> dict:
        """Scan and inventory raw data."""
        inventory = {
            "total_files": 0,
            "total_size_mb": 0,
            "categories": {},
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }

        for category in self.processed_data.keys():
            cat_dir = self.data_dir / category
            cat_dir.mkdir(exist_ok=True)

            files = list(cat_dir.glob("**/*"))
            file_count = len([f for f in files if f.is_file()])
            total_size = sum(f.stat().st_size for f in files if f.is_file()) / (1024 * 1024)

            inventory["categories"][category] = {
                "file_count": file_count,
                "size_mb": round(total_size, 2)
            }

            inventory["total_files"] += file_count
            inventory["total_size_mb"] += total_size

        inventory["total_size_mb"] = round(inventory["total_size_mb"], 2)
        return inventory

    def process_raw_data(self) -> None:
        """Process all raw data."""
        print("📊 L0: Processing Raw Data")
        print("════════════════════════════════════════")
        print("")

        inventory = self.scan_data_directory()

        print("📁 Data Inventory:")
        for category, stats in inventory["categories"].items():
            print(f"   {category:20s}: {stats['file_count']:3d} files ({stats['size_mb']:8.2f} MB)")

        print(f"\n📈 Summary:")
        print(f"   Total Files: {inventory['total_files']}")
        print(f"   Total Size: {inventory['total_size_mb']:.2f} MB")

        # Save inventory
        self._save_inventory(inventory)

    def _save_inventory(self, inventory: dict) -> None:
        """Save data inventory."""
        inventory_file = self.data_dir / "inventory.json"
        with open(inventory_file, 'w') as f:
            json.dump(inventory, f, indent=2)

        print(f"\n✅ Inventory saved to {inventory_file}")


def main():
    """Run L0 data processing."""
    processor = L0DataProcessor()
    processor.process_raw_data()


if __name__ == "__main__":
    main()
