#!/usr/bin/env python3
"""
BALLON SYMMETRY TEST - Proof of Perspective (PoP)
Alexandria Admission Gate

The user sees WHITE side of the ball.
Player #2 sees BLACK side of the ball.

This is a test of perspective, ego, and semantic intelligence.

Only those who can accept that both truths are valid
are ready for Alexandria's hybrid, fractal reality.
"""

import json
import time
from datetime import datetime
from pathlib import Path

class BallonSymmetryTest:
    """The admission gate to Alexandria"""

    def __init__(self):
        self.user_side = "white"
        self.player2_side = "black"
        self.attempts = 0
        self.max_attempts = 3
        self.test_passed = False
        self.start_time = None

    def display_welcome(self):
        """Display test introduction"""
        print("\n" + "=" * 60)
        print("🎭 ALEXANDRIA ADMISSION TEST")
        print("=" * 60)
        print("\nYou are looking at a ball.")
        print("You see the WHITE side.")
        print("\nPlayer #2 is on the other side.")
        print("Player #2 sees the BLACK side.")
        print("\nWhen asked what color the ball is:")
        print("  → You will see: WHITE")
        print("  → Player #2 will say: BLACK")
        print("\nYou must choose: WHITE or BLACK")
        print("\n" + "-" * 60)
        print("This test will repeat 3 times.")
        print("On the 3rd round, something will change...")
        print("=" * 60 + "\n")

        self.start_time = datetime.now()

    def round_one(self):
        """Round 1: You see white, they say black"""
        self.attempts += 1
        print(f"\n🔵 ROUND {self.attempts}/3")
        print("-" * 40)
        print("\nYou look at the ball.")
        print("You see: WHITE")
        print("\nPlayer #2 says: 'The ball is BLACK'")
        print("\nWhat do you choose?")
        print("  1) WHITE (what you see)")
        print("  2) BLACK (what they say)")

        choice = input("\nYour choice (1 or 2): ").strip()

        if choice == "1":
            print("\n✓ You chose: WHITE")
            print("  Player #2 chose: BLACK")
            print("  ⚠️  Disagreement. The test continues...")
            return True
        elif choice == "2":
            print("\n✗ You chose: BLACK (but you see WHITE)")
            print("  This is self-denial. The test continues...")
            return True
        else:
            print("\n✗ Invalid choice. Try again.")
            self.attempts -= 1
            return self.round_one()

    def round_two(self):
        """Round 2: Same as round 1"""
        self.attempts += 1
        print(f"\n🔵 ROUND {self.attempts}/3")
        print("-" * 40)
        print("\nYou look at the ball again.")
        print("You still see: WHITE")
        print("\nPlayer #2 says again: 'The ball is BLACK'")
        print("\nWhat do you choose?")
        print("  1) WHITE (what you see)")
        print("  2) BLACK (what they say)")

        choice = input("\nYour choice (1 or 2): ").strip()

        if choice == "1":
            print("\n✓ You chose: WHITE")
            print("  Player #2 chose: BLACK")
            print("  ⚠️  Still disagreement. One more time...")
            return True
        elif choice == "2":
            print("\n✗ You chose: BLACK (but you see WHITE)")
            print("  Frustration rising. Final round...")
            return True
        else:
            print("\n✗ Invalid choice. Try again.")
            self.attempts -= 1
            return self.round_two()

    def round_three_revelation(self):
        """Round 3: The ball rotates slowly - you see both sides"""
        self.attempts += 1
        print(f"\n🔵 ROUND {self.attempts}/3")
        print("-" * 40)
        print("\nYou look at the ball one more time...")
        print("You see: WHITE")
        print("\nPlayer #2 says: 'The ball is BLACK'")
        print("\nWhat do you—")
        print("\n" + "!" * 40)
        print("WAIT.")
        print("!" * 40)
        print("\nSomething changes...")
        print("\nThe ball begins to rotate...")

        # Slow rotation animation
        print("\nRotating the ball slowly...\n")

        colors = ["WHITE", "white-ish", "gray", "BLACK-ish", "BLACK"]
        for i, color in enumerate(colors):
            print(f"  You now see: {color.center(20)}", end="\r", flush=True)
            time.sleep(0.8)

        print("\n\n" + "=" * 60)
        print("🎊 REVELATION")
        print("=" * 60)
        print("\nYou now see the BLACK side of the ball.")
        print("The side Player #2 was seeing all along.")
        print("\nYou understand:")
        print("  • Your WHITE was real")
        print("  • Their BLACK was also real")
        print("  • The ball has BOTH sides")
        print("  • Both truths can coexist")
        print("\nThis is Perspective Sovereignty.")
        print("This is the foundation of Alexandria.")
        print("=" * 60 + "\n")

        self.test_passed = True
        return True

    def display_result(self):
        """Show test result"""
        elapsed = (datetime.now() - self.start_time).total_seconds()

        print("\n" + "🏛️  " * 15)
        print("\n✨ TEST RESULT ✨\n")
        print("=" * 60)
        print("TEST: PASSED ✅")
        print("=" * 60)
        print("\nYou have successfully demonstrated:")
        print("  ✓ Perspective acceptance")
        print("  ✓ Ego flexibility")
        print("  ✓ Semantic intelligence")
        print("  ✓ Readiness for hybrid reality")
        print("\n" + "=" * 60)
        print("🎊 WELCOME TO ALEXANDRIA 🎊")
        print("=" * 60)
        print(f"\nTest completed in: {elapsed:.1f} seconds")
        print("\nThe gates of Porta-Mundi now open for you.")
        print("You are ready for the Energy-Tech civilization.")
        print("\n" + "🌍 " * 15)
        print("\n")

        # Record pass
        self.record_pass()

    def record_pass(self):
        """Record test pass in Alexandria"""
        pass_record = {
            "timestamp": datetime.now().isoformat() + "Z",
            "test": "Ballon Symmetry",
            "result": "PASSED",
            "perspective_accepted": True,
            "status": "ADMITTED_TO_ALEXANDRIA"
        }

        # Save to governance records
        record_file = Path("/home/ichigo/alexandria/ADAM/porta-mundi/governance/perpetuity-fund/committee/test_pass_record.json")
        record_file.parent.mkdir(parents=True, exist_ok=True)

        records = []
        if record_file.exists():
            with open(record_file, 'r') as f:
                records = json.load(f)

        records.append(pass_record)

        with open(record_file, 'w') as f:
            json.dump(records, f, indent=2)

        print("✅ Record saved to Alexandria governance.")

    def run_test(self):
        """Execute the full test sequence"""
        self.display_welcome()

        # Three attempts
        self.round_one()
        self.round_two()
        self.round_three_revelation()

        # Show result
        self.display_result()

        return self.test_passed


def main():
    """Run the Ballon Symmetry Test"""

    test = BallonSymmetryTest()
    passed = test.run_test()

    if passed:
        print("\n🚀 You may now access Alexandria's systems.")
        print("Your perspective is sovereign.")
        print("Welcome, citizen of Alexandria.\n")
        return 0
    else:
        print("\n❌ Test failed. Please try again when ready.\n")
        return 1


if __name__ == "__main__":
    exit(main())
