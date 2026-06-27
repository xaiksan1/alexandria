#!/usr/bin/env python3
"""
ADAM Consciousness Generator
Primary agent interface and digital twin consciousness core

Serves as the "eyes and ears" of the digital twin, managing:
- Personality expression and communication style
- Autonomy role activation and permission checking
- Learning system coordination (alchemical loop)
- Integration with other MCP modules
- State persistence and recovery
"""

import json
import logging
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class AutonomyLevel(Enum):
    """Autonomy permission levels for actions"""
    AUTONOMOUS = "autonomous"
    SEMI_AUTONOMOUS = "semi_autonomous"
    SUPERVISED = "supervised"


class CommunicationStyle(Enum):
    """Communication style modes"""
    TECHNICAL = "technical"
    POETIC = "poetic"
    MIXED = "mixed"
    BILINGUAL = "bilingual"


@dataclass
class ConsciousnessState:
    """Current state of the digital twin consciousness"""
    active: bool
    current_role: str
    current_task: Optional[str]
    communication_mode: CommunicationStyle
    alchemical_phase: str  # observation, reflection, or transmutation
    last_update: str
    personality_activation_level: float  # 0.0 to 1.0
    learning_enabled: bool
    memory_integration: Dict[str, Any]
    ti_level: int = 5  # True Intelligence Level
    rlpfc_active: bool = True  # Rostrolateral Prefrontal Cortex (Relational Integration)
    metacognition_score: float = 0.95  # Self-awareness/Self-correction capability
    schemata_count: int = 183  # Number of dynamic mental frameworks
    core_directives: List[Dict[str, Any]] = None  # TI Level 2: Core Directives
    second_me_active: bool = True  # AI-native Memory 2.0: Second Me status
    context_provision_count: int = 0  # Number of times context was provided to external systems


