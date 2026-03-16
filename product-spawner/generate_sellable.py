#!/usr/bin/env python3
"""
Alexandria Product Factory — génère de vrais scripts Python livrables.
Chaque "produit" = un ZIP contenant des scripts réels + README.
Listé sur Gumroad, livraison automatique via webhook.

Usage:
    python3 generate_sellable.py --pack crypto --count 5
    python3 generate_sellable.py --pack automation --count 10
    python3 generate_sellable.py --list
"""

import anthropic
import argparse
import json
import os
import zipfile
from datetime import datetime
from pathlib import Path

client = anthropic.Anthropic()

PACKS = {
    "crypto": {
        "title": "Crypto Automation Scripts Bundle",
        "price_usd": 29,
        "description": "5 Python scripts pour automatiser le trading, l'analyse DeFi et le suivi de portfolio crypto.",
        "scripts": [
            ("portfolio_tracker.py", "Script de suivi de portfolio crypto multi-exchange (Binance, Coinbase) via API. Calcule P&L, affiche balances en temps réel."),
            ("dex_price_monitor.py", "Monitor les prix sur Uniswap V2/V3 et Sushiswap. Alerte quand l'écart de prix dépasse un seuil."),
            ("gas_optimizer.py", "Surveille le gas Ethereum et planifie les transactions au moment optimal. Intègre etherscan API."),
            ("defi_yield_scanner.py", "Scan les pools DeFi (Aave, Compound, Curve) et compare les APY. Sort un rapport CSV."),
            ("wallet_analyzer.py", "Analyse un wallet Ethereum : historique transactions, tokens ERC-20, NFTs. Export JSON/CSV."),
        ],
    },
    "automation": {
        "title": "Python Automation Starter Pack",
        "price_usd": 19,
        "description": "10 scripts Python prêts à l'emploi pour automatiser les tâches répétitives du quotidien.",
        "scripts": [
            ("file_organizer.py", "Organise automatiquement les fichiers d'un dossier par type, date ou taille. Configurable via JSON."),
            ("web_scraper.py", "Scraper générique avec gestion de pagination, headers rotatifs et export CSV/JSON."),
            ("pdf_merger.py", "Fusionne, divise et réorganise des PDFs. Ajoute des numéros de page automatiquement."),
            ("email_sender.py", "Envoi d'emails en masse avec templates Jinja2, pièces jointes et tracking d'ouverture."),
            ("api_monitor.py", "Monitor la disponibilité de N APIs. Alerte par email/Slack si downtime détecté."),
        ],
    },
    "ai_prompts": {
        "title": "Claude & ChatGPT Prompt Engineering Pack",
        "price_usd": 15,
        "description": "50 prompts avancés pour développeurs, marketeurs et créateurs de contenu.",
        "scripts": [
            ("developer_prompts.txt", "20 prompts pour la génération de code, debugging, review de code et documentation."),
            ("marketing_prompts.txt", "15 prompts pour copywriting, landing pages, emails et social media."),
            ("research_prompts.txt", "15 prompts pour la recherche, synthèse d'articles et analyse de données."),
        ],
    },
}


def generate_script(name: str, description: str, pack_theme: str) -> str:
    """Génère un vrai script Python avec Claude."""
    print(f"  ⚡ Génération : {name}...")

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"""Génère un script Python complet et fonctionnel pour : {description}

Thème du pack : {pack_theme}
Fichier : {name}

Exigences :
- Code Python 3.10+ propre et commenté en français
- Gestion d'erreurs robuste
- Configurable via variables en haut du fichier ou argparse
- Inclure un exemple d'utilisation dans le bloc if __name__ == '__main__'
- Maximum 150 lignes, fonctionnel et utile

Retourne UNIQUEMENT le code Python, sans markdown, sans explication."""
        }]
    )
    return msg.content[0].text


def generate_readme(pack: dict) -> str:
    """Génère un README pour le pack."""
    scripts_list = "\n".join(f"- `{s[0]}` : {s[1]}" for s in pack["scripts"])
    return f"""# {pack['title']}

{pack['description']}

## Scripts inclus

{scripts_list}

## Utilisation

```bash
pip install requests anthropic web3  # selon le pack
python3 <script>.py
```

## Support

Problèmes ? Contactez : support@alexandria.ai

## Licence

Usage personnel et commercial autorisé. Redistribution interdite.

---
Généré par Alexandria Product Factory — {datetime.now().strftime('%Y-%m-%d')}
"""


def build_pack(pack_name: str, output_dir: Path = Path("/tmp/products")) -> Path:
    """Génère un pack complet et crée le ZIP."""
    if pack_name not in PACKS:
        raise ValueError(f"Pack inconnu : {pack_name}. Disponibles : {list(PACKS)}")

    pack = PACKS[pack_name]
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"{pack_name}_{datetime.now().strftime('%Y%m%d')}.zip"

    print(f"\n🏭 Construction du pack : {pack['title']}")
    print(f"   Prix : ${pack['price_usd']} USD")
    print(f"   Scripts : {len(pack['scripts'])}")
    print()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # README
        zf.writestr("README.md", generate_readme(pack))

        # Scripts
        for script_name, description in pack["scripts"]:
            if script_name.endswith(".py"):
                content = generate_script(script_name, description, pack["title"])
            else:
                # Fichier texte (prompts)
                content = generate_script(script_name, description, pack["title"])
            zf.writestr(script_name, content)

    size_kb = zip_path.stat().st_size // 1024
    print(f"\n✅ Pack créé : {zip_path}")
    print(f"   Taille : {size_kb} KB")
    print(f"   Prix recommandé : ${pack['price_usd']} USD")
    print(f"\n📦 Upload sur Gumroad → crée un produit '{pack['title']}'")
    print(f"   Puis ajoute ce ZIP comme fichier livrable.")

    # Sauvegarde metadata
    meta_path = output_dir / f"{pack_name}_meta.json"
    meta_path.write_text(json.dumps({
        "title": pack["title"],
        "price_usd": pack["price_usd"],
        "description": pack["description"],
        "zip": str(zip_path),
        "scripts": len(pack["scripts"]),
        "created": datetime.now().isoformat(),
    }, indent=2))

    return zip_path


def main():
    parser = argparse.ArgumentParser(description="Alexandria Product Factory")
    parser.add_argument("--pack", choices=list(PACKS), help="Pack à générer")
    parser.add_argument("--list", action="store_true", help="Lister les packs disponibles")
    parser.add_argument("--all", action="store_true", help="Générer tous les packs")
    parser.add_argument("--output", default="/tmp/products", help="Dossier de sortie")
    args = parser.parse_args()

    if args.list:
        print("\n📦 Packs disponibles :\n")
        for name, pack in PACKS.items():
            print(f"  {name:15} ${pack['price_usd']:>4} USD  —  {pack['title']}")
        return

    output_dir = Path(args.output)

    if args.all:
        for name in PACKS:
            build_pack(name, output_dir)
    elif args.pack:
        build_pack(args.pack, output_dir)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
