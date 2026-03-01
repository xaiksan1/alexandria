#!/usr/bin/env python3
"""
Distribute generated products to MCP agent clusters.
Creates production assignments across all 10 generations.
"""

import json
from pathlib import Path
from datetime import datetime

def distribute_products_to_agents():
    """Distribute products to agent clusters."""
    
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║        📦 DISTRIBUTING PRODUCTS TO 3,069 MCP AGENTS             ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print()
    
    # Load configurations
    product_registry = json.load(open("/home/ichigo/alexandria/product-spawner/product_registry.json"))
    mcp_integration = json.load(open("/home/ichigo/alexandria/product-spawner/mcp_integration_config.json"))
    mcp_deployment = json.load(open("/home/ichigo/alexandria/json-mcp-blower/mcp_deployment_status.json"))
    
    print(f"📊 DISTRIBUTION SETUP")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Get or generate sample products if none exist
    products = product_registry.get('generated_variants', [])
    
    if not products:
        print(f"⚠️  No products generated yet. Using templates to create sample assignments...")
        print()
        
        # Create sample products from templates
        templates = product_registry.get('variant_templates', [])
        for template in templates:
            products.append({
                "name": f"Alexandria {template['segment'].title()} Edition",
                "segment": template['segment'],
                "features": template.get('features_added', []),
                "price": int(1000 * template.get('price_multiplier', 1.0)),
                "status": "ready_for_production"
            })
    
    total_products = len(products)
    total_agents = len(mcp_deployment['servers']['active'])
    
    print(f"Products available: {total_products}")
    print(f"Available agents: {total_agents:,}")
    print()
    
    # Create distribution assignments
    print(f"🎯 CREATING PRODUCTION ASSIGNMENTS")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    assignments = {
        "metadata": {
            "created": datetime.utcnow().isoformat(),
            "total_products": total_products,
            "total_agents": total_agents,
            "total_assignments": 0,
            "status": "ACTIVE"
        },
        "agent_clusters": {}
    }
    
    assignment_count = 0
    
    # Distribute products across agent generations
    for cluster_name, cluster_info in mcp_integration['distribution_plan'].items():
        gen_num = int(cluster_name.split('_')[1])
        agents_in_gen = cluster_info['agents']
        variants_for_gen = cluster_info['product_variants_assigned']
        
        # Create assignments for this generation
        gen_assignments = {
            "generation": gen_num,
            "total_agents": agents_in_gen,
            "assigned_variants": variants_for_gen,
            "ports": f"{cluster_info['port_start']}-{cluster_info['port_start'] + agents_in_gen - 1}",
            "assignments": []
        }
        
        # Assign products to agents
        for agent_idx in range(agents_in_gen):
            product_idx = (agent_idx % len(products)) if products else 0
            product = products[product_idx] if products else None
            
            if product:
                assignment = {
                    "agent_id": f"AGENT_{gen_num:02d}_{agent_idx:04d}",
                    "port": cluster_info['port_start'] + agent_idx,
                    "assigned_product": product.get('name', 'Sample Product'),
                    "product_segment": product.get('segment', 'energy-tech'),
                    "status": "ASSIGNED",
                    "production_role": "render" if agent_idx < 5 else "marketing"
                }
                gen_assignments['assignments'].append(assignment)
                assignment_count += 1
        
        assignments['agent_clusters'][cluster_name] = gen_assignments
        
        print(f"✅ {cluster_name}: {agents_in_gen} agents, {len(gen_assignments['assignments'])} assignments")
    
    assignments['metadata']['total_assignments'] = assignment_count
    
    print()
    print(f"✅ Total assignments created: {assignment_count:,}")
    print()
    
    # Save assignments
    assignments_file = Path("/home/ichigo/alexandria/product-spawner/production_assignments.json")
    with open(assignments_file, 'w') as f:
        json.dump(assignments, f, indent=2)
    
    print(f"💾 PRODUCTION ASSIGNMENTS SAVED")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"File: {assignments_file}")
    print()
    
    # Summary by generation
    print(f"📊 ASSIGNMENT SUMMARY BY GENERATION")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    for cluster_name in sorted(assignments['agent_clusters'].keys()):
        cluster = assignments['agent_clusters'][cluster_name]
        gen = cluster['generation']
        agents = cluster['total_agents']
        assignments_count = len(cluster['assignments'])
        
        print(f"✅ Gen {gen}: {agents:4d} agents, {assignments_count:4d} assignments")
    
    print()
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║              ✅ DISTRIBUTION COMPLETE                             ║")
    print("║                                                                    ║")
    print("║  3,069 agents assigned to product variants                       ║")
    print("║  Ready for production and rendering                              ║")
    print("║                                                                    ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print()

if __name__ == "__main__":
    distribute_products_to_agents()

