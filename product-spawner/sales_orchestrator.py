#!/usr/bin/env python3
"""
Product-Spawner: Sales Orchestrator
Generates 100+ market-targeted product variants using Claude API.
Integrated with Alexandria energy-tech ecosystem.
"""

import json
import json5
import sys
import os
from pathlib import Path
from datetime import datetime

try:
    import google.generativeai as genai
except ImportError:
    print("❌ Missing: pip install google-generativeai")
    sys.exit(1)


class ProductSpawner:
    """Generate product variants using Gemini API."""

    def __init__(self, registry_path: str = "product_registry.json"):
        self.registry_path = Path(registry_path)
        self.registry = self._load_registry()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ Missing: export GEMINI_API_KEY=...")
            sys.exit(1)
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")
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
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=8000,
                    temperature=0.7,
                )
            )

            # Parse response
            response_text = response.text

            # Extract JSON from response (handle markdown blocks + incomplete JSON)
            try:
                # Try markdown code blocks first
                if "```json" in response_text:
                    start = response_text.find("```json") + 7
                    end = response_text.find("```", start)
                    variants_json = response_text[start:end].strip()
                elif "```" in response_text:
                    start = response_text.find("```") + 3
                    end = response_text.find("```", start)
                    variants_json = response_text[start:end].strip()
                else:
                    # Try to find raw JSON array
                    start = response_text.find('[')
                    end = response_text.rfind(']') + 1
                    variants_json = response_text[start:end]

                if variants_json:
                    # Clean incomplete JSON - find last complete object
                    if not variants_json.rstrip().endswith(']'):
                        # Find last complete }, then add ]
                        last_brace = variants_json.rfind('}')
                        if last_brace > 0:
                            variants_json = variants_json[:last_brace+1] + ']'

                    variants = json5.loads(variants_json)
                else:
                    print("⚠️  No JSON found in response")
                    variants = []
            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠️  JSON parse error: {e}")
                print(f"Response length: {len(response_text)} chars")
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
