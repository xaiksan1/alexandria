#!/usr/bin/env python3
"""
MEMBER ONBOARDING INTEGRATION
Bridges admission test → member card generation → governance records

Workflow:
1. ballon-symmetry.py completes and records pass
2. member-onboarding.py detects pass
3. Prompts for member identity details
4. Issues member card via member-card-generator.py
5. Records in governance/perpetuity-fund/committee/
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Import member card generator
sys.path.insert(0, str(Path(__file__).parent))
from member_card_generator import MemberCardGenerator


class MemberOnboarding:
    """Orchestrates admission → member card issuance"""

    def __init__(self):
        self.test_pass_file = Path("/home/ichigo/alexandria/ADAM/porta-mundi/governance/perpetuity-fund/committee/test_pass_record.json")
        self.member_registry_file = Path("/home/ichigo/alexandria/ADAM/porta-mundi/governance/perpetuity-fund/committee/member-registry.json")
        self.onboarding_log_file = Path("/home/ichigo/alexandria/ADAM/porta-mundi/governance/perpetuity-fund/committee/onboarding-log.json")

        self.card_generator = MemberCardGenerator()
        self.load_onboarding_log()

    def load_onboarding_log(self):
        """Load or initialize onboarding log"""
        if self.onboarding_log_file.exists():
            with open(self.onboarding_log_file, 'r') as f:
                self.onboarding_log = json.load(f)
        else:
            self.onboarding_log = {
                "sessions": [],
                "total_admitted": 0,
                "total_issued": 0,
                "active_members": [],
                "last_updated": datetime.now().isoformat()
            }
            self.save_onboarding_log()

    def save_onboarding_log(self):
        """Persist onboarding log"""
        self.onboarding_log["last_updated"] = datetime.now().isoformat()
        with open(self.onboarding_log_file, 'w') as f:
            json.dump(self.onboarding_log, f, indent=2)

    def get_latest_admission(self) -> Optional[Dict[str, Any]]:
        """Retrieve latest admission test pass"""
        if not self.test_pass_file.exists():
            return None

        with open(self.test_pass_file, 'r') as f:
            records = json.load(f)

        if records:
            return records[-1]  # Latest record
        return None

    def check_unprocessed_admissions(self) -> list:
        """Find admission tests not yet converted to member cards"""
        if not self.test_pass_file.exists():
            return []

        with open(self.test_pass_file, 'r') as f:
            records = json.load(f)

        # Get already processed test timestamps
        processed = set(session.get("test_timestamp") for session in self.onboarding_log.get("sessions", []))

        # Return unprocessed tests
        return [r for r in records if r.get("timestamp") not in processed]

    def interactive_member_registration(self, admission_test: Dict[str, Any]) -> Dict[str, str]:
        """
        Interactively collect member identity details

        Returns member name and identity role
        """

        print("\n" + "=" * 60)
        print("🎭 ALEXANDRIA MEMBER REGISTRATION")
        print("=" * 60)

        print(f"\nTest Passed: {admission_test.get('test', 'Ballon Symmetry')}")
        print(f"Perspective Accepted: {admission_test.get('perspective_accepted')}")

        # Get member name
        while True:
            name = input("\nEnter your full name: ").strip()
            if len(name) >= 2:
                break
            print("⚠️  Please enter a valid name.")

        # Get identity role
        identity_options = {
            "1": "Architect Identity",
            "2": "Engineer Identity",
            "3": "Scholar Identity",
            "4": "Foundling Identity",
            "5": "Observer Identity"
        }

        print("\nSelect your Identity Role:")
        for key, value in identity_options.items():
            print(f"  {key}) {value}")

        choice = input("\nYour choice (1-5) [1]: ").strip() or "1"
        identity = identity_options.get(choice, identity_options["1"])

        # Confirm
        print(f"\n✓ Name: {name}")
        print(f"✓ Identity: {identity}")

        return {
            "name": name,
            "identity": identity
        }

    def process_admission_to_member_card(self, admission_test: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process single admission test to member card issuance

        Args:
            admission_test: Result from ballon-symmetry.py test

        Returns:
            Issued member card or None if cancelled
        """

        # Check if already processed
        existing_session = next(
            (s for s in self.onboarding_log.get("sessions", []) if s.get("test_timestamp") == admission_test.get("timestamp")),
            None
        )

        if existing_session:
            print(f"⚠️  This admission already processed: {existing_session.get('member_id')}")
            return None

        # Interactive registration
        member_info = self.interactive_member_registration(admission_test)

        # Generate member card
        member_card = self.card_generator.issue_member_card(
            name=member_info["name"],
            identity=member_info["identity"],
            test_result=admission_test,
            timestamp=datetime.now().isoformat() + "Z"
        )

        # Generate HTML card file
        files = self.card_generator.generate_member_card_files(member_card)

        # Record onboarding session
        session = {
            "member_id": member_card["member_id"],
            "name": member_info["name"],
            "identity": member_info["identity"],
            "test_timestamp": admission_test.get("timestamp"),
            "member_card_issued": datetime.now().isoformat() + "Z",
            "trust_level": member_card["trust_level"],
            "ninja_modules": member_card["ninja_modules"],
            "card_files": files,
            "status": "ACTIVE"
        }

        self.onboarding_log["sessions"].append(session)
        self.onboarding_log["total_admitted"] += 1
        self.onboarding_log["total_issued"] += 1
        self.onboarding_log["active_members"].append(member_card["member_id"])
        self.save_onboarding_log()

        print("\n" + "=" * 60)
        print("✅ MEMBER CARD ISSUED")
        print("=" * 60)
        print(f"Member ID: {member_card['member_id']}")
        print(f"Trust Level: {member_card['trust_level']}")
        print(f"Ninja Modules: {', '.join(member_card['ninja_modules'])}")
        print(f"\nCard Files:")
        print(f"  JSON: {files['json_file']}")
        print(f"  HTML: {files['html_file']}")
        print("\n🎊 Welcome to Alexandria! 🎊\n")

        return member_card

    def process_batch(self) -> int:
        """Process all unprocessed admissions"""

        unprocessed = self.check_unprocessed_admissions()

        if not unprocessed:
            print("✓ No unprocessed admissions found.")
            return 0

        print(f"\n📋 Found {len(unprocessed)} unprocessed admission(s)\n")

        issued_count = 0
        for admission in unprocessed:
            try:
                if self.process_admission_to_member_card(admission):
                    issued_count += 1
            except KeyboardInterrupt:
                print("\n⚠️  Processing interrupted.")
                break
            except Exception as e:
                print(f"\n❌ Error processing admission: {e}")
                continue

        return issued_count

    def display_member_registry(self):
        """Display current member registry"""

        self.card_generator.load_registry()
        registry = self.card_generator.registry

        print("\n" + "=" * 60)
        print("📊 ALEXANDRIA MEMBER REGISTRY")
        print("=" * 60)
        print(f"\nTotal Members: {registry['total_members']}")
        print(f"Total Issued Cards: {len(registry['issued_cards'])}")

        print("\nTrust Level Distribution:")
        stats = self.card_generator.get_member_stats()
        for level, count in stats['trust_level_distribution'].items():
            print(f"  {level}: {count}")

        if registry['issued_cards']:
            print("\nRecent Members:")
            for member_id in registry['issued_cards'][-5:]:
                member = registry['members'].get(member_id)
                if member:
                    print(f"  • {member['name']} ({member['trust_level']})")

        print()

    def generate_governance_report(self) -> str:
        """Generate governance report for perpetuity fund"""

        self.load_onboarding_log()
        self.card_generator.load_registry()

        total_members = self.card_generator.registry['total_members']
        active_members = len(self.onboarding_log.get('active_members', []))

        trust_distribution = self.card_generator.get_member_stats()['trust_level_distribution']

        report = f"""# Alexandria Member Governance Report

**Date**: {datetime.now().isoformat()}

## Summary

- **Total Members Admitted**: {total_members}
- **Active Members**: {active_members}
- **Onboarding Sessions**: {len(self.onboarding_log.get('sessions', []))}

## Trust Level Distribution

"""

        for level, count in trust_distribution.items():
            percentage = (count / total_members * 100) if total_members > 0 else 0
            report += f"- **{level}**: {count} ({percentage:.1f}%)\n"

        report += f"""

## Member Rights & Privileges

### ALPHA_ARCHITECT
- Full Alexandria system access
- Governance committee participation
- Ninja module suite: SYS_OPT, NET_TUNNEL, STEGO_X
- Energy-tech resource allocation

### BETA_ENGINEER
- Extended system access
- Project participation
- Ninja modules: NET_TUNNEL, STEGO_X
- Developer documentation access

### GAMMA_SCHOLAR
- Learning resources access
- Research participation
- Ninja module: STEGO_X
- Community contribution

### FOUNDLING
- Observer access
- Mentorship program
- Foundation building resources

### OBSERVER
- Limited access
- Learning resources
- Monitoring capability

## Perpetuity Fund Impact

Each new member contributes to Alexandria's sustainability through:
1. **Perspective Sovereignty**: Validates hybrid reality consciousness
2. **Semantic Intelligence**: Demonstrates linguistic sophistication
3. **Governance Participation**: Democratic oversight of 25% perpetuity allocation
4. **Knowledge Capital**: Adds to collective intelligence

---

*Report generated by Member Onboarding System*
*Porta-Mundi · Alexandria Governance*
"""

        return report


