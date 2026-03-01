#!/usr/bin/env python3
"""
Deploy actual MCP agents with exponential growth.
Fixes the UI/Agent confusion and creates real agent instances.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from mcp_factory import MCPFactory
from bootstrap_loop import BootstrapLoop

def deploy_exponential_agents():
    """Generate and deploy MCP agents with true exponential growth."""
    
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║  🚀 EXPONENTIAL MCP AGENT DEPLOYMENT (Fixes UI→Agent confusion) ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print()
    
    # Load schema
    schema_path = Path("mcp-schema.json")
    with open(schema_path) as f:
        schema = json.load(f)
    
    fractal = schema['fractal_config']
    initial = fractal['initial_generation']
    growth_rate = fractal['growth_rate']
    max_gens = fractal['max_iterations']
    
    print("📊 FRACTAL CONFIGURATION")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"Initial Agents: {initial}")
    print(f"Growth Rate: {growth_rate}x per generation")
    print(f"Max Generations: {max_gens}")
    print()
    
    # Calculate all generations
    print("🎯 GENERATION PLAN")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    total_agents = 0
    gen_summary = {}
    
    for gen_num in range(max_gens):
        gen_size = int(initial * (growth_rate ** gen_num))
        gen_summary[gen_num] = gen_size
        total_agents += gen_size
        
        bar = "█" * min(gen_size // 20, 50)
        print(f"Gen {gen_num}: {gen_size:4d} agents {bar} (cumulative: {total_agents:,})")
    
    print()
    print(f"🎉 TOTAL: {total_agents:,} agents across {max_gens} generations")
    print(f"   Multiplication factor: {total_agents / initial:.0f}x")
    print()
    
    # Create bootstrap loop
    loop = BootstrapLoop()
    
    print("🏭 GENERATING AGENTS")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Create all generations
    all_agents = []
    for gen_num in range(max_gens):
        gen_size = gen_summary[gen_num]
        agents = loop.factory.create_generation(gen_num, gen_size)
        all_agents.extend(agents)
        print(f"✅ Gen {gen_num}: {len(agents)} agents created")
    
    print()
    
    # Save agents
    agents_dir = Path("agents_exponential")
    agents_dir.mkdir(exist_ok=True)
    
    print("💾 SAVING AGENT INSTANCES")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    for agent in all_agents:
        agent_file = agents_dir / f"{agent['id']}.json"
        with open(agent_file, 'w') as f:
            json.dump(agent, f, indent=2)
    
    print(f"✅ Saved {len(all_agents)} agent configs to agents_exponential/")
    
    # Save registry
    registry = {
        "metadata": {
            "total_agents": len(all_agents),
            "generations": max_gens,
            "generated_at": datetime.utcnow().isoformat(),
            "growth_rate": growth_rate,
            "initial_agents": initial
        },
        "agents_by_generation": gen_summary,
        "agent_ids": [a["id"] for a in all_agents],
        "status": "DEPLOYED"
    }
    
    registry_file = agents_dir / "registry.json"
    with open(registry_file, 'w') as f:
        json.dump(registry, f, indent=2)
    
    print(f"✅ Registry saved to agents_exponential/registry.json")
    print()
    
    # Fix JSBLON to track AGENTS instead of UIs
    print("🔧 FIXING JSBLON (UI→Agent correction)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    jsblon_file = Path("/home/ichigo/alexandria/ADAM/jsblon/anima_mundi_core.jsblon")
    try:
        with open(jsblon_file) as f:
            jsblon = json.load(f)
        
        # Replace UI tracking with AGENT tracking
        jsblon['_meta']['agent_count'] = len(all_agents)
        jsblon['_meta']['current_generation'] = max_gens - 1
        jsblon['_meta']['total_agents_deployed'] = len(all_agents)
        jsblon['_meta']['status'] = 'AGENT_DEPLOYMENT_MODE'
        jsblon['_meta']['mode'] = 'EXPONENTIAL_MCP_AGENTS'
        jsblon['_meta']['description'] = f'{initial} initial → {total_agents:,} agents (2.0x exponential)'
        jsblon['_meta']['updated'] = datetime.utcnow().isoformat()
        
        # Remove UI count (was the mistake)
        if 'current_ui_count' in jsblon['_meta']:
            del jsblon['_meta']['current_ui_count']
        
        with open(jsblon_file, 'w') as f:
            json.dump(jsblon, f, indent=2)
        
        print("✅ JSBLON corrected: UI→Agent tracking")
        print(f"   Agent Count: {len(all_agents)}")
        print(f"   Deployment Status: COMPLETE")
        print()
    except Exception as e:
        print(f"⚠️  Could not update JSBLON: {e}")
    
    # Final summary
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║         ✅ EXPONENTIAL MCP AGENT DEPLOYMENT COMPLETE           ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print()
    print(f"📊 DEPLOYMENT SUMMARY")
    print(f"   Total Agents: {len(all_agents):,}")
    print(f"   Generations: {max_gens}")
    print(f"   Growth Rate: {growth_rate}x exponential")
    print(f"   Agent Registry: agents_exponential/registry.json")
    print(f"   Individual Configs: agents_exponential/*.json")
    print()
    print("🚀 Next: Deploy MCP servers and establish endpoints")
    print()

if __name__ == "__main__":
    deploy_exponential_agents()

