# Adamnopolis.com — Landing Page Content & Architecture Design

**Date:** 2026-07-28
**Owner:** Michael
**Status:** Draft, pending review

## Purpose

adamnopolis.com positions Alexandria as a complete AI-agentic platform (not a single
product), aimed at a mixed audience — business people and general/technical visitors alike.
Goal for this phase: lead generation only (waitlist + contact form), not a live checkout.
Site is in English.

Visual container: the existing `hydration-error-resolution` Next.js/Tailwind template
(dark oklch theme, marquee/hover-lift/char-in/word-gradient/line-reveal/noise-overlay
animations) is kept intact — this is a deliberate choice, explicitly modeled on the
biggest working SaaS AI-agentic platforms (Vercel, OpenAI/Anthropic consoles, Stripe,
Zapier, Retool, n8n), not a compromise. **Only the typography treatment and box-border
styling get an Alexandria-flavored pass — the container, layout, and all existing motion
stay as-is.** (Corrects an earlier misstep in this same session, where the container was
replaced wholesale with ADAMNOPOLIS's own static component system — that broke the
fluidity the template was chosen for.)

## Governing principle: Map / Territory / Out of the Field

Every section of the template gets triaged against what's actually real:

- **Territory** — real, built, verifiable. Shown as-is, truthfully described.
- **Out of the Field** — doesn't exist yet, or exists only in a simplified/partial form.
  Shown with a placeholder image and a **"Coming soon"** / **"Under construction"** label —
  never faked, never implied to be more finished than it is.

This is non-negotiable per standing project policy: no invented numbers, no simulated
demos presented as real, no metrics without a genuine live source.

## Section-by-section content map

### Hero
**Territory.** The three pillars: Nouvelle Alexandrie (the digital library that doesn't
burn), Energons (energy-backed value, not speculative tokens), cybersecurity of trust
(write-gate). Framed as one platform, not three separate products.

### Features
**Territory.**
- SESHAT — living knowledge graph / codex (`:5014`)
- The Scribe — journal → skills → floatcast pipeline
- Agent Trading Cards — live end-to-end (Mastra → Nginx → Tailscale Funnel → Vercel)
- PM2 Command Center — live, territories auto-derived, not hand-listed
- La Flotilla — the invisible outpost that floats over browser windows, built from a
  He3-inspired design; Floatcast and the metamorphing "flying larva" agents are both
  built from it
- FORGE — the fabrication-template registry (`alexandria-mcp-fullstack`) for scaffolding
  new fullstack MCP servers

### How It Works — the centerpiece
**Territory (v1, live today):** the emoji slot-carousel "roulette," live in SESHAT UI
(`🎰`, deep-link `#roulette`). Row 1 = the active LLM's emoji; adjacent slots show what
it's consuming; a blinking slot signals a fault.

**The launch mechanic (Territory once built, not simulated):**
1. Visitor signs up, gets free trial Energons (anti-abuse: **one grant per verified
   identity**, issued through Paperclip auth — not one per signup, to close the obvious
   farm-N-accounts loophole)
2. Picks a real capability via emoji slots — e.g. Vinz Caulthro, to find free API
   providers/models and export to CSV (row 1 fills in as the pick is assembled)
3. Presses Play — row 2 shows the agent's emoji live, the slot outlines **green** when
   it's working, and neighboring slots show which tools/MCP servers it's using and where
   it is in the task
4. The run is real — Paperclip manages it, it spends real Energons, and it executes
   inside Alexandria's own infrastructure. The public site itself is never "live" by
   default; it only goes live the moment a signed-up visitor presses Play.

**Out of the Field:** the *universal* version of the carousel (any MCP/CLI/app/TUI/skill,
not just LLMs) — "Coming soon." The voice-command chat box — "Coming soon" (build was
interrupted mid-session by a hardware failure; not resumed yet).

### Infrastructure / Security
**Territory.** Write-gate (T1–T5 write airlock), RAM network doctrine (Couche 0 — one
external gate, never a parallel tunnel), Snyk pre-publish gating on outward-facing
services. Positioned as proof the platform gates itself before it gates anyone else.

