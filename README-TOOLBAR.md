# 🔷 Alexandria Toolbar Extension

## Overview

A modern browser extension for unified access to all Alexandria monorepo applications.

**Status:** ✅ **READY TO USE**

## What It Does

Click the 🔷 icon in your browser to access:
- 🎬 FILMMAKER - 3D Content Automation
- 🧠 SECOND-ME - AI Self Training System
- 📦 PRODUCT-SPAWNER - Product Variant Generator
- 🔄 JSON-MCP-BLOWER - Agent Multiplication System
- 🌐 ANIMA-MUNDI - Enterprise Platform
- 🎥 RENDERS - Output Storage & Gallery

## Quick Install (2 minutes)

### Chrome
1. Open: `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select: `/home/ichigo/alexandria/alexandria-toolbar/dist/`

### Firefox
1. Open: `about:debugging#/runtime/this-firefox`
2. Click "Load Temporary Add-on"
3. Select: `/home/ichigo/alexandria/alexandria-toolbar/dist/manifest.json`

**Then:** Click ⚙️ Settings and change SECOND-ME port to 3001

## Key Features

✨ **One-Click Launch** - Open any Alexandria app instantly
🔍 **Status Monitoring** - Real-time service health checks
⚙️ **Configurable** - Custom ports via settings
🌙 **Dark Mode** - Modern interface matching your style
🔗 **Cross-Browser** - Works with Chrome and Firefox

## Getting Started

**Step 1: Install the Extension**
```bash
# See above for Chrome/Firefox installation
```

**Step 2: Start Your Apps**
```bash
# Terminal 1: FILMMAKER
cd /home/ichigo/alexandria/filmmaker-web && npm install && npm run dev

# Terminal 2: SECOND-ME
cd /home/ichigo/alexandria/Second-Me && make start

# Terminal 3: PRODUCT-SPAWNER (optional)
cd /home/ichigo/alexandria/product-spawner
export ANTHROPIC_API_KEY="sk-..."
python3 sales_orchestrator.py
```

**Step 3: Use the Toolbar**
- Click 🔷 icon anytime
- See all services and their status
- Click to launch dashboards

## Documentation

- **Quick Start:** `/alexandria-toolbar/QUICK_START.md`
- **Installation:** `/alexandria-toolbar/INSTALLATION_GUIDE.md`
- **Full Details:** `/alexandria-toolbar/README.md`
- **Project Info:** `/alexandria-toolbar/PROJECT_SUMMARY.md`

## File Location

```
/home/ichigo/alexandria/alexandria-toolbar/
├── dist/              (Production build - ready to install)
├── src/               (Source code)
├── README.md          (Full documentation)
├── QUICK_START.md     (2-minute setup)
├── INSTALLATION_GUIDE.md
└── install.sh         (Installation helper)
```

## Technical Details

- **Framework:** Manifest V3 (Chrome/Firefox)
- **Tech Stack:** Vanilla JS + Tailwind CSS
- **Bundle Size:** ~15 KB gzipped
- **Build Tool:** Vite 5
- **Status:** Production-ready

## Troubleshooting

**Can't see the extension icon?**
- Go to `chrome://extensions/` (or `about:debugging` in Firefox)
- Find "Alexandria Toolbar"
- If it's not there, click "Load unpacked" and select `dist/`

**Services show as "Stopped"?**
- Check Settings ⚙️ → Port Configuration
- Verify services are actually running
- Click Refresh 🔄

**Port 3000 conflict?**
- Open Settings ⚙️ (top of extension)
- Change SECOND-ME port to 3001
- Click Save

For more help, see **INSTALLATION_GUIDE.md**

## What's Included

✅ Complete source code (15 files)
✅ Production build ready (dist/ folder)
✅ PNG icons (16x, 48x, 128x)
✅ Dark mode UI with Tailwind
✅ Settings page
✅ Health checking logic
✅ Comprehensive documentation
✅ Installation scripts

## System Requirements

- Chrome 90+ OR Firefox 109+
- Modern browser with ES6 support
- Localhost access (for health checks)

## Support

- Check `/alexandria-toolbar/QUICK_START.md` first (2 min)
- See `/alexandria-toolbar/INSTALLATION_GUIDE.md` for detailed help
- Review `/CLAUDE.md` for full Alexandria project info
- Report issues in the extension's Settings page

---

**Version:** 1.0.0
**Status:** ✅ Complete & Ready to Use
**Tested:** Chrome & Firefox ✅

🚀 **Click the 🔷 icon to get started!**