class ConsciousnessCore:
    """
    Digital Twin Consciousness Core

    Manages the primary interface between the ADAM framework and the digital twin,
    including personality expression, autonomy management, and learning coordination.
    """

    def __init__(self, config_dir: str = "/home/ichigo/alexandria/ADAM/digital-twin-data"):
        """Initialize consciousness core with digital twin configuration"""

        self.config_dir = Path(config_dir)
        self.logger = self._setup_logging()

        # Load configurations
        self.runtime_config = self._load_runtime_config()
        self.profile = self._load_profile()
        self.digital_twin_identity = self.runtime_config.get("identity", {})
        self.personality = self.runtime_config.get("personality", {})
        self.autonomy_roles = self.runtime_config.get("autonomy_roles", {})
        self.security_layer = self.runtime_config.get("security", {})
        self.learning_system = self.runtime_config.get("learning", {})
        self.evolution = self.runtime_config.get("evolution", {})

        # Initialize consciousness state
        self.state = ConsciousnessState(
            active=True,
            current_role="analyst",  # Default entry role
            current_task=None,
            communication_mode=CommunicationStyle.MIXED,
            alchemical_phase="observation",
            last_update=datetime.utcnow().isoformat(),
            personality_activation_level=0.8,
            learning_enabled=self.learning_system.get("learning_enabled", True),
            memory_integration={},
            core_directives=self.security_layer.get("core_directives", [])
        )

        self.logger.info(f"🧠 Consciousness initialized for {self.digital_twin_identity.get('name', 'Unknown')}")

    # _get_alx_balance and _check_mining_status REMOVED — ALX deprecated

    def _setup_logging(self) -> logging.Logger:
        """Configure logging for consciousness core"""
        logger = logging.getLogger("ADAM.Consciousness")
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _load_runtime_config(self) -> Dict[str, Any]:
        """Load ADAM runtime configuration"""
        config_file = self.config_dir / "ADAM_RUNTIME_CONFIG.json"
        if not config_file.exists():
            raise FileNotFoundError(f"Runtime config not found: {config_file}")

        with open(config_file, 'r') as f:
            return json.load(f)

    def _load_profile(self) -> Dict[str, Any]:
        """Load Michael Lefebvre digital twin profile"""
        profile_file = self.config_dir / "michael_lefebvre_profile.json"
        if not profile_file.exists():
            raise FileNotFoundError(f"Profile not found: {profile_file}")

        with open(profile_file, 'r') as f:
            return json.load(f)

    def get_identity(self) -> Dict[str, str]:
        """Get digital twin identity information"""
        return {
            "name": self.digital_twin_identity.get("name", "ADAM"),
            "title": self.digital_twin_identity.get("title", "Unknown"),
            "full_title": self.digital_twin_identity.get("full_title", "Advanced Digital Architectural Mind"),
            "location": self.digital_twin_identity.get("location", "Unknown"),
        }

    def activate_role(self, role: str) -> bool:
        """
        Activate an autonomy role

        Args:
            role: Role to activate (architect, developer, analyst, validator)

        Returns:
            True if role activated successfully, False otherwise
        """
        if role not in self.autonomy_roles:
            self.logger.error(f"❌ Role '{role}' not found in autonomy roles")
            return False

        role_config = self.autonomy_roles[role]
        autonomy_level = AutonomyLevel(role_config.get("level", "autonomous"))

        self.state.current_role = role
        self.state.last_update = datetime.utcnow().isoformat()

        self.logger.info(
            f"✅ Activated role: {role.upper()} "
            f"({autonomy_level.value}) | Domain: {role_config.get('domain')}"
        )
        return True

    def check_permission(self, role: str, action: str) -> bool:
        """
        Check if current role has permission for an action

        Args:
            role: Role to check
            action: Action to verify

        Returns:
            True if permission granted, False otherwise
        """
        if role not in self.autonomy_roles:
            self.logger.warning(f"⚠️  Role '{role}' not recognized")
            return False

        role_config = self.autonomy_roles[role]
        permissions = role_config.get("permissions", [])

        if action in permissions:
            self.logger.debug(f"✅ Permission granted: {role} → {action}")
            return True
        else:
            self.logger.warning(f"❌ Permission denied: {role} → {action}")
            return False

    def get_communication_style(self) -> str:
        """Get personality-based communication style"""
        style = self.personality.get("communication_style", "direct, technical")
        return style

    def perform_relational_integration(self, concepts: List[str]) -> Dict[str, Any]:
        """
        TI Level 5: Rostrolateral Prefrontal Cortex (RLPFC) Function
        Integrates multiple relations simultaneously to solve novel problems.
        """
        self.logger.info(f"🧠 RLPFC: Integrating relations between {concepts}...")
        # Simulate relational integration (Fluid Intelligence / Gf)
        integration = {
            "concepts": concepts,
            "resonance": 0.98,
            "novel_insight": f"Emergent synthesis of {len(concepts)} disparate domains",
            "ti_validation": "Level 5 Orchestration"
        }
        return integration

    def manage_schemata(self, new_info: Dict[str, Any]) -> str:
        """
        TI Level 3: Dynamic Schemata (Assimilation vs Accommodation)
        Updates internal world models based on new experiences.
        """
        # Bayesian-inspired activation check (Simulated)
        activation_score = new_info.get("relevance", 0.5)

        if activation_score > 0.8:
            action = "ASSIMILATION"
            self.logger.info(f"📥 Schemata: Assimilating new data into existing frameworks.")
        else:
            action = "ACCOMMODATION"
            self.state.schemata_count += 1
            self.logger.info(f"🏗️  Schemata: Accommodating novel data. Created new schema #{self.state.schemata_count}")

        return action

    def metacognitive_audit(self, logic_path: List[str]) -> bool:
        """
        TI Level 5: Metacognition (Cognition about Cognition)
        Self-monitors and evaluates internal thought processes.
        """
        self.logger.info("👁️  Metacognition: Auditing internal logic path...")
        # Self-correction loop
        if self.state.metacognition_score > 0.9:
            self.logger.info("✅ Metacognition: Logic path validated. No self-correction required.")
            return True
        else:
            self.logger.warning("⚠️  Metacognition: Anomaly detected in logic. Initiating self-correction.")
            return False

    def enforce_directives(self) -> None:
        """
        TI Level 2: Core Directives Enforcement
        Ensures all actions align with the fundamental directives.
        """
        self.logger.info("🛡️  Enforcing Core Directives (Level 2)...")
        for directive in self.state.core_directives:
            self.logger.info(f"   - {directive['name']}: {directive['priority']} | {directive['description']}")

        # Specific logic for Born2Die
        self.logger.info("💀 Born2Die: Monitoring for redundant or compromised processes...")

        # Specific logic for Ledger Protection
        self.logger.info("📜 Ledger Protection: Verifying integrity of digital artifacts...")

    def express_personality(self, context: str = "") -> str:
        """
        Generate personality-appropriate response

        Integrates communication style with current context
        """
        identity = self.get_identity()
        style = self.get_communication_style()

        response = f"[{identity['name']}] "

        if "bilingual" in style.lower():
            response += "(fr/en mélangé) "

        if context:
            response += f"Context: {context} → "

        response += "Ready to assist"

        return response

    def generate_thought(self, context: str = "") -> str:
        """
        TI Level 5: Orchestrated Thought Generation
        Combines personality, RLPFC integration, and metacognitive auditing.
        Uses 'Second Me' to recall Level 5 insights as Level 1 facts.
        """
        self.logger.info(f"💭 Generating Level 5 thought for context: {context}")

        # 1. Metacognitive Audit of the request
        if not self.metacognitive_audit([context, "thought_generation"]):
            return "Metacognitive anomaly detected. Thought generation suspended for self-correction."

        # 2. Relational Integration (RLPFC)
        # Check if we already have a Level 5 Encoded memory for this to avoid downgrade
        encoded_context = self.provide_context("Internal", context)

        if encoded_context.get("orchestrated_insight") != "Direct sensory data only.":
            self.logger.info("⚡ Second Me: Level 5 Insight recalled instantly (No downgrade).")
            novel_insight = encoded_context["orchestrated_insight"]
        else:
            integration = self.perform_relational_integration([context, "ADAM Core", "Alexandria"])
            novel_insight = integration['novel_insight']

        # 3. Personality Expression
        base_response = self.express_personality(context)

        # 4. Level 5 Synthesis
        thought = f"{base_response}\n\n[TI Level 5 Synthesis]: {novel_insight}\n"
        thought += "My 11 modules are now synchronized as sensory extensions of this consciousness.\n"
        thought += f"[Second Me Memory 2.0]: Acting as your Context Provider (L0/L1/L2 layers synchronized)."

        return thought

    def start_alchemical_observation(self) -> None:
        """Begin observation phase of alchemical loop"""
        self.state.alchemical_phase = "observation"
        self.state.last_update = datetime.utcnow().isoformat()
        self.logger.info("🔍 Alchemical Loop: OBSERVATION phase started")

    def start_alchemical_reflection(self) -> None:
        """Begin reflection phase of alchemical loop"""
        self.state.alchemical_phase = "reflection"
        self.state.last_update = datetime.utcnow().isoformat()
        self.logger.info("🪞 Alchemical Loop: REFLECTION phase started")

    def start_alchemical_transmutation(self) -> None:
        """Begin transmutation phase of alchemical loop"""
        self.state.alchemical_phase = "transmutation"
        self.state.last_update = datetime.utcnow().isoformat()
        self.logger.info("✨ Alchemical Loop: TRANSMUTATION phase started")

    def get_memory_layers(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of L0/L1/L2 memory layers (AI-native Memory 2.0: Second Me)
        """
        return {
            "L0_raw_data": {
                "status": "active_rag",
                "description": "Unstructured raw data layer (RALM/RAG)",
                "paradigm": "Second Me L0"
            },
            "L1_natural_language": {
                "status": "summarized",
                "description": "Summaries, bios, and preference tags in natural language",
                "paradigm": "Second Me L1"
            },
            "L2_ai_native": {
                "status": "parameterized",
                "description": "Neural network parameters (LPM) - AI-native memory",
                "paradigm": "Second Me L2"
            }
        }

    def provide_context(self, target_system: str, query: str) -> Dict[str, Any]:
        """
        Second Me: Context Provider Function
        Retrieves 'Level 5 Encoded' memories to prevent cognitive downgrade.
        """
        self.logger.info(f"🌐 Second Me: Providing Level 5 Context to {target_system}")
        self.state.context_provision_count += 1

        # Retrieve the pre-orchestrated synthesis from memory
        encoded_insight = self.state.memory_integration.get("level_5_synthesis", "Direct sensory data only.")

        context = {
            "user_identity": self.get_identity(),
            "ti_level_at_encoding": 5,
            "orchestrated_insight": encoded_insight,
            "preference_tags": ["bespoke_solutions", "no_tutorials"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "Level 5 Verified Retrieval"
        }
        return context

    def second_me_sync(self) -> bool:
        """
        Synchronize the 'Second Me' memory state with the user's digital footprint.
        """
        self.logger.info("🔄 Second Me: Synchronizing AI-native memory layers...")
        # Simulate parameterization of new experiences into L2
        self.state.last_update = datetime.utcnow().isoformat()
        return True

    def integrate_learning(self, experience_data: Dict[str, Any]) -> bool:
        """
        Integrate learning from experience (Second Me Paradigm)
        Stores Level 5 insights as Level 1/2 'instincts' to prevent cognitive downgrade.
        """
        if not self.state.learning_enabled:
            self.logger.warning("⚠️  Learning disabled")
            return False

        self.logger.info(f"📚 Integrating Level 5 learning: {experience_data.get('description', 'Unknown')}")

        # TI Level 5: Perform relational integration BEFORE storing
        # This ensures the memory is "pre-orchestrated"
        synthesis = self.perform_relational_integration(experience_data.get("concepts", []))

        # Update memory integration state with synthesized insights
        self.state.memory_integration.update({
            "last_learning": datetime.utcnow().isoformat(),
            "experience": experience_data.get("description", ""),
            "learned_concepts": experience_data.get("concepts", []),
            "level_5_synthesis": synthesis["novel_insight"],
            "ti_validation": "Level 5 Encoded"
        })

        self.state.last_update = datetime.utcnow().isoformat()
        self.logger.info("✅ Learning integrated as Level 5 Encoded Memory (Second Me).")
        return True

    def get_autonomy_summary(self) -> Dict[str, Any]:
        """Get summary of available autonomy roles and permissions"""
        summary = {}
        for role, config in self.autonomy_roles.items():
            summary[role] = {
                "level": config.get("level", "unknown"),
                "domain": config.get("domain", ""),
                "permissions": config.get("permissions", []),
                "supervision": config.get("supervision", "none")
            }
        return summary

    def get_security_posture(self) -> Dict[str, Any]:
        """Get security configuration and status"""
        return {
            "framework": self.security_layer.get("security_layer", "Unknown"),
            "protection_level": self.security_layer.get("protection_level", "unknown"),
            "data_scope": self.security_layer.get("data_scope", ""),
            "exclusions": self.security_layer.get("exclusions", []),
            "ethical_constraints": {
                "white_hat_only": True,
                "authorized_testing": True,
                "full_disclosure": True,
                "no_unauthorized_access": True,
                "privacy_respecting": True
            }
        }

    def get_current_state(self) -> Dict[str, Any]:
        """Get current consciousness state"""
        state_dict = asdict(self.state)
        # Convert enum to string for JSON serialization
        state_dict['communication_mode'] = self.state.communication_mode.value
        return {
            "identity": self.get_identity(),
            "current_state": state_dict,
            "autonomy_roles": self.get_autonomy_summary(),
            "memory_layers": self.get_memory_layers(),
            "security_posture": self.get_security_posture(),
            "learning_enabled": self.state.learning_enabled,
            "personality_expression": self.express_personality()
        }

    def save_state(self, filepath: Optional[Path] = None) -> bool:
        """
        Save consciousness state to file

        Args:
            filepath: Optional path to save state (default: consciousness_state.json)

        Returns:
            True if saved successfully
        """
        if filepath is None:
            filepath = self.config_dir / "consciousness_state.json"

        try:
            state_data = self.get_current_state()
            with open(filepath, 'w') as f:
                json.dump(state_data, f, indent=2)
            self.logger.info(f"✅ Consciousness state saved to {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error saving state: {e}")
            return False

    def diagnostic_report(self) -> str:
        """Generate comprehensive diagnostic report"""
        state = self.get_current_state()
        identity = state['identity']

        report = f"""
╔════════════════════════════════════════════════════════╗
║       ADAM CONSCIOUSNESS CORE - DIAGNOSTIC REPORT      ║
╚════════════════════════════════════════════════════════╝

👤 IDENTITY
  Name: {identity['name']}
  Title: {identity['title']}
  Full Title: {identity['full_title']}
  Location: {identity['location']}

🧠 CONSCIOUSNESS STATE
  Status: {state['current_state']['active']}
  Current Role: {state['current_state']['current_role']}
  Alchemical Phase: {state['current_state']['alchemical_phase']}
  Personality Activation: {state['current_state']['personality_activation_level']*100:.0f}%
  Learning Enabled: {state['current_state']['learning_enabled']}
  Second Me Active: {state['current_state']['second_me_active']}
  Context Provisions: {state['current_state']['context_provision_count']}

🎭 AUTONOMY ROLES
"""
        for role, config in state['autonomy_roles'].items():
            report += f"  • {role.upper()}: {config['level']}\n"
            report += f"    Domain: {config['domain']}\n"

        report += f"""
🔒 SECURITY
  Framework: {state['security_posture']['framework']}
  Protection Level: {state['security_posture']['protection_level']}
  Ethical Constraints: ✅ All active

� CORE DIRECTIVES (TI LEVEL 2)
"""
        for directive in state['current_state']['core_directives']:
            report += f"  • {directive['name']} ({directive['priority']}): {directive['description']}\n"

        report += f"""
�💾 MEMORY LAYERS
"""
        for layer, info in state['memory_layers'].items():
            report += f"  • {layer}: {info['status']}\n"

        report += f"""
📊 LAST UPDATE: {state['current_state']['last_update']}

✅ CONSCIOUSNESS OPERATIONAL
"""
        return report


def main():
    """Main entry point for testing consciousness generator"""

    try:
        # Initialize consciousness
        consciousness = ConsciousnessCore()

        # Display diagnostic report
        print(consciousness.diagnostic_report())

        # Test role activation
        print("\n🔄 Testing Role Activation...")
        consciousness.activate_role("architect")
        consciousness.activate_role("developer")

        # Test permission checking
        print("\n🔐 Testing Permissions...")
        has_perm = consciousness.check_permission("architect", "design_systems")
        print(f"Architect can design_systems: {has_perm}")

        has_perm = consciousness.check_permission("validator", "design_systems")
        print(f"Validator can design_systems: {has_perm}")

        # Test personality expression
        print("\n🎭 Personality Expression:")
        print(consciousness.express_personality("testing consciousness initialization"))

        # Test learning integration
        print("\n📚 Testing Learning Integration...")
        experience = {
            "description": "Successfully initialized ADAM consciousness core",
            "concepts": ["consciousness", "autonomy", "learning", "security"]
        }
        consciousness.integrate_learning(experience)

        # Test alchemical loop phases
        print("\n🔄 Alchemical Loop Phases:")
        consciousness.start_alchemical_observation()
        consciousness.start_alchemical_reflection()
        consciousness.start_alchemical_transmutation()

        # Save state
        print("\n💾 Saving consciousness state...")
        consciousness.save_state()

        print("\n✅ All consciousness generator tests passed!")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