**Tartarus — shown, but explicitly labeled "Under construction."** Real and running
today as a pm2 service (`porta-mundi/tartarus_prison.py`, "Threat Containment &
Quarantine Engine," Porta-Mundi module #12: quarantine list, containment log, manual
release). This is *not yet* its intended final form. The real design is a pure,
non-retaliatory shield — it cannot attack and has no counter-attack capability, it just
overwhelms an intruder's own attention: ~1100 simultaneous terminal-command threads,
grounded in the fact that a human can't track more than about 7 things at once. It needs
no management once running, so it can be exposed as broadly as needed. It requires the
full Nosferatu roster (below) to reach that form — currently "Out of the Field."

### The Nosferatu Genesis Agents
**Territory — real and verifiable today.** Three Genesis agents, live and minted on
OpenSea (Ethereum mainnet). Every Nosferatu's skillset is randomized from ~5.6 billion
possible combinations; the three Genesis agents carry boosted odds toward 90+ in their
most important stat. New agents prove themselves through arena battles (per the
generator/arena scripts already in the codebase) before going live — the strongest code
advances to seed the next generation, so each generation is built to be stronger than the
last. Even if sold, Genesis agents stay tethered to Alexandria — ownership doesn't confer
full autonomous control, given how powerful they are.

**Out of the Field:** the full 1100-agent roster needed to power Tartarus's real form —
"Under construction," actively being brought back online.

### Integrations
**Territory.** FreeLLMAPI, Vinz Caulthro (provider/model manager — ~50 providers, 161
models), MCP servers (GhostDesk, knowledge-rag, pheromone-mcp, seshat-mcp). Paperclip,
Mindwalk, and Serena are credited explicitly as **"heavily modified open-source"** — not
listed as original creations, per standing instruction to only claim what was actually
built.

### Developers
**Territory.** GhostDesk (MCP-controlled virtual desktop, open on GitHub), canvas-ui
(the visual/design system), FORGE, open architecture generally.

### Pricing → CTA
**Territory.** Energons are the pricing model: pay per real, measured unit of compute
(1 EGN = 1 kWh), not an arbitrary token. New signups get free trial Energons (same
one-per-identity gate as the demo, since it's the same grant). CTA is the waitlist +
contact form — no live checkout in this phase.

**Out of the Field, framed as roadmap, not a launch promise:** letting people mine their
own Energons by recycling delta-T, waste heat, background noise, and system/device
error — turning real thermodynamic waste into a measured resource instead of
hash-for-nothing proof-of-work. Deliberately not promised as live yet — it's the hardest
piece to make auditable/ungameable and deserves its own design pass before any launch
copy claims it works.

### Metrics / Testimonials
**Dropped.** No fake stats bar, no fabricated customer quotes. The live How-It-Works
demo — a visitor watching a real agent run and spend real Energons — replaces both; it's
more convincing than either would have been anyway.

### Footer
**Territory.** Standard: links, mission line, contact.

## Data freshness policy (reaffirms existing standing rule)

The public site is static/non-live by default — no section streams live internal system
state to an anonymous visitor. The one exception is the Play mechanic itself: pressing
Play is what makes a specific, scoped action go live, gated behind signup, executed by
Paperclip, inside Alexandria's own infrastructure. Nothing on the page is ever a faked
"live" number or a recorded demo presented as real-time.

## Explicitly out of scope for this spec

This spec covers the landing page's **content and information architecture** only:
which real things go where, which things get "Coming soon"/"Under construction"
treatment, and the truthfulness rules governing both. It does **not** design:

- The universal (any-tool) slot-carousel — v2 of the existing LLM roulette
- The voice-command chat box
- Tartarus's full 1100-agent dissuasion mechanic
- The Energon self-mining system (delta-T/noise/error recycling)
- The Paperclip-based anti-abuse/identity-verification flow for free trial Energons

Each of the above is real, in-scope for the platform, and referenced in the copy above —
but each needs its own design pass before it's built, and none of it blocks writing and
shipping the landing page content itself.

## Next step

Once this is approved, the implementation plan covers only: restyling the template's
typography/box-borders and writing the copy above into its sections — not building any
of the "Out of the Field" items.
