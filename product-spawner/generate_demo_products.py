#!/usr/bin/env python3
"""
Generate 100+ demo products for Alexandria Energy ecosystem.
Simulates Claude API product generation without requiring API key.
Creates realistic product variants for testing the full workflow.
"""

import json
from pathlib import Path
from datetime import datetime

def generate_demo_products():
    """Generate 100+ realistic product variants."""
    
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║       🏭 GENERATING 100+ DEMO PRODUCTS FOR ALEXANDRIA            ║")
    print("║       (Simulating Claude API - Full Workflow Demo)               ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print()
    
    # Load registry
    registry_path = Path("product_registry.json")
    with open(registry_path) as f:
        registry = json.load(f)
    
    # Define product templates (simulating Claude output)
    markets = ["enterprise", "mining", "research", "renewable", "crypto", "startup", "government", "nonprofit"]
    features_pool = {
        "enterprise": ["Multi-cluster support", "Enterprise SLA", "24/7 monitoring", "API integration", "Custom branding", "SSO/SAML"],
        "mining": ["XMRig integration", "Pool management", "Rig monitoring", "Revenue tracking", "Difficulty adjustment", "Failover"],
        "research": ["Data export formats", "Peer review ready", "Citation support", "Open data API", "Academic license", "Publication ready"],
        "renewable": ["Solar integration", "Wind integration", "Grid balancing", "Carbon tracking", "Sustainability reports", "Green certifications"],
        "crypto": ["Blockchain integration", "Smart contracts", "Wallet integration", "Exchange APIs", "DeFi compatible", "NFT support"],
        "startup": ["Scalable infrastructure", "Cost optimization", "Performance analytics", "Growth tracking", "Pivot-friendly", "MVP ready"],
        "government": ["Compliance reporting", "Audit trails", "Security hardened", "Data sovereignty", "Regulatory compliant", "GDPR ready"],
        "nonprofit": ["Grant tracking", "Impact metrics", "Donor dashboards", "Transparency reporting", "Cost-effective", "Community friendly"]
    }
    
    # Generate 100 unique products
    variants = []
    
    print(f"📊 GENERATING PRODUCT VARIANTS")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    product_counter = 0
    
    for market in markets:
        # Generate 12-13 variants per market
        variants_per_market = 13 if market != markets[-1] else 12
        
        for i in range(variants_per_market):
            product_counter += 1
            
            base_price = registry['seed_product']['base_price']
            price_multiplier = {
                "enterprise": 3.5,
                "mining": 2.0,
                "research": 1.5,
                "renewable": 2.5,
                "crypto": 2.8,
                "startup": 1.2,
                "government": 4.0,
                "nonprofit": 0.8
            }[market]
            
            # Select features for this variant
            base_features = registry['seed_product']['base_features'][:3]
            market_features = features_pool[market][:(i % 3) + 2]
            
            product = {
                "id": f"PRODUCT_{product_counter:03d}",
                "name": f"Alexandria {market.title()} Suite v{product_counter}",
                "market": market,
                "description": f"Energy tracking and computational work quantification for {market} sector",
                "base_features": base_features,
                "market_specific_features": market_features,
                "price_usd": int(base_price * price_multiplier + (i * 50)),
                "energy_integration": f"Tracks {0.5 + (i * 0.1):.1f} kWh per unit",
                "value_proposition": f"Purpose-built energy solution for {market} organizations",
                "market_segment": market,
                "variant_number": i + 1,
                "generation_time": datetime.utcnow().isoformat()
            }
            
            variants.append(product)
            
            if product_counter % 20 == 0:
                print(f"✅ Generated {product_counter} products...")
    
    print(f"✅ Generated {len(variants)} total products")
    print()
    
    # Update registry
    registry['generated_variants'] = variants
    registry['metadata']['total_variants_generated'] = len(variants)
    registry['metadata']['variants_ready_for_production'] = len(variants)
    registry['metadata']['generation_timestamp'] = datetime.utcnow().isoformat()
    registry['metadata']['generation_mode'] = 'DEMO'
    
    # Save registry
    with open(registry_path, 'w') as f:
        json.dump(registry, f, indent=2)
    
    print(f"💾 REGISTRY UPDATED")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"✅ Saved {len(variants)} variants to product_registry.json")
    print()
    
    # Create product export
    export_data = {
        "metadata": {
            "total_products": len(variants),
            "by_market": {}
        },
        "products": variants
    }
    
    # Count by market
    for market in markets:
        count = len([v for v in variants if v['market'] == market])
        export_data['metadata']['by_market'][market] = count
    
    export_file = Path("products_export.csv")
    
    # Create CSV header
    csv_content = "Product ID,Name,Market,Price USD,Features,Energy Integration,Value Proposition\n"
    
    for v in variants:
        features = "; ".join(v['market_specific_features'])
        csv_content += f"{v['id']},\"{v['name']}\",{v['market']},${v['price_usd']},\"{features}\",{v['energy_integration']},\"{v['value_proposition']}\"\n"
    
    with open(export_file, 'w') as f:
        f.write(csv_content)
    
    print(f"📊 PRODUCT SUMMARY BY MARKET")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    for market, count in export_data['metadata']['by_market'].items():
        market_products = [v for v in variants if v['market'] == market]
        avg_price = sum(p['price_usd'] for p in market_products) / len(market_products)
        print(f"✅ {market.upper():12s}: {count:2d} products | Avg price: ${avg_price:7.0f}")
    
    print()
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║           ✅ 100+ PRODUCTS GENERATED & READY FOR PRODUCTION      ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print()
    
    print(f"📁 FILES CREATED")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"✅ product_registry.json (updated with {len(variants)} variants)")
    print(f"✅ products_export.csv ({export_file.stat().st_size} bytes)")
    print()
    
    print(f"🚀 NEXT STEP: Distribute to 3,069 agents")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"python3 distribute_products_to_agents.py")
    print()

if __name__ == "__main__":
    generate_demo_products()

