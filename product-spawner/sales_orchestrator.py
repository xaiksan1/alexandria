#!/usr/bin/env python3
"""
Product-Spawner: Sales Orchestrator
Generates 100+ market-targeted product variants using Claude API.
Integrated with Alexandria energy-tech ecosystem.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

try:
    from anthropic import Anthropic
except ImportError:
    print("❌ Missing: pip install anthropic")
    sys.exit(1)


class ProductSpawner:
    """Generate product variants using Claude API."""

    def __init__(self, registry_path: str = "product_registry.json"):
        self.registry_path = Path(registry_path)
        self.registry = self._load_registry()
        self.client = Anthropic()
        self.variants = []

    def _load_registry(self) -> dict:
        """Load product registry."""
        if self.registry_path.exists():
            with open(self.registry_path) as f:
                return json.load(f)
        return {
            "metadata": {"version": "2.0.0"},
            "seed_product": {},
            "generated_variants": []
        }

    def _save_registry(self):
        """Save updated registry."""
        self.registry["metadata"]["total_variants_generated"] = len(self.variants)
        self.registry["generated_variants"] = self.variants
        with open(self.registry_path, 'w') as f:
            json.dump(self.registry, f, indent=2)

    def generate_variants(self, seed: str = None, count: int = 100) -> list:
        """Generate product variants using Claude."""
        if seed is None:
            seed = self.registry["seed_product"].get("name", "Alexandria Energy Node")

        print(f"\n🏭 Generating {count} product variants for: {seed}")
        print("════════════════════════════════════════════════════════════")
        print("")

        prompt = f"""You are a product innovation expert specializing in energy-tech solutions.

Seed Product: {seed}

Generate exactly {count} distinct product variants targeting different market segments.

For each variant, provide:
1. Product Name
2. Target Market (enterprise/mining/research/renewable/crypto/startup)
3. Key Features (3-5 unique features)
4. Price Point (USD)
5. Unique Value Proposition (1-2 sentences)
6. Energy Integration (How it tracks/uses computational work energy)

Format as JSON array. Ensure variants are truly different and address real market needs.
Focus on energy-tech, computational work quantification, and carbon tracking."""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse response
            response_text = response.content[0].text

            # Extract JSON from response
            try:
                # Try to find JSON array
                start = response_text.find('[')
                end = response_text.rfind(']') + 1
                if start >= 0 and end > start:
                    variants_json = response_text[start:end]
                    variants = json.loads(variants_json)
                else:
                    print("⚠️  No JSON array found in response")
                    variants = []
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON parse error: {e}")
                variants = []

            self.variants = variants
            self._save_registry()

            print(f"✅ Generated {len(self.variants)} variants")
            return self.variants

        except Exception as e:
            print(f"❌ Error generating variants: {e}")
            return []

    def export_csv(self, output_path: str = "products_export.csv"):
        """Export variants to CSV."""
        if not self.variants:
            print("❌ No variants to export")
            return

        try:
            import csv

            with open(output_path, 'w', newline='') as f:
                if self.variants and isinstance(self.variants[0], dict):
                    fieldnames = self.variants[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.variants)

            print(f"✅ Exported {len(self.variants)} variants to {output_path}")

        except Exception as e:
            print(f"❌ Export error: {e}")

    def display_sample(self, count: int = 5):
        """Display sample variants."""
        if not self.variants:
            print("❌ No variants generated yet")
            return

        print(f"\n📋 Sample Variants (showing {min(count, len(self.variants))}/{len(self.variants)}):")
        print("════════════════════════════════════════════════════════════")

        for i, variant in enumerate(self.variants[:count], 1):
            if isinstance(variant, dict):
                print(f"\n{i}. {variant.get('Product Name', 'N/A')}")
                print(f"   Market: {variant.get('Target Market', 'N/A')}")
                print(f"   Price: ${variant.get('Price Point', 'N/A')}")
                print(f"   Value: {variant.get('Unique Value Proposition', 'N/A')[:80]}")


def main():
    """Main entry point."""
    spawner = ProductSpawner()

    # Get seed product
    seed = None
    if len(sys.argv) > 1:
        seed = " ".join(sys.argv[1:])

    # Generate variants
    variants = spawner.generate_variants(seed=seed, count=100)

    if variants:
        # Display samples
        spawner.display_sample(count=10)

        # Export to CSV
        spawner.export_csv()

        print("\n" + "="*60)
        print("✅ PRODUCT SPAWNER COMPLETE")
        print(f"   Generated: {len(variants)} variants")
        print(f"   Registry: product_registry.json")
        print(f"   Export: products_export.csv")
        print("="*60)
    else:
        print("\n❌ Product generation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
