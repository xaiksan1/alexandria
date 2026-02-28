#!/bin/bash
# JSON-MCP-Blower Startup Script
# Runs bootstrap loop and real-time watcher

set -e

echo "🚀 JSON-MCP-Blower: Exponential Agent Generation"
echo "════════════════════════════════════════════════════════"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found"
    exit 1
fi

# Check dependencies
python3 << 'EOF'
try:
    import json
    print("✅ json module available")
except:
    print("❌ json module missing")
    exit(1)
EOF

# Run bootstrap if schema exists
if [ -f "mcp-schema.json" ]; then
    echo "📊 Running Bootstrap Loop..."
    python3 bootstrap_loop.py
    echo ""
else
    echo "⚠️  mcp-schema.json not found"
    exit 1
fi

# Optional: Start watcher if watchdog available
echo "👁️  Starting JSON Watcher (real-time monitoring)..."
echo "   Edit mcp-schema.json to trigger generation"
echo ""

python3 << 'EOF'
try:
    from json_watcher import JSONWatcher
    watcher = JSONWatcher()
    watcher.start_watching()
except ImportError:
    print("ℹ️  watchdog not installed (optional)")
    print("   Install for real-time monitoring: pip install watchdog")
except KeyboardInterrupt:
    pass
EOF

echo ""
echo "✅ JSON-MCP-Blower complete"
