#!/usr/bin/env python3
"""
MEMBER CARD GENERATOR - Alexandria Governance
Issues and manages member cards post-admission

Integration Points:
- ballon-symmetry.py: Produces admission test passes
- Governance: Stores member cards in perpetuity records
- Portal: Renders cards dynamically
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class MemberCardGenerator:
    """Generates Alexandria member cards for admitted citizens"""

    def __init__(self):
        self.card_dir = Path("/home/ichigo/alexandria/ADAM/porta-mundi/governance/perpetuity-fund/committee/member-cards")
        self.card_dir.mkdir(parents=True, exist_ok=True)

        self.registry_file = self.card_dir / "member-registry.json"
        self.load_registry()

    def load_registry(self):
        """Load or initialize member registry"""
        if self.registry_file.exists():
            with open(self.registry_file, 'r') as f:
                self.registry = json.load(f)
        else:
            self.registry = {
                "total_members": 0,
                "members": {},
                "issued_cards": [],
                "last_updated": datetime.now().isoformat()
            }
            self.save_registry()

    def save_registry(self):
        """Persist member registry"""
        self.registry["last_updated"] = datetime.now().isoformat()
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2)

    def generate_member_id(self) -> str:
        """Generate unique Alexandria member ID"""
        # Format: 0xARCH{hex_uuid}
        return f"0xARCH{uuid.uuid4().hex[:12].upper()}"

    def determine_trust_level(self, test_metadata: Dict[str, Any]) -> str:
        """Determine trust level based on test performance"""
        elapsed_seconds = test_metadata.get("elapsed_seconds", 0)
        perspective_accepted = test_metadata.get("perspective_accepted", False)

        if not perspective_accepted:
            return "OBSERVER"

        if elapsed_seconds < 30:
            return "ALPHA_ARCHITECT"
        elif elapsed_seconds < 60:
            return "BETA_ENGINEER"
        elif elapsed_seconds < 120:
            return "GAMMA_SCHOLAR"
        else:
            return "FOUNDLING"

    def select_ninja_modules(self, trust_level: str) -> list:
        """Assign ninja modules based on trust level"""
        modules_pool = {
            "ALPHA_ARCHITECT": ["SYS_OPT", "NET_TUNNEL", "STEGO_X"],
            "BETA_ENGINEER": ["NET_TUNNEL", "STEGO_X"],
            "GAMMA_SCHOLAR": ["STEGO_X"],
            "OBSERVER": ["LOG_MONITOR"]
        }
        return modules_pool.get(trust_level, ["LOG_MONITOR"])

    def generate_avatar_url(self, member_id: str) -> str:
        """Generate deterministic avatar from member ID"""
        seed = member_id.replace("0xARCH", "")
        return f"https://api.dicebear.com/7.x/bottts-neutral/svg?seed={seed}"

    def issue_member_card(
        self,
        name: str,
        identity: str,
        test_result: Dict[str, Any],
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Issue a new Alexandria member card

        Args:
            name: Member's full name
            identity: Member's role/identity
            test_result: Result from ballon-symmetry.py test
            timestamp: ISO timestamp of card issuance

        Returns:
            Member card object
        """

        timestamp = timestamp or datetime.now().isoformat() + "Z"
        member_id = self.generate_member_id()
        trust_level = self.determine_trust_level(test_result)
        ninja_modules = self.select_ninja_modules(trust_level)

        member_card = {
            "member_id": member_id,
            "name": name,
            "identity": identity,
            "avatar_url": self.generate_avatar_url(member_id),
            "wallet_id": member_id,
            "trust_level": trust_level,
            "ninja_modules": ninja_modules,
            "issued_timestamp": timestamp,
            "expires_timestamp": "Never_Immutability_Active",
            "perspective_accepted": test_result.get("perspective_accepted", False),
            "test_elapsed_seconds": test_result.get("elapsed_seconds", 0),
            "test_timestamp": test_result.get("timestamp"),
            "status": "ACTIVE"
        }

        # Store card
        card_file = self.card_dir / f"{member_id}.json"
        with open(card_file, 'w') as f:
            json.dump(member_card, f, indent=2)

        # Update registry
        self.registry["members"][member_id] = {
            "name": name,
            "identity": identity,
            "trust_level": trust_level,
            "issued": timestamp,
            "status": "ACTIVE"
        }
        self.registry["issued_cards"].append(member_id)
        self.registry["total_members"] += 1
        self.save_registry()

        print(f"✅ Member card issued: {name} ({member_id})")
        print(f"   Trust Level: {trust_level}")
        print(f"   Ninja Modules: {', '.join(ninja_modules)}")

        return member_card

    def get_member_card(self, member_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve member card by ID"""
        card_file = self.card_dir / f"{member_id}.json"
        if card_file.exists():
            with open(card_file, 'r') as f:
                return json.load(f)
        return None

    def render_html_card(self, member_card: Dict[str, Any]) -> str:
        """Render member card as HTML"""

        modules_html = "\n".join([
            f'<span class="ninja-badge">{module}</span>'
            for module in member_card["ninja_modules"]
        ])

        quote_pool = [
            "La connaissance est la seule clé qui ne s'use jamais.",
            "L'énergie est pensée matérialisée.",
            "La perspective est souveraineté.",
            "Nous sommes la civilisation que nous construisons.",
            "L'immutabilité est notre fondation."
        ]

        quote = quote_pool[hash(member_card["member_id"]) % len(quote_pool)]

        html = f"""<!DOCTYPE html>
<html lang="fr" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alexandria Member Pass - {member_card['name']}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;700&family=Inter:wght@400;600;900&display=swap" rel="stylesheet">
    <style>
        :root {{ --primary: #f59e0b; --bg: #050300; --gold-glow: rgba(245, 158, 11, 0.4); }}
        body {{ font-family: 'Inter', sans-serif; background-color: var(--bg); color: #fff; overflow: hidden; }}
        .mono {{ font-family: 'Fira Code', monospace; }}

        .member-card {{
            background: linear-gradient(135deg, rgba(20, 20, 20, 0.9) 0%, rgba(5, 5, 5, 1) 100%);
            border: 1px solid rgba(245, 158, 11, 0.2);
            box-shadow: 0 0 40px rgba(0,0,0,0.5), inset 0 0 20px rgba(245, 158, 11, 0.05);
            transition: transform 0.6s cubic-bezier(0.23, 1, 0.32, 1);
            transform-style: preserve-3d;
        }}

        .ninja-badge {{
            background: rgba(245, 158, 11, 0.1);
            border: 1px solid rgba(245, 158, 11, 0.2);
            font-size: 8px;
            padding: 2px 6px;
            border-radius: 4px;
            color: var(--primary);
        }}

        .hologram-effect {{
            position: absolute;
            inset: 0;
            background: linear-gradient(125deg, transparent 0%, rgba(255,255,255,0.05) 45%, rgba(245, 158, 11, 0.1) 50%, rgba(255,255,255,0.05) 55%, transparent 100%);
            background-size: 200% 200%;
            animation: holo 5s infinite linear;
            pointer-events: none;
        }}

        @keyframes holo {{
            0% {{ background-position: -200% -200%; }}
            100% {{ background-position: 200% 200%; }}
        }}

        .chip {{
            width: 40px;
            height: 30px;
            background: linear-gradient(135deg, #d4af37 0%, #f59e0b 100%);
            border-radius: 4px;
            position: relative;
            overflow: hidden;
        }}
        .chip::after {{
            content: '';
            position: absolute;
            inset: 0;
            background: repeating-linear-gradient(90deg, transparent, transparent 4px, rgba(0,0,0,0.2) 4px, rgba(0,0,0,0.2) 5px);
        }}
    </style>
</head>
<body class="min-h-screen flex items-center justify-center p-6 bg-[radial-gradient(circle_at_center,_var(--gold-glow)_0%,_transparent_70%)]">

    <div class="max-w-md w-full perspective-1000">
        <div id="card" class="member-card p-8 rounded-[2rem] relative overflow-hidden">
            <div class="hologram-effect"></div>

            <!-- Card Header -->
            <div class="flex justify-between items-start mb-12 relative z-10">
                <div>
                    <h1 class="text-xl font-black italic tracking-tighter uppercase leading-none">Alexandria<span class="text-amber-500">Pass</span></h1>
                    <p class="text-[8px] mono opacity-40 uppercase tracking-[0.2em] mt-1">Anima Mundi Library Member</p>
                </div>
                <div class="chip"></div>
            </div>

            <!-- Card Body -->
            <div class="space-y-6 relative z-10">
                <div class="flex items-center gap-6">
                    <div class="w-20 h-20 rounded-2xl bg-gradient-to-br from-amber-500/20 to-black border border-amber-500/30 flex items-center justify-center text-3xl overflow-hidden">
                        <img src="{member_card['avatar_url']}" class="w-full h-full object-cover opacity-80" alt="Avatar">
                    </div>
                    <div>
                        <div class="text-[10px] mono text-amber-500 font-bold uppercase mb-1">{member_card['identity']}</div>
                        <div class="text-lg font-bold tracking-tight text-white uppercase">{member_card['name']}</div>
                        <div class="text-[9px] mono opacity-40 break-all mt-1">{member_card['wallet_id']}</div>
                    </div>
                </div>

                <div class="pt-6 border-t border-white/5 space-y-4">
                    <div class="flex justify-between items-end">
                        <div class="space-y-1">
                            <div class="text-[8px] mono opacity-40 uppercase">Ninja Modules Carried</div>
                            <div class="flex gap-2">
                                {modules_html}
                            </div>
                        </div>
                        <div class="text-right">
                            <div class="text-[8px] mono opacity-40 uppercase">Trust Level</div>
                            <div class="text-xs font-bold text-amber-500">{member_card['trust_level']}</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Footer -->
            <div class="mt-12 flex justify-between items-center relative z-10">
                <div class="text-[7px] mono opacity-20 uppercase">
                    Issued: {member_card['issued_timestamp'][:10]}<br>
                    Expires: {member_card['expires_timestamp']}
                </div>
                <div class="flex gap-1">
                    <div class="w-1 h-8 bg-amber-500/20"></div>
                    <div class="w-2 h-8 bg-amber-500/40"></div>
                    <div class="w-1 h-8 bg-amber-500/10"></div>
                    <div class="w-4 h-8 bg-amber-500/60"></div>
                </div>
            </div>
        </div>

        <!-- UI Action -->
        <div class="mt-8 text-center">
            <button onclick="rotateCard()" class="px-6 py-2 bg-amber-600 text-black font-black text-[10px] uppercase rounded-full hover:bg-white transition-all shadow-lg">Scanner la Carte ✨</button>
            <p class="text-[8px] mono opacity-30 mt-4 uppercase tracking-widest">"{quote}"</p>
            <p class="text-[7px] mono opacity-20 mt-6">Member ID: {member_card['member_id']}</p>
        </div>
    </div>

    <script>
        function rotateCard() {{
            const card = document.getElementById('card');
            card.style.transform = 'rotateY(360deg)';
            setTimeout(() => {{
                card.style.transform = 'rotateY(0deg)';
                addLog();
            }}, 600);
        }}

        function addLog() {{
            console.log("[SYSTEM] Member Authenticated. Welcome, {member_card['name']}.");
            console.log("[GOVERNANCE] Trust Level: {member_card['trust_level']}");
            console.log("[MODULES] Loaded: {', '.join(member_card['ninja_modules'])}");
        }}

        // Tilt effect
        document.addEventListener('mousemove', (e) => {{
            const card = document.getElementById('card');
            const xAxis = (window.innerWidth / 2 - e.pageX) / 25;
            const yAxis = (window.innerHeight / 2 - e.pageY) / 25;
            card.style.transform = `rotateY(${{xAxis}}deg) rotateX(${{yAxis}}deg)`;
        }});
    </script>
</body>
</html>"""

        return html

    def generate_member_card_files(self, member_card: Dict[str, Any]) -> Dict[str, str]:
        """Generate HTML card file from member data"""

        html = self.render_html_card(member_card)

        # Save HTML card
        card_html_file = self.card_dir / f"{member_card['member_id']}-card.html"
        with open(card_html_file, 'w', encoding='utf-8') as f:
            f.write(html)

        return {
            "json_file": str(self.card_dir / f"{member_card['member_id']}.json"),
            "html_file": str(card_html_file)
        }

    def list_all_members(self) -> list:
        """List all issued member cards"""
        self.load_registry()
        return self.registry.get("issued_cards", [])

    def get_member_stats(self) -> Dict[str, Any]:
        """Get member statistics"""
        self.load_registry()

        trust_levels = {}
        for member_id in self.registry.get("issued_cards", []):
            card = self.get_member_card(member_id)
            if card:
                level = card.get("trust_level", "UNKNOWN")
                trust_levels[level] = trust_levels.get(level, 0) + 1

        return {
            "total_members": self.registry["total_members"],
            "trust_level_distribution": trust_levels,
            "last_updated": self.registry.get("last_updated")
        }


def main():
    """Demo member card generation"""

    generator = MemberCardGenerator()

    # Demo: Issue a test card
    test_result = {
        "timestamp": datetime.now().isoformat() + "Z",
        "perspective_accepted": True,
        "elapsed_seconds": 25
    }

    card = generator.issue_member_card(
        name="Michael Lefebvre",
        identity="Architect Identity",
        test_result=test_result
    )

    files = generator.generate_member_card_files(card)
    print(f"\n📋 Card Files Generated:")
    print(f"   JSON: {files['json_file']}")
    print(f"   HTML: {files['html_file']}")

    print(f"\n📊 Member Stats:")
    stats = generator.get_member_stats()
    print(f"   Total Members: {stats['total_members']}")
    print(f"   Trust Levels: {stats['trust_level_distribution']}")


if __name__ == "__main__":
    main()