def main():
    """Main entry point"""

    import argparse

    parser = argparse.ArgumentParser(description="Alexandria Member Onboarding")
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Process all unprocessed admissions"
    )
    parser.add_argument(
        "--registry",
        action="store_true",
        help="Display member registry"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate governance report"
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Process latest admission test"
    )

    args = parser.parse_args()

    onboarding = MemberOnboarding()

    if args.batch:
        issued = onboarding.process_batch()
        print(f"\n✅ Issued {issued} member card(s)")

    elif args.registry:
        onboarding.display_member_registry()

    elif args.report:
        report = onboarding.generate_governance_report()
        print(report)

        # Save report
        report_file = Path("/home/ichigo/alexandria/ADAM/porta-mundi/governance/perpetuity-fund/committee/member-governance-report.md")
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"\n✅ Report saved to {report_file}")

    elif args.latest:
        latest = onboarding.get_latest_admission()
        if latest:
            print(f"Latest admission: {latest.get('timestamp')}")
            onboarding.process_admission_to_member_card(latest)
        else:
            print("No admission tests found.")

    else:
        # Default: check for unprocessed and offer to process
        unprocessed = onboarding.check_unprocessed_admissions()

        if unprocessed:
            print(f"Found {len(unprocessed)} unprocessed admission(s)")
            response = input("Process now? (y/n): ").strip().lower()
            if response == 'y':
                issued = onboarding.process_batch()
                print(f"\n✅ Issued {issued} member card(s)")
        else:
            print("✓ All admissions processed. No pending onboarding.")

        onboarding.display_member_registry()


if __name__ == "__main__":
    main()
